#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from developmental_runtime import Decision, DevelopmentalState, EvidenceRef


def evidence(name: str) -> EvidenceRef:
    return EvidenceRef(
        verifier="v158-selftest-verifier",
        decision=Decision.VERIFIED,
        artifact=f"selftest://{name}",
        digest=(name.encode().hex() + "0" * 64)[:64],
        scope="v158-selftest",
    )


def main() -> None:
    out = Path("artifacts/v158")
    out.mkdir(parents=True, exist_ok=True)

    state = DevelopmentalState(V={"authority": "external-only", "mode": "selftest"})
    state.set_discovery_policy(
        "closure-first-v1",
        {"closure_before_invention": True, "attempt_budget": 8},
        evidence("policy"),
    )

    state.install_capability(
        "O2",
        {"requires": ["O1"], "provides": ["later-target"], "source": "sealed-recipe"},
        evidence("o2"),
        scope={"stream": "demo"},
    )
    cold = sorted(state.closure([]))

    state.install_capability(
        "O1",
        {"requires": [], "provides": ["O1-ready"], "source": "episode-1"},
        evidence("o1"),
        scope={"stream": "demo"},
    )
    warm = sorted(state.closure([]))
    before_restart_hash = state.state_hash()

    snapshot = state.snapshot()
    (out / "state.json").write_text(json.dumps(snapshot, indent=2, sort_keys=True))

    restored = DevelopmentalState.replay(snapshot["events"])
    after_restart_hash = restored.state_hash()

    restored.revoke("O1", evidence("ancestor-ablation"), reason="self-test ancestor ablation")
    ablated = sorted(restored.closure([]))

    result = {
        "schema": "v158-selftest-result-v1",
        "event_chain_valid_before_restart": state.verify_event_chain(),
        "event_chain_valid_after_restart": restored.verify_event_chain(),
        "state_hash_before_restart": before_restart_hash,
        "state_hash_after_restart": after_restart_hash,
        "restart_exact": before_restart_hash == after_restart_hash,
        "cold_reaches_later_target": "later-target" in cold,
        "warm_reaches_later_target": "later-target" in warm,
        "ancestor_ablation_removes_later_target": "later-target" not in ablated,
        "cold_closure": cold,
        "warm_closure": warm,
        "ablated_closure": ablated,
    }
    result["pass"] = all(
        [
            result["event_chain_valid_before_restart"],
            result["event_chain_valid_after_restart"],
            result["restart_exact"],
            not result["cold_reaches_later_target"],
            result["warm_reaches_later_target"],
            result["ancestor_ablation_removes_later_target"],
        ]
    )
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
