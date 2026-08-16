#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

# Reuse V145A's runtime optimization only. We deliberately bypass its candidate
# apply wrapper below so V150 can compare strict apply with strict->recount.
import v145_precompiled_runner  # noqa: F401
import bugsinpy_four_arm as base
import bugsinpy_exact_runtime as exact
import v145_natural_third_rung_causal as v145

EXPECTED_RESULT_SHA256 = "cf93c37fe1a3a5aaeba7add755fbb3e5b5b33c123273a915683d564777cb33b9"
EXPECTED_MODEL = "Qwen/Qwen3.5-9B"
EXPECTED_SEEDS = [202608161, 202608162, 202608163]
EXPECTED_ARMS = ["D_COLD", "D_PLUS_O1", "D_PLUS_SHAM"]
TASK = ("youtube-dl", 32)


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def run_git(work: Path, args: list[str]) -> dict[str, Any]:
    started = time.perf_counter()
    p = subprocess.run(["git", *args], cwd=work, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    return {
        "returncode": p.returncode,
        "output": p.stdout[-8000:],
        "duration_ms": round((time.perf_counter() - started) * 1000, 3),
    }


def transport(work: Path, diff: str) -> dict[str, Any]:
    paths = v145.changed_files(diff)
    if v145.rejects_tests(paths):
        return {"status": "FORBIDDEN_TEST_EDIT", "changed_files": paths}
    with tempfile.NamedTemporaryFile("w", suffix=".diff", encoding="utf-8", delete=False) as fh:
        fh.write(diff)
        patch = Path(fh.name)
    try:
        strict_check = run_git(work, ["apply", "--check", str(patch)])
        if strict_check["returncode"] == 0:
            strict_apply = run_git(work, ["apply", str(patch)])
            if strict_apply["returncode"] != 0:
                return {
                    "status": "STRICT_APPLY_RACE_FAILURE", "changed_files": paths,
                    "strict_check": strict_check, "strict_apply": strict_apply,
                }
            return {
                "status": "APPLIED_STRICT", "changed_files": paths,
                "strict_check": strict_check, "strict_apply": strict_apply,
            }

        recount_check = run_git(work, ["apply", "--check", "--recount", str(patch)])
        if recount_check["returncode"] != 0:
            return {
                "status": "UNTRANSPORTABLE", "changed_files": paths,
                "strict_check": strict_check, "recount_check": recount_check,
            }
        recount_apply = run_git(work, ["apply", "--recount", str(patch)])
        if recount_apply["returncode"] != 0:
            return {
                "status": "RECOUNT_APPLY_RACE_FAILURE", "changed_files": paths,
                "strict_check": strict_check, "recount_check": recount_check,
                "recount_apply": recount_apply,
            }
        return {
            "status": "APPLIED_RECOUNT", "changed_files": paths,
            "strict_check": strict_check, "recount_check": recount_check,
            "recount_apply": recount_apply,
        }
    finally:
        patch.unlink(missing_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v149-result", required=True)
    ap.add_argument("--bugsinpy", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    result_path = Path(a.v149_result)
    raw = result_path.read_bytes()
    actual_sha = sha_bytes(raw)
    if actual_sha != EXPECTED_RESULT_SHA256:
        raise SystemExit(f"R10 artifact hash mismatch: {actual_sha}")
    frozen = json.loads(raw)
    if frozen.get("canonical_id") != "V145_NATURAL_THIRD_RUNG_CAUSAL":
        raise SystemExit("R10 wrong canonical id")
    if frozen.get("model") != EXPECTED_MODEL or frozen.get("seeds") != EXPECTED_SEEDS:
        raise SystemExit("R10 frozen model/seed mismatch")
    t2 = frozen.get("T2") or {}
    rows = t2.get("rows") or {}
    if sorted(rows) != sorted(EXPECTED_ARMS):
        raise SystemExit("R10 frozen arm mismatch")

    bugsinpy = Path(a.bugsinpy)

    # One baseline creates/validates the reusable exact-runtime template.
    with tempfile.TemporaryDirectory(prefix="v150-baseline-") as td:
        work = base.checkout_buggy(bugsinpy, TASK[0], TASK[1], Path(td))
        baseline = exact.native_test(bugsinpy, work)
    if baseline.get("infrastructure_error"):
        raise SystemExit("R10 baseline infrastructure error: " + str(baseline["infrastructure_error"]))
    if baseline.get("passed"):
        raise SystemExit("R10 baseline unexpectedly passes")

    replay_rows: list[dict[str, Any]] = []
    for arm in EXPECTED_ARMS:
        for source_row in rows[arm]:
            seed = source_row["seed"]
            for attempt in source_row.get("attempts", []):
                call = attempt["call"]
                response = attempt.get("response") or {}
                text = response.get("text") or ""
                row: dict[str, Any] = {
                    "arm": arm,
                    "seed": seed,
                    "call": call,
                    "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "v149_patch_error": attempt.get("patch_error"),
                }
                try:
                    diff = base.extract_diff(text)
                except Exception as exc:
                    row.update(status="EXTRACT_FAILURE", error=f"{exc.__class__.__name__}: {exc}")
                    replay_rows.append(row)
                    continue
                row["diff_sha256"] = hashlib.sha256(diff.encode()).hexdigest()

                with tempfile.TemporaryDirectory(prefix=f"v150-{arm}-{seed}-{call}-") as td:
                    work = base.checkout_buggy(bugsinpy, TASK[0], TASK[1], Path(td))
                    tr = transport(work, diff)
                    row["transport"] = tr
                    if tr["status"] not in {"APPLIED_STRICT", "APPLIED_RECOUNT"}:
                        row["status"] = tr["status"]
                        replay_rows.append(row)
                        continue
                    verdict = exact.native_test(bugsinpy, work)
                    row["verdict"] = verdict
                    if verdict.get("infrastructure_error"):
                        row["status"] = "R10"
                    elif verdict.get("passed"):
                        row["status"] = "VERIFIED_SOLVED"
                    else:
                        row["status"] = "VERIFIED_FAILED"
                    replay_rows.append(row)

    by_arm: dict[str, dict[str, int]] = {}
    for arm in EXPECTED_ARMS:
        rr = [x for x in replay_rows if x["arm"] == arm]
        by_arm[arm] = {
            "n": len(rr),
            "strict_applied": sum(x.get("transport", {}).get("status") == "APPLIED_STRICT" for x in rr),
            "recount_applied": sum(x.get("transport", {}).get("status") == "APPLIED_RECOUNT" for x in rr),
            "untransportable": sum(x.get("transport", {}).get("status") == "UNTRANSPORTABLE" for x in rr),
            "verifier_reached": sum("verdict" in x for x in rr),
            "verified_solved": sum(x.get("status") == "VERIFIED_SOLVED" for x in rr),
        }

    rescued = [x for x in replay_rows if x.get("transport", {}).get("status") == "APPLIED_RECOUNT"]
    o1_solved = [x for x in replay_rows if x["arm"] == "D_PLUS_O1" and x.get("status") == "VERIFIED_SOLVED"]
    any_r10 = any(x.get("status") == "R10" for x in replay_rows)
    if any_r10:
        verdict = "R10_INCONCLUSIVE"
    elif o1_solved:
        verdict = "PASS_V150_O1_POSTHOC_SEMANTIC_CANDIDATE_EXISTS"
    elif rescued:
        verdict = "PASS_V150_NO_O1_SEMANTIC_RESCUE"
    else:
        verdict = "NULL_V150_RECOUNT_DOES_NOT_APPLY"

    out = {
        "canonical_id": "V150_FROZEN_OUTPUT_TRANSPORT_REPLAY",
        "verdict": verdict,
        "claim_boundary": "Post-hoc transport diagnostic only; never a causal O1->O2 result.",
        "source_run_id": 31941708089,
        "source_result_sha256": actual_sha,
        "task": "youtube-dl/32",
        "model_calls": 0,
        "candidate_content_mutations": 0,
        "baseline": baseline,
        "summary": by_arm,
        "recount_rescued_n": len(rescued),
        "o1_verified_solved_n": len(o1_solved),
        "rows": replay_rows,
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ["verdict", "summary", "recount_rescued_n", "o1_verified_solved_n"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
