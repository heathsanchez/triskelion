from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import time
from pathlib import Path

import bugsinpy_four_arm as base
import protected_exact_runtime as exact_runtime
import source_context_ranker_v2 as context_adapter
import structured_edit_protocol_v2 as edits
from river_qwen35_provider import Qwen35ChatRiverProvider

ARMS = ["cold", "raw_memory", "always_on", "verified"]
CAP_SHA = "d550b49d855681b3ec68944249265fabb8d4da59b160af15f98a6ed96b2e0380"
RAW_SHA = "f0852bd16fc45f0080be8d0ba9391d4c14746f3126b66a1d448413117313b212"


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

    if hashlib.sha256(args.capability.read_bytes()).hexdigest() != CAP_SHA:
        raise SystemExit("frozen capability hash mismatch")
    if hashlib.sha256(args.raw_memory.read_bytes()).hexdigest() != RAW_SHA:
        raise SystemExit("frozen raw-memory hash mismatch")

    bundle = json.loads(args.bundle.read_text())
    canonical = json.dumps({k: v for k, v in bundle.items() if k != "bundle_sha256"}, sort_keys=True, separators=(",", ":"))
    if hashlib.sha256(canonical.encode()).hexdigest() != bundle["bundle_sha256"]:
        raise SystemExit("protected bundle hash mismatch")

    cap = base.load_capability(args.capability)
    raw_memory = args.raw_memory.read_text()
    started = time.perf_counter()

    with tempfile.TemporaryDirectory(prefix="cp3-protected-cell-") as raw:
        work = base.checkout_buggy(args.bugsinpy, bundle["project"], int(bundle["bug_id"]), Path(raw))
        for rel, expected in bundle["context_file_sha256"].items():
            p = work / rel
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                raise SystemExit(f"buggy source drift for sanitized context file: {rel}")

        task = base.Task(
            task_id=bundle["case"], source=bundle["context"], tests=[], split="protected", source_group=bundle["project"],
            metadata={"project": bundle["project"], "bug_id": bundle["bug_id"], "failure_class": bundle["failure_class"], "context_files": bundle["context_files"]},
        )
        selected, memory = base.memory_view(args.arm, cap, raw_memory, task)
        prompt = edits.visible_request(bundle["project"], int(bundle["bug_id"]), bundle["failure_text"], bundle["context"])
        if memory:
            prompt += "\n\n" + memory

        provider = Qwen35ChatRiverProvider(base.MODEL)
        seed = base.SEED + args.case_index
        response_row = None
        edit_payload = ""
        infrastructure_error = None
        patch_error = None
        verdict = None
        calls_used = 0
        tokens_used = 0

        try:
            response = provider.sample(prompt, seed=seed, max_tokens=base.MAX_TOKENS)
            calls_used = 1
            response_row = response.to_dict()
            tokens_used = int(response.output_tokens or 0)
            response_row["text_sha256"] = hashlib.sha256(response.text.encode()).hexdigest()
            edit_payload = edits.extract_edits(response.text)
            edits.apply_edits(work, edit_payload)
        except Exception as exc:
            if response_row is None:
                infrastructure_error = f"{exc.__class__.__name__}: {exc}"
            else:
                patch_error = f"{exc.__class__.__name__}: {exc}"

        if infrastructure_error is None and patch_error is None:
            verdict = exact_runtime.native_test(args.bugsinpy, work)

        scope_match = base.matches_scope(cap.scope, task)
        result = {
            "protocol": "TRISKELION_CP3_FOUR_ARM_V2",
            "case": bundle["case"], "arm": args.arm, "case_index": args.case_index,
            "model": base.MODEL, "temperature": 0.0, "max_tokens_per_call": base.MAX_TOKENS,
            "max_calls_per_cell": 2, "calls_used": calls_used, "tokens_used": tokens_used,
            "seed": seed, "input_hash": bundle["bundle_sha256"], "bundle_sha256": bundle["bundle_sha256"],
            "model_output_hash": response_row.get("text_sha256") if response_row else None,
            "candidate_patch_hash": hashlib.sha256(edit_payload.encode()).hexdigest() if edit_payload else None,
            "capability_file_sha256": CAP_SHA, "raw_memory_sha256": RAW_SHA,
            "capability_available": args.arm in {"always_on", "verified"},
            "capability_invoked": bool(selected), "selected": selected,
            "activation_reason": "always_on" if args.arm == "always_on" else ("scope_match" if args.arm == "verified" and scope_match else ("scope_miss" if args.arm == "verified" else "not_available")),
            "scope_matched": scope_match if args.arm == "verified" else None,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "response": response_row,
            "infrastructure_error": infrastructure_error, "patch_error": patch_error,
            "verdict": verdict, "verifier_decision": None if verdict is None else bool(verdict.get("passed")),
            "native_test_result": verdict, "local_regression_result": verdict,
            "protected_native_evaluations": 1 if verdict is not None else 0,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "infrastructure_status": "OK" if infrastructure_error is None and not (verdict or {}).get("infrastructure_error") else "INFRASTRUCTURE_ERROR",
        }
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({k: result[k] for k in ["case", "arm", "capability_invoked", "scope_matched", "calls_used", "infrastructure_status", "verifier_decision"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
