#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import v145_precompiled_runner  # noqa: F401
import bugsinpy_four_arm as base
import bugsinpy_exact_runtime as exact_runtime
import structured_edit_protocol_v2 as sed

T2 = ("youtube-dl", 32)
RAW_ARM = "D_PLUS_RAW_T1"
CALL1_SHA = "69002ebf51a2842e41639dd21d1d5c196ee65feac42470bdbef24067264f40bb"

base.native_test = exact_runtime.native_test


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def project_edit_payloads(text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    dec = json.JSONDecoder()
    pos = 0
    accepted: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    ordinal = 0
    needle = '"edits":'
    while True:
        k = text.find(needle, pos)
        if k < 0:
            break
        ordinal += 1
        start = k + len(needle)
        row: dict[str, Any] = {"ordinal": ordinal, "key_offset": k}
        try:
            value, end = dec.raw_decode(text, start)
            row["decoded_end"] = end
            if not isinstance(value, list):
                raise ValueError("edits field did not decode to array")
            payload = sed.extract_edits(json.dumps({"edits": value}, ensure_ascii=False))
            h = sha_text(payload)
            row.update(status="VALID", payload_sha256=h, changed_files=sed.changed_files(payload))
            accepted.append({"ordinal": ordinal, "payload": payload, "payload_sha256": h})
            pos = end
        except Exception as exc:
            row.update(status="INVALID", error=f"{exc.__class__.__name__}: {exc}")
            pos = start + 1
        audit.append(row)
    return accepted, audit


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v153-result", type=Path, required=True)
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("output exists; refusing overwrite")
    args.out.mkdir(parents=True)

    source_bytes = args.v153_result.read_bytes()
    source = json.loads(source_bytes)
    result: dict[str, Any] = {
        "canonical_id": "V153F_EXHAUSTIVE_RIVAL_REPLAY_DIAGNOSTIC",
        "protocol": "protocols/V153F_EXHAUSTIVE_RIVAL_REPLAY_DIAGNOSTIC.md",
        "source_v153_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "source_v153_verdict": source.get("verdict"),
        "model_calls": 0,
        "call1_payload_sha256": CALL1_SHA,
        "rows": [],
    }

    infra_errors = 0
    total_distinct = 0
    total_executable = 0
    total_failed = 0
    total_solved = 0

    raw_rows = source.get("rows", {}).get(RAW_ARM, [])
    for rr in raw_rows:
        call2 = next((a for a in rr.get("attempts", []) if a.get("call") == 2), None)
        row: dict[str, Any] = {"seed": rr.get("seed"), "rivals": []}
        if not call2 or not isinstance((call2.get("response") or {}).get("text"), str):
            row["status"] = "NO_CALL2_TEXT"
            result["rows"].append(row)
            continue

        accepted, audit = project_edit_payloads(call2["response"]["text"])
        row["projection_audit"] = audit

        seen: set[str] = set()
        distinct: list[dict[str, Any]] = []
        for p in accepted:
            h = p["payload_sha256"]
            if h == CALL1_SHA or h in seen:
                continue
            seen.add(h)
            distinct.append(p)

        row["distinct_rival_count"] = len(distinct)
        total_distinct += len(distinct)

        for p in distinct:
            r: dict[str, Any] = {
                "ordinal": p["ordinal"],
                "payload_sha256": p["payload_sha256"],
            }
            with tempfile.TemporaryDirectory(prefix=f"v153f-{rr.get('seed')}-{p['ordinal']}-") as td:
                try:
                    work = base.checkout_buggy(args.bugsinpy, T2[0], T2[1], Path(td))
                    sed.apply_edits(work, p["payload"])
                except Exception as exc:
                    r.update(status="TRANSPORT_FAILURE", error=f"{exc.__class__.__name__}: {exc}")
                    row["rivals"].append(r)
                    continue

                verdict = exact_runtime.native_test(args.bugsinpy, work)
                r["native_verdict"] = verdict
                if verdict.get("infrastructure_error"):
                    infra_errors += 1
                    r.update(status="R10", error=verdict["infrastructure_error"])
                elif verdict.get("passed"):
                    total_executable += 1
                    total_solved += 1
                    r.update(status="VERIFIED_SOLVED")
                else:
                    total_executable += 1
                    total_failed += 1
                    r.update(status="VERIFIED_FAILED")
            row["rivals"].append(r)

        if any(r.get("status") == "VERIFIED_SOLVED" for r in row["rivals"]):
            row["status"] = "HAS_SOLVING_RIVAL"
        elif any(r.get("status") in {"VERIFIED_FAILED", "VERIFIED_SOLVED"} for r in row["rivals"]):
            row["status"] = "EXECUTABLE_RIVALS_ALL_FAILED"
        elif distinct:
            row["status"] = "RIVALS_NOT_EXECUTABLE"
        else:
            row["status"] = "NO_DISTINCT_RIVALS"
        result["rows"].append(row)

    result["summary"] = {
        "raw_seeds": len(result["rows"]),
        "distinct_frozen_rivals": total_distinct,
        "executable_rivals": total_executable,
        "verified_failed_rivals": total_failed,
        "verified_solved_rivals": total_solved,
        "infrastructure_errors": infra_errors,
    }

    if infra_errors:
        verdict = "R10_DIAGNOSTIC_INCONCLUSIVE"
    elif total_solved >= 1:
        verdict = "DIAGNOSTIC_V153_SELECTION_POLICY_OBSTRUCTION"
    elif total_executable >= 2:
        verdict = "DIAGNOSTIC_V153_CANDIDATE_SET_SEMANTIC_TRAP"
    elif total_distinct >= 1:
        verdict = "DIAGNOSTIC_V153_EXECUTION_COVERAGE_INSUFFICIENT"
    else:
        verdict = "DIAGNOSTIC_V153_NO_DISTINCT_FROZEN_RIVALS"
    result["verdict"] = verdict

    p = args.out / "V153F_RESULT.json"
    p.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(p.read_text())


if __name__ == "__main__":
    main()
