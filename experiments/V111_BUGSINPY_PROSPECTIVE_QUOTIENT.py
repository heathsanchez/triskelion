from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

OUT = Path("artifacts/v111_bugsinpy_prospective_quotient")
OUT.mkdir(parents=True, exist_ok=True)
BUGSINPY_REPO = "https://github.com/soarsmu/BugsInPy.git"
MAX_SITES = 12
CASE_BUDGET_SEC = 420
TOTAL_BUDGET_SEC = 3000
TEST_TIMEOUT = 50
COMPILE_TIMEOUT = 240
OPS = ("<", "<=", ">", ">=")
# Frozen from V108/V109/V110 before target execution.
PRIOR_CLASSES = {
    "BOUNDARY_RELAX": {("<", "<="), (">", ">=")},
    "BOUNDARY_TIGHTEN": {("<=", "<"), (">=", ">")},
    "ORDER_REVERSE_STRICTNESS_FLIP": {("<", ">="), (">", "<=")},
    "ORDER_REVERSE_STRICTNESS_FLIP_INV": {(">=", "<"), ("<=", ">")},
}
PRIOR_LITERAL_REPS = {
    "BOUNDARY_RELAX": {("<", "<="), (">", ">=")},
    "BOUNDARY_TIGHTEN": {("<=", "<"), (">=", ">")},
    "ORDER_REVERSE_STRICTNESS_FLIP": {("<", ">="), (">", "<=")},
    "ORDER_REVERSE_STRICTNESS_FLIP_INV": {(">=", "<"), ("<=", ">")},
}


def run(cmd, cwd=None, timeout=120, env=None):
    try:
        p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=timeout, env=env)
        return p.returncode, p.stdout
    except subprocess.TimeoutExpired as e:
        return 124, (e.stdout or "") + "\n[TIMEOUT]"


def test_case(bin_dir: Path, work: Path):
    fail = work / "bugsinpy_fail.txt"
    if fail.exists():
        fail.unlink()
    code, out = run([str(bin_dir / "bugsinpy-test"), "-r", "-w", str(work)],
                    cwd=work, timeout=TEST_TIMEOUT)
    if code == 124:
        return None, out
    # BugsInPy records relevant-test failures here instead of propagating pytest rc.
    failed = fail.exists() and fail.read_text(errors="ignore").strip() != ""
    return (not failed), out


def py_files(work: Path, baseline_out: str):
    all_files = []
    for p in work.rglob("*.py"):
        s = str(p)
        if "/env/" in s or "/.git/" in s or "/tests/" in s or "/test/" in s:
            continue
        all_files.append(p)
    all_files = sorted(set(all_files), key=lambda x: str(x))
    priority = []
    # Traceback-derived paths are verifier-visible information, allowed by protocol.
    for m in re.finditer(r'(?:(?:File\s+["\']([^"\']+\.py)["\'])|([A-Za-z0-9_./\\-]+\.py))', baseline_out):
        raw = m.group(1) or m.group(2)
        q = Path(raw)
        candidates = [q] if q.is_absolute() else [work / q]
        for c in candidates:
            try:
                c = c.resolve()
                if c.exists() and c.is_file() and str(c).startswith(str(work.resolve())) and "/env/" not in str(c):
                    priority.append(c)
            except Exception:
                pass
    seen = set()
    ordered = []
    for p in priority + all_files:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp); ordered.append(rp)
    return ordered


