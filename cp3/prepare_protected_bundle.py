from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from bugsinpy_four_arm import checkout_buggy, collect_context, failure_class
from bugsinpy_four_arm_v2 import native_test


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
        work = checkout_buggy(args.bugsinpy, args.project, args.bug_id, Path(raw))
        baseline = native_test(args.bugsinpy, work)
        if baseline.get("infrastructure_error"):
            raise SystemExit(f"protected sanitizer infrastructure negative: {baseline['infrastructure_error']}")
        if baseline.get("passed"):
            raise SystemExit("protected sanitizer reproduction negative: buggy revision passed")
        context, files = collect_context(work, baseline["test_output"])
        hashes = {}
        for rel in files:
            p = work / rel
            hashes[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
        bundle = {
            "schema": "TRISKELION_CP3_PROTECTED_BUNDLE_V1",
            "case": f"{args.project}/{args.bug_id}",
            "project": args.project,
            "bug_id": args.bug_id,
            "failure_class": failure_class(baseline["test_output"]),
            "failure_text": baseline["test_output"],
            "context": context,
            "context_files": files,
            "context_file_sha256": hashes,
            "forbidden_information": [
                "reference_patch", "fixed_production_source", "developer_solution_text", "prior_protected_arm_outcomes"
            ],
            "fixed_information_accessed": False,
            "bundle_sha256": None,
        }
        canonical = json.dumps({k: v for k, v in bundle.items() if k != "bundle_sha256"}, sort_keys=True, separators=(",", ":"))
        bundle["bundle_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
        args.out.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"case": bundle["case"], "bundle_sha256": bundle["bundle_sha256"], "context_files": files}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
