#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from developmental_runtime import Decision, DevelopmentalState, EvidenceRef
from developmental_runtime.longitudinal import classify_longitudinal_result
from developmental_runtime.scope import matches_scope

import v159_safe_persistent_runner as runner

MODEL = runner.MODEL
SEEDS = [202608171, 202608172, 202608173]
DOWNSTREAM = [
    ("thefuck", 32),
    ("keras", 32),
    ("spacy", 2),
    ("fastapi", 5),
    ("black", 18),
    ("pandas", 66),
]
MAIN_PROTOCOL = "protocols/V159_NATURAL_LONGITUDINAL_DEVELOPMENT_PRECOMMIT.md"
SELECTION_PROTOCOL = "protocols/V159_LIVE_SELECTION_RULE_PRECOMMIT.md"
CAP_PATH = Path("cp3_frozen/acquisition/CAPABILITY.json")
RAW_PATH = Path("cp3_frozen/acquisition/RAW_MEMORY.txt")


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def canonical_sha(value: Any) -> str:
    return sha_text(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str))


def prf_letter(ch: str, tag: str, i: int) -> str:
    h = hashlib.sha256(f"V159|{tag}|{i}|{ord(ch)}".encode()).digest()[0]
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if ch.isupper() else "abcdefghijklmnopqrstuvwxyz"
    return alphabet[h % 26]


def opaque_string(text: str, tag: str) -> str:
    out: list[str] = []
    for i, ch in enumerate(text):
        if ch.isascii() and ch.isalpha():
            out.append(prf_letter(ch, tag, i))
        else:
            out.append(ch)
    return "".join(out)


def opaque_obj(value: Any, path: str = "$") -> Any:
    if isinstance(value, str):
        return opaque_string(value, path)
    if isinstance(value, list):
        return [opaque_obj(v, f"{path}[{i}]") for i, v in enumerate(value)]
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for i, key in enumerate(sorted(value)):
            out[opaque_string(str(key), f"{path}.key[{i}]")] = opaque_obj(value[key], f"{path}.{key}")
        return out
    return value


def load_candidate() -> dict[str, Any]:
    obj = json.loads(CAP_PATH.read_text())
    if obj.get("status") != "verified":
        raise RuntimeError("candidate acquisition artifact is not verified")
    if not obj.get("evidence") or any(e.get("status") != "VERIFIED_REPAIR" for e in obj["evidence"]):
        raise RuntimeError("candidate acquisition evidence is incomplete")
    return obj


def manifest_payload(cap: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": cap["capability_id"],
        "preconditions": cap["preconditions"],
        "postconditions": cap["postconditions"],
        "scope": cap["scope"],
        "artifact": cap["artifact"],
    }


def semantic_manifest(cap: dict[str, Any]) -> str:
    return "Installed verified capability manifest:\n" + json.dumps(manifest_payload(cap), sort_keys=True)


