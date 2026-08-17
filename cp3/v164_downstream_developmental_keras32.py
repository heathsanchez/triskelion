#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from developmental_runtime import Decision, DevelopmentalState, EvidenceRef
import v159_safe_persistent_runner as runner
from v159_natural_longitudinal_live import RAW_PATH, load_candidate, opaque_manifest, rag_memory, task_context

MODEL = runner.MODEL
SEEDS = [202608171, 202608172, 202608173]
PROTOCOL = "protocols/V164_DOWNSTREAM_DEVELOPMENTAL_KERAS32_PRECOMMIT.md"
V163_PROTOCOL = "protocols/V163_SEMANTIC_CAPABILITY_QUALIFICATION_CONFIRMATION_PRECOMMIT.md"
V163_VERDICT = "PASS_V163_SEMANTIC_CAPABILITY_CAUSALLY_QUALIFIED"
V163_COMMIT = "829e6c61cd5e4583f0b57d44d699c14ac6d28164"


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def canonical_sha(x: Any) -> str:
    return sha_text(json.dumps(x, sort_keys=True, separators=(",", ":"), default=str))


def build_state(cap: dict[str, Any], downstream_task: dict[str, Any]) -> tuple[DevelopmentalState, dict[str, Any]]:
    state = DevelopmentalState()
    protocol_digest = sha_text(Path(V163_PROTOCOL).read_text())
    state.set_verifier_config(
        "bugsinpy-exact-runtime-v164",
        {"adapter": "cp3.bugsinpy_exact_runtime.native_test", "model": MODEL, "max_calls": 3, "max_tokens": runner.MAX_TOKENS},
        EvidenceRef(verifier="V164_PROTOCOL_AUDIT", decision=Decision.VERIFIED, artifact=PROTOCOL,
                    digest=sha_text(Path(PROTOCOL).read_text()), scope="apparatus configuration only"),
    )
    state.set_discovery_policy(
        "v164-frozen-downstream",
        {"qualification_case": "thefuck/32", "downstream_case": "keras/32", "seeds": SEEDS,
         "v163_commit": V163_COMMIT, "v163_verdict": V163_VERDICT},
        EvidenceRef(verifier="V164_PROTOCOL_AUDIT", decision=Decision.VERIFIED, artifact=PROTOCOL,
                    digest=sha_text(Path(PROTOCOL).read_text()), scope="downstream selection policy"),
    )
    qualification_record = {
        "verdict": V163_VERDICT,
        "commit": V163_COMMIT,
        "protocol_sha256": protocol_digest,
        "qualification_case": "thefuck/32",
        "semantic_solved_n": 2,
        "control_max_solved_n": 0,
    }
    state.install_capability(
        cap["capability_id"],
        {"name": cap.get("name"), "type": cap.get("type"), "artifact": cap["artifact"],
         "preconditions": cap["preconditions"], "postconditions": cap["postconditions"],
         "requires": list(cap.get("dependencies", [])), "provides": [cap["capability_id"]],
         "source_artifact_sha256": cap.get("artifact_sha256"), "qualification_case": "thefuck/32",
         "qualification_verdict": V163_VERDICT},
        EvidenceRef(verifier="BUGSINPY_NATIVE_QUALIFICATION_V163", decision=Decision.VERIFIED,
                    artifact="github-actions://32005192728/V163_RESULT.json", digest=canonical_sha(qualification_record),
                    scope="qualified on thefuck/32; downstream scope remains frozen capability scope",
                    metadata=qualification_record),
        scope=cap["scope"],
    )
    before = state.state_hash()
    restored = DevelopmentalState.replay(state.snapshot()["events"])
    after = restored.state_hash()
    ctx = task_context(downstream_task)
    active = cap["capability_id"] in restored.active_capabilities(ctx)
    audit = {"state_hash_before": before, "state_hash_after": after, "restart_exact": before == after,
             "event_chain_valid": restored.verify_event_chain(), "downstream_scope_active": active,
             "event_count": len(restored.events)}
    return restored, audit


def memory_from_state(state: DevelopmentalState, cap_id: str, task: dict[str, Any]) -> str:
    ctx = task_context(task)
    if cap_id not in state.active_capabilities(ctx):
        return ""
    cap = state.O[cap_id]
    payload = {"id": cap_id, "preconditions": cap["preconditions"], "postconditions": cap["postconditions"],
               "scope": state.S[cap_id]["scope"], "artifact": cap["artifact"]}
    return "Installed verified capability manifest:\n" + json.dumps(payload, sort_keys=True)


