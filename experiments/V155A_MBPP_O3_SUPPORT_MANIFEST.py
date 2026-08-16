#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

PROTOCOL = "V155A_MBPP_O3_SUPPORT_MANIFEST"
UPSTREAM_COMMIT = "1eb8bb0cbe5fd9072311ae3fd760e3644fee690b"
DATA_URL = f"https://raw.githubusercontent.com/google-research/google-research/{UPSTREAM_COMMIT}/mbpp/sanitized-mbpp.json"
REQUIRED_KEYS = {"task_id", "code", "test_imports", "test_list"}
MIN_MULTI_SITE_TASKS = 20
MIN_TOTAL_STRICT_SITES = 50
TIMEOUT_SECONDS = 5


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch_dataset() -> bytes:
    req = urllib.request.Request(DATA_URL, headers={"User-Agent": "triskelion-v155a"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def strict_sites(code: str) -> tuple[list[dict[str, Any]], str | None]:
    try:
        tree = ast.parse(code)
    except Exception as exc:
        return [], f"{exc.__class__.__name__}: {exc}"
    out: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1 or len(node.comparators) != 1:
            continue
        op_obj = node.ops[0]
        if isinstance(op_obj, ast.Lt):
            op = "<"
        elif isinstance(op_obj, ast.Gt):
            op = ">"
        else:
            continue
        out.append({"lineno": int(node.lineno), "col_offset": int(node.col_offset), "operator": op})
    out.sort(key=lambda x: (x["lineno"], x["col_offset"], x["operator"]))
    return out, None


def baseline_task(rec: dict[str, Any]) -> dict[str, Any]:
    task_id = rec["task_id"]
    code = rec["code"]
    imports = rec.get("test_imports") or []
    tests = rec.get("test_list") or []
    sites, parse_error = strict_sites(code)
    row: dict[str, Any] = {
        "task_id": task_id,
        "strict_site_count": len(sites),
        "strict_sites": sites,
        "parse_error": parse_error,
    }
    if parse_error:
        row.update(baseline_valid=False, baseline_status="PARSE_FAIL")
        return row
    payload = "\n".join([*imports, code, *tests]) + "\n"
    with tempfile.TemporaryDirectory(prefix=f"v155a_{task_id}_") as td:
        p = Path(td) / "task.py"
        p.write_text(payload, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(p)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=TIMEOUT_SECONDS,
            )
            row["baseline_returncode"] = proc.returncode
            row["baseline_output_tail"] = proc.stdout[-2000:]
            row["baseline_valid"] = proc.returncode == 0
            row["baseline_status"] = "PASS" if proc.returncode == 0 else "TEST_FAIL"
        except subprocess.TimeoutExpired as exc:
            row.update(
                baseline_valid=False,
                baseline_status="TIMEOUT",
                baseline_output_tail=(exc.stdout or "")[-2000:] if isinstance(exc.stdout, str) else "",
            )
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    try:
        raw = fetch_dataset()
        data = json.loads(raw)
    except Exception as exc:
        result = {"protocol": PROTOCOL, "verdict": "R10_INCONCLUSIVE", "reason": f"dataset_fetch_or_parse:{exc.__class__.__name__}:{exc}"}
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2)); return

    schema = {
        "top_level_type": type(data).__name__,
        "item_count": len(data) if isinstance(data, list) else None,
        "first_item_keys": sorted(data[0].keys()) if isinstance(data, list) and data and isinstance(data[0], dict) else None,
        "dataset_sha256": sha256_bytes(raw),
    }
    print("SCHEMA_FIRST", json.dumps(schema, sort_keys=True), flush=True)
    if not isinstance(data, list) or not data or not all(isinstance(x, dict) and REQUIRED_KEYS <= set(x) for x in data):
        result = {"protocol": PROTOCOL, "verdict": "R10_INCONCLUSIVE", "reason": "schema_mismatch", "schema": schema}
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2)); return

    rows: list[dict[str, Any]] = []
    for rec in data:
        row = baseline_task(rec)
        rows.append(row)
        print(json.dumps({k: row.get(k) for k in ["task_id", "baseline_status", "strict_site_count"]}, sort_keys=True), flush=True)

    baseline_valid = [r for r in rows if r.get("baseline_valid")]
    multi = [r for r in baseline_valid if r.get("strict_site_count", 0) >= 2]
    total_sites = sum(int(r.get("strict_site_count", 0)) for r in baseline_valid)
    complete = len(rows) == len(data)
    if not complete:
        verdict = "R10_INCONCLUSIVE"
    elif len(multi) >= MIN_MULTI_SITE_TASKS and total_sites >= MIN_TOTAL_STRICT_SITES:
        verdict = "PASS_V155A_MBPP_O3_SUPPORT_MANIFEST"
    else:
        verdict = "CORPUS_CEILING_V155A_MBPP_O3_SUPPORT"

    result = {
        "protocol": PROTOCOL,
        "verdict": verdict,
        "upstream_repo": "google-research/google-research",
        "upstream_commit": UPSTREAM_COMMIT,
        "dataset_path": "mbpp/sanitized-mbpp.json",
        "schema": schema,
        "complete_audit": complete,
        "task_count": len(rows),
        "baseline_valid_task_count": len(baseline_valid),
        "baseline_invalid_task_count": len(rows) - len(baseline_valid),
        "baseline_valid_multi_strict_task_count": len(multi),
        "baseline_valid_total_strict_sites": total_sites,
        "min_multi_site_tasks": MIN_MULTI_SITE_TASKS,
        "min_total_strict_sites": MIN_TOTAL_STRICT_SITES,
        "rows": rows,
        "claim_boundary": "Source/support manifest only; no comparison relaxation, SAFE/SENSITIVE labels, O3 fitting, or developmental claim.",
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ["verdict", "task_count", "baseline_valid_task_count", "baseline_valid_multi_strict_task_count", "baseline_valid_total_strict_sites"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
