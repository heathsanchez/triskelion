#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import v159_safe_persistent_runner as runner
from v159_natural_longitudinal_live import load_candidate, opaque_manifest, semantic_manifest
from v160_routing_vs_content import RIGHT_LOCUS, combine, locus_signal

MODEL = runner.MODEL
SEEDS = [202608171, 202608172, 202608173]
PROTOCOL = "protocols/V161_LOCAL_INSTANTIATION_BINDING_PRECOMMIT.md"
FIELD_WIDTH = 96


def _field(value: str) -> str:
    if len(value) > FIELD_WIDTH:
        raise RuntimeError(f"binding field exceeds frozen width: {len(value)} > {FIELD_WIDTH}")
    return value.ljust(FIELD_WIDTH)


def binding_packet(*, right: bool) -> str:
    # Both packets expose exactly the same verifier-observed examples. Only the
    # proposed local binding relation changes. This is not replacement code.
    if right:
        bind = "bind the rule to standalone command-token structure for the command name ls"
        reject = "arbitrary substring occurrence such as lsof is not the command token ls"
    else:
        bind = "bind the rule to arbitrary substring occurrence containing the characters ls"
        reject = "standalone command-token structure should not constrain matching for ls"
    return (
        "LOCAL INSTANTIATION PACKET (not replacement code):\n"
        "Observed positives: ls | ls file.py | ls /opt\n"
        "Observed negatives: ls -lah /opt | pacman -S binutils | lsof\n"
        f"BIND_RELATION={_field(bind)}\n"
        f"DISCRIMINATOR={_field(reject)}"
    )


def token_bound_mechanism(row: dict[str, Any]) -> bool:
    """Weak secondary endpoint only; never upgrades a semantic failure."""
    markers = ("split(", "startswith(", "re.match", "re.search", "\\b", "command.script.split")
    for attempt in row.get("attempts", []):
        if attempt.get("transport_error"):
            continue
        response = attempt.get("response") or {}
        text = json.dumps(response, sort_keys=True)
        if any(marker in text for marker in markers):
            return True
        return False
    return False


def mechanism(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "first_executable_token_bound_n": sum(token_bound_mechanism(r) for r in rows),
        "any_executable_right_locus_n": sum(
            any(
                not a.get("transport_error") and RIGHT_LOCUS in (a.get("changed_files") or [])
                for a in r.get("attempts", [])
            )
            for r in rows
        ),
    }


def classify(summary: dict[str, Any], mech: dict[str, Any]) -> str:
    n = len(SEEDS)
    if any(v.get("n_comparable") != n for v in summary.values()):
        return "OBSTRUCTED_V161_R10_INSUFFICIENT_COMPARABLE"

    right = summary["SEM_LOCUS_RIGHT_BIND"].get("solved_n", 0)
    none = summary["SEM_LOCUS_NONE"].get("solved_n", 0)
    wrong = summary["SEM_LOCUS_WRONG_BIND"].get("solved_n", 0)
    opaque = summary["OPAQUE_LOCUS_RIGHT_BIND"].get("solved_n", 0)
    cold = summary["COLD_LOCUS_RIGHT_BIND"].get("solved_n", 0)

    if right >= 1 and right > none and right > wrong:
        if right > max(opaque, cold):
            return "PASS_V161_LOCAL_INSTANTIATION_CAUSALLY_COMPLETES_TRANSFER"
        return "V161_LOCAL_BINDING_SUFFICIENT_CAPABILITY_SEMANTICS_NOT_NEEDED"

    right_mech = mech["SEM_LOCUS_RIGHT_BIND"]["first_executable_token_bound_n"]
    none_mech = mech["SEM_LOCUS_NONE"]["first_executable_token_bound_n"]
    wrong_mech = mech["SEM_LOCUS_WRONG_BIND"]["first_executable_token_bound_n"]
    if right_mech > max(none_mech, wrong_mech):
        return "OBSTRUCTED_V161_BINDING_REPAIRED_NO_VERIFIED_SOLUTION"
    return "NEGATIVE_V161_LOCAL_BINDING_NOT_CAUSAL"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    cap = load_candidate()
    semantic = semantic_manifest(cap)
    opaque, opaque_audit = opaque_manifest(cap)
    locus = locus_signal(RIGHT_LOCUS)
    right_bind = binding_packet(right=True)
    wrong_bind = binding_packet(right=False)
    if len(right_bind) != len(wrong_bind):
        raise RuntimeError("right/wrong binding packets are not length matched")

    task = runner.prepare_task(args.bugsinpy, "thefuck", 32)
    if task.get("status") != "READY":
        result = {
            "canonical_id": "V161_LOCAL_INSTANTIATION_BINDING",
            "verdict": "OBSTRUCTED_V161_TASK_NOT_READY",
            "task": task,
        }
        args.out.joinpath("V161_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    memories = {
        "SEM_LOCUS_NONE": combine(semantic, locus),
        "SEM_LOCUS_RIGHT_BIND": combine(semantic, locus, right_bind),
        "SEM_LOCUS_WRONG_BIND": combine(semantic, locus, wrong_bind),
        "OPAQUE_LOCUS_RIGHT_BIND": combine(opaque, locus, right_bind),
        "COLD_LOCUS_RIGHT_BIND": combine(locus, right_bind),
    }

    provider = runner.Qwen35ChatRiverProvider(MODEL)
    rows: dict[str, list[dict[str, Any]]] = {arm: [] for arm in memories}
    for seed in SEEDS:
        for arm, memory in memories.items():
            rows[arm].append(runner.run_seed_arm(provider, args.bugsinpy, task, arm=arm, seed=seed, memory=memory))

    summary = {arm: runner.arm_summary(values) for arm, values in rows.items()}
    mech = {arm: mechanism(values) for arm, values in rows.items()}
    verdict = classify(summary, mech)
    result = {
        "canonical_id": "V161_LOCAL_INSTANTIATION_BINDING",
        "protocol": PROTOCOL,
        "model": MODEL,
        "seeds": SEEDS,
        "task": "thefuck/32",
        "right_locus": RIGHT_LOCUS,
        "binding_packet_chars": len(right_bind),
        "binding_packets_length_matched": len(right_bind) == len(wrong_bind),
        "opaque_control": opaque_audit,
        "summary": summary,
        "mechanism": mech,
        "rows": rows,
        "verdict": verdict,
        "scientific_outcome": "PASS" if verdict.startswith("PASS_") else ("OBSTRUCTED" if verdict.startswith("OBSTRUCTED_") else "NEGATIVE"),
    }
    args.out.joinpath("V161_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": verdict, "summary": summary, "mechanism": mech}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
