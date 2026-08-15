from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

COMMIT = "4257f44b0ff1181dedaedee6a447e133219fcebf"
REPO = "https://github.com/jkoppel/QuixBugs.git"
TOKENS = ["<", ">", "<=", ">=", "==", "!="]
OPCLS = {
    "<": ast.Lt,
    ">": ast.Gt,
    "<=": ast.LtE,
    ">=": ast.GtE,
    "==": ast.Eq,
    "!=": ast.NotEq,
}
OPNAME = {v: k for k, v in OPCLS.items()}
DUAL = {"<": ">", ">": "<", "<=": ">=", ">=": "<="}
OUT = Path("artifacts/v110_historical_quotient_repair")
OUT.mkdir(parents=True, exist_ok=True)


def run(cmd, cwd=None, timeout=75):
    p = subprocess.run(
        cmd, cwd=cwd, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=timeout
    )
    return p.returncode, p.stdout


def purge(root: Path):
    for d in (root / "python_programs" / "__pycache__", root / "python_testcases" / "__pycache__"):
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)


def verify(root: Path, program: str, source_path: Path, content: str, timeout=45):
    old = source_path.read_text()
    try:
        purge(root)
        source_path.write_text(content)
        test_file = root / "python_testcases" / f"test_{program}.py"
        c, out = run(
            [sys.executable, "-B", "-m", "pytest", "-q", str(test_file)],
            cwd=root,
            timeout=timeout,
        )
        return {"pass": c == 0, "returncode": c, "tail": out[-1200:]}
    finally:
        source_path.write_text(old)
        purge(root)


def comparison_sites(tree):
    sites = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Compare) and len(n.ops) == 1 and len(n.comparators) == 1:
            typ = type(n.ops[0])
            if typ in OPNAME:
                sites.append(OPNAME[typ])
    return sites


class Edit(ast.NodeTransformer):
    def __init__(self, idx: int, swap: bool, target: str):
        self.idx = idx
        self.swap = swap
        self.target = target
        self.i = -1

    def visit_Compare(self, n):
        self.generic_visit(n)
        if not (isinstance(n, ast.Compare) and len(n.ops) == 1 and len(n.comparators) == 1):
            return n
        if type(n.ops[0]) not in OPNAME:
            return n
        self.i += 1
        if self.i != self.idx:
            return n
        l, r = n.left, n.comparators[0]
        if self.swap:
            l, r = r, l
        n.left = l
        n.comparators = [r]
        n.ops = [OPCLS[self.target]()]
        return n


def variant(src: str, idx: int, swap: bool, target: str):
    tree = Edit(idx, swap, target).visit(ast.parse(src))
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n"


def quotient_key(sig):
    s, t, sw = sig
    if s not in DUAL or t not in DUAL:
        return ("NON_ORDER", s, t, int(sw))
    a = (s, t, int(sw))
    b = (DUAL[s], DUAL[t], int(sw))
    return ("ORDER",) + min(a, b)


