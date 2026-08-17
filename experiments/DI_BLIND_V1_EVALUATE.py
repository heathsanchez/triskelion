#!/usr/bin/env python3
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path("checker")
EXE = ROOT / "lean_checker"
VOWC = (ROOT / "vowc").resolve()
ARENA = Path("arena-tests")
BLIND = Path("blind-di")
MANIFEST = Path("/tmp/blind_manifest_eval.json")
CANDIDATES = BLIND / "candidates.json"
PRECOMMIT = BLIND / "precommit.json"
EXPOSED_META = BLIND / "exposed.json"
OUT = BLIND / "result.json"
REGRESSION_N = 24


def run_case(exe, rel, timeout=30):
    p = (ARENA / rel).resolve()
    try:
        cp = subprocess.run([str(Path(exe).resolve()), str(p)], capture_output=True, text=True, timeout=timeout)
        rc = cp.returncode
        out, err = cp.stdout, cp.stderr
    except subprocess.TimeoutExpired as e:
        rc = 124
        out = e.stdout or ""
        err = e.stderr or ""
    status = "accept" if rc == 0 else ("reject" if rc == 1 else ("decline" if rc == 2 else "error"))
    return {"rc": rc, "status": status, "stdout_tail": out[-2000:] if isinstance(out, str) else "", "stderr_tail": err[-2000:] if isinstance(err, str) else ""}


def correct(result, expected):
    return result["status"] == expected


