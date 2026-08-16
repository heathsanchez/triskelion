#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import bugsinpy_four_arm as base
import structured_edit_protocol_v2 as sed

T2 = ("youtube-dl", 32)
ARMS = ["D_COLD", "D_PLUS_O1_COMPILED", "D_PLUS_RAW_T1", "D_PLUS_SHAM_O1", "D_PLUS_SHAM_RAW"]


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def strip_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        first = s.find("\n")
        last = s.rfind("```")
        if first >= 0 and last > first:
            s = s[first + 1:last].strip()
    return s


def parse_alternatives(text: str) -> tuple[list[dict[str, Any]], str | None]:
    raw = strip_fences(text)
    try:
        obj = json.loads(raw)
    except Exception:
        # bounded recovery: decode the first JSON object only
        i = raw.find("{")
        if i < 0:
            return [], "NO_JSON_OBJECT"
        try:
            obj, _ = json.JSONDecoder().raw_decode(raw, i)
        except Exception as exc:
            return [], f"JSON_DECODE: {exc.__class__.__name__}: {exc}"
    alts = obj.get("alternatives") if isinstance(obj, dict) else None
    if not isinstance(alts, list):
        return [], "NO_ALTERNATIVES_LIST"
    out: list[dict[str, Any]] = []
    for rank, alt in enumerate(alts[:3], start=1):
        row: dict[str, Any] = {"rank": rank}
        if not isinstance(alt, dict) or not isinstance(alt.get("edits"), list):
            row.update(status="INVALID", error="alternative missing edits list")
            out.append(row)
            continue
        try:
            payload = sed.extract_edits(json.dumps({"edits": alt["edits"]}, ensure_ascii=False))
            row.update(status="VALID", payload=payload, payload_sha256=sha_text(payload), diagnosis=alt.get("diagnosis"))
        except Exception as exc:
            row.update(status="INVALID", error=f"{exc.__class__.__name__}: {exc}")
        out.append(row)
    return out, None


def referenced_paths(payloads: list[str]) -> set[str]:
    paths: set[str] = set()
    for p in payloads:
        for e in json.loads(p)["edits"]:
            paths.add(e["path"])
    return paths


def load_state(work: Path, paths: set[str]) -> dict[str, str | None]:
    state: dict[str, str | None] = {}
    for rel in paths:
        f = work / rel
        state[rel] = f.read_text(encoding="utf-8") if f.is_file() else None
    return state