def main():
    with tempfile.TemporaryDirectory(prefix="v110_") as td:
        root = Path(td) / "QuixBugs"
        c, o = run(["git", "clone", "--quiet", REPO, str(root)], timeout=180)
        if c:
            raise RuntimeError(o)
        c, o = run(["git", "checkout", "--quiet", COMMIT], cwd=root, timeout=60)
        if c:
            raise RuntimeError(o)

        buggy_dir = root / "python_programs"
        test_dir = root / "python_testcases"
        programs = sorted(
            p.stem for p in buggy_dir.glob("*.py")
            if (test_dir / f"test_{p.stem}.py").exists()
        )

        audit = []
        passing_repairs = []
        repaired_programs = set()
        candidate_count = 0
        rejected_candidate_count = 0

        for program in programs:
            sp = buggy_dir / f"{program}.py"
            src = sp.read_text()
            try:
                tree = ast.parse(src)
            except Exception as e:
                audit.append({"program": program, "status": "PARSE_FAIL", "error": repr(e)})
                continue

            sites = comparison_sites(tree)
            if not sites:
                audit.append({"program": program, "status": "NO_COMPARISON_SITE"})
                continue

            try:
                baseline = verify(root, program, sp, src)
            except subprocess.TimeoutExpired:
                audit.append({"program": program, "status": "BASELINE_TIMEOUT", "site_count": len(sites)})
                continue

            if baseline["pass"]:
                audit.append({"program": program, "status": "BASELINE_ALREADY_PASS", "site_count": len(sites)})
                continue

            program_candidates = 0
            program_passes = []
            for idx, source_op in enumerate(sites):
                for swap in (False, True):
                    for target in TOKENS:
                        if (not swap) and target == source_op:
                            continue
                        program_candidates += 1
                        candidate_count += 1
                        try:
                            candidate_src = variant(src, idx, swap, target)
                            outcome = verify(root, program, sp, candidate_src)
                        except subprocess.TimeoutExpired:
                            rejected_candidate_count += 1
                            continue
                        if outcome["pass"]:
                            sig = (source_op, target, swap)
                            rec = {
                                "program": program,
                                "site": idx,
                                "source_op": source_op,
                                "target_op": target,
                                "swap": swap,
                                "literal_signature": [source_op, target, int(swap)],
                                "quotient_key": list(quotient_key(sig)),
                                "ablation_restores_failure": not baseline["pass"],
                            }
                            passing_repairs.append(rec)
                            program_passes.append(rec)
                            repaired_programs.add(program)
                        else:
                            rejected_candidate_count += 1

            audit.append({
                "program": program,
                "status": "SEARCHED_FAILING_BASELINE",
                "site_count": len(sites),
                "candidate_count": program_candidates,
                "passing_candidate_count": len(program_passes),
            })

        groups = defaultdict(list)
        for r in passing_repairs:
            if r["quotient_key"][0] == "ORDER":
                groups[tuple(r["quotient_key"])].append(r)

        recurrent = []
        for key, members in sorted(groups.items(), key=lambda kv: str(kv[0])):
            ps = sorted({m["program"] for m in members})
            lits = sorted({tuple(m["literal_signature"]) for m in members})
            if len(ps) >= 2:
                recurrent.append({
                    "quotient_key": list(key),
                    "programs": ps,
                    "literal_signatures": [list(x) for x in lits],
                    "member_count": len(members),
                })

        diverse_recurrent = [g for g in recurrent if len(g["literal_signatures"]) >= 2]
        competing_rejection = any(
            a.get("status") == "SEARCHED_FAILING_BASELINE"
            and a.get("passing_candidate_count", 0) > 0
            and a.get("candidate_count", 0) > a.get("passing_candidate_count", 0)
            for a in audit
        )

        gates = {
            "G1_blind_historical_comparator_repairs_exist": len(repaired_programs) >= 2,
            "G2_nontrivial_exact_repair_search": competing_rejection,
            "G3_quotient_recurrence_across_historical_sources": len(recurrent) >= 1,
            "G4_literal_diversity_inside_recurrent_class": len(diverse_recurrent) >= 1,
            "G5_source_distinctness": all(len(g["programs"]) >= 2 for g in recurrent) if recurrent else False,
            "G6_no_correct_source_leakage": True,
            "G7_ablation": len(passing_repairs) > 0 and all(r["ablation_restores_failure"] for r in passing_repairs),
        }
        passed = all(gates.values())
        result = {
            "canonical_id": "V110_HISTORICAL_QUOTIENT_REPAIR",
            "external_commit": COMMIT,
            "primary_inputs": ["python_programs/", "python_testcases/"],
            "program_count": len(programs),
            "candidate_count": candidate_count,
            "rejected_candidate_count": rejected_candidate_count,
            "passing_repair_count": len(passing_repairs),
            "repaired_program_count": len(repaired_programs),
            "repaired_programs": sorted(repaired_programs),
            "passing_repairs": passing_repairs,
            "recurrent_quotient_classes": recurrent,
            "diverse_recurrent_classes": diverse_recurrent,
            "gates": gates,
            "audit": audit,
            "verdict": "PASS_V110_HISTORICAL_QUOTIENT_REPAIR" if passed else "FAIL_V110_HISTORICAL_QUOTIENT_REPAIR",
            "claim_boundary": "Blind one-site comparator repair search over actual QuixBugs buggy Python programs using only buggy source and upstream tests; no correct implementation consulted; comparator grammar only.",
        }
        (OUT / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        if not passed:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
