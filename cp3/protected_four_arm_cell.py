from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from bugsinpy_four_arm import (
    MODEL, SEED, MAX_TOKENS, RiverProvider, Task,
    apply_diff, checkout_buggy, extract_diff, load_capability,
    memory_view, visible_request,
)
from bugsinpy_four_arm_v2 import native_test

ARMS = ["cold", "raw_memory", "always_on", "verified"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--arm", choices=ARMS, required=True)
    ap.add_argument("--case-index", type=int, required=True)
    ap.add_argument("--capability", type=Path, required=True)
    ap.add_argument("--raw-memory", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("protected cell output exists; refusing to overwrite")
    args.out.parent.mkdir(parents=True, exist_ok=True)

    bundle = json.loads(args.bundle.read_text())
    canonical = json.dumps({k: v for k, v in bundle.items() if k != "bundle_sha256"}, sort_keys=True, separators=(",", ":"))
    if hashlib.sha256(canonical.encode()).hexdigest() != bundle["bundle_sha256"]:
        raise SystemExit("protected bundle hash mismatch")
    cap = load_capability(args.capability)
    raw_memory = args.raw_memory.read_text()

    with tempfile.TemporaryDirectory(prefix="cp3-protected-cell-") as raw:
        work = checkout_buggy(args.bugsinpy, bundle["project"], int(bundle["bug_id"]), Path(raw))
        for rel, expected in bundle["context_file_sha256"].items():
            p = work / rel
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                raise SystemExit(f"buggy source drift for sanitized context file: {rel}")

        task = Task(
            task_id=bundle["case"],
            source=bundle["context"],
            tests=[],
            split="protected",
            source_group=bundle["project"],
            metadata={
                "project": bundle["project"],
                "bug_id": bundle["bug_id"],
                "failure_class": bundle["failure_class"],
                "context_files": bundle["context_files"],
            },
        )
        selected, memory = memory_view(args.arm, cap, raw_memory, task)
        prompt = visible_request(bundle["project"], int(bundle["bug_id"]), bundle["failure_text"], bundle["context"])
        if memory:
            prompt += "\n\n" + memory
        provider = RiverProvider(MODEL)
        seed = SEED + args.case_index

        infrastructure_error = None
        patch_error = None
        response_row = None
        diff = ""
        try:
            response = provider.sample(prompt, seed=seed, max_tokens=MAX_TOKENS)
            response_row = response.to_dict()
            response_row["text_sha256"] = hashlib.sha256(response.text.encode()).hexdigest()
            diff = extract_diff(response.text)
            apply_diff(work, diff)
        except Exception as exc:
            if response_row is None:
                infrastructure_error = f"{exc.__class__.__name__}: {exc}"
            else:
                patch_error = f"{exc.__class__.__name__}: {exc}"

        verdict = None
        if infrastructure_error is None and patch_error is None:
            verdict = native_test(args.bugsinpy, work)

        result = {
            "protocol": "TRISKELION_CP3_FOUR_ARM_V1",
            "case": bundle["case"],
            "arm": args.arm,
            "case_index": args.case_index,
            "model": MODEL,
            "temperature": 0.0,
            "max_tokens": MAX_TOKENS,
            "seed": seed,
            "bundle_sha256": bundle["bundle_sha256"],
            "capability_file_sha256": hashlib.sha256(args.capability.read_bytes()).hexdigest(),
            "raw_memory_sha256": hashlib.sha256(raw_memory.encode()).hexdigest(),
            "selected": selected,
            "scope_matched": bool(selected) if args.arm == "verified" else None,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "response": response_row,
            "diff_sha256": hashlib.sha256(diff.encode()).hexdigest() if diff else None,
            "infrastructure_error": infrastructure_error,
            "patch_error": patch_error,
            "verdict": verdict,
            "protected_native_evaluations": 1 if verdict is not None else 0,
        }
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({k: result[k] for k in ["case", "arm", "selected", "scope_matched", "infrastructure_error", "patch_error", "protected_native_evaluations", "verdict"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
