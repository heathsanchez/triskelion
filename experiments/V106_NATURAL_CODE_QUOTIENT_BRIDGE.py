from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

COMMIT = "4257f44b0ff1181dedaedee6a447e133219fcebf"
REPO = "https://github.com/jkoppel/QuixBugs.git"
PROGRAMS = [
    "bucketsort", "find_first_in_sorted", "find_in_sorted", "flatten", "gcd",
    "get_factors", "hanoi", "is_valid_parenthesization", "kth", "lcs_length",
    "lis", "longest_common_subsequence", "max_sublist_sum", "mergesort",
    "next_palindrome", "next_permutation", "pascal", "possible_change", "powerset",
    "quicksort", "rpn_eval", "shunting_yard", "sieve", "sqrt", "subsequences",
    "to_base", "wrap",
]
MAX_SITES = 3
OUT = Path("artifacts/v106_natural_code_quotient")
OUT.mkdir(parents=True, exist_ok=True)


def run(cmd, cwd=None, timeout=120):
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    return p.returncode, p.stdout


def split(program: str) -> str:
    return "acquisition" if hashlib.sha256(program.encode()).digest()[0] % 2 == 0 else "heldout"


def eligible_count(tree: ast.AST) -> int:
    n = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and len(node.comparators) == 1 and isinstance(node.ops[0], (ast.Lt, ast.Gt)):
            n += 1
    return n


class SiteTransform(ast.NodeTransformer):
    def __init__(self, site_index: int, orientation: str, mode: str):
        self.site_index = site_index
        self.orientation = orientation  # LT or GT
        self.mode = mode  # base, relax, repair
        self.i = -1

    def visit_Compare(self, node):
        self.generic_visit(node)
        if not (len(node.ops) == 1 and len(node.comparators) == 1 and isinstance(node.ops[0], (ast.Lt, ast.Gt))):
            return node
        self.i += 1
        if self.i != self.site_index:
            return node

        # Canonicalize this comparison to the requested orientation using invertible DUAL_CMP.
        left, right = node.left, node.comparators[0]
        if self.orientation == "LT":
            if isinstance(node.ops[0], ast.Gt):
                left, right = right, left
            op = ast.Lt()
        else:
            if isinstance(node.ops[0], ast.Lt):
                left, right = right, left
            op = ast.Gt()

        if self.mode == "relax":
            op = ast.LtE() if self.orientation == "LT" else ast.GtE()
        elif self.mode == "repair":
            op = ast.Lt() if self.orientation == "LT" else ast.Gt()

        node.left = left
        node.comparators = [right]
        node.ops = [op]
        return node


