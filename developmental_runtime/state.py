from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


SCHEMA_VERSION = "developmental-state-v1"


class Decision(str, Enum):
    VERIFIED = "VERIFIED"
    REFUTED = "REFUTED"
    OBSTRUCTED = "OBSTRUCTED"


class ObjectKind(str, Enum):
    CAPABILITY = "capability"
    LAW = "law"
    SCOPE = "scope"
    QUOTIENT = "quotient"
    ORGAN = "organ"
    CONSTRUCTOR = "constructor"
    DISCOVERY_POLICY = "discovery_policy"
    OBSTRUCTION = "obstruction"


@dataclass(frozen=True)
class EvidenceRef:
    """External decision evidence. Truth is never inferred from prose or model output."""

    verifier: str
    decision: Decision
    artifact: str
    digest: str
    scope: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def permits_admission(self) -> bool:
        return self.decision is Decision.VERIFIED and bool(self.verifier and self.artifact and self.digest)


@dataclass(frozen=True)
class DevelopmentalEvent:
    index: int
    kind: str
    object_kind: str
    object_id: str
    payload: Mapping[str, Any]
    evidence: Mapping[str, Any]
    parent_hash: str
    event_hash: str

    @staticmethod
    def compute_hash(
        *,
        index: int,
        kind: str,
        object_kind: str,
        object_id: str,
        payload: Mapping[str, Any],
        evidence: Mapping[str, Any],
        parent_hash: str,
    ) -> str:
        canonical = json.dumps(
            {
                "index": index,
                "kind": kind,
                "object_kind": object_kind,
                "object_id": object_id,
                "payload": payload,
                "evidence": evidence,
                "parent_hash": parent_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return sha256(canonical.encode()).hexdigest()


@dataclass
class DevelopmentalState:
    """One explicit A_t state.

    Omega: reasoning alphabet / primitive metalanguage
    O: verified capabilities/operators
    L: scoped laws
    S: applicability/lifecycle state
    Pi: operational distinctions/quotients
    G: reusable organs/circuits
    K: constructor machinery
    D: discovery/search policy
    V: external verifier configuration

    Mutations are admitted only through evidence-bearing events. The event log is
    hash chained and can reconstruct the exact retained state without replaying
    raw model conversations.
    """

    Omega: dict[str, dict[str, Any]] = field(default_factory=dict)
    O: dict[str, dict[str, Any]] = field(default_factory=dict)
    L: dict[str, dict[str, Any]] = field(default_factory=dict)
    S: dict[str, dict[str, Any]] = field(default_factory=dict)
    Pi: dict[str, dict[str, Any]] = field(default_factory=dict)
    G: dict[str, dict[str, Any]] = field(default_factory=dict)
    K: dict[str, dict[str, Any]] = field(default_factory=dict)
    D: dict[str, Any] = field(default_factory=dict)
    V: dict[str, Any] = field(default_factory=dict)
    events: list[DevelopmentalEvent] = field(default_factory=list)

    def state_hash(self) -> str:
        return sha256(
            json.dumps(self.snapshot(include_events=False), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def snapshot(self, *, include_events: bool = True) -> dict[str, Any]:
        out = {
            "schema": SCHEMA_VERSION,
            "Omega": self.Omega,
            "O": self.O,
            "L": self.L,
            "S": self.S,
            "Pi": self.Pi,
            "G": self.G,
            "K": self.K,
            "D": self.D,
            "V": self.V,
        }
        if include_events:
            out["events"] = [asdict(event) for event in self.events]
        return out

    def _append(
        self,
        *,
        kind: str,
        object_kind: ObjectKind,
        object_id: str,
        payload: Mapping[str, Any],
        evidence: EvidenceRef,
    ) -> DevelopmentalEvent:
        if not evidence.permits_admission():
            raise ValueError("retained state may change only on VERIFIED external evidence")
        parent_hash = self.events[-1].event_hash if self.events else "GENESIS"
        evidence_dict = asdict(evidence)
        evidence_dict["decision"] = evidence.decision.value
        index = len(self.events)
        event_hash = DevelopmentalEvent.compute_hash(
            index=index,
            kind=kind,
            object_kind=object_kind.value,
            object_id=object_id,
            payload=dict(payload),
            evidence=evidence_dict,
            parent_hash=parent_hash,
        )
        event = DevelopmentalEvent(
            index=index,
            kind=kind,
            object_kind=object_kind.value,
            object_id=object_id,
            payload=dict(payload),
            evidence=evidence_dict,
            parent_hash=parent_hash,
            event_hash=event_hash,
        )
        self.events.append(event)
        return event

    def install_capability(
        self,
        capability_id: str,
        capability: Mapping[str, Any],
        evidence: EvidenceRef,
        *,
        scope: Mapping[str, Any] | None = None,
    ) -> DevelopmentalEvent:
        if capability_id in self.O and self.S.get(capability_id, {}).get("status") != "revoked":
            raise ValueError(f"capability already installed: {capability_id}")
        payload = {"capability": dict(capability), "scope": dict(scope or {})}
        event = self._append(
            kind="install",
            object_kind=ObjectKind.CAPABILITY,
            object_id=capability_id,
            payload=payload,
            evidence=evidence,
        )
        self.O[capability_id] = dict(capability)
        self.S[capability_id] = {"status": "active", "scope": dict(scope or {}), "admitted_by": event.event_hash}
        return event

    def install_law(self, law_id: str, law: Mapping[str, Any], evidence: EvidenceRef) -> DevelopmentalEvent:
        event = self._append(
            kind="install",
            object_kind=ObjectKind.LAW,
            object_id=law_id,
            payload=dict(law),
            evidence=evidence,
        )
        self.L[law_id] = {**dict(law), "admitted_by": event.event_hash}
        return event

    def install_organ(self, organ_id: str, organ: Mapping[str, Any], evidence: EvidenceRef) -> DevelopmentalEvent:
        event = self._append(
            kind="install",
            object_kind=ObjectKind.ORGAN,
            object_id=organ_id,
            payload=dict(organ),
            evidence=evidence,
        )
        self.G[organ_id] = {**dict(organ), "admitted_by": event.event_hash}
        return event

    def install_constructor(
        self, constructor_id: str, constructor: Mapping[str, Any], evidence: EvidenceRef
    ) -> DevelopmentalEvent:
        event = self._append(
            kind="install",
            object_kind=ObjectKind.CONSTRUCTOR,
            object_id=constructor_id,
            payload=dict(constructor),
            evidence=evidence,
        )
        self.K[constructor_id] = {**dict(constructor), "admitted_by": event.event_hash}
        return event

    def refine_quotient(
        self, quotient_id: str, quotient: Mapping[str, Any], evidence: EvidenceRef
    ) -> DevelopmentalEvent:
        previous = self.Pi.get(quotient_id)
        payload = {"previous": previous, "next": dict(quotient)}
        event = self._append(
            kind="refine",
            object_kind=ObjectKind.QUOTIENT,
            object_id=quotient_id,
            payload=payload,
            evidence=evidence,
        )
        self.Pi[quotient_id] = {**dict(quotient), "admitted_by": event.event_hash}
        return event

    def refine_scope(
        self, object_id: str, scope: Mapping[str, Any], evidence: EvidenceRef
    ) -> DevelopmentalEvent:
        if object_id not in self.S:
            raise KeyError(f"no scoped retained object: {object_id}")
        payload = {"previous": self.S[object_id].get("scope", {}), "next": dict(scope)}
        event = self._append(
            kind="refine",
            object_kind=ObjectKind.SCOPE,
            object_id=object_id,
            payload=payload,
            evidence=evidence,
        )
        self.S[object_id]["scope"] = dict(scope)
        self.S[object_id]["scope_admitted_by"] = event.event_hash
        return event

    def revoke(self, object_id: str, evidence: EvidenceRef, *, reason: str) -> DevelopmentalEvent:
        if object_id not in self.S:
            raise KeyError(f"cannot revoke unknown scoped object: {object_id}")
        event = self._append(
            kind="revoke",
            object_kind=ObjectKind.SCOPE,
            object_id=object_id,
            payload={"reason": reason},
            evidence=evidence,
        )
        self.S[object_id]["status"] = "revoked"
        self.S[object_id]["revoked_by"] = event.event_hash
        self.S[object_id]["reason"] = reason
        return event

    def set_discovery_policy(
        self, policy_id: str, policy: Mapping[str, Any], evidence: EvidenceRef
    ) -> DevelopmentalEvent:
        event = self._append(
            kind="set",
            object_kind=ObjectKind.DISCOVERY_POLICY,
            object_id=policy_id,
            payload=dict(policy),
            evidence=evidence,
        )
        self.D = {"id": policy_id, **dict(policy), "admitted_by": event.event_hash}
        return event

    def record_obstruction(
        self, obstruction_id: str, obstruction: Mapping[str, Any], evidence: EvidenceRef
    ) -> DevelopmentalEvent:
        # An obstruction may be retained only when an external boundary has
        # verified the observation that defines it. It is knowledge, not success.
        return self._append(
            kind="record",
            object_kind=ObjectKind.OBSTRUCTION,
            object_id=obstruction_id,
            payload=dict(obstruction),
            evidence=evidence,
        )

    def active_capabilities(self, context: Mapping[str, Any] | None = None) -> list[str]:
        context = dict(context or {})
        active: list[str] = []
        for cid in sorted(self.O):
            state = self.S.get(cid, {})
            if state.get("status") != "active":
                continue
            scope = state.get("scope", {})
            if all(context.get(key) == value for key, value in scope.items()):
                active.append(cid)
        return active

    def closure(self, seeds: Iterable[str], *, max_rounds: int = 16) -> set[str]:
        """Small explicit closure engine for prerequisite-labelled retained objects.

        Capabilities/laws/organs/constructors may declare `requires: [ids...]` and
        `provides: [symbols...]`. This is deliberately representation-agnostic: it
        records discoverability structure without pretending to solve a domain.
        """
        reached = set(seeds)
        objects: list[tuple[str, Mapping[str, Any]]] = []
        objects.extend(self.O.items())
        objects.extend(self.L.items())
        objects.extend(self.G.items())
        objects.extend(self.K.items())
        for _ in range(max_rounds):
            before = len(reached)
            for object_id, obj in objects:
                if object_id in self.S and self.S[object_id].get("status") == "revoked":
                    continue
                requires = set(obj.get("requires", []))
                if requires <= reached:
                    reached.add(object_id)
                    reached.update(obj.get("provides", []))
            if len(reached) == before:
                return reached
        raise RuntimeError("closure did not stabilize within max_rounds")

    def verify_event_chain(self) -> bool:
        parent = "GENESIS"
        for i, event in enumerate(self.events):
            if event.index != i or event.parent_hash != parent:
                return False
            expected = DevelopmentalEvent.compute_hash(
                index=event.index,
                kind=event.kind,
                object_kind=event.object_kind,
                object_id=event.object_id,
                payload=event.payload,
                evidence=event.evidence,
                parent_hash=event.parent_hash,
            )
            if expected != event.event_hash:
                return False
            parent = event.event_hash
        return True

    @classmethod
    def replay(cls, events: Iterable[Mapping[str, Any]]) -> "DevelopmentalState":
        state = cls()
        for raw in events:
            event = DevelopmentalEvent(**dict(raw))
            evidence_raw = dict(event.evidence)
            evidence_raw["decision"] = Decision(evidence_raw["decision"])
            evidence = EvidenceRef(**evidence_raw)
            if not evidence.permits_admission():
                raise ValueError("event stream contains a non-admissible mutation")
            expected_parent = state.events[-1].event_hash if state.events else "GENESIS"
            if event.parent_hash != expected_parent:
                raise ValueError("event chain parent mismatch")
            expected_hash = DevelopmentalEvent.compute_hash(
                index=event.index,
                kind=event.kind,
                object_kind=event.object_kind,
                object_id=event.object_id,
                payload=event.payload,
                evidence=event.evidence,
                parent_hash=event.parent_hash,
            )
            if expected_hash != event.event_hash:
                raise ValueError("event hash mismatch")
            state.events.append(event)
            state._apply_replayed_event(event)
        return state

    def _apply_replayed_event(self, event: DevelopmentalEvent) -> None:
        kind = event.object_kind
        oid = event.object_id
        payload = dict(event.payload)
        if kind == ObjectKind.CAPABILITY.value and event.kind == "install":
            self.O[oid] = dict(payload["capability"])
            self.S[oid] = {"status": "active", "scope": dict(payload.get("scope", {})), "admitted_by": event.event_hash}
        elif kind == ObjectKind.LAW.value and event.kind == "install":
            self.L[oid] = {**payload, "admitted_by": event.event_hash}
        elif kind == ObjectKind.ORGAN.value and event.kind == "install":
            self.G[oid] = {**payload, "admitted_by": event.event_hash}
        elif kind == ObjectKind.CONSTRUCTOR.value and event.kind == "install":
            self.K[oid] = {**payload, "admitted_by": event.event_hash}
        elif kind == ObjectKind.QUOTIENT.value and event.kind == "refine":
            self.Pi[oid] = {**dict(payload["next"]), "admitted_by": event.event_hash}
        elif kind == ObjectKind.SCOPE.value and event.kind == "refine":
            if oid not in self.S:
                raise ValueError(f"scope refinement before object installation: {oid}")
            self.S[oid]["scope"] = dict(payload["next"])
            self.S[oid]["scope_admitted_by"] = event.event_hash
        elif kind == ObjectKind.SCOPE.value and event.kind == "revoke":
            if oid not in self.S:
                raise ValueError(f"revocation before object installation: {oid}")
            self.S[oid].update(status="revoked", revoked_by=event.event_hash, reason=payload["reason"])
        elif kind == ObjectKind.DISCOVERY_POLICY.value and event.kind == "set":
            self.D = {"id": oid, **payload, "admitted_by": event.event_hash}
        elif kind == ObjectKind.OBSTRUCTION.value and event.kind == "record":
            pass
        else:
            raise ValueError(f"unsupported replay event: {event.kind}/{kind}")
