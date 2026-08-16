#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

# Reuse the proven precompiled exact-runtime apparatus only.
import v145_precompiled_runner  # noqa: F401
import bugsinpy_four_arm as base
import bugsinpy_exact_runtime as exact_runtime
import structured_edit_protocol_v2 as sed
import v145_natural_third_rung_causal as v145
from river_qwen35_provider import Qwen35ChatRiverProvider
from v149_context_resolver import resolve_context

MODEL = "Qwen/Qwen3.5-9B"
MAX_TOKENS = 2048
MAX_CALLS = 2
SEEDS = [202608161, 202608162, 202608163]
T1 = ("httpie", 5)
T2 = ("youtube-dl", 32)
EXPECTED_T1_DIFF_SHA256 = "b7f419e7993e92164969b7a99689f01dfa279ce2d1615e25fce0bb21486f472d"
EXPECTED_O1_ARTIFACT_SHA256 = "7ebb7fb26da6d137c13c1a08bafd7e540dbd52f25e04cf4298502e5ce5428546"

base.native_test = exact_runtime.native_test
v145.base.native_test = exact_runtime.native_test

O1 = {
    "capability_id": "V145.O1",
    "generation": "O1",
    "instruction": "When parsing key-value pairs with custom separators, first identify all escape sequences (a backslash followed by a separator) and record their byte spans. Then, iterate through separator matches; only treat a separator as a delimiter if it does not fall entirely within the span of any identified escape sequence.",
    "preconditions": [
        "A parser accepts custom key-value separators.",
        "Input may contain escaped occurrences of those separators.",
        "Current parsing incorrectly treats escaped separators as delimiters."
    ],
    "postconditions": [
        "Escaped separator spans are identified before splitting.",
        "Separators inside recorded escape spans are ignored as delimiters.",
        "Key-value pairs are split only on unescaped separator occurrences."
    ],
    "applicability_test": "Apply when item/key-value parsing fails an assertion involving a backslash-escaped custom separator and the observed output shows an escaped separator was split as if it were structural.",
    "ancestor_ids": [],
    "source_intervention_sha256": EXPECTED_T1_DIFF_SHA256,
    "artifact_sha256": EXPECTED_O1_ARTIFACT_SHA256,
}


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def verify_o1_identity() -> None:
    cap = dict(O1)
    stored = cap.pop("artifact_sha256")
    actual = hashlib.sha256(json.dumps(cap, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if stored != EXPECTED_O1_ARTIFACT_SHA256 or actual != EXPECTED_O1_ARTIFACT_SHA256:
        raise RuntimeError(f"O1 identity mismatch stored={stored} computed={actual}")


def prepare_t2(bugsinpy: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="v151-prep-t2-") as td:
        work = base.checkout_buggy(bugsinpy, T2[0], T2[1], Path(td))
        baseline = exact_runtime.native_test(bugsinpy, work)
        if baseline.get("infrastructure_error"):
            return {"status": "R10", "reason": baseline["infrastructure_error"], "baseline": baseline}
        if baseline.get("passed"):
            return {"status": "REPRODUCTION_NEGATIVE", "baseline": baseline}
        context, files, audit = resolve_context(work, baseline.get("test_output", ""), max_files=6, max_chars=36000)
        prompt = sed.visible_request(T2[0], T2[1], baseline.get("test_output", ""), context)
        return {
            "status": "READY",
            "project": T2[0],
            "bug_id": T2[1],
            "baseline": baseline,
            "context_files": files,
            "context_audit": audit,
            "context_sha256": sha_text(context),
            "visible_prompt": prompt,
            "visible_prompt_sha256": sha_text(prompt),
        }


def raw_t1_memory(t1: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    evidence = {
        "failure_class": t1.get("failure_class"),
        "failing_test_tail": t1.get("baseline_failure_tail", "")[-5000:],
        "changed_files": t1.get("changed_files", []),
        "verified_intervention": t1.get("diff", ""),
        "ancestors": [],
    }
    memory = "RETAINED VERIFIED ACQUISITION TRACE:\n" + json.dumps(evidence, sort_keys=True)
    return memory, evidence


def sham_for(n: int) -> str:
    seed = 'RETAINED CONTROL STATE: {"kind":"SHAM","instruction":"neutral placeholder only; no repair semantics","evidence":"none"}'
    filler = "|neutral-control-token"
    out = seed
    while len(out) < n:
        out += filler
    return out[:n]


def response_cost(row: dict[str, Any] | None, text: str) -> dict[str, Any]:
    return v145.response_cost(row, text)


def run_seed_arm(provider: Qwen35ChatRiverProvider, bugsinpy: Path, task: dict[str, Any],
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

    for call_idx in range(1, MAX_CALLS + 1):
        prompt = prompt0 + feedback
        try:
            response = provider.sample(prompt, seed=seed + call_idx - 1, max_tokens=MAX_TOKENS)
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
            row["edit_payload_sha256"] = sha_text(payload)
            row["changed_files"] = sed.changed_files(payload)
        except Exception as exc:
            row["transport_error"] = f"extract: {exc.__class__.__name__}: {exc}"
            attempts.append(row)
            feedback = (
                "\n\nTRANSPORT FEEDBACK FROM PRIOR ATTEMPT:\n"
                "Your previous answer did not satisfy the required structured-edit JSON schema. "
                "Return ONLY JSON with 1-3 exact replacement edits; copy each old string exactly from the shown buggy source."
            )
            continue

        with tempfile.TemporaryDirectory(prefix=f"v151-{arm}-{seed}-") as td:
            try:
                work = base.checkout_buggy(bugsinpy, T2[0], T2[1], Path(td))
                sed.apply_edits(work, payload)
            except Exception as exc:
                row["transport_error"] = f"apply: {exc.__class__.__name__}: {exc}"
                attempts.append(row)
                feedback = (
                    "\n\nTRANSPORT FEEDBACK FROM PRIOR ATTEMPT:\n"
                    "The structured edit did not apply to the unchanged buggy checkout. "
                    "Use only a production Python path shown in source context and copy old text exactly so it occurs once."
                )
                continue

            verdict = exact_runtime.native_test(bugsinpy, work)
            verifier_calls += 1
            verifier_ms += float(verdict.get("duration_ms") or 0)
            row["verdict"] = verdict
            attempts.append(row)
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
                    "successful_edit_payload_sha256": sha_text(payload),
                    "changed_files": sed.changed_files(payload), "attempts": attempts,
                    "model_calls": call_idx,
                    "generated_tokens": generated_tokens if token_metric_available else None,
                    "output_chars_proxy": output_chars, "verifier_calls": verifier_calls,
                    "verifier_ms": verifier_ms, "retained_state_chars": len(memory),
                    "wall_ms": round((time.perf_counter() - started) * 1000, 3),
                }

            fail_tail = verdict.get("test_output", "")[-7000:]
            feedback = (
                "\n\nNATIVE VERIFIER FEEDBACK FROM PRIOR ATTEMPT:\n"
                "The applied candidate did not pass. Diagnose this residual and return revised structured-edit JSON only.\n"
                + fail_tail
            )

    return {
        "arm": arm, "seed": seed, "status": "UNSOLVED", "solved": False,
        "attempts": attempts, "model_calls": MAX_CALLS,
        "generated_tokens": generated_tokens if token_metric_available else None,
        "output_chars_proxy": output_chars, "verifier_calls": verifier_calls,
        "verifier_ms": verifier_ms, "retained_state_chars": len(memory),
        "wall_ms": round((time.perf_counter() - started) * 1000, 3),
    }


def arm_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    comparable = [r for r in rows if r.get("status") != "R10"]
    solved = [r for r in comparable if r.get("solved")]
    calls = [r["calls_to_solve"] for r in solved if r.get("calls_to_solve") is not None]
    toks = [r["generated_tokens"] for r in solved if r.get("generated_tokens") is not None]
    chars = [r["output_chars_proxy"] for r in solved if r.get("output_chars_proxy") is not None]
    return {
        "n_total": len(rows), "n_comparable": len(comparable), "n_r10": len(rows) - len(comparable),
        "solved_n": len(solved),
        "median_calls_to_solve": statistics.median(calls) if calls else None,
        "median_generated_tokens": statistics.median(toks) if toks else None,
        "median_output_chars_proxy": statistics.median(chars) if chars else None,
        "verifier_calls": sum(int(r.get("verifier_calls") or 0) for r in rows),
        "transport_failures": sum(
            1 for r in rows for a in r.get("attempts", []) if a.get("transport_error")
        ),
    }


def advantage(target: dict[str, Any], cold: dict[str, Any], sham: dict[str, Any]) -> str:
    controls = [cold, sham]
    if target["n_comparable"] != len(SEEDS) or any(c["n_comparable"] != len(SEEDS) for c in controls):
        return "R10_INSUFFICIENT_COMPARABLE"
    if all(target["solved_n"] > c["solved_n"] for c in controls):
        return "REACHABILITY"
    if all(target["solved_n"] >= c["solved_n"] for c in controls):
        tied = [c for c in controls if c["solved_n"] == target["solved_n"]]
        if tied and target["solved_n"] > 0:
            tc = target.get("median_calls_to_solve")
            if tc is not None and all(c.get("median_calls_to_solve") is not None for c in tied):
                if all(tc < c["median_calls_to_solve"] for c in tied):
                    return "EFFICIENCY"
                if any(tc != c["median_calls_to_solve"] for c in tied):
                    return "NULL"
            tt = target.get("median_generated_tokens")
            if tt is not None and all(c.get("median_generated_tokens") is not None for c in tied):
                if all(tt < c["median_generated_tokens"] for c in tied):
                    return "EFFICIENCY"
            tch = target.get("median_output_chars_proxy")
            if tch is not None and all(c.get("median_output_chars_proxy") is not None for c in tied):
                if all(tch < c["median_output_chars_proxy"] for c in tied):
                    return "EFFICIENCY"
    return "NULL"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("output directory exists; refusing to overwrite evidence")
    args.out.mkdir(parents=True)

    result: dict[str, Any] = {
        "canonical_id": "V151_CAPABILITY_COMPILATION_LOSS_SEPARATOR",
        "protocol": "protocols/V151_CAPABILITY_COMPILATION_LOSS_SEPARATOR_PRECOMMIT.md",
        "model": MODEL, "max_tokens": MAX_TOKENS, "max_calls": MAX_CALLS,
        "seeds": SEEDS, "T1": "httpie/5", "T2": "youtube-dl/32",
        "output_protocol": "structured_edit_protocol_v2",
    }

    try:
        verify_o1_identity()
    except Exception as exc:
        result.update(verdict="R10_INCONCLUSIVE", reason=f"O1 identity: {exc}")
        args.out.joinpath("V151_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True)); return

    t1 = v145.verify_acquisition_intervention(args.bugsinpy, *T1)
    result["T1_intervention"] = {k: v for k, v in t1.items() if k != "diff"}
    if t1.get("status") != "VERIFIED" or t1.get("diff_sha256") != EXPECTED_T1_DIFF_SHA256:
        result.update(verdict="R10_INCONCLUSIVE", reason="T1 intervention identity/replay mismatch")
        args.out.joinpath("V151_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True)); return

    task = prepare_t2(args.bugsinpy)
    result["T2_prepared"] = {k: v for k, v in task.items() if k != "visible_prompt"}
    if task.get("status") != "READY":
        result.update(verdict="R10_INCONCLUSIVE", reason="T2 context/reproduction not ready")
        args.out.joinpath("V151_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True)); return

    o1mem = v145.capability_memory([O1])
    rawmem, raw_evidence = raw_t1_memory(t1)
    sham_o1 = sham_for(len(o1mem))
    sham_raw = sham_for(len(rawmem))
    assert len(sham_o1) == len(o1mem) and len(sham_raw) == len(rawmem)
    result["memory"] = {
        "o1_chars": len(o1mem), "o1_sha256": sha_text(o1mem),
        "raw_chars": len(rawmem), "raw_sha256": sha_text(rawmem),
        "raw_evidence_sha256": hashlib.sha256(json.dumps(raw_evidence, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "sham_o1_sha256": sha_text(sham_o1), "sham_raw_sha256": sha_text(sham_raw),
        "o1_artifact_sha256": EXPECTED_O1_ARTIFACT_SHA256,
    }

    provider = Qwen35ChatRiverProvider(MODEL)
    memories = {
        "D_COLD": "",
        "D_PLUS_O1_COMPILED": o1mem,
        "D_PLUS_RAW_T1": rawmem,
        "D_PLUS_SHAM_O1": sham_o1,
        "D_PLUS_SHAM_RAW": sham_raw,
    }
    rows: dict[str, list[dict[str, Any]]] = {k: [] for k in memories}
    for seed in SEEDS:
        for arm in ["D_COLD", "D_PLUS_O1_COMPILED", "D_PLUS_RAW_T1", "D_PLUS_SHAM_O1", "D_PLUS_SHAM_RAW"]:
            rows[arm].append(run_seed_arm(provider, args.bugsinpy, task, arm, seed, memories[arm]))

    summaries = {k: arm_summary(v) for k, v in rows.items()}
    o1adv = advantage(summaries["D_PLUS_O1_COMPILED"], summaries["D_COLD"], summaries["D_PLUS_SHAM_O1"])
    rawadv = advantage(summaries["D_PLUS_RAW_T1"], summaries["D_COLD"], summaries["D_PLUS_SHAM_RAW"])
    result["rows"] = rows
    result["summary"] = summaries
    result["compiled_o1_advantage"] = o1adv
    result["raw_t1_advantage"] = rawadv

    if any(s["n_comparable"] != len(SEEDS) for s in summaries.values()):
        verdict = "R10_INCONCLUSIVE"
    elif o1adv in {"REACHABILITY", "EFFICIENCY"} and rawadv in {"REACHABILITY", "EFFICIENCY"}:
        verdict = "PASS_V151_BOTH_REPRESENTATIONS_SIGNAL"
    elif o1adv in {"REACHABILITY", "EFFICIENCY"}:
        verdict = "PASS_V151_COMPILED_O1_CAUSAL_SIGNAL"
    elif rawadv in {"REACHABILITY", "EFFICIENCY"} and summaries["D_PLUS_RAW_T1"]["solved_n"] > 0:
        verdict = "PASS_V151_CAPABILITY_COMPILATION_LOSS"
    else:
        verdict = "NEGATIVE_V151_NO_T1_DEVELOPMENTAL_SIGNAL_WITHIN_BUDGET"
    result["verdict"] = verdict

    args.out.joinpath("V151_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": verdict,
        "compiled_o1_advantage": o1adv,
        "raw_t1_advantage": rawadv,
        "summary": summaries,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