def simulate(state0: dict[str, str | None], payload: str) -> tuple[bool, dict[str, str | None], dict[str, Any] | None]:
    state = dict(state0)
    for idx, edit in enumerate(json.loads(payload)["edits"], start=1):
        rel = edit["path"]
        text = state.get(rel)
        if text is None:
            return False, state, {"edit_index": idx, "path": rel, "reason": "MISSING_FILE", "old_count": None}
        count = text.count(edit["old"])
        if count != 1:
            return False, state, {"edit_index": idx, "path": rel, "reason": "OLD_COUNT_NOT_ONE", "old_count": count, "old_sha256": sha_text(edit["old"])}
        state[rel] = text.replace(edit["old"], edit["new"], 1)
    return True, state, None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v154-result", type=Path, required=True)
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("output exists; refusing overwrite")
    args.out.mkdir(parents=True)

    src_bytes = args.v154_result.read_bytes()
    src = json.loads(src_bytes)
    result: dict[str, Any] = {
        "canonical_id": "V154A_ACTUAL_STATE_RIVAL_GROUNDING_AUDIT",
        "protocol": "protocols/V154A_ACTUAL_STATE_RIVAL_GROUNDING_AUDIT.md",
        "source_v154_sha256": hashlib.sha256(src_bytes).hexdigest(),
        "source_v154_verdict": src.get("verdict"),
        "source_v154_commit": "d13d1f0c5b22570a33da321cf995233514e3b0c1",
        "model_calls": 0,
        "verifier_calls": 0,
        "rows": [],
    }

    missed = 0
    mixed_state = 0
    actual_exec = 0
    valid_total = 0
    inconsistencies = 0

    for arm in ARMS:
        for rr in src.get("rows", {}).get(arm, []):
            seed = rr.get("seed")
            attempts = rr.get("attempts", [])
            c1 = next((a for a in attempts if a.get("call") == 1), None)
            c2 = next((a for a in attempts if a.get("call") == 2), None)
            row: dict[str, Any] = {"arm": arm, "seed": seed, "alternatives": []}
            if not c2 or not isinstance((c2.get("response") or {}).get("text"), str):
                row["status"] = "NO_CALL2_RESPONSE"
                result["rows"].append(row)
                continue

            call1_payload: str | None = None
            call1_applied = bool(c1 and isinstance(c1.get("verdict"), dict))
            if call1_applied:
                try:
                    call1_payload = sed.extract_edits(c1["response"]["text"])
                except Exception as exc:
                    result.update(verdict="R10_DIAGNOSTIC_INCONCLUSIVE", reason=f"cannot reconstruct applied call1 {arm}/{seed}: {exc}")
                    p=args.out/"V154A_RESULT.json"; p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(p.read_text()); return

            alts, parse_error = parse_alternatives(c2["response"]["text"])
            row["parse_error"] = parse_error
            selected_sha = c2.get("selected_payload_sha256")
            row["selected_payload_sha256"] = selected_sha
            row["selected_reached_verifier_in_v154"] = isinstance(c2.get("verdict"), dict)
            row["v154_transport_error"] = c2.get("transport_error")
            row["actual_state"] = "POST_CALL1" if call1_applied else "CLEAN"

            payloads = [a["payload"] for a in alts if a.get("status") == "VALID"]
            if call1_payload:
                payloads.append(call1_payload)
            paths = referenced_paths(payloads) if payloads else set()

            try:
                with tempfile.TemporaryDirectory(prefix=f"v154a-{arm}-{seed}-") as td:
                    work = base.checkout_buggy(args.bugsinpy, T2[0], T2[1], Path(td))
                    clean = load_state(work, paths)
            except Exception as exc:
                result.update(verdict="R10_DIAGNOSTIC_INCONCLUSIVE", reason=f"clean checkout {arm}/{seed}: {exc}")
                p=args.out/"V154A_RESULT.json"; p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(p.read_text()); return

            actual = clean
            if call1_payload:
                ok, actual2, fail = simulate(clean, call1_payload)
                if not ok:
                    result.update(verdict="R10_DIAGNOSTIC_INCONCLUSIVE", reason=f"recorded applied call1 does not simulate {arm}/{seed}: {fail}")
                    p=args.out/"V154A_RESULT.json"; p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(p.read_text()); return
                actual = actual2

            selected_actual = None
            nonselected_exec = False
            for alt in alts:
                ar = {k:v for k,v in alt.items() if k != "payload"}
                if alt.get("status") != "VALID":
                    row["alternatives"].append(ar)
                    continue
                valid_total += 1
                h = alt["payload_sha256"]
                ar["duplicates_call1"] = bool(call1_payload and h == sha_text(call1_payload))
                ar["was_selected"] = h == selected_sha
                clean_ok, _, clean_fail = simulate(clean, alt["payload"])
                actual_ok, _, actual_fail = simulate(actual, alt["payload"])
                ar["clean_applies"] = clean_ok
                ar["clean_failure"] = clean_fail
                ar["actual_applies"] = actual_ok
                ar["actual_failure"] = actual_fail
                if actual_ok and not ar["duplicates_call1"]:
                    actual_exec += 1
                    if not ar["was_selected"]:
                        nonselected_exec = True
                if ar["was_selected"]:
                    selected_actual = actual_ok
                if (not actual_ok) and clean_ok and call1_applied:
                    mixed_state += 1
                row["alternatives"].append(ar)

            selected_reached = row["selected_reached_verifier_in_v154"]
            if selected_sha and selected_actual is True and not selected_reached:
                inconsistencies += 1
                row["execution_audit_inconsistent"] = True
            if selected_reached is False and nonselected_exec:
                missed += 1
                row["missed_executable_rival"] = True
            else:
                row["missed_executable_rival"] = False
            row["status"] = "AUDITED"
            result["rows"].append(row)

    result["summary"] = {
        "valid_projected_alternatives": valid_total,
        "actual_state_executable_alternatives": actual_exec,
        "missed_executable_rival_arm_seeds": missed,
        "clean_only_while_actual_post_call1": mixed_state,
        "execution_audit_inconsistencies": inconsistencies,
    }

    if inconsistencies:
        verdict = "R10_V154_EXECUTION_AUDIT_INCONSISTENT"
    elif missed:
        verdict = "DIAGNOSTIC_V154_SELECTION_POLICY_MISSES_EXECUTABLE_RIVAL"
    elif mixed_state:
        verdict = "DIAGNOSTIC_V154_STATE_SEMANTICS_STILL_MIXED"
    elif valid_total and actual_exec == 0:
        verdict = "DIAGNOSTIC_V154_CANDIDATE_SET_NOT_EXECUTABLE_ON_ACTUAL_STATE"
    elif actual_exec:
        verdict = "DIAGNOSTIC_V154_EXECUTABLE_RIVALS_EXIST_BUT_NO_SELECTION_MISS"
    else:
        verdict = "R10_DIAGNOSTIC_INCONCLUSIVE"
    result["verdict"] = verdict

    p=args.out/"V154A_RESULT.json"
    p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(p.read_text())


if __name__ == "__main__":
    main()
