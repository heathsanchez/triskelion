#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import v159_safe_persistent_runner as runner
from v159_natural_longitudinal_live import RAW_PATH, load_candidate, opaque_manifest, rag_memory, semantic_manifest
from v160_routing_vs_content import RIGHT_LOCUS, combine, locus_signal

MODEL = runner.MODEL
SEEDS = [202608171, 202608172, 202608173]
PROTOCOL = "protocols/V163_SEMANTIC_CAPABILITY_QUALIFICATION_CONFIRMATION_PRECOMMIT.md"


def executable_right_locus(row: dict[str, Any], *, first_only: bool = False) -> bool:
    attempts = row.get("attempts") or []
    if first_only:
        attempts = attempts[:1]
    for attempt in attempts:
        if attempt.get("transport_error"):
            continue
        if RIGHT_LOCUS in (attempt.get("changed_files") or []):
            return True
    return False


def post_first_executable_refinement(row: dict[str, Any]) -> bool:
    attempts = row.get("attempts") or []
    for attempt in attempts[1:]:
        if attempt.get("transport_error"):
            continue
        if RIGHT_LOCUS in (attempt.get("changed_files") or []):
            return True
    return False


def mechanism(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "call1_executable_right_locus_n": sum(executable_right_locus(r, first_only=True) for r in rows),
        "post_first_executable_refinement_n": sum(post_first_executable_refinement(r) for r in rows),
        "solved_payload_sha256": sorted(
            r.get("successful_edit_payload_sha256")
            for r in rows
            if r.get("solved") and r.get("successful_edit_payload_sha256")
        ),
    }


def classify(summary: dict[str, Any]) -> str:
    n = len(SEEDS)
    if any(v.get("n_comparable") != n for v in summary.values()):
        return "OBSTRUCTED_V163_R10_INSUFFICIENT_COMPARABLE"
    sem = int(summary["SEM_CONFIRM"].get("solved_n", 0))
    controls = [
        int(summary[k].get("solved_n", 0))
        for k in ("OPAQUE_CONFIRM", "COLD_CONFIRM", "RAW_CONFIRM", "RAG_CONFIRM")
    ]
    if sem >= 2 and sem > max(controls):
        return "PASS_V163_SEMANTIC_CAPABILITY_CAUSALLY_QUALIFIED"
    if sem >= 2:
        return "V163_CAPABILITY_NOT_SEMANTICALLY_IDENTIFIED"
    return "NEGATIVE_V163_SEMANTIC_CAPABILITY_DOES_NOT_REPLICATE"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("output exists; refusing to overwrite frozen evidence")
    args.out.mkdir(parents=True)

    cap = load_candidate()
    semantic = semantic_manifest(cap)
    opaque, opaque_audit = opaque_manifest(cap)
    raw = RAW_PATH.read_text()
    locus = locus_signal(RIGHT_LOCUS)

    task = runner.prepare_task(args.bugsinpy, "thefuck", 32)
    if task.get("status") != "READY":
        result = {
            "canonical_id": "V163_SEMANTIC_CAPABILITY_CONFIRMATION",
            "verdict": "OBSTRUCTED_V163_TASK_NOT_READY",
            "task": task,
        }
        args.out.joinpath("V163_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    memories = {
        "SEM_CONFIRM": combine(semantic, locus),
        "OPAQUE_CONFIRM": combine(opaque, locus),
        "COLD_CONFIRM": locus,
        "RAW_CONFIRM": combine(raw, locus),
        "RAG_CONFIRM": combine(rag_memory(raw, task), locus),
    }

    old_max_calls = runner.MAX_CALLS
    runner.MAX_CALLS = 3
    try:
        provider = runner.Qwen35ChatRiverProvider(MODEL)
        rows: dict[str, list[dict[str, Any]]] = {arm: [] for arm in memories}
        for seed in SEEDS:
            for arm, memory in memories.items():
                rows[arm].append(
                    runner.run_seed_arm(
                        provider,
                        args.bugsinpy,
                        task,
                        arm=arm,
                        seed=seed,
                        memory=memory,
                    )
                )
    finally:
        runner.MAX_CALLS = old_max_calls

    summary = {arm: runner.arm_summary(values) for arm, values in rows.items()}
    mech = {arm: mechanism(values) for arm, values in rows.items()}
    verdict = classify(summary)
    result = {
        "canonical_id": "V163_SEMANTIC_CAPABILITY_CONFIRMATION",
        "protocol": PROTOCOL,
        "model": MODEL,
        "seeds": SEEDS,
        "task": "thefuck/32",
        "max_calls": 3,
        "right_locus": RIGHT_LOCUS,
        "binding": "NONE_ALL_ARMS",
        "opaque_control": opaque_audit,
        "summary": summary,
        "mechanism": mech,
        "rows": rows,
        "verdict": verdict,
        "scientific_outcome": "PASS" if verdict.startswith("PASS_") else ("OBSTRUCTED" if verdict.startswith("OBSTRUCTED_") else "NEGATIVE"),
    }
    args.out.joinpath("V163_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": verdict, "summary": summary, "mechanism": mech}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