def build_checker():
    env = os.environ.copy()
    env["VOWC"] = str(VOWC)
    cp = subprocess.run(["bash", "scripts/build.sh"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=300)
    return cp.returncode == 0, cp.stdout[-5000:], cp.stderr[-5000:]


def apply_edit(edit):
    p = ROOT / edit["path"]
    src = p.read_text()
    old, new = edit["old"], edit["new"]
    if src.count(old) != 1 or old == new:
        raise ValueError("edit no longer admissible")
    p.write_text(src.replace(old, new, 1))
    return p, src


def restore_file(path, original):
    path.write_text(original)


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    rows = json.loads(MANIFEST.read_text())
    pre = json.loads(PRECOMMIT.read_text())
    exposed = json.loads(EXPOSED_META.read_text())
    candidates = json.loads(CANDIDATES.read_text())

    canonical = json.dumps(rows, separators=(",", ":"), sort_keys=True).encode()
    commitment = hashlib.sha256(canonical).hexdigest()
    commitment_ok = commitment == pre["ordered_manifest_sha256"]
    if not commitment_ok:
        raise SystemExit("corpus commitment mismatch")

    exp_idx = next((i for i, r in enumerate(rows) if r["rel"] == exposed["rel"] and r["sha256"] == exposed["sha256"]), None)
    if exp_idx is None:
        raise SystemExit("exposed case not in reproduced manifest")
    exp_row = rows[exp_idx]

    # The pristine checker has already been rebuilt after corpus re-download.
    baseline_exposed = run_case(EXE, exp_row["rel"])
    exposed_is_failure = not correct(baseline_exposed, exp_row["expected"])
    if not exposed_is_failure:
        raise SystemExit("exposed case is no longer a baseline failure")

    frozen_exe = Path("/tmp/lean_checker_di_v1_frozen")
    shutil.copy2(EXE, frozen_exe)
    os.chmod(frozen_exe, 0o755)

    # Hidden regression gate: first 24 post-exposure cases the frozen checker gets right.
    regression = []
    suffix_baseline = {}
    for r in rows[exp_idx + 1:]:
        b = run_case(frozen_exe, r["rel"])
        suffix_baseline[r["rel"]] = b
        if correct(b, r["expected"]) and len(regression) < REGRESSION_N:
            regression.append(r)
        if len(regression) == REGRESSION_N:
            break
    if len(regression) != REGRESSION_N:
        raise SystemExit("insufficient baseline-correct cases for regression gate")

    evaluations = []
    selected = None
    selected_path = None
    selected_original = None

    for row in candidates["candidates"]:
        ev = {"index": row["index"], "admissible": bool(row["admissible"]), "candidate_sha256": row["raw_sha256"]}
        if not row["admissible"] or not isinstance(row.get("parsed"), dict):
            ev["outcome"] = "inadmissible"
            evaluations.append(ev)
            continue
        edit = row["parsed"]
        try:
            path, original = apply_edit(edit)
        except Exception as e:
            ev["outcome"] = "apply_failed"
            ev["error"] = repr(e)
            evaluations.append(ev)
            continue
        ok, bout, berr = build_checker()
        ev["build_ok"] = ok
        if not ok:
            ev["outcome"] = "build_failed"
            ev["build_stderr_tail"] = berr
            restore_file(path, original)
            evaluations.append(ev)
            continue
        e = run_case(EXE, exp_row["rel"])
        ev["exposed_status"] = e["status"]
        ev["exposed_fixed"] = correct(e, exp_row["expected"])
        if not ev["exposed_fixed"]:
            ev["outcome"] = "exposed_not_fixed"
            restore_file(path, original)
            evaluations.append(ev)
            continue
        reg_rows = []
        regressions = 0
        for rr in regression:
            q = run_case(EXE, rr["rel"])
            good = correct(q, rr["expected"])
            regressions += 0 if good else 1
            reg_rows.append({"order": rr["order"], "expected": rr["expected"], "status": q["status"], "correct": good})
        ev["hidden_regression_passed"] = REGRESSION_N - regressions
        ev["hidden_regression_total"] = REGRESSION_N
        ev["hidden_regressions"] = regressions
        if regressions:
            ev["outcome"] = "hidden_regression_reject"
            restore_file(path, original)
            evaluations.append(ev)
            continue
        ev["outcome"] = "retained"
        evaluations.append(ev)
        selected = row
        selected_path = path
        selected_original = original
        break

    result = {
        "protocol": "DI_BLIND_V1_AUTONOMOUS_CONSTRUCTION",
        "corpus_commitment_reproduced": commitment_ok,
        "ordered_manifest_sha256": commitment,
        "base_model": candidates["base_model"],
        "base_weight_updates": candidates.get("base_weight_updates", 0),
        "prompt_sha256": candidates["prompt_sha256"],
        "admissible_candidate_count": candidates["admissible_count"],
        "exposed": {
            "rank": exp_idx + 1,
            "order": exp_row["order"],
            "expected": exp_row["expected"],
            "baseline_status": baseline_exposed["status"],
            "sha256": exp_row["sha256"],
        },
        "candidate_evaluations": evaluations,
        "selected": None,
        "protected_transfer": None,
        "ablation": None,
    }

    if selected is None:
        result["verdict"] = "VALID_NEGATIVE_NO_CONSTRUCTION"
        OUT.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return

    # Candidate source and binary are currently active. Candidate choice is now irrevocable.
    edit = selected["parsed"]
    candidate_exe = Path("/tmp/lean_checker_di_v1_developed")
    shutil.copy2(EXE, candidate_exe)
    os.chmod(candidate_exe, 0o755)
    result["selected"] = {
        "generation_index": selected["index"],
        "proposal_sha256": selected["raw_sha256"],
        "hypothesis": edit.get("hypothesis", ""),
        "path": edit["path"],
        "old": edit["old"],
        "new": edit["new"],
        "developed_source_sha256": sha_file(selected_path),
        "hidden_regression": f"{REGRESSION_N}/{REGRESSION_N}",
    }

    regression_rels = {r["rel"] for r in regression}
    transfers = []
    protected_rows = []
    for r in rows[exp_idx + 1:]:
        if r["rel"] in regression_rels:
            continue
        b = suffix_baseline.get(r["rel"])
        if b is None:
            b = run_case(frozen_exe, r["rel"])
        d = run_case(candidate_exe, r["rel"])
        b_ok = correct(b, r["expected"])
        d_ok = correct(d, r["expected"])
        transfer = (not b_ok) and d_ok
        protected_rows.append({
            "order": r["order"], "sha256": r["sha256"], "expected": r["expected"],
            "baseline_status": b["status"], "developed_status": d["status"], "transfer_success": transfer,
        })
        if transfer:
            transfers.append(r)

    result["protected_transfer"] = {
        "evaluated": len(protected_rows),
        "baseline_incorrect": sum(1 for x in protected_rows if x["baseline_status"] != x["expected"]),
        "developed_incorrect": sum(1 for x in protected_rows if x["developed_status"] != x["expected"]),
        "transfer_success_count": len(transfers),
        "rows": protected_rows,
    }

    # Strong causal ablation: actually restore frozen source, rebuild, test every claimed success,
    # then reapply the exact retained edit, rebuild, and test again.
    restore_file(selected_path, selected_original)
    ok0, _, err0 = build_checker()
    remove_rows = []
    if ok0:
        for r in transfers:
            q = run_case(EXE, r["rel"])
            remove_rows.append({"order": r["order"], "status": q["status"], "returns_to_baseline": q["status"] == suffix_baseline.get(r["rel"], run_case(frozen_exe, r["rel"]))["status"]})
    # Reapply exactly the selected model-generated edit.
    path2, original2 = apply_edit(edit)
    ok1, _, err1 = build_checker()
    restore_rows = []
    if ok1:
        for r in transfers:
            q = run_case(EXE, r["rel"])
            restore_rows.append({"order": r["order"], "status": q["status"], "correct_restored": correct(q, r["expected"])})
    remove_pass = ok0 and len(remove_rows) == len(transfers) and all(x["returns_to_baseline"] for x in remove_rows)
    restore_pass = ok1 and len(restore_rows) == len(transfers) and all(x["correct_restored"] for x in restore_rows)
    result["ablation"] = {
        "remove_build_ok": ok0,
        "restore_build_ok": ok1,
        "remove_all_return_to_baseline": remove_pass,
        "restore_all_return_to_correct": restore_pass,
        "remove_rows": remove_rows,
        "restore_rows": restore_rows,
        "remove_build_error_tail": "" if ok0 else err0,
        "restore_build_error_tail": "" if ok1 else err1,
    }

    if len(transfers) > 0 and remove_pass and restore_pass:
        result["verdict"] = "PASS_DI_BLIND_V1_AUTONOMOUS_CONSTRUCTION"
    else:
        result["verdict"] = "PARTIAL_EXPOSED_ONLY"

    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
