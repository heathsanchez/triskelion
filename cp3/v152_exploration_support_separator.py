#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import v151_capability_compilation_loss_separator as v151
from v152_exploration_provider import Qwen35ChatRiverProviderV152, TEMPERATURE

SUBSTANTIVE_ARMS = ["D_COLD", "D_PLUS_O1_COMPILED", "D_PLUS_RAW_T1"]


def distinct_first_hashes(rows: list[dict]) -> list[str]:
    out = []
    for row in rows:
        attempts = row.get("attempts") or []
        if not attempts:
            continue
        h = attempts[0].get("response_sha256")
        if isinstance(h, str) and h not in out:
            out.append(h)
    return out


def classify(inner: dict, diversity_ok: bool) -> str:
    if not diversity_ok:
        return "R10_INSUFFICIENT_PROPOSAL_DIVERSITY"
    if inner.get("verdict") == "R10_INCONCLUSIVE":
        return "R10_INCONCLUSIVE"
    compiled = inner.get("compiled_o1_advantage") in {"REACHABILITY", "EFFICIENCY"}
    raw = inner.get("raw_t1_advantage") in {"REACHABILITY", "EFFICIENCY"}
    if raw and not compiled:
        return "PASS_V152_CAPABILITY_COMPILATION_LOSS_UNDER_EXPLORATION"
    if compiled and raw:
        return "PASS_V152_BOTH_RETAINED_STATES_CAUSALLY_USEFUL"
    if compiled:
        return "PASS_V152_COMPILED_O1_CAUSAL_ADVANTAGE_UNDER_EXPLORATION"
    return "NEGATIVE_V152_NO_T1_DEVELOPMENTAL_SIGNAL_UNDER_SAMPLED_BUDGET"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    # Run the unchanged V151 science with the single precommitted provider intervention.
    v151.Qwen35ChatRiverProvider = Qwen35ChatRiverProviderV152
    inner_out = args.out / "inner_v151"
    old_argv = sys.argv[:]
    try:
        sys.argv = [old_argv[0], "--bugsinpy", str(args.bugsinpy), "--out", str(inner_out)]
        v151.main()
    finally:
        sys.argv = old_argv

    p = inner_out / "V151_RESULT.json"
    if not p.is_file():
        result = {
            "canonical_id": "V152_EXPLORATION_SUPPORT_SEPARATOR",
            "temperature": TEMPERATURE,
            "verdict": "R10_INCONCLUSIVE",
            "reason": "inner V151 result missing",
        }
    else:
        inner = json.loads(p.read_text())
        diversity = {
            arm: distinct_first_hashes(inner.get("rows", {}).get(arm, []))
            for arm in SUBSTANTIVE_ARMS
        }
        diversity_ok = all(len(v) >= 2 for v in diversity.values())
        result = {
            "canonical_id": "V152_EXPLORATION_SUPPORT_SEPARATOR",
            "protocol": "protocols/V152_EXPLORATION_SUPPORT_SEPARATOR_PRECOMMIT.md",
            "temperature": TEMPERATURE,
            "substantive_first_response_hashes": diversity,
            "diversity_gate": diversity_ok,
            "compiled_o1_advantage": inner.get("compiled_o1_advantage"),
            "raw_t1_advantage": inner.get("raw_t1_advantage"),
            "inner_v151_verdict": inner.get("verdict"),
            "summary": inner.get("summary"),
            "verdict": classify(inner, diversity_ok),
            "inner_result_relpath": "inner_v151/V151_RESULT.json",
        }

    args.out.mkdir(parents=True, exist_ok=True)
    args.out.joinpath("V152_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
