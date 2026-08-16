#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import time
from pathlib import Path
from typing import Any

import v145_precompiled_runner  # noqa: F401
import bugsinpy_four_arm as base
import bugsinpy_exact_runtime as exact_runtime
import structured_edit_protocol_v2 as sed
import v151_capability_compilation_loss_separator as exp

# Bind the compiled arm to the exact immutable V149 O1 object.
exp.O1 = {
    "ancestor_ids": [],
    "applicability_test": "Run the test suite for the item parsing module. If the test case involving an escaped separator (e.g., input containing a backslash followed by a separator character) fails with an assertion error indicating incorrect key-value splitting, this policy is applicable.",
    "artifact_sha256": "7ebb7fb26da6d137c13c1a08bafd7e540dbd52f25e04cf4298502e5ce5428546",
    "capability_id": "V145.O1",
    "generation": "O1",
    "instruction": "When parsing key-value pairs with custom separators, first identify all escape sequences (a backslash followed by a separator) and record their byte spans. Then, iterate through separator matches; only treat a separator as a delimiter if it does not fall entirely within the span of any identified escape sequence.",
    "postconditions": [
        "The parser correctly identifies the position of all escape sequences before processing separators.",
        "Separators located within the span of an escape sequence are ignored as delimiters.",
        "The resulting key-value pairs accurately reflect the intended structure, with escaped separators preserved as part of the key or value.",
        "Tests for escaped separators pass successfully."
    ],
    "preconditions": [
        "The system is parsing key-value pairs using a parser that accepts custom separators.",
        "The input string may contain escaped separators (represented as a backslash followed by the separator character).",
        "The current implementation fails to correctly distinguish between escaped separators and actual delimiters, causing incorrect key-value splitting."
    ],
    "source_intervention_sha256": "b7f419e7993e92164969b7a99689f01dfa279ce2d1615e25fce0bb21486f472d"
}

base.native_test = exact_runtime.native_test
exp.base.native_test = exact_runtime.native_test


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def response_cost(row: dict[str, Any] | None, text: str) -> dict[str, Any]:
    return exp.response_cost(row, text)


def run_seed_arm_stateful(provider, bugsinpy: Path, task: dict[str, Any],
                          arm: str, seed: int, memory: str) -> dict[str, Any]:
    started = time.perf_counter()
    prompt0 = task["visible_prompt"] + (("\n\n" + memory) if memory else "")
    feedback = ""
    attempts: list[dict[str, Any]] = []
    verifier_calls = 0
    verifier_ms = 0.0
    generated_tokens = 0
    output_chars = 0
    token_metric_available = True
    prior_executed_payload: str | None = None
    prior_executed_sha: str | None = None
    prior_raw_response: str | None = None

    for call_idx in range(1, exp.MAX_CALLS + 1):
        prompt = prompt0 + feedback
        try:
            response = provider.sample(prompt, seed=seed + call_idx - 1, max_tokens=exp.MAX_TOKENS)
            text = response.text
            rr = response.to_dict()
        except Exception as exc:
            return {
                "arm": arm, "seed": seed, "status": "R10",
                "reason": f"provider error: {exc.__class__.__name__}: {exc}",
                "attempts": attempts, "model_calls": call_idx - 1,
                "verifier_calls": verifier_calls, "verifier_ms": verifier_ms,
                "wall_ms": round((time.perf_counter() - started) * 1000, 3),
            }

        prior_raw_response = text
        c = response_cost(rr, text)
        output_chars += c["output_chars_proxy"]
        if c["generated_tokens"] is None:
            token_metric_available = False
        else:
            generated_tokens += c["generated_tokens"]
        row: dict[str, Any] = {
            "call": call_idx,
            "prompt_sha256": sha_text(prompt),
            "response_sha256": sha_text(text),
            "response_cost": c,
            "response": rr,
        }

        try:
            payload = sed.extract_edits(text)
            payload_sha = sha_text(payload)
            row["edit_payload_sha256"] = payload_sha
            row["changed_files"] = sed.changed_files(payload)
            if call_idx == 2 and prior_executed_sha is not None:
                row["distinct_second_candidate"] = payload_sha != prior_executed_sha
                if payload_sha == prior_executed_sha:
                    row["repeat_rejected"] = True
                    attempts.append(row)
                    continue
        except Exception as exc:
            row["transport_error"] = f"extract: {exc.__class__.__name__}: {exc}"
            attempts.append(row)
            if call_idx < exp.MAX_CALLS:
                feedback = (
                    "\n\nATTEMPT STATE FROM PRIOR CALL:\n"
                    "The prior raw response was:\n" + text[-6000:] +
                    "\n\nTRANSPORT RESULT:\n"
                    f"{row['transport_error']}\n"
                    "That action was not executable. Do not regenerate the same malformed response. "
                    "Return ONLY valid structured-edit JSON with 1-3 exact replacement edits copied from the shown source."
                )
            continue

        with tempfile.TemporaryDirectory(prefix=f"v152-{arm}-{seed}-") as td:
            try:
                work = base.checkout_buggy(bugsinpy, exp.T2[0], exp.T2[1], Path(td))
                sed.apply_edits(work, payload)
            except Exception as exc:
                row["transport_error"] = f"apply: {exc.__class__.__name__}: {exc}"
                attempts.append(row)
                if call_idx < exp.MAX_CALLS:
                    feedback = (
                        "\n\nATTEMPT STATE FROM PRIOR CALL:\n"
                        "The prior normalized structured edit was:\n" + payload +
                        "\nSHA256: " + payload_sha +
                        "\n\nTRANSPORT RESULT:\n" + row["transport_error"] +
                        "\nThat action did not apply. Do not repeat it. Use only source shown in context and copy old text exactly."
                    )
                continue

            verdict = exact_runtime.native_test(bugsinpy, work)
            verifier_calls += 1
            verifier_ms += float(verdict.get("duration_ms") or 0)
            row["verdict"] = verdict
            attempts.append(row)
            prior_executed_payload = payload
            prior_executed_sha = payload_sha

            if verdict.get("infrastructure_error"):
                return {
                    "arm": arm, "seed": seed, "status": "R10", "reason": verdict["infrastructure_error"],
                    "attempts": attempts, "model_calls": call_idx, "verifier_calls": verifier_calls,
                    "verifier_ms": verifier_ms, "wall_ms": round((time.perf_counter() - started) * 1000, 3),
                }
            if verdict.get("passed"):
                return {
                    "arm": arm, "seed": seed, "status": "VERIFIED_SOLVED", "solved": True,
                    "calls_to_solve": call_idx, "successful_edit_payload": payload,
                    "successful_edit_payload_sha256": payload_sha,
                    "changed_files": sed.changed_files(payload), "attempts": attempts,
                    "model_calls": call_idx,
                    "generated_tokens": generated_tokens if token_metric_available else None,
                    "output_chars_proxy": output_chars, "verifier_calls": verifier_calls,
                    "verifier_ms": verifier_ms, "retained_state_chars": len(memory),
                    "wall_ms": round((time.perf_counter() - started) * 1000, 3),
                }

            if call_idx < exp.MAX_CALLS:
                fail_tail = verdict.get("test_output", "")[-7000:]
                feedback = (
                    "\n\nATTEMPT STATE FROM PRIOR CALL:\n"
                    "The following normalized structured edit was executed and is now VERIFIER-DISPROVED:\n" + payload +
                    "\nSHA256: " + payload_sha +
                    "\n\nNATIVE VERIFIER FEEDBACK:\n" + fail_tail +
                    "\nThe executed hypothesis failed. Do NOT repeat this edit exactly or make an equivalent edit with the same mechanism. "
                    "Treat it as falsified evidence and search for a substantively different repair hypothesis. "
                    "Return revised structured-edit JSON only."
                )

    return {
        "arm": arm, "seed": seed, "status": "UNSOLVED", "solved": False,
        "attempts": attempts, "model_calls": exp.MAX_CALLS,
        "generated_tokens": generated_tokens if token_metric_available else None,
        "output_chars_proxy": output_chars, "verifier_calls": verifier_calls,
        "verifier_ms": verifier_ms, "retained_state_chars": len(memory),
        "wall_ms": round((time.perf_counter() - started) * 1000, 3),
    }


