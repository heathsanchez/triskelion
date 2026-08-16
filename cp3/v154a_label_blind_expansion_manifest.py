#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import qualify_remaining as q
import bugsinpy_exact_runtime as exact
import v145r1_qualify_clean_pandas_exact as checkout

PROTOCOL = "V154A_LABEL_BLIND_EXPANSION_MANIFEST"
CASES_PER_PROJECT = 2
MIN_STRICT_SITES = 3
EXCLUDED_PARTS = {
    "test", "tests", "testing", ".git", ".cp3_tools", "env", "venv", ".venv",
    "site-packages", "build", "dist", "doc", "docs", "example", "examples",
    "benchmark", "benchmarks",
}


def site_rank(path: str, lineno: int, col: int, op: str) -> str:
    return hashlib.sha256(f"{path}:{lineno}:{col}:{op}".encode()).hexdigest()


def production_file(rel: Path) -> bool:
    low = [p.lower() for p in rel.parts]
    name = rel.name.lower()
    if any(p in EXCLUDED_PARTS for p in low):
        return False
    if name.startswith("test_") or name.endswith("_test.py"):
        return False
    return rel.suffix == ".py"


def strict_sites(work: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    sites: list[dict[str, Any]] = []
    parse_errors: list[dict[str, str]] = []
    for p in sorted(work.rglob("*.py")):
        try:
            rel = p.relative_to(work)
        except Exception:
            continue
        if not production_file(rel):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="strict")
            tree = ast.parse(text)
        except Exception as exc:
            parse_errors.append({"path": str(rel), "error": f"{exc.__class__.__name__}: {exc}"})
            continue
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
            rec = {
                "relative_path": str(rel),
                "lineno": int(node.lineno),
                "col_offset": int(node.col_offset),
                "operator": op,
            }
            rec["site_rank"] = site_rank(rec["relative_path"], rec["lineno"], rec["col_offset"], op)
            sites.append(rec)
    sites.sort(key=lambda r: (r["site_rank"], r["relative_path"], r["lineno"], r["col_offset"], r["operator"]))
    return sites, parse_errors


def selected_cases(manifest: list[tuple[str, int]]) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for project in q.EXPECTED_PROJECTS:
        ids = sorted([i for p, i in manifest if p == project], key=lambda i: q.candidate_rank(project, i))
        out.extend((project, i) for i in ids[:CASES_PER_PROJECT])
    return out