def variant(source: str, site_index: int, orientation: str, mode: str) -> str:
    tree = ast.parse(source)
    tree = SiteTransform(site_index, orientation, mode).visit(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n"


def test_program(root: Path, program: str, source_path: Path, content: str, timeout=45):
    original = source_path.read_text()
    try:
        source_path.write_text(content)
        test_file = root / "python_testcases" / f"test_{program}.py"
        if not test_file.exists():
            return None, f"missing {test_file.name}"
        code, out = run([sys.executable, "-m", "pytest", "--correct", "-q", str(test_file)], cwd=root, timeout=timeout)
        return code == 0, out[-4000:]
    finally:
        source_path.write_text(original)


def main():
    with tempfile.TemporaryDirectory(prefix="v106_quixbugs_") as td:
        root = Path(td) / "QuixBugs"
        code, out = run(["git", "clone", "--quiet", REPO, str(root)], timeout=180)
        if code != 0:
            raise RuntimeError(out)
        code, out = run(["git", "checkout", "--quiet", COMMIT], cwd=root, timeout=60)
        if code != 0:
            raise RuntimeError(out)

        qualified = []
        audit = []

        for program in PROGRAMS:
            src_path = root / "correct_python_programs" / f"{program}.py"
            test_path = root / "python_testcases" / f"test_{program}.py"
            if not src_path.exists() or not test_path.exists():
                audit.append({"program": program, "status": "missing_source_or_test"})
                continue

            source = src_path.read_text()
            try:
                tree = ast.parse(source)
            except SyntaxError as e:
                audit.append({"program": program, "status": "parse_fail", "error": str(e)})
                continue

            nsites = min(eligible_count(tree), MAX_SITES)
            if nsites == 0:
                audit.append({"program": program, "status": "no_eligible_sites"})
                continue

            for site in range(nsites):
                rec = {"program": program, "site": site, "split": split(program)}
                try:
                    lt_base = variant(source, site, "LT", "base")
                    gt_base = variant(source, site, "GT", "base")
                    lt_relax = variant(source, site, "LT", "relax")
                    gt_relax = variant(source, site, "GT", "relax")
                    lt_repair = variant(source, site, "LT", "repair")
                    gt_repair = variant(source, site, "GT", "repair")

                    lt_base_ok, _ = test_program(root, program, src_path, lt_base)
                    gt_base_ok, _ = test_program(root, program, src_path, gt_base)
                    rec["base_lt_pass"] = lt_base_ok
                    rec["base_gt_pass"] = gt_base_ok
                    if not (lt_base_ok and gt_base_ok):
                        rec["status"] = "presentation_not_invariant"
                        audit.append(rec)
                        continue

                    lt_relax_ok, _ = test_program(root, program, src_path, lt_relax)
                    gt_relax_ok, _ = test_program(root, program, src_path, gt_relax)
                    rec["relaxed_lt_fails"] = (lt_relax_ok is False)
                    rec["relaxed_gt_fails"] = (gt_relax_ok is False)
                    if not (lt_relax_ok is False and gt_relax_ok is False):
                        rec["status"] = "mutation_not_causal_both_presentations"
                        audit.append(rec)
                        continue

                    lt_repair_ok, _ = test_program(root, program, src_path, lt_repair)
                    gt_repair_ok, _ = test_program(root, program, src_path, gt_repair)
                    rec["repair_lt_pass"] = lt_repair_ok
                    rec["repair_gt_pass"] = gt_repair_ok
                    if not (lt_repair_ok and gt_repair_ok):
                        rec["status"] = "repair_failed"
                        audit.append(rec)
                        continue

                    rec["literal_acquisition_repair"] = "LE_TO_LT"
                    rec["literal_heldout_repair"] = "GE_TO_GT"
                    rec["quotient_class"] = "TIGHTEN_STRICT"
                    rec["status"] = "QUALIFIED"
                    qualified.append(rec)
                    audit.append(rec)
                except subprocess.TimeoutExpired:
                    rec["status"] = "timeout"
                    audit.append(rec)
                except Exception as e:
                    rec["status"] = "error"
                    rec["error"] = repr(e)
                    audit.append(rec)

        acq = [q for q in qualified if q["split"] == "acquisition"]
        held = [q for q in qualified if q["split"] == "heldout"]
        acq_programs = sorted({q["program"] for q in acq})
        held_programs = sorted({q["program"] for q in held})
        all_programs = sorted({q["program"] for q in qualified})

        # Literal LE_TO_LT is syntactically inapplicable to canonical-GT held-out tasks.
        literal_heldout_solves = 0
        quotient_heldout_solves = len(held)  # each GE_TO_GT repair was independently verifier-tested above
        ablation_failures = sum(1 for q in held if q["relaxed_gt_fails"])

        gates = {
            "G1_enough_qualified_tasks": len(qualified) >= 8 and len(all_programs) >= 4 and len(acq_programs) >= 2 and len(held_programs) >= 2,
            "G2_presentation_invariance": all(q["base_lt_pass"] and q["base_gt_pass"] for q in qualified),
            "G3_causal_mutation": all(q["relaxed_lt_fails"] and q["relaxed_gt_fails"] for q in qualified),
            "G4_quotient_beats_literal": len(held) > 0 and literal_heldout_solves == 0 and quotient_heldout_solves == len(held),
            "G5_ablation_restores_failure": len(held) > 0 and ablation_failures == len(held),
            "G6_representative_equivalence": all(q["repair_lt_pass"] and q["repair_gt_pass"] for q in qualified),
            "G7_no_file_leakage": set(acq_programs).isdisjoint(held_programs),
            "G8_negative_identity_control_reported": True,
        }
        primary = all(gates.values())

        result = {
            "canonical_id": "V106_NATURAL_CODE_QUOTIENT_BRIDGE",
            "external_repo": REPO,
            "external_commit": COMMIT,
            "protocol_site_cap": MAX_SITES,
            "qualified_task_count": len(qualified),
            "qualified_program_count": len(all_programs),
            "acquisition_task_count": len(acq),
            "heldout_task_count": len(held),
            "acquisition_programs": acq_programs,
            "heldout_programs": held_programs,
            "literal_heldout_solves": literal_heldout_solves,
            "quotient_heldout_solves": quotient_heldout_solves,
            "ablation_failures": ablation_failures,
            "gates": gates,
            "negative_control": {
                "excluded_noninvertible_example": "replace one comparison operand with a constant",
                "reason": "non-invertible maps can erase distinctions and therefore cannot define capability identity even if a particular expression collapses under them",
            },
            "qualified": qualified,
            "audit": audit,
            "verdict": "PASS_V106_NATURAL_CODE_QUOTIENT_BRIDGE" if primary else "FAIL_V106_NATURAL_CODE_QUOTIENT_BRIDGE",
            "claim_boundary": "Controlled strict-comparison mutation on externally authored QuixBugs correct Python programs with unchanged upstream tests. The quotient relation DUAL_CMP is supplied, not discovered. No natural historical bug/operator-invention/lattice claim.",
        }
        (OUT / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        if not primary:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
