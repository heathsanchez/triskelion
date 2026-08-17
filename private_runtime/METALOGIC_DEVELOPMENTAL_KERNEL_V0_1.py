#!/usr/bin/env python3
"""Metalogic Developmental Kernel v0.1

Private prototype of the explicit developmental state machinery behind the public demo.
This is intentionally model-agnostic and verifier-first.

Core law:
  verified invariance -> quotient/compress
  counterexample      -> split/recover distinction

Core loop:
  experience -> residual -> obstruction -> minimal contrast ->
  distinction/representation/operator -> verify -> install -> project -> revise
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Iterable, Optional
import copy
import hashlib
import json


class Status(str, Enum):
    PROVISIONAL = "PROVISIONAL"
    VERIFIED = "VERIFIED"
    REFUTED = "REFUTED"
    OBSTRUCTED = "OBSTRUCTED"
    REVOKED = "REVOKED"
    SUPERSEDED = "SUPERSEDED"


class Kind(str, Enum):
    EXPERIENCE = "EXPERIENCE"
    LAW = "LAW"
    CAPABILITY = "CAPABILITY"
    APPLICABILITY = "APPLICABILITY"
    BOUNDARY = "BOUNDARY"
    OBSTRUCTION = "OBSTRUCTION"
    RESIDUAL = "RESIDUAL"
    REPRESENTATION = "REPRESENTATION"
    LENS = "LENS"
    CONSTRUCTOR = "CONSTRUCTOR"
    DISPOSITION = "DISPOSITION"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    QUOTIENT = "QUOTIENT"
    DEPENDENCY = "DEPENDENCY"


@dataclass(frozen=True)
class Evidence:
    verifier: str
    verdict: str
    payload_hash: str
    protocol_hash: str = ""
    artifact: str = ""


@dataclass
class Node:
    id: str
    kind: Kind
    scope: dict[str, Any] = field(default_factory=dict)
    evidence: list[Evidence] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    invalidators: list[str] = field(default_factory=list)
    status: Status = Status.PROVISIONAL
    version: int = 1
    created_by: str = ""
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Edge:
    src: str
    relation: str
    dst: str
    evidence_ids: tuple[str, ...] = ()


@dataclass
class Experience:
    id: str
    state: Any
    action: Any
    consequence: Any
    evidence: Evidence
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class CapabilitySpec:
    content: Any
    entry: Any
    applicability: Any
    composition: Any
    termination: Any
    recovery: Any


@dataclass
class DevelopmentalState:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    ledger: list[Experience] = field(default_factory=list)
    active_version: int = 0

    def clone(self) -> "DevelopmentalState":
        return copy.deepcopy(self)

    def install(self, node: Node) -> None:
        self.nodes[node.id] = node
        self.active_version += 1

    def link(self, src: str, relation: str, dst: str, *evidence_ids: str) -> None:
        self.edges.append(Edge(src, relation, dst, tuple(evidence_ids)))
        self.active_version += 1

    def revoke(self, node_id: str, counterexample_id: str) -> None:
        n = self.nodes[node_id]
        n.status = Status.REVOKED
        n.invalidators.append(counterexample_id)
        n.version += 1
        self.active_version += 1

    def active(self, kinds: Optional[set[Kind]] = None) -> list[Node]:
        xs = [n for n in self.nodes.values() if n.status in {Status.VERIFIED, Status.PROVISIONAL}]
        return xs if kinds is None else [n for n in xs if n.kind in kinds]

    def fingerprint(self) -> str:
        payload = {
            "nodes": {k: asdict(v) for k, v in sorted(self.nodes.items())},
            "edges": [asdict(e) for e in self.edges],
            "version": self.active_version,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


class VerifiedWorldMap:
    """Warranted subgraph of the broader developmental state."""
    def __init__(self, state: DevelopmentalState):
        self.state = state

    def nodes(self) -> list[Node]:
        return [n for n in self.state.nodes.values() if n.status == Status.VERIFIED]

    def edges(self) -> list[Edge]:
        valid = {n.id for n in self.nodes()}
        return [e for e in self.state.edges if e.src in valid and e.dst in valid]


class ActiveLens:
    """Situation-specific projection of addressable developmental organization."""
    def __init__(self, selector: Callable[[Node, Any], bool]):
        self.selector = selector

    def project(self, state: DevelopmentalState, world_state: Any) -> list[Node]:
        return [n for n in state.active() if self.selector(n, world_state)]


@dataclass(frozen=True)
class Continuation:
    id: str
    action: Any
    enabled_by: tuple[str, ...] = ()
    blocked_by: tuple[str, ...] = ()


class ContinuationSpace:
    """Currently admissible future continuations C(s)."""
    def __init__(self, generator: Callable[[Any, list[Node]], Iterable[Continuation]]):
        self.generator = generator

    def admissible(self, world_state: Any, active_nodes: list[Node]) -> list[Continuation]:
        return [c for c in self.generator(world_state, active_nodes) if not c.blocked_by]


@dataclass
class UpdateProposal:
    operation: str  # retain/split/merge/promote/revoke/reopen/construct/quotient
    target_ids: list[str]
    candidate: Optional[Node]
    rationale: str
    deciding_test: Any


class DevelopmentController:
    """Smallest deciding test first. Verifier results are authority."""
    def __init__(self, verifier: Callable[[Any], Evidence]):
        self.verifier = verifier

    def append_experience(self, state: DevelopmentalState, exp: Experience) -> None:
        state.ledger.append(exp)

    def accept(self, state: DevelopmentalState, proposal: UpdateProposal) -> Evidence:
        ev = self.verifier(proposal.deciding_test)
        if ev.verdict != "PASS":
            return ev
        op = proposal.operation
        if op in {"retain", "promote", "construct", "reopen"}:
            if proposal.candidate is None:
                raise ValueError("candidate required")
            proposal.candidate.evidence.append(ev)
            proposal.candidate.status = Status.VERIFIED
            state.install(proposal.candidate)
        elif op == "revoke":
            for target in proposal.target_ids:
                state.revoke(target, proposal.candidate.id if proposal.candidate else "counterexample")
        elif op == "split":
            for target in proposal.target_ids:
                state.nodes[target].status = Status.SUPERSEDED
                state.nodes[target].version += 1
            if proposal.candidate is not None:
                proposal.candidate.evidence.append(ev)
                proposal.candidate.status = Status.VERIFIED
                state.install(proposal.candidate)
        elif op == "quotient":
            if proposal.candidate is None:
                raise ValueError("quotient node required")
            proposal.candidate.evidence.append(ev)
            proposal.candidate.status = Status.VERIFIED
            state.install(proposal.candidate)
            for target in proposal.target_ids:
                state.link(proposal.candidate.id, "QUOTIENTS", target)
        elif op == "merge":
            if proposal.candidate is None:
                raise ValueError("merge node required")
            proposal.candidate.evidence.append(ev)
            proposal.candidate.status = Status.VERIFIED
            state.install(proposal.candidate)
            for target in proposal.target_ids:
                state.nodes[target].status = Status.SUPERSEDED
                state.link(proposal.candidate.id, "REFINES", target)
        else:
            raise ValueError(f"unknown update operation: {op}")
        return ev


class ResidualOntologyLoop:
    """Persistent residuals are evidence that the current ontology may be inadequate."""
    def __init__(self, contrast_miner: Callable[[list[Experience]], Any], constructor: Callable[[Any], Node]):
        self.contrast_miner = contrast_miner
        self.constructor = constructor

    def propose(self, residual_experiences: list[Experience]) -> UpdateProposal:
        contrast = self.contrast_miner(residual_experiences)
        candidate = self.constructor(contrast)
        return UpdateProposal(
            operation="construct",
            target_ids=[e.id for e in residual_experiences],
            candidate=candidate,
            rationale="persistent residual -> minimal contrast -> missing distinction/operator",
            deciding_test={"contrast": contrast, "candidate": candidate.id},
        )


class CompressionLaw:
    """A law gives permission to forget; a counterexample withdraws that permission."""
    @staticmethod
    def quotient(state: DevelopmentalState, quotient_node: Node, member_ids: list[str], evidence: Evidence) -> None:
        quotient_node.status = Status.VERIFIED
        quotient_node.evidence.append(evidence)
        state.install(quotient_node)
        for mid in member_ids:
            state.link(quotient_node.id, "QUOTIENTS", mid)

    @staticmethod
    def split(state: DevelopmentalState, quotient_id: str, separator: Node, counterexample: Node) -> None:
        q = state.nodes[quotient_id]
        q.status = Status.SUPERSEDED
        q.invalidators.append(counterexample.id)
        q.version += 1
        state.install(counterexample)
        state.install(separator)
        state.link(separator.id, "REFINES", quotient_id, counterexample.id)


class CheckpointStore:
    def __init__(self):
        self._snapshots: dict[str, DevelopmentalState] = {}

    def save(self, name: str, state: DevelopmentalState) -> str:
        self._snapshots[name] = state.clone()
        return state.fingerprint()

    def restore(self, name: str) -> DevelopmentalState:
        return self._snapshots[name].clone()


class ConsolidationGate:
    """Fast explicit development -> optional slow neural consolidation."""
    def eligible(self, node: Node, min_verified_evidence: int = 2) -> bool:
        return (
            node.status == Status.VERIFIED
            and len(node.evidence) >= min_verified_evidence
            and bool(node.scope)
            and not node.invalidators
        )


def developmental_update(
    state: DevelopmentalState,
    experience: Experience,
    propose: Callable[[DevelopmentalState, Experience], list[UpdateProposal]],
    controller: DevelopmentController,
) -> DevelopmentalState:
    """One explicit E_t + D_t -> D_{t+1} step."""
    new = state.clone()
    controller.append_experience(new, experience)
    for proposal in propose(new, experience):
        controller.accept(new, proposal)
    return new


if __name__ == "__main__":
    # Self-test of reversible explicit developmental state.
    def verifier(test: Any) -> Evidence:
        payload = json.dumps(test, sort_keys=True, default=str)
        return Evidence("SELF_TEST", "PASS", hashlib.sha256(payload.encode()).hexdigest())

    s0 = DevelopmentalState()
    cp = CheckpointStore()
    cp.save("birth", s0)
    cap = Node(
        id="C1",
        kind=Kind.CAPABILITY,
        scope={"world": "toy"},
        data={"spec": asdict(CapabilitySpec("op", "entry", "scope", "compose", "stop", "recover"))},
    )
    proposal = UpdateProposal("promote", [], cap, "self-test", {"candidate": "C1"})
    ctl = DevelopmentController(verifier)
    ctl.accept(s0, proposal)
    assert s0.nodes["C1"].status == Status.VERIFIED
    assert cp.restore("birth").nodes == {}
    print("PASS_METALOGIC_DEVELOPMENTAL_KERNEL_V0_1")