def classify_case(repo: Path, project: str, bug_id: int) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "case": f"{project}/{bug_id}",
        "project": project,
        "bug_id": bug_id,
        "case_rank": q.candidate_rank(project, bug_id),
        "selected_without_substitution": True,
    }
    with tempfile.TemporaryDirectory(prefix=f"v154a_{project}_{bug_id}_") as td:
        root = Path(td)
        try:
            work = checkout.checkout_version(repo, project, bug_id, 1, root / "fixed")
        except Exception as exc:
            rec.update(status="CHECKOUT_INELIGIBLE", eligible=False, reason=f"{exc.__class__.__name__}: {exc}")
            return rec

        try:
            version = exact._python_version(work)
        except Exception as exc:
            rec.update(status="RUNTIME_METADATA_INELIGIBLE", eligible=False, reason=f"{exc.__class__.__name__}: {exc}")
            return rec
        rec["python_version"] = version
        if version not in exact.PYTHON_IMAGES:
            rec.update(status="UNSUPPORTED_RUNTIME", eligible=False, reason=f"no_frozen_exact_image:{version}")
            return rec
        rec["python_image"] = exact.PYTHON_IMAGES[version]

        baseline = exact.native_test(repo, work)
        rec["baseline"] = baseline
        if baseline.get("infrastructure_error"):
            rec.update(status="BASELINE_INFRASTRUCTURE_INELIGIBLE", eligible=False, reason=str(baseline.get("infrastructure_error")))
            return rec
        if not baseline.get("passed"):
            rec.update(status="FIXED_BASELINE_NOT_PASSING", eligible=False, reason="fixed_native_verifier_failed")
            return rec

        sites, parse_errors = strict_sites(work)
        rec["strict_site_count"] = len(sites)
        rec["strict_sites"] = sites
        rec["parse_errors"] = parse_errors
        if len(sites) < MIN_STRICT_SITES:
            rec.update(status="INSUFFICIENT_STRICT_SITES", eligible=False, reason=f"strict_sites={len(sites)}<{MIN_STRICT_SITES}")
            return rec
        rec.update(status="ELIGIBLE", eligible=True, reason="fixed_pass_supported_runtime_and_min_strict_sites")
        return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="v154a_bugsinpy_") as td:
        repo = Path(td) / "BugsInPy"
        clone = q.run(["git", "clone", "--depth", "1", "https://github.com/soarsmu/BugsInPy.git", str(repo)], timeout=600)
        if clone.returncode != 0:
            result = {"protocol": PROTOCOL, "verdict": "R10_INCONCLUSIVE", "reason": "clone_failed", "log_tail": clone.stdout[-12000:]}
            args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            print(json.dumps(result, indent=2, sort_keys=True)); return

        manifest = q.enumerate_manifest(repo)
        corpus_ok = (
            len(manifest) == q.EXPECTED_BUG_COUNT
            and sorted({p for p, _ in manifest}) == sorted(q.EXPECTED_PROJECTS)
        )
        chosen = selected_cases(manifest) if corpus_ok else []
        if not corpus_ok or len(chosen) != len(q.EXPECTED_PROJECTS) * CASES_PER_PROJECT:
            result = {
                "protocol": PROTOCOL,
                "verdict": "R10_INCONCLUSIVE",
                "reason": "corpus_or_selection_mismatch",
                "observed_bug_count": len(manifest),
                "chosen_count": len(chosen),
                "corpus_lock": q.EXPECTED_CORPUS_LOCK,
            }
            args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            print(json.dumps(result, indent=2, sort_keys=True)); return

        rows: list[dict[str, Any]] = []
        for project, bug_id in chosen:
            rec = classify_case(repo, project, bug_id)
            rows.append(rec)
            print(json.dumps({
                "case": rec["case"], "status": rec.get("status"), "eligible": rec.get("eligible"),
                "python_version": rec.get("python_version"), "strict_site_count": rec.get("strict_site_count"),
            }, sort_keys=True), flush=True)

        projects_with_eligible = sorted({r["project"] for r in rows if r.get("eligible")})
        eligible_cases = [r["case"] for r in rows if r.get("eligible")]
        complete_audit = len(rows) == 34 and {r["case"] for r in rows} == {f"{p}/{i}" for p, i in chosen}
        if not complete_audit:
            verdict = "R10_INCONCLUSIVE"
        elif len(projects_with_eligible) >= 12:
            verdict = "PASS_V154A_LABEL_BLIND_EXPANSION_MANIFEST"
        else:
            verdict = "CORPUS_CEILING_V154A_EXPANSION_MANIFEST"

        result = {
            "protocol": PROTOCOL,
            "verdict": verdict,
            "selection": "first two IDs per project by SHA256(project/id), no substitution",
            "cases_per_project": CASES_PER_PROJECT,
            "min_strict_sites": MIN_STRICT_SITES,
            "observed_bug_count": len(manifest),
            "corpus_lock": q.EXPECTED_CORPUS_LOCK,
            "selected_case_count": len(chosen),
            "complete_34_case_audit": complete_audit,
            "eligible_case_count": len(eligible_cases),
            "eligible_cases": eligible_cases,
            "projects_with_eligible_count": len(projects_with_eligible),
            "projects_with_eligible": projects_with_eligible,
            "cases": rows,
            "claim_boundary": "Manifest/support eligibility only. No relaxed mutation was executed and no O3 label or performance was observed.",
        }
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({k: result[k] for k in ["verdict","eligible_case_count","projects_with_eligible_count","projects_with_eligible"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