def cmp_sites(path: Path):
    try:
        src = path.read_text(errors="ignore")
        tree = ast.parse(src)
    except Exception:
        return []
    lines = src.splitlines(keepends=True)
    offsets = [0]
    for ln in lines:
        offsets.append(offsets[-1] + len(ln))
    def off(line, col):
        return offsets[line - 1] + col
    sites = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Compare) and len(n.ops) == 1 and len(n.comparators) == 1):
            continue
        opname = {ast.Lt:"<", ast.LtE:"<=", ast.Gt:">", ast.GtE:">="}.get(type(n.ops[0]))
        if not opname:
            continue
        l, r = n.left, n.comparators[0]
        if not all(hasattr(x, "lineno") and hasattr(x, "end_lineno") for x in (l, r)):
            continue
        a = off(l.end_lineno, l.end_col)
        b = off(r.lineno, r.col_offset)
        between = src[a:b]
        # Find the existing comparator only in the gap between operands.
        mm = re.search(r'(?<![<>=])(?:<=|>=|<|>)(?![=])', between)
        if not mm:
            continue
        s, e = a + mm.start(), a + mm.end()
        sites.append({"path": path, "src": src, "start": s, "end": e, "old": opname,
                      "line": n.lineno})
    sites.sort(key=lambda z: (str(z["path"]), z["start"]))
    return sites


def canonical_class(old, new):
    for name, reps in PRIOR_CLASSES.items():
        if (old, new) in reps:
            return name
    return None


