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
        "canonical_id": "V153D_RIVAL_PAYLOAD_PROJECTION_DIAGNOSTIC",
        "source_v153_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "source_v153_verdict": source.get("verdict"),
        "model_calls": 0,
        "call1_payload_sha256": CALL1_SHA,
        "rows": [],
    }

    raw_rows = source.get("rows", {}).get(RAW_ARM, [])
    for rr in raw_rows:
        call2 = next((a for a in rr.get("attempts", []) if a.get("call") == 2), None)
        row: dict[str, Any] = {"seed": rr.get("seed")}
        if not call2 or not isinstance((call2.get("response") or {}).get("text"), str):
            row.update(status="NO_CALL2_TEXT")
            result["rows"].append(row)
            continue
        text = call2["response"]["text"]
        accepted, audit = project_edit_payloads(text)
        row["projection_audit"] = audit
        row["valid_projected_payloads"] = len(accepted)
        seen: set[str] = set()
        selected = None
        for p in accepted:
            h = p["payload_sha256"]
            duplicate_earlier = h in seen
            seen.add(h)
            p["duplicates_call1"] = h == CALL1_SHA
            p["duplicates_earlier"] = duplicate_earlier
            if selected is None and h != CALL1_SHA and not duplicate_earlier:
                selected = p
        row["projected_payloads"] = [{k:v for k,v in p.items() if k != "payload"} for p in accepted]
        if selected is None:
            row.update(status="NO_DISTINCT_PROJECTED_RIVAL")
            result["rows"].append(row)
            continue

        row["selected_ordinal"] = selected["ordinal"]
        row["selected_payload_sha256"] = selected["payload_sha256"]
        with tempfile.TemporaryDirectory(prefix=f"v153d-{rr.get('seed')}-") as td:
            try:
                work = base.checkout_buggy(args.bugsinpy, T2[0], T2[1], Path(td))
                sed.apply_edits(work, selected["payload"])
            except Exception as exc:
                row.update(status="SELECTED_TRANSPORT_FAILURE", error=f"{exc.__class__.__name__}: {exc}")
                result["rows"].append(row)
                continue
            verdict = exact_runtime.native_test(args.bugsinpy, work)
            row["native_verdict"] = verdict
            if verdict.get("infrastructure_error"):
                row.update(status="R10", error=verdict["infrastructure_error"])
            elif verdict.get("passed"):
                row.update(status="VERIFIED_SOLVED")
            else:
                row.update(status="VERIFIED_FAILED")
        result["rows"].append(row)

    present = sum(1 for r in result["rows"] if r.get("selected_payload_sha256"))
    reached = sum(1 for r in result["rows"] if r.get("status") in {"VERIFIED_SOLVED", "VERIFIED_FAILED"})
    solved = sum(1 for r in result["rows"] if r.get("status") == "VERIFIED_SOLVED")
    r10 = sum(1 for r in result["rows"] if r.get("status") == "R10")
    result["summary"] = {
        "raw_seeds": len(result["rows"]),
        "distinct_payload_rival_seeds": present,
        "selected_rivals_reaching_verifier": reached,
        "selected_rivals_solved": solved,
        "r10": r10,
        "payload_rivals_present": present >= 2,
        "payload_rivals_reach_verifier": reached >= 1,
        "payload_rival_solves_t2": solved >= 1,
    }
    if r10:
        result["verdict"] = "R10_DIAGNOSTIC_INCONCLUSIVE"
    elif solved:
        result["verdict"] = "DIAGNOSTIC_V153_PAYLOAD_RIVAL_SOLVES_T2"
    elif present >= 2 and reached >= 1:
        result["verdict"] = "DIAGNOSTIC_V153_PAYLOAD_RIVALS_REACH_VERIFIER"
    elif present >= 2:
        result["verdict"] = "DIAGNOSTIC_V153_PAYLOAD_RIVALS_PRESENT"
    else:
        result["verdict"] = "DIAGNOSTIC_V153_PAYLOAD_RIVALS_NOT_ESTABLISHED"

    p = args.out / "V153D_RESULT.json"
    p.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(p.read_text())


if __name__ == "__main__":
    main()
