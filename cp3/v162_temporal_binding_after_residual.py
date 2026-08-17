#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import v159_safe_persistent_runner as runner
from v159_natural_longitudinal_live import load_candidate, opaque_manifest, semantic_manifest
from v160_routing_vs_content import RIGHT_LOCUS, combine, locus_signal
from v161_local_instantiation_binding import binding_packet

MODEL = runner.MODEL
SEEDS = [202608171, 202608172, 202608173]
PROTOCOL = "protocols/V162_TEMPORAL_BINDING_AFTER_RESIDUAL_PRECOMMIT.md"


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class TemporalBindingProvider:
    def __init__(self, inner: Any, binding: str):
        self.inner = inner
        self.binding = binding
        self.call_n = 0
        self.audit: list[dict[str, Any]] = []

    def sample(self, prompt: str, *, seed: int, max_tokens: int):
        self.call_n += 1
        injected = self.call_n >= 2 and bool(self.binding)
        actual = prompt + (("\n\n" + self.binding) if injected else "")
        self.audit.append({
            "call": self.call_n,
            "binding_injected": injected,
            "base_prompt_sha256": sha_text(prompt),
            "actual_prompt_sha256": sha_text(actual),
            "actual_prompt_chars": len(actual),
        })
        return self.inner.sample(actual, seed=seed, max_tokens=max_tokens)


def post_first_executable_refinement(row: dict[str, Any]) -> bool:
    attempts = row.get("attempts") or []
    for attempt in attempts[1:]:
        if attempt.get("transport_error"):
            continue
        if RIGHT_LOCUS in (attempt.get("changed_files") or []):
            return True
    return False


def final_failure_marker(row: dict[str, Any]) -> str | None:
    attempts = row.get("attempts") or []
    for attempt in reversed(attempts):
        verdict = attempt.get("verdict") or {}
        text = verdict.get("test_output") or ""
        if not text:
            continue
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        for ln in reversed(lines):
            if "AssertionError" in ln or ln.startswith("E ") or ln.startswith(">"):
                return ln[-500:]
    return None


def mechanism(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "call1_executable_right_locus_n": sum(
            bool((r.get("attempts") or []))
            and not (r.get("attempts") or [])[0].get("transport_error")
            and RIGHT_LOCUS in ((r.get("attempts") or [])[0].get("changed_files") or [])
            for r in rows
        ),
        "post_first_executable_refinement_n": sum(post_first_executable_refinement(r) for r in rows),
        "final_failure_markers": [final_failure_marker(r) for r in rows],
    }


def classify(summary: dict[str, Any], mech: dict[str, Any]) -> str:
    n = len(SEEDS)
    if any(v.get("n_comparable") != n for v in summary.values()):
        return "OBSTRUCTED_V162_R10_INSUFFICIENT_COMPARABLE"

    right = summary["SEM_TEMP_RIGHT_BIND"].get("solved_n", 0)
    none = summary["SEM_TEMP_NONE"].get("solved_n", 0)
    wrong = summary["SEM_TEMP_WRONG_BIND"].get("solved_n", 0)
    opaque = summary["OPAQUE_TEMP_RIGHT_BIND"].get("solved_n", 0)
    cold = summary["COLD_TEMP_RIGHT_BIND"].get("solved_n", 0)

    if right >= 1 and right > none and right > wrong:
        if right > max(opaque, cold):
            return "PASS_V162_TEMPORAL_BINDING_CAUSALLY_COMPLETES_TRANSFER"
        return "V162_TEMPORAL_BINDING_SUFFICIENT_CAPABILITY_SEMANTICS_NOT_NEEDED"

    rref = mech["SEM_TEMP_RIGHT_BIND"]["post_first_executable_refinement_n"]
    nref = mech["SEM_TEMP_NONE"]["post_first_executable_refinement_n"]
    wref = mech["SEM_TEMP_WRONG_BIND"]["post_first_executable_refinement_n"]
    if rref > max(nref, wref):
        return "OBSTRUCTED_V162_TEMPORAL_BINDING_MOVES_FRONTIER_NO_SOLUTION"
    return "NEGATIVE_V162_TEMPORAL_BINDING_NOT_CAUSAL"


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
            "canonical_id": "V162_TEMPORAL_BINDING_AFTER_RESIDUAL",
            "verdict": "OBSTRUCTED_V162_TASK_NOT_READY",
            "task": task,
        }
        args.out.joinpath("V162_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    initial_memories = {
        "SEM_TEMP_NONE": combine(semantic, locus),
        "SEM_TEMP_RIGHT_BIND": combine(semantic, locus),
        "SEM_TEMP_WRONG_BIND": combine(semantic, locus),
        "OPAQUE_TEMP_RIGHT_BIND": combine(opaque, locus),
        "COLD_TEMP_RIGHT_BIND": locus,
    }
    later_bindings = {
        "SEM_TEMP_NONE": "",
        "SEM_TEMP_RIGHT_BIND": right_bind,
        "SEM_TEMP_WRONG_BIND": wrong_bind,
        "OPAQUE_TEMP_RIGHT_BIND": right_bind,
        "COLD_TEMP_RIGHT_BIND": right_bind,
    }

    # Frozen V162 intervention: one additional verifier-guided refinement step.
    old_max_calls = runner.MAX_CALLS
    runner.MAX_CALLS = 3
    try:
        inner = runner.Qwen35ChatRiverProvider(MODEL)
        rows: dict[str, list[dict[str, Any]]] = {arm: [] for arm in initial_memories}
        for seed in SEEDS:
            for arm, memory in initial_memories.items():
                temporal = TemporalBindingProvider(inner, later_bindings[arm])
                row = runner.run_seed_arm(
                    temporal,
                    args.bugsinpy,
                    task,
                    arm=arm,
                    seed=seed,
                    memory=memory,
                )
                row["temporal_prompt_audit"] = temporal.audit
                row["binding_starts_after_call1"] = True
                rows[arm].append(row)
    finally:
        runner.MAX_CALLS = old_max_calls

    summary = {arm: runner.arm_summary(values) for arm, values in rows.items()}
    mech = {arm: mechanism(values) for arm, values in rows.items()}
    verdict = classify(summary, mech)
    result = {
        "canonical_id": "V162_TEMPORAL_BINDING_AFTER_RESIDUAL",
        "protocol": PROTOCOL,
        "model": MODEL,
        "seeds": SEEDS,
        "task": "thefuck/32",
        "max_calls": 3,
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
    args.out.joinpath("V162_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": verdict, "summary": summary, "mechanism": mech}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
