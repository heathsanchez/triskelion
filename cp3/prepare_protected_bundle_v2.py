from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import bugsinpy_four_arm as base
import protected_exact_runtime as exact_runtime
import source_context_ranker_v2 as context_adapter

base.native_test = exact_runtime.native_test
base.collect_context = context_adapter.collect_context


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--bug-id", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("protected bundle already exists; refusing to overwrite")
    args.out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="cp3-protected-sanitize-") as raw:
        work = base.checkout_buggy(args.bugsinpy, args.project, args.bug_id, Path(raw))
        baseline = exact_runtime.native_test(args.bugsinpy, work)
        if baseline.get("infrastructure_error"):
            raise SystemExit(f"protected sanitizer infrastructure negative: {baseline['infrastructure_error']}")
        if baseline.get("passed"):
            raise SystemExit("protected sanitizer reproduction negative: buggy revision passed")
        context, files = context_adapter.collect_context(work, baseline["test_output"])
        hashes = {rel: hashlib.sha256((work / rel).read_bytes()).hexdigest() for rel in files}
        bundle = {
            "schema": "TRISKELION_CP3_PROTECTED_BUNDLE_V2",
            "case": f"{args.project}/{args.bug_id}",
            "project": args.project,
            "bug_id": args.bug_id,
            "python_version": baseline.get("python_version"),
            "python_image": baseline.get("python_image"),
            "failure_class": base.failure_class(baseline["test_output"]),
            "failure_text": baseline["test_output"],
            "context": context,
            "context_files": files,
            "context_file_sha256": hashes,
            "forbidden_information": ["reference_patch", "fixed_production_source", "developer_solution_text", "prior_protected_arm_outcomes"],
            "fixed_information_accessed": False,
            "sanitizer_native_evaluations": 1,
            "bundle_sha256": None,
        }
        canonical = json.dumps({k: v for k, v in bundle.items() if k != "bundle_sha256"}, sort_keys=True, separators=(",", ":"))
        bundle["bundle_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
        args.out.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"case": bundle["case"], "bundle_sha256": bundle["bundle_sha256"], "python_version": bundle["python_version"], "context_files": files}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
