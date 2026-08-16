#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import v155_source_state_synchronization_separator as v155

exp = v155.exp
LOWER = "abcdefghijklmnopqrstuvwxyz"
UPPER = LOWER.upper()
SUB_LOWER = "qwertyuiopasdfghjklzxcvbnm"
SUB_UPPER = SUB_LOWER.upper()
TRANS = str.maketrans(LOWER + UPPER, SUB_LOWER + SUB_UPPER)
_state: dict[str, Any] = {}
_orig_raw_t1_memory = exp.raw_t1_memory
_orig_sham_for = exp.sham_for


def scrub_value(x: Any) -> Any:
    if isinstance(x, str):
        return x.translate(TRANS)
    if isinstance(x, list):
        return [scrub_value(v) for v in x]
    if isinstance(x, dict):
        return {k: scrub_value(v) for k, v in x.items()}
    return x


def raw_t1_memory_capture(t1: dict[str, Any]):
    rawmem, evidence = _orig_raw_t1_memory(t1)
    scrubbed_evidence = scrub_value(evidence)
    matched = "RETAINED VERIFIED ACQUISITION TRACE:\n" + json.dumps(scrubbed_evidence, sort_keys=True)
    if len(matched) != len(rawmem):
        raise RuntimeError(f"V156_CONTROL_LENGTH_MISMATCH raw={len(rawmem)} matched={len(matched)}")
    _state["rawmem"] = rawmem
    _state["matched"] = matched
    _state["matched_sha256"] = hashlib.sha256(matched.encode()).hexdigest()
    _state["raw_sha256"] = hashlib.sha256(rawmem.encode()).hexdigest()
    return rawmem, evidence


def sham_for_matched(n: int) -> str:
    matched = _state.get("matched")
    rawmem = _state.get("rawmem")
    if isinstance(matched, str) and isinstance(rawmem, str) and n == len(rawmem):
        return matched
    return _orig_sham_for(n)


def rival_execution_success(rr: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    detail: dict[str, Any] = {}
    call2 = None
    for a in rr.get("attempts", []):
        if a.get("call") == 2:
            call2 = a
            break
    if not isinstance(call2, dict):
        return False, {"reason": "NO_CALL2"}
    sync = ((call2.get("response") or {}).get("v155_source_sync") or {})
    detail.update(
        sync_injected=bool(sync.get("injected")),
        alternatives_emitted=int(call2.get("alternatives_emitted") or 0),
        alternatives_valid=int(call2.get("alternatives_valid") or 0),
        alternatives_distinct_from_call1=int(call2.get("alternatives_distinct_from_call1") or 0),
        selected_rank=call2.get("selected_rank"),
        transport_error=call2.get("transport_error"),
        verifier_reached=isinstance(call2.get("verdict"), dict),
    )
    ok = (
        detail["sync_injected"]
        and detail["alternatives_emitted"] == 3
        and detail["alternatives_valid"] == 3
        and detail["alternatives_distinct_from_call1"] == 3
        and detail["selected_rank"] is not None
        and not detail["transport_error"]
        and detail["verifier_reached"]
    )
    return ok, detail


def postprocess(out: Path) -> None:
    # V155 postprocess preserves all inherited summaries and synchronization audits.
    v155.postprocess(out)
    r = json.loads((out / "V155_RESULT.json").read_text())
    r["canonical_id"] = "V156_FORMAT_MATCHED_RAW_T1_SEMANTIC_SEPARATOR"
    r["protocol"] = "protocols/V156_FORMAT_MATCHED_RAW_T1_SEMANTIC_SEPARATOR_PRECOMMIT.md"

    construction_ok = (
        isinstance(_state.get("rawmem"), str)
        and isinstance(_state.get("matched"), str)
        and len(_state["rawmem"]) == len(_state["matched"])
    )
    r["v156_control"] = {
        "construction_ok": construction_ok,
        "substitution_source": LOWER,
        "substitution_target": SUB_LOWER,
        "raw_chars": len(_state.get("rawmem", "")),
        "matched_chars": len(_state.get("matched", "")),
        "raw_sha256": _state.get("raw_sha256"),
        "matched_sha256": _state.get("matched_sha256"),
        "json_keys_preserved": True,
        "only_ascii_letters_in_string_values_substituted": True,
    }

    per_arm: dict[str, Any] = {}
    for arm, rows in r.get("rows", {}).items():
        success = 0
        details = []
        for rr in rows:
            ok, d = rival_execution_success(rr)
            success += int(ok)
            details.append({"seed": rr.get("seed"), "success": ok, **d})
        per_arm[arm] = {"success_n": success, "n": len(rows), "details": details}
    r["rival_execution_capability"] = per_arm

    summaries = r.get("summary", {})
    comparable = all(v.get("n_comparable") == len(exp.SEEDS) for v in summaries.values())
    R = per_arm.get("D_PLUS_RAW_T1", {}).get("success_n", 0)
    M = per_arm.get("D_PLUS_SHAM_RAW", {}).get("success_n", 0)
    C = per_arm.get("D_COLD", {}).get("success_n", 0)

    if not construction_ok:
        verdict = "R10_INCONCLUSIVE_V156_CONTROL_CONSTRUCTION"
    elif not comparable:
        verdict = "R10_INCONCLUSIVE_V156"
    elif R >= 2 and (R - M) >= 2 and (R - C) >= 2:
        verdict = "PASS_V156_RAW_T1_SEMANTIC_RIVAL_EXECUTION_SIGNAL"
    elif M >= 2 and abs(R - M) <= 1:
        verdict = "NEGATIVE_V156_FORMAT_SERIALIZATION_EXPLAINS_RIVAL_EXECUTION"
    elif R < 2:
        verdict = "OBSTRUCTED_V156_RAW_T1_RIVAL_EXECUTION_NOT_REPLICATED"
    else:
        verdict = "OBSTRUCTED_V156_INTERMEDIATE_RIVAL_EXECUTION_SEPARATION_INSUFFICIENT"

    r["v156_primary"] = {
        "raw_t1_success_n": R,
        "format_matched_control_success_n": M,
        "cold_success_n": C,
        "raw_minus_matched": R - M,
        "raw_minus_cold": R - C,
        "task_solved_n": {a: s.get("solved_n") for a, s in summaries.items()},
    }
    r["verdict"] = verdict
    (out / "V156_RESULT.json").write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "v156_control": r["v156_control"],
        "v156_primary": r["v156_primary"],
        "rival_execution_success_n": {a: v["success_n"] for a, v in per_arm.items()},
    }, indent=2, sort_keys=True))


def main() -> None:
    exp.raw_t1_memory = raw_t1_memory_capture
    exp.sham_for = sham_for_matched
    exp.run_seed_arm = v155.run_seed_arm_synced
    try:
        exp.main()
        ap = argparse.ArgumentParser(add_help=False)
        ap.add_argument("--out", type=Path, required=True)
        args, _ = ap.parse_known_args()
        postprocess(args.out)
    finally:
        exp.raw_t1_memory = _orig_raw_t1_memory
        exp.sham_for = _orig_sham_for


if __name__ == "__main__":
    main()