def postprocess(out: Path) -> None:
    src = out / "V151_RESULT.json"
    if not src.is_file():
        raise RuntimeError("V151 base result missing")
    r = json.loads(src.read_text())
    raw_rows = r.get("rows", {}).get("D_PLUS_RAW_T1", [])
    raw_distinct = 0
    raw_distinct_verified = 0
    for rr in raw_rows:
        for a in rr.get("attempts", []):
            if a.get("call") == 2 and a.get("distinct_second_candidate") is True:
                raw_distinct += 1
                if isinstance(a.get("verdict"), dict):
                    raw_distinct_verified += 1
                break

    s1 = raw_distinct >= 2
    compiled = r.get("compiled_o1_advantage") in {"REACHABILITY", "EFFICIENCY"}
    raw = r.get("raw_t1_advantage") in {"REACHABILITY", "EFFICIENCY"}
    all_comparable = all(v.get("n_comparable") == len(exp.SEEDS) for v in r.get("summary", {}).values())

    if not s1:
        verdict = "OBSTRUCTED_SEARCH_POLICY_STILL_COLLAPSED"
    elif raw and not compiled:
        verdict = "PASS_V152_CAPABILITY_COMPILATION_LOSS"
    elif compiled:
        verdict = "PASS_V152_COMPILED_DEVELOPMENTAL_SIGNAL"
    elif raw:
        verdict = "PASS_V152_RAW_DEVELOPMENTAL_SIGNAL"
    elif all_comparable and raw_distinct_verified >= 1:
        verdict = "NEGATIVE_V152_NO_T1_DEVELOPMENTAL_SIGNAL_UNDER_STATEFUL_SEARCH"
    else:
        verdict = "R10_OR_INSUFFICIENT_STATEFUL_EVIDENCE"

    r["canonical_id"] = "V152_ATTEMPT_STATE_THREADING_SEPARATOR"
    r["protocol"] = "protocols/V152_ATTEMPT_STATE_THREADING_SEPARATOR_PRECOMMIT.md"
    r["state_threading"] = {
        "raw_distinct_second_candidates": raw_distinct,
        "raw_distinct_second_candidates_reaching_verifier": raw_distinct_verified,
        "S1_breaks_repeat_attractor": s1,
        "v151b_raw_distinct_baseline": 0,
    }
    r["verdict"] = verdict
    (out / "V152_RESULT.json").write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")


def main() -> None:
    exp.run_seed_arm = run_seed_arm_stateful
    exp.main()
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--out", type=Path, required=True)
    args, _ = ap.parse_known_args()
    postprocess(args.out)
    print((args.out / "V152_RESULT.json").read_text())


if __name__ == "__main__":
    main()
