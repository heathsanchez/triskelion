from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .artifacts import apply_artifact
from .models import Capability, Task
from .registry import CapabilityRegistry
from .scope import matches_scope
from .verifier import PythonSubprocessVerifier


class Runtime:
    def __init__(self, state_dir: Path | str):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.registry = CapabilityRegistry(self.state_dir / "CAPABILITY_REGISTRY.json")
        self.verifier = PythonSubprocessVerifier()
        self.ledger_path = self.state_dir / "DEVELOPMENT_LEDGER.jsonl"
        self.graph_path = self.state_dir / "DEVELOPMENT_GRAPH.json"
        if not self.graph_path.exists():
            self.graph_path.write_text('{"edges": [], "nodes": []}\n')

    def _event(self, event: str, payload: dict[str, Any]) -> None:
        row = {"event": event, "monotonic_ns": time.monotonic_ns(), **payload}
        with self.ledger_path.open("a") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    def _graph_node(self, cap: Capability) -> None:
        graph = json.loads(self.graph_path.read_text())
        graph["nodes"] = [n for n in graph["nodes"] if n.get("id") != cap.capability_id]
        graph["nodes"].append({"id": cap.capability_id, "kind": "capability", "status": cap.status})
        for task_id in cap.acquired_from:
            graph["edges"].append({"from": task_id, "to": cap.capability_id, "type": "DISCOVERED_FROM"})
        for dep in cap.dependencies:
            graph["edges"].append({"from": dep, "to": cap.capability_id, "type": "DEPENDS_ON"})
        self.graph_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n")

    def closure(self, task: Task, scoped: bool = True) -> list[str]:
        applicable = []
        for cap in self.registry.capabilities.values():
            if not cap.enabled or cap.status in {"revoked", "superseded"}:
                continue
            if scoped and not matches_scope(cap.scope, task):
                continue
            applicable.append(cap.capability_id)
        return sorted(applicable)

    def solve(self, task: Task, mode: str = "verified") -> dict[str, Any]:
        source = task.source
        selected: list[str] = []
        if mode == "cold":
            caps: list[Capability] = []
        elif mode == "raw_memory":
            caps = [c for c in self.registry.capabilities.values() if c.enabled]
            caps = [c for c in caps if c.artifact.get("name") == "guard_zero_division"]
        elif mode == "always_on":
            caps = [c for c in self.registry.capabilities.values() if c.enabled]
        elif mode == "verified":
            caps = [self.registry.capabilities[cid] for cid in self.closure(task, scoped=True)]
        else:
            raise ValueError(f"unknown mode: {mode}")
        for cap in sorted(caps, key=lambda c: (c.artifact.get("execution_order", 100), c.capability_id)):
            source = apply_artifact(cap.artifact["name"], source)
            selected.append(cap.capability_id)
        verdict = self.verifier.verify(task, source)
        self._event("solve", {"task_id": task.task_id, "mode": mode, "selected": selected, "verdict": verdict.to_dict()})
        return {"task_id": task.task_id, "mode": mode, "selected": selected, "candidate": source, "verdict": verdict.to_dict()}

    def explain(self, task: Task) -> dict[str, Any]:
        return {"task_id": task.task_id, "applicable_capabilities": self.closure(task), "classification_if_unsolved": "H_OPERATOR"}

    def list_capabilities(self) -> list[dict[str, Any]]:
        return [self.registry.capabilities[k].to_dict() for k in sorted(self.registry.capabilities)]

    def inspect(self, capability_id: str) -> dict[str, Any]:
        return self.registry.capabilities[capability_id].to_dict()

    def install(self, capability: Capability) -> None:
        self.registry.install(capability); self._graph_node(capability)
        self._event("install", {"capability_id": capability.capability_id})

    def disable(self, capability_id: str) -> None:
        self.registry.disable(capability_id); self._event("disable", {"capability_id": capability_id})

    def enable(self, capability_id: str) -> None:
        self.registry.enable(capability_id); self._event("enable", {"capability_id": capability_id})

    def uninstall(self, capability_id: str) -> Capability:
        cap = self.registry.uninstall(capability_id); self._event("uninstall", {"capability_id": capability_id}); return cap

    def verify(self, capability_id: str, tasks: list[Task]) -> dict[str, Any]:
        cap = self.registry.capabilities[capability_id]
        outcomes = []
        for task in tasks:
            source = apply_artifact(cap.artifact["name"], task.source)
            outcomes.append(self.verifier.verify(task, source).to_dict())
        passed = all(o["passed"] for o in outcomes)
        self._event("verify_capability", {"capability_id": capability_id, "passed": passed, "outcomes": outcomes})
        return {"passed": passed, "outcomes": outcomes}

    def compose(self, capability_ids: list[str], task: Task) -> dict[str, Any]:
        source = task.source
        for cid in capability_ids:
            source = apply_artifact(self.registry.capabilities[cid].artifact["name"], source)
        return {"candidate": source, "verdict": self.verifier.verify(task, source).to_dict()}

    def revoke(self, capability_id: str, evidence: dict[str, Any]) -> None:
        self.registry.revoke(capability_id, evidence); self._event("revoke", {"capability_id": capability_id, "evidence": evidence})

    def export_capability(self, capability_id: str, path: Path | str) -> None:
        self.registry.export(capability_id, Path(path))

    def import_capability(self, path: Path | str) -> Capability:
        cap = self.registry.import_file(Path(path)); self._graph_node(cap); return cap

    def replay_lineage(self, capability_id: str) -> list[dict[str, Any]]:
        graph = json.loads(self.graph_path.read_text())
        return [edge for edge in graph["edges"] if edge["to"] == capability_id or edge["from"] == capability_id]

    def ablate(self, capability_id: str, task: Task) -> dict[str, Any]:
        cap = self.registry.capabilities[capability_id]
        was_enabled = cap.enabled
        self.disable(capability_id)
        try:
            return self.solve(task, mode="verified")
        finally:
            if was_enabled:
                self.enable(capability_id)
