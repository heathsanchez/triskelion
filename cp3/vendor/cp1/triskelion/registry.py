from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .models import Capability


class CapabilityRegistry:
    def __init__(self, path: Path):
        self.path = path
        self.capabilities: dict[str, Capability] = {}
        if path.exists():
            payload = json.loads(path.read_text())
            self.capabilities = {
                item["capability_id"]: Capability.from_dict(item)
                for item in payload.get("capabilities", [])
            }

    @staticmethod
    def artifact_hash(capability: Capability) -> str:
        blob = json.dumps(capability.artifact, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode()).hexdigest()

    def save(self) -> None:
        payload = {
            "schema_version": "1.0",
            "capabilities": [
                self.capabilities[key].to_dict() for key in sorted(self.capabilities)
            ],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def install(self, capability: Capability) -> None:
        capability.artifact_sha256 = self.artifact_hash(capability)
        capability.status = "installed"
        capability.enabled = True
        self.capabilities[capability.capability_id] = capability
        self.save()

    def enable(self, capability_id: str) -> None:
        cap = self.capabilities[capability_id]
        if cap.status == "revoked":
            raise ValueError("revoked capability cannot be enabled")
        cap.enabled = True
        cap.status = "installed"
        self.save()

    def disable(self, capability_id: str) -> None:
        cap = self.capabilities[capability_id]
        cap.enabled = False
        cap.status = "inactive"
        self.save()

    def uninstall(self, capability_id: str) -> Capability:
        cap = self.capabilities.pop(capability_id)
        self.save()
        return cap

    def revoke(self, capability_id: str, evidence: dict) -> None:
        cap = self.capabilities[capability_id]
        cap.enabled = False
        cap.status = "revoked"
        cap.counterexamples.append(evidence)
        self.save()

    def export(self, capability_id: str, path: Path) -> None:
        cap = self.capabilities[capability_id]
        path.write_text(json.dumps(cap.to_dict(), indent=2, sort_keys=True) + "\n")

    def import_file(self, path: Path) -> Capability:
        cap = Capability.from_dict(json.loads(path.read_text()))
        if cap.artifact_sha256 != self.artifact_hash(cap):
            raise ValueError("artifact hash mismatch")
        self.install(cap)
        return cap
