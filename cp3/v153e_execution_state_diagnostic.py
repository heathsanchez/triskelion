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
from v153d_rival_payload_projection_diagnostic import project_edit_payloads

T2 = ("youtube-dl", 32)
RAW_ARM = "D_PLUS_RAW_T1"

base.native_test = exact_runtime.native_test


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


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
    rows: list[dict[str, Any]] = []

    for rr in source.get("rows", {}).get(RAW_ARM, []):
        row: dict[str, Any] = {"seed": rr.get("seed")}
        call1 = next((a for a in rr.get("attempts", []) if a.get("call") == 1), None)
        call2 = next((a for a in rr.get("attempts", []) if a.get("call") == 2), None)
        if not call1 or not call2:
            row["status"] = "MISSING_FROZEN_ATTEMPT"
            rows.append(row); continue
        try:
            call1_text = call1["response"]["text"]
            p1 = sed.extract_edits(call1_text)
            h1 = sha_text(p1)
        except Exception as exc:
            row.update(status="CALL1_PARSE_FAILURE", error=f"{exc.__class__.__name__}: {exc}")
            rows.append(row); continue

        accepted, audit = project_edit_payloads(call2["response"]["text"])
        seen: set[str] = set()
        selected = None
        for p in accepted:
            h = p["payload_sha256"]
            dup = h in seen
            seen.add(h)
            if selected is None and h != h1 and not dup:
                selected = p
        row["call1_payload_sha256"] = h1
        row["projection_audit"] = audit
        if selected is None:
            row["status"] = "NO_DISTINCT_PROJECTED_RIVAL"
            rows.append(row); continue
        row["selected_rival_ordinal"] = selected["ordinal"]
        row["selected_rival_sha256"] = selected["payload_sha256"]

        with tempfile.TemporaryDirectory(prefix=f"v153e-{rr.get('seed')}-") as td:
            try:
                work = base.checkout_buggy(args.bugsinpy, T2[0], T2[1], Path(td))
                sed.apply_edits(work, p1)
                row["call1_applied"] = True
                sed.apply_edits(work, selected["payload"])
                row["rival_applied_on_call1_state"] = True
            except Exception as exc:
                row.update(status="STATEFUL_TRANSPORT_FAILURE", error=f"{exc.__class__.__name__}: {exc}")
                rows.append(row); continue
            verdict = exact_runtime.native_test(args.bugsinpy, work)
            row["native_verdict"] = verdict
            if verdict.get("infrastructure_error"):
                row.update(status="R10", error=verdict["infrastructure_error"])
            elif verdict.get("passed"):
                row["status"] = "VERIFIED_SOLVED"
            else:
                row["status"] = "VERIFIED_FAILED"
        rows.append(row)

    reached = sum(1 for r in rows if r.get("status") in {"VERIFIED_SOLVED", "VERIFIED_FAILED"})
    solved = sum(1 for r in rows if r.get("status") == "VERIFIED_SOLVED")
    r10 = sum(1 for r in rows if r.get("status") == "R10")
    if r10:
        verdict = "R10_DIAGNOSTIC_INCONCLUSIVE"
    elif solved:
        verdict = "DIAGNOSTIC_V153_STATEFUL_EXECUTION_SOLVES_T2"
    elif reached:
        verdict = "DIAGNOSTIC_V153_STATEFUL_EXECUTION_REACHES_VERIFIER"
    else:
        verdict = "DIAGNOSTIC_V153_STATEFUL_EXECUTION_NOT_SUPPORTED"
    result = {
        "canonical_id": "V153E_EXECUTION_STATE_DIAGNOSTIC",
        "source_v153_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "model_calls": 0,
        "rows": rows,
        "summary": {"raw_seeds": len(rows), "stateful_rivals_reaching_verifier": reached, "stateful_rivals_solved": solved, "r10": r10},
        "verdict": verdict,
    }
    p = args.out / "V153E_RESULT.json"
    p.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(p.read_text())

if __name__ == "__main__":
    main()
