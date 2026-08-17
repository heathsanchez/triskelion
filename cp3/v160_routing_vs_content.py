#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import v159_safe_persistent_runner as runner
from v159_natural_longitudinal_live import load_candidate, opaque_manifest, semantic_manifest

MODEL = runner.MODEL
SEEDS = [202608171, 202608172, 202608173]
PROTOCOL = "protocols/V160_ROUTING_VS_CAPABILITY_CONTENT_PRECOMMIT.md"
RIGHT_LOCUS = "thefuck/rules/ls_lah.py"
WRONG_LOCUS = "thefuck/rules/apt_get.py"
LOCUS_WIDTH = 48


def locus_signal(path: str) -> str:
    if len(path) > LOCUS_WIDTH:
        raise RuntimeError("locus path exceeds frozen width")
    return (
        "VERIFIER-DERIVED LOCUS SIGNAL (not a solution):\n"
        "Ground diagnosis and candidate edits at this source locus first. "
        "Do not edit tests.\n"
        f"SOURCE_LOCUS={path.ljust(LOCUS_WIDTH)}"
    )


def combine(*parts: str) -> str:
    return "\n\n".join(p for p in parts if p)


def first_exec_hits(row: dict[str, Any], locus: str) -> bool:
    for attempt in row.get("attempts", []):
        if attempt.get("transport_error"):
            continue
        changed = attempt.get("changed_files") or []
        return locus in changed
    return False


def any_exec_hits(row: dict[str, Any], locus: str) -> bool:
    for attempt in row.get("attempts", []):
        if attempt.get("transport_error"):
            continue
        if locus in (attempt.get("changed_files") or []):
            return True
    return False


def mechanism(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "first_executable_right_locus_n": sum(first_exec_hits(r, RIGHT_LOCUS) for r in rows),
        "any_executable_right_locus_n": sum(any_exec_hits(r, RIGHT_LOCUS) for r in rows),
        "first_executable_wrong_locus_n": sum(first_exec_hits(r, WRONG_LOCUS) for r in rows),
        "any_executable_wrong_locus_n": sum(any_exec_hits(r, WRONG_LOCUS) for r in rows),
    }


def classify(summary: dict[str, Any], mech: dict[str, Any]) -> str:
    n = len(SEEDS)
    if any(v.get("n_comparable") != n for v in summary.values()):
        return "OBSTRUCTED_V160_R10_INSUFFICIENT_COMPARABLE"

    sem_none = summary["SEM_NONE"].get("solved_n", 0)
    sem_right = summary["SEM_RIGHT"].get("solved_n", 0)
    sem_wrong = summary["SEM_WRONG"].get("solved_n", 0)
    opaque_right = summary["OPAQUE_RIGHT"].get("solved_n", 0)
    cold_right = summary["COLD_RIGHT"].get("solved_n", 0)

    if sem_right >= 1 and sem_right > sem_wrong and sem_right > sem_none:
        if sem_right > max(opaque_right, cold_right):
            return "PASS_V160_ROUTING_CAUSALLY_RESCUES_SEMANTIC_CAPABILITY"
        return "V160_LOCUS_SIGNAL_SUFFICIENT_CAPABILITY_SEMANTICS_NOT_NEEDED"

    right_route = mech["SEM_RIGHT"]["any_executable_right_locus_n"]
    none_route = mech["SEM_NONE"]["any_executable_right_locus_n"]
    wrong_route = mech["SEM_WRONG"]["any_executable_right_locus_n"]
    if right_route > max(none_route, wrong_route):
        return "OBSTRUCTED_V160_ROUTING_REPAIRED_NO_SEMANTIC_SOLUTION"
    return "NEGATIVE_V160_EXPLICIT_LOCUS_DOES_NOT_REPAIR_ROUTING"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    cap = load_candidate()
    semantic = semantic_manifest(cap)
    opaque, opaque_audit = opaque_manifest(cap)
    right = locus_signal(RIGHT_LOCUS)
    wrong = locus_signal(WRONG_LOCUS)
    if len(right) != len(wrong):
        raise RuntimeError("right/wrong locus signals are not length matched")

    task = runner.prepare_task(args.bugsinpy, "thefuck", 32)
    if task.get("status") != "READY":
        result = {
            "canonical_id": "V160_ROUTING_VS_CAPABILITY_CONTENT",
            "verdict": "OBSTRUCTED_V160_TASK_NOT_READY",
            "task": task,
        }
        args.out.joinpath("V160_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    memories = {
        "SEM_NONE": semantic,
        "SEM_RIGHT": combine(semantic, right),
        "SEM_WRONG": combine(semantic, wrong),
        "OPAQUE_RIGHT": combine(opaque, right),
        "COLD_RIGHT": right,
    }

    provider = runner.Qwen35ChatRiverProvider(MODEL)
    rows: dict[str, list[dict[str, Any]]] = {arm: [] for arm in memories}
    for seed in SEEDS:
        for arm, memory in memories.items():
            rows[arm].append(
                runner.run_seed_arm(provider, args.bugsinpy, task, arm=arm, seed=seed, memory=memory)
            )

    summary = {arm: runner.arm_summary(values) for arm, values in rows.items()}
    mech = {arm: mechanism(values) for arm, values in rows.items()}
    verdict = classify(summary, mech)
    result = {
        "canonical_id": "V160_ROUTING_VS_CAPABILITY_CONTENT",
        "protocol": PROTOCOL,
        "model": MODEL,
        "seeds": SEEDS,
        "task": "thefuck/32",
        "right_locus": RIGHT_LOCUS,
        "wrong_locus": WRONG_LOCUS,
        "locus_signal_chars": len(right),
        "locus_signals_length_matched": len(right) == len(wrong),
        "opaque_control": opaque_audit,
        "summary": summary,
        "mechanism": mech,
        "rows": rows,
        "verdict": verdict,
        "scientific_outcome": "PASS" if verdict.startswith("PASS_") else ("OBSTRUCTED" if verdict.startswith("OBSTRUCTED_") else "NEGATIVE"),
    }
    args.out.joinpath("V160_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": verdict, "summary": summary, "mechanism": mech}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