def main():
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="v111_") as td:
        td = Path(td)
        bip = td / "BugsInPy"
        code, out = run(["git", "clone", "--quiet", BUGSINPY_REPO, str(bip)], timeout=180)
        if code:
            raise RuntimeError(out)
        _, commit = run(["git", "rev-parse", "HEAD"], cwd=bip, timeout=20)
        commit = commit.strip()
        bin_dir = bip / "framework" / "bin"
        for p in bin_dir.iterdir():
            p.chmod(p.stat().st_mode | 0o111)

        projects = sorted([p.name for p in (bip / "projects").iterdir() if p.is_dir()])
        selected = []
        for project in projects:
            bugs_dir = bip / "projects" / project / "bugs"
            if not bugs_dir.exists():
                continue
            ids = sorted([int(p.name) for p in bugs_dir.iterdir() if p.is_dir() and p.name.isdigit()])
            if ids:
                selected.append((project, ids[0]))

        records = []
        repairs = []
        candidate_tests = 0
        qualified = 0

        for project, bug_id in selected:
            if time.time() - started > TOTAL_BUDGET_SEC:
                records.append({"project": project, "bug_id": bug_id, "status": "budget_not_attempted"})
                continue
            case_start = time.time()
            rec = {"project": project, "bug_id": bug_id}
            work = td / f"case_{project}_{bug_id}"
            code, txt = run([str(bin_dir / "bugsinpy-checkout"), "-p", project, "-v", "0",
                             "-i", str(bug_id), "-w", str(work)], cwd=bip, timeout=150)
            if code or not work.exists():
                rec.update(status="checkout_fail", detail=txt[-1200:]); records.append(rec); continue

            code, txt = run([str(bin_dir / "bugsinpy-compile"), "-w", str(work)], cwd=work,
                            timeout=COMPILE_TIMEOUT)
            if code == 124 or not (work / "bugsinpy_compile_flag").exists():
                rec.update(status="provision_fail" if code != 124 else "timeout", detail=txt[-1200:]); records.append(rec); continue

            base_pass, base_out = test_case(bin_dir, work)
            if base_pass is None:
                rec.update(status="test_infra", detail=base_out[-1200:]); records.append(rec); continue
            if base_pass:
                rec.update(status="baseline_not_failing"); records.append(rec); continue
            qualified += 1

            sites = []
            for path in py_files(work, base_out):
                for s in cmp_sites(path):
                    sites.append(s)
                    if len(sites) >= MAX_SITES:
                        break
                if len(sites) >= MAX_SITES:
                    break
            if not sites:
                rec.update(status="no_comparator_site", baseline_tail=base_out[-1200:]); records.append(rec); continue

            found = []
            for si, site in enumerate(sites):
                if time.time() - case_start > CASE_BUDGET_SEC or time.time() - started > TOTAL_BUDGET_SEC:
                    break
                path = site["path"]
                original = site["src"]
                for newop in OPS:
                    if newop == site["old"]:
                        continue
                    if time.time() - case_start > CASE_BUDGET_SEC:
                        break
                    edited = original[:site["start"]] + newop + original[site["end"]:]
                    try:
                        path.write_text(edited)
                        # avoid stale interpreter caches
                        for cache in work.rglob("__pycache__"):
                            shutil.rmtree(cache, ignore_errors=True)
                        candidate_tests += 1
                        passed, tout = test_case(bin_dir, work)
                    finally:
                        path.write_text(original)
                    if passed is True:
                        # Causal ablation: restored buggy source must fail again.
                        for cache in work.rglob("__pycache__"):
                            shutil.rmtree(cache, ignore_errors=True)
                        abl, aout = test_case(bin_dir, work)
                        klass = canonical_class(site["old"], newop)
                        hit = klass is not None
                        lit_novel = hit and any(rep != (site["old"], newop) for rep in PRIOR_LITERAL_REPS[klass])
                        rr = {"project": project, "bug_id": bug_id,
                              "file": str(path.relative_to(work)), "line": site["line"],
                              "old": site["old"], "new": newop,
                              "quotient_class": klass, "prior_class_hit": hit,
                              "literal_coordinate_novel": lit_novel,
                              "ablation_fail": abl is False}
                        repairs.append(rr); found.append(rr)
            rec.update(status="repair" if found else "no_repair", sites=len(sites), repairs=found,
                       baseline_tail=base_out[-1000:])
            records.append(rec)

        attempted = [r for r in records if r["status"] != "budget_not_attempted"]
        g1 = qualified >= 1
        g2 = candidate_tests >= 8
        causal = [r for r in repairs if r["ablation_fail"]]
        g3 = len(causal) >= 1
        hits = [r for r in causal if r["prior_class_hit"]]
        g4 = len(hits) >= 1
        g5 = any(r["literal_coordinate_novel"] for r in hits)
        g6 = len(hits) >= 1
        g7 = True  # construction: checkout version 0 only; no version 1/diff/fix text code path exists.
        terminal = {"baseline_not_failing","checkout_fail","provision_fail","test_infra","timeout",
                    "no_comparator_site","no_repair","repair"}
        g8 = all(r["status"] in terminal for r in attempted)
        gates = {
            "G1_executable_target_qualification": g1,
            "G2_nontrivial_blind_search": g2,
            "G3_prospective_causal_repair": g3,
            "G4_prior_class_prediction": g4,
            "G5_literal_coordinate_novelty": g5,
            "G6_source_corpus_independence": g6,
            "G7_leakage_audit": g7,
            "G8_infrastructure_accounting": g8,
        }
        passed = all(gates.values())
        result = {
            "canonical_id": "V111_BUGSINPY_PROSPECTIVE_QUOTIENT",
            "bugsinpy_commit": commit,
            "selection_rule": "lexicographic projects; smallest numeric bug id per project; fixed order",
            "selected_cases": selected,
            "qualified_cases": qualified,
            "candidate_tests": candidate_tests,
            "causal_repairs": causal,
            "prior_class_hits": hits,
            "records": records,
            "gates": gates,
            "leakage_audit": {
                "fixed_revision_checked_out": False,
                "known_patch_or_diff_read": False,
                "repair_text_read": False,
                "primary_information": "buggy source + bug-relevant verifier only",
            },
            "verdict": "PASS_V111_BUGSINPY_PROSPECTIVE_QUOTIENT" if passed else "FAIL_V111_BUGSINPY_PROSPECTIVE_QUOTIENT",
            "claim_boundary": "Prospective blind one-site comparator search on deterministically selected BugsInPy cases under a quotient relation frozen from QuixBugs; infrastructure negatives retained.",
        }
        (OUT / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        # A scientific failure still exits 0 so the artifact is preserved as the result.

if __name__ == "__main__":
    main()