def mechanism(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "call1_executable_n": sum(bool(r.get("attempts")) and not r["attempts"][0].get("transport_error") for r in rows),
        "post_first_executable_refinement_n": sum(any(not a.get("transport_error") for a in (r.get("attempts") or [])[1:]) for r in rows),
        "solved_payload_sha256": sorted(r.get("successful_edit_payload_sha256") for r in rows if r.get("solved") and r.get("successful_edit_payload_sha256")),
    }


def classify(summary: dict[str, Any], state_audit: dict[str, Any]) -> str:
    if not (state_audit["restart_exact"] and state_audit["event_chain_valid"] and state_audit["downstream_scope_active"]):
        return "OBSTRUCTED_V164_STATE_OR_SCOPE"
    n = len(SEEDS)
    if any(v.get("n_comparable") != n for v in summary.values()):
        return "OBSTRUCTED_V164_R10_INSUFFICIENT_COMPARABLE"
    dev = int(summary["DEV_ADMITTED"].get("solved_n", 0))
    alts = [int(summary[k].get("solved_n", 0)) for k in ("ANCESTOR_MINUS", "OPAQUE_MATCHED", "RAW", "RAG")]
    if dev >= 1 and dev > max(alts):
        return "PASS_V164_NATURAL_DEVELOPMENTAL_COMPOUNDING"
    if dev >= 1 and dev <= max(alts):
        return "V164_DOWNSTREAM_NOT_SEMANTICALLY_IDENTIFIED"
    return "NEGATIVE_V164_QUALIFIED_ANCESTOR_NO_DOWNSTREAM_ADVANTAGE"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("output exists; refusing to overwrite frozen evidence")
    args.out.mkdir(parents=True)

    cap = load_candidate()
    raw = RAW_PATH.read_text()
    task = runner.prepare_task(args.bugsinpy, "keras", 32)
    if task.get("status") != "READY":
        result = {"canonical_id": "V164_DOWNSTREAM_DEVELOPMENTAL_KERAS32", "verdict": "OBSTRUCTED_V164_TASK_NOT_READY", "task": task}
        args.out.joinpath("V164_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True)); return

    state, state_audit = build_state(cap, task)
    if not (state_audit["restart_exact"] and state_audit["event_chain_valid"] and state_audit["downstream_scope_active"]):
        result = {"canonical_id": "V164_DOWNSTREAM_DEVELOPMENTAL_KERAS32", "state_audit": state_audit, "verdict": "OBSTRUCTED_V164_STATE_OR_SCOPE"}
        args.out.joinpath("V164_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True)); return

    dev = memory_from_state(state, cap["capability_id"], task)
    opaque, opaque_audit = opaque_manifest(cap)
    memories = {"DEV_ADMITTED": dev, "ANCESTOR_MINUS": "", "OPAQUE_MATCHED": opaque,
                "RAW": raw, "RAG": rag_memory(raw, task)}

    old_max_calls = runner.MAX_CALLS
    runner.MAX_CALLS = 3
    try:
        provider = runner.Qwen35ChatRiverProvider(MODEL)
        rows = {arm: [] for arm in memories}
        for seed in SEEDS:
            for arm, memory in memories.items():
                rows[arm].append(runner.run_seed_arm(provider, args.bugsinpy, task, arm=arm, seed=seed, memory=memory))
    finally:
        runner.MAX_CALLS = old_max_calls

    summary = {arm: runner.arm_summary(v) for arm, v in rows.items()}
    mech = {arm: mechanism(v) for arm, v in rows.items()}
    verdict = classify(summary, state_audit)
    result = {"canonical_id": "V164_DOWNSTREAM_DEVELOPMENTAL_KERAS32", "protocol": PROTOCOL,
              "v163_commit": V163_COMMIT, "v163_verdict": V163_VERDICT, "model": MODEL, "seeds": SEEDS,
              "task": "keras/32", "max_calls": 3, "state_audit": state_audit, "opaque_control": opaque_audit,
              "summary": summary, "mechanism": mech, "rows": rows, "verdict": verdict,
              "scientific_outcome": "PASS" if verdict.startswith("PASS_") else ("OBSTRUCTED" if verdict.startswith("OBSTRUCTED_") else "NEGATIVE")}
    args.out.joinpath("V164_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": verdict, "state_audit": state_audit, "summary": summary, "mechanism": mech}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