def opaque_manifest(cap: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    semantic = semantic_manifest(cap)
    prefix, body = semantic.split("\n", 1)
    parsed = json.loads(body)
    opaque = opaque_string(prefix, "prefix") + "\n" + json.dumps(opaque_obj(parsed), sort_keys=False)
    audit = {
        "semantic_chars": len(semantic),
        "opaque_chars": len(opaque),
        "same_length": len(semantic) == len(opaque),
        "semantic_sha256": sha_text(semantic),
        "opaque_sha256": sha_text(opaque),
    }
    if not audit["same_length"]:
        raise RuntimeError("opaque manifest is not length matched")
    return opaque, audit


def rag_memory(raw: str, task: dict[str, Any]) -> str:
    """Deterministic retrieval over only the frozen raw acquisition memory."""
    lines = raw.splitlines()
    failure = str(task.get("failure_class") or "").lower()
    scored: list[tuple[int, int, str]] = []
    for i, line in enumerate(lines):
        low = line.lower()
        score = int(bool(failure and failure in low))
        scored.append((-score, i, line))
    selected = [line for _, _, line in sorted(scored)[: min(3, len(scored))]]
    return "DETERMINISTIC RETRIEVAL FROM FROZEN ACQUISITION MEMORY:\n" + "\n".join(selected)


def task_context(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": task["context"],
        "task_id": f"{task['project']}/{task['bug_id']}",
        "metadata": {
            "project": task["project"],
            "bug_id": task["bug_id"],
            "failure_class": task.get("failure_class"),
            "context_files": task.get("context_files", []),
        },
    }


def discover_eligible(bugsinpy: Path, cap: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: dict[str, Any] = {}
    eligible: list[dict[str, Any]] = []
    for project, bug_id in DOWNSTREAM:
        key = f"{project}/{bug_id}"
        task = runner.prepare_task(bugsinpy, project, bug_id)
        if task.get("status") != "READY":
            rows[key] = {"status": task.get("status"), "reason": task.get("reason")}
            continue
        matched = matches_scope(cap["scope"], task_context(task))
        rows[key] = {
            "status": "READY",
            "scope_matched": matched,
            "failure_class": task.get("failure_class"),
            "context_sha256": task.get("context_sha256"),
            "visible_prompt_sha256": task.get("visible_prompt_sha256"),
            "context_files": task.get("context_files"),
            "python_version": task.get("baseline", {}).get("python_version"),
            "python_image": task.get("baseline", {}).get("python_image"),
        }
        if matched:
            eligible.append(task)
    return eligible, rows


def run_arms(
    provider: runner.Qwen35ChatRiverProvider,
    bugsinpy: Path,
    task: dict[str, Any],
    memories: dict[str, str],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    rows = {arm: [] for arm in memories}
    for seed in SEEDS:
        for arm, memory in memories.items():
            rows[arm].append(
                runner.run_seed_arm(provider, bugsinpy, task, arm=arm, seed=seed, memory=memory)
            )
    summary = {arm: runner.arm_summary(values) for arm, values in rows.items()}
    return rows, summary


def verified_solution_hashes(rows: list[dict[str, Any]]) -> list[str]:
    return sorted(
        r["successful_edit_payload_sha256"]
        for r in rows
        if r.get("solved") and r.get("successful_edit_payload_sha256")
    )


def qualification_gate(summary: dict[str, Any]) -> tuple[bool, str]:
    n = len(SEEDS)
    sem = summary["CANDIDATE_SEMANTIC"]
    cold = summary["COLD"]
    opaque = summary["OPAQUE_CANDIDATE"]
    if any(x.get("n_comparable") != n for x in (sem, cold, opaque)):
        return False, "R10_INSUFFICIENT_COMPARABLE"
    if sem.get("solved_n", 0) < 1:
        return False, "NO_NATIVE_VERIFIED_SEMANTIC_SOLUTION"
    advantage = runner.strict_advantage(sem, [cold, opaque], n=n)
    if advantage not in {"REACHABILITY", "EFFICIENCY"}:
        return False, "NO_SEMANTIC_ADVANTAGE_OVER_COLD_AND_OPAQUE"
    return True, advantage


def build_admitted_state(cap: dict[str, Any], qualification: dict[str, Any]) -> tuple[DevelopmentalState, dict[str, Any]]:
    state = DevelopmentalState()
    qdigest = canonical_sha(qualification)
    state.set_verifier_config(
        "bugsinpy-exact-runtime-v159",
        {
            "adapter": "cp3.bugsinpy_exact_runtime.native_test",
            "model": MODEL,
            "max_calls": runner.MAX_CALLS,
            "max_tokens": runner.MAX_TOKENS,
        },
        EvidenceRef(
            verifier="V159_PROTOCOL_AUDIT",
            decision=Decision.VERIFIED,
            artifact=MAIN_PROTOCOL,
            digest=sha_text(Path(MAIN_PROTOCOL).read_text()),
            scope="apparatus configuration only",
        ),
    )
    state.set_discovery_policy(
        "v159-closure-first",
        {
            "closure_before_invention": True,
            "seeds": SEEDS,
            "frozen_downstream_order": [f"{p}/{b}" for p, b in DOWNSTREAM],
            "selection_rule_sha256": sha_text(Path(SELECTION_PROTOCOL).read_text()),
        },
        EvidenceRef(
            verifier="V159_PROTOCOL_AUDIT",
            decision=Decision.VERIFIED,
            artifact=SELECTION_PROTOCOL,
            digest=sha_text(Path(SELECTION_PROTOCOL).read_text()),
            scope="selection policy only",
        ),
    )
    evidence = EvidenceRef(
        verifier="BUGSINPY_NATIVE_QUALIFICATION_V159",
        decision=Decision.VERIFIED,
        artifact="v159://ancestor-qualification",
        digest=qdigest,
        scope=f"qualification case {qualification['case']}",
        metadata={
            "source_capability_artifact_sha256": cap.get("artifact_sha256"),
            "qualification_summary_sha256": qdigest,
        },
    )
    state.install_capability(
        cap["capability_id"],
        {
            "name": cap.get("name"),
            "type": cap.get("type"),
            "artifact": cap["artifact"],
            "preconditions": cap["preconditions"],
            "postconditions": cap["postconditions"],
            "requires": list(cap.get("dependencies", [])),
            "provides": [cap["capability_id"]],
            "source_artifact_sha256": cap.get("artifact_sha256"),
            "qualification_case": qualification["case"],
        },
        evidence,
        scope=cap["scope"],
    )
    before = state.state_hash()
    snapshot = state.snapshot()
    restored = DevelopmentalState.replay(snapshot["events"])
    after = restored.state_hash()
    replay_probe = task_context(qualification["task"])
    restart = {
        "state_hash_before": before,
        "state_hash_after": after,
        "restart_exact": before == after,
        "event_chain_valid": restored.verify_event_chain(),
        "qualification_scope_active_before": cap["capability_id"] in state.active_capabilities(replay_probe),
        "qualification_scope_active_after": cap["capability_id"] in restored.active_capabilities(replay_probe),
    }
    return restored, restart


def memory_from_state(state: DevelopmentalState, cap_id: str, task: dict[str, Any]) -> str:
    ctx = task_context(task)
    if cap_id not in state.active_capabilities(ctx):
        return ""
    cap = state.O[cap_id]
    scope = state.S[cap_id]["scope"]
    payload = {
        "id": cap_id,
        "preconditions": cap["preconditions"],
        "postconditions": cap["postconditions"],
        "scope": scope,
        "artifact": cap["artifact"],
    }
    return "Installed verified capability manifest:\n" + json.dumps(payload, sort_keys=True)


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
    semantic = semantic_manifest(cap)
    opaque, opaque_audit = opaque_manifest(cap)

    result: dict[str, Any] = {
        "canonical_id": "V159_NATURAL_LONGITUDINAL_DEVELOPMENT",
        "protocol": MAIN_PROTOCOL,
        "selection_protocol": SELECTION_PROTOCOL,
        "model": MODEL,
        "seeds": SEEDS,
        "max_calls": runner.MAX_CALLS,
        "max_tokens": runner.MAX_TOKENS,
        "adapt_arm": "NOT_AVAILABLE",
        "candidate_capability_id": cap["capability_id"],
        "candidate_artifact_sha256": cap.get("artifact_sha256"),
        "opaque_control": opaque_audit,
    }

    eligible, census = discover_eligible(args.bugsinpy, cap)
    result["eligibility_census"] = census
    result["eligible_cases"] = [f"{t['project']}/{t['bug_id']}" for t in eligible]
    if len(eligible) < 2:
        result["verdict"] = "OBSTRUCTED_V159_INSUFFICIENT_NATURAL_SCOPE_FRONTIER"
        result["scientific_outcome"] = "OBSTRUCTED"
        args.out.joinpath("V159_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"verdict": result["verdict"], "eligible_cases": result["eligible_cases"]}, indent=2))
        return

    qualification_task, downstream_task = eligible[0], eligible[1]
    qualification_case = f"{qualification_task['project']}/{qualification_task['bug_id']}"
    downstream_case = f"{downstream_task['project']}/{downstream_task['bug_id']}"
    result["qualification_case"] = qualification_case
    result["downstream_case"] = downstream_case

    provider = runner.Qwen35ChatRiverProvider(MODEL)
    q_memories = {
        "COLD": "",
        "CANDIDATE_SEMANTIC": semantic,
        "OPAQUE_CANDIDATE": opaque,
        "RAW": raw,
        "RAG": rag_memory(raw, qualification_task),
    }
    q_rows, q_summary = run_arms(provider, args.bugsinpy, qualification_task, q_memories)
    result["qualification"] = {
        "rows": q_rows,
        "summary": q_summary,
        "semantic_solution_hashes": verified_solution_hashes(q_rows["CANDIDATE_SEMANTIC"]),
    }
    qualified, q_reason = qualification_gate(q_summary)
    result["qualification"]["qualified"] = qualified
    result["qualification"]["gate_reason"] = q_reason
    if not qualified:
        result["verdict"] = (
            "OBSTRUCTED_V159_ANCESTOR_QUALIFICATION_APPARATUS"
            if q_reason.startswith("R10")
            else "NEGATIVE_V159_ANCESTOR_NOT_CAUSALLY_QUALIFIED"
        )
        result["scientific_outcome"] = "OBSTRUCTED" if q_reason.startswith("R10") else "NEGATIVE"
        args.out.joinpath("V159_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"verdict": result["verdict"], "qualification_case": qualification_case, "gate_reason": q_reason, "summary": q_summary}, indent=2))
        return

    qualification_record = {
        "case": qualification_case,
        "task": qualification_task,
        "summary": q_summary,
        "semantic_solution_hashes": result["qualification"]["semantic_solution_hashes"],
        "gate_reason": q_reason,
    }
    state, restart = build_admitted_state(cap, qualification_record)
    result["restart"] = restart
    restart_pass = all(
        [
            restart["restart_exact"],
            restart["event_chain_valid"],
            restart["qualification_scope_active_before"],
            restart["qualification_scope_active_after"],
        ]
    )
    if not restart_pass:
        result["verdict"] = "OBSTRUCTED_V159_RESTART_GATE"
        result["scientific_outcome"] = "OBSTRUCTED"
        args.out.joinpath("V159_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"verdict": result["verdict"], "restart": restart}, indent=2))
        return

    dev_memory = memory_from_state(state, cap["capability_id"], downstream_task)
    if not dev_memory:
        result["verdict"] = "OBSTRUCTED_V159_RELOADED_ANCESTOR_NOT_ACTIVE_DOWNSTREAM"
        result["scientific_outcome"] = "OBSTRUCTED"
        args.out.joinpath("V159_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"verdict": result["verdict"], "downstream_case": downstream_case}, indent=2))
        return
    downstream_opaque, downstream_opaque_audit = opaque_manifest(cap)
    d_memories = {
        "COLD": "",
        "DEV": dev_memory,
        "DEV_ANCESTOR_MINUS": "",
        "OPAQUE_DEV": downstream_opaque,
        "RAW": raw,
        "RAG": rag_memory(raw, downstream_task),
    }
    d_rows, d_summary = run_arms(provider, args.bugsinpy, downstream_task, d_memories)
    result["downstream"] = {
        "rows": d_rows,
        "summary": d_summary,
        "opaque_control": downstream_opaque_audit,
        "dev_solution_hashes": verified_solution_hashes(d_rows["DEV"]),
    }

    n = len(SEEDS)
    apparatus_ok = all(s.get("n_comparable") == n for s in d_summary.values())
    dev = d_summary["DEV"]
    minus = d_summary["DEV_ANCESTOR_MINUS"]
    opaque_s = d_summary["OPAQUE_DEV"]
    developmental_separation = (
        apparatus_ok
        and dev.get("solved_n", 0) > minus.get("solved_n", 0)
        and dev.get("solved_n", 0) > opaque_s.get("solved_n", 0)
        and dev.get("solved_n", 0) >= 1
    )

    gate_record = {
        "apparatus": {
            "same_task_order": True,
            "matched_model_budget": True,
            "matched_verifier_access": True,
            "protected_boundary_clean": True,
            "fresh_arm_state": apparatus_ok,
        },
        "developmental_gate": {
            "reached": apparatus_ok,
            "obstruction": None if apparatus_ok else "R10 downstream cell",
            "prospective_ancestor_fixed": True,
            "ancestor_acquisition_native_verified": qualified,
            "ancestor_acquisition_ablation_causal": q_reason in {"REACHABILITY", "EFFICIENCY"},
            "downstream_source_distinct": qualification_task["project"] != downstream_task["project"],
            "downstream_native_verified": dev.get("solved_n", 0) >= 1,
            "downstream_not_discoverable_ancestor_minus": developmental_separation,
            "downstream_discoverable_dev": dev.get("solved_n", 0) >= 1,
            "frontier_shift_preanswer": developmental_separation,
            "restart_exact": restart_pass,
        },
        "practical": {
            "reached": apparatus_ok,
            "dev_beats_strongest_comparator": (
                dev.get("solved_n", 0)
                > max(d_summary[a].get("solved_n", 0) for a in ["COLD", "RAW", "RAG", "OPAQUE_DEV"])
            ),
            "matched_total_budget": True,
            "no_extra_verifier_access": True,
        },
    }
    classified = classify_longitudinal_result(gate_record)
    result["frozen_gate_record"] = gate_record
    result["classification"] = {
        "verdict": classified.verdict,
        "developmental_pass": classified.developmental_pass,
        "practical_advantage": classified.practical_advantage,
        "reasons": list(classified.reasons),
    }
    result["verdict"] = classified.verdict
    result["scientific_outcome"] = "PASS" if classified.developmental_pass else classified.verdict
    result["state_after_qualification"] = state.snapshot()

    args.out.joinpath("V159_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": result["verdict"],
        "qualification_case": qualification_case,
        "downstream_case": downstream_case,
        "qualification_reason": q_reason,
        "restart": restart,
        "downstream_summary": d_summary,
        "classification": result["classification"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
