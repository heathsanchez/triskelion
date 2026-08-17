from __future__ import annotations

from enum import Enum
from typing import Any, Mapping

from .scope import matches_scope
from .state import (
    Decision,
    DevelopmentalEvent,
    DevelopmentalState as _DevelopmentalStateV1,
    EvidenceRef,
    ObjectKind,
)


SCHEMA_VERSION = "developmental-state-v2"


class _ExtendedObjectKind(str, Enum):
    VERIFIER = "verifier"


class DevelopmentalState(_DevelopmentalStateV1):
    """V2 developmental state: every state-bearing field is event-replayable.

    V1 exposed ``V`` in the state hash but allowed callers to inject it directly
    at construction time. That meant an event-only restart could reconstruct
    capabilities, laws, scopes, quotients, organs, constructors and discovery
    policy while still losing verifier configuration. V2 closes that gap by
    making verifier configuration a first-class verified event and evaluates
    capability scope through the portable serialized CP1/CP3 DSL.

    Direct construction with non-empty ``V`` remains technically possible for
    backwards compatibility, but a state intended to satisfy the V158/V159
    restart gate MUST set it through ``set_verifier_config``.
    """

    def snapshot(self, *, include_events: bool = True) -> dict[str, Any]:
        out = super().snapshot(include_events=include_events)
        out["schema"] = SCHEMA_VERSION
        return out

    def set_verifier_config(
        self,
        verifier_id: str,
        config: Mapping[str, Any],
        evidence: EvidenceRef,
    ) -> DevelopmentalEvent:
        event = self._append(
            kind="set",
            object_kind=_ExtendedObjectKind.VERIFIER,  # type: ignore[arg-type]
            object_id=verifier_id,
            payload=dict(config),
            evidence=evidence,
        )
        self.V = {"id": verifier_id, **dict(config), "admitted_by": event.event_hash}
        return event

    def active_capabilities(self, context: Mapping[str, Any] | None = None) -> list[str]:
        ctx = dict(context or {})
        active: list[str] = []
        for cid in sorted(self.O):
            lifecycle = self.S.get(cid, {})
            if lifecycle.get("status") != "active":
                continue
            scope = lifecycle.get("scope", {})
            if matches_scope(scope, ctx):
                active.append(cid)
        return active

    def _apply_replayed_event(self, event: DevelopmentalEvent) -> None:
        if event.object_kind == _ExtendedObjectKind.VERIFIER.value and event.kind == "set":
            self.V = {"id": event.object_id, **dict(event.payload), "admitted_by": event.event_hash}
            return
        super()._apply_replayed_event(event)
