from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import bugsinpy_four_arm as base
import bugsinpy_exact_runtime as exact_runtime
import structured_edit_protocol_v2 as sed
from river_qwen35_provider import Qwen35ChatRiverProvider
from v149_context_resolver import resolve_context

MODEL = "Qwen/Qwen3.5-9B"
MAX_TOKENS = 2048
MAX_CALLS = 2
WINDOW = 40

# Deliberately do NOT import v145_precompiled_runner or any V151-V157 module.
# Every cell gets a fresh checkout and every verifier call uses the full exact
# historical compile+test adapter.
base.native_test = exact_runtime.native_test


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def prepare_task(bugsinpy: Path, project: str, bug_id: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"v159-prep-{project}-") as td:
        work = base.checkout_buggy(bugsinpy, project, bug_id, Path(td))
        baseline = exact_runtime.native_test(bugsinpy, work)
        if baseline.get("infrastructure_error"):
            return {"status": "R10", "reason": baseline["infrastructure_error"], "baseline": baseline}
        if baseline.get("passed"):
            return {"status": "REPRODUCTION_NEGATIVE", "baseline": baseline}
        context, files, audit = resolve_context(work, baseline.get("test_output", ""), max_files=6, max_chars=36000)
        prompt = sed.visible_request(project, bug_id, baseline.get("test_output", ""), context)
        file_hashes = {}
        for rel in files:
            p = work / rel
            if p.is_file():
                file_hashes[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
        return {
            "status": "READY",
            "project": project,
            "bug_id": bug_id,
            "baseline": baseline,
            "failure_class": base.failure_class(baseline.get("test_output", "")),
            "context": context,
            "context_files": files,
            "context_audit": audit,
            "context_sha256": sha_text(context),
            "context_file_sha256": file_hashes,
            "visible_prompt": prompt,
            "visible_prompt_sha256": sha_text(prompt),
        }


def _assert_clean_identity(work: Path, task: dict[str, Any]) -> None:
    for rel, expected in task.get("context_file_sha256", {}).items():
        p = work / rel
        if not p.is_file():
            raise RuntimeError(f"clean source missing: {rel}")
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"clean source hash mismatch for {rel}: {actual} != {expected}")


def _current_snapshot(work: Path, payload: str) -> tuple[str, dict[str, str]]:
    blocks: list[str] = []
    hashes: dict[str, str] = {}
    for rel in sed.changed_files(payload):
        p = work / rel
        if not p.is_file():
            raise RuntimeError(f"changed path disappeared: {rel}")
        raw = p.read_bytes()
        hashes[rel] = hashlib.sha256(raw).hexdigest()
        lines = raw.decode("utf-8", errors="strict").splitlines()
        cp = subprocess.run(
            ["git", "diff", "--unified=0", "--", rel],
            cwd=work,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        if cp.returncode:
            raise RuntimeError(f"git diff failed for {rel}: {cp.stderr[-500:]}")
        spans: list[list[int]] = []
        for m in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", cp.stdout, re.MULTILINE):
            start, count = int(m.group(1)), int(m.group(2) or "1")
            anchor = max(1, start)
            spans.append([max(1, anchor - WINDOW), min(len(lines), anchor + max(count, 1) - 1 + WINDOW)])
        if not spans:
            raise RuntimeError(f"no current-side hunk for {rel}")
        spans.sort()
        merged: list[list[int]] = []
        for lo, hi in spans:
            if not merged or lo > merged[-1][1] + 1:
                merged.append([lo, hi])
            else:
                merged[-1][1] = max(merged[-1][1], hi)
        blocks.append(f"FILE {rel} CURRENT_SHA256 {hashes[rel]}")
        for lo, hi in merged:
            blocks.append(f"CURRENT LINES {lo}-{hi}")
            blocks.extend(f"{n:05d}: {lines[n-1]}" for n in range(lo, hi + 1))
    if not blocks:
        raise RuntimeError("empty current-source snapshot")
    return "\n".join(blocks), hashes


def _response_cost(row: dict[str, Any] | None, text: str) -> dict[str, Any]:
    completion_tokens = None
    if isinstance(row, dict):
        for candidate in (row.get("usage"), row.get("metadata"), row):
            if not isinstance(candidate, dict):
                continue
            for key in ("completion_tokens", "output_tokens", "generated_tokens"):
                value = candidate.get(key)
                if isinstance(value, int):
                    completion_tokens = value
                    break
            if completion_tokens is not None:
                break
    return {
        "generated_tokens": completion_tokens,
        "output_chars_proxy": len(text),
        "token_metric": "provider_generated_tokens" if completion_tokens is not None else "output_chars_proxy",
    }


def run_seed_arm(
    provider: Qwen35ChatRiverProvider,
    bugsinpy: Path,
    task: dict[str, Any],
    *,
    arm: str,
    seed: int,
    memory: str,
) -> dict[str, Any]:
    started = time.perf_counter()
    prompt0 = task["visible_prompt"] + (("\n\n" + memory) if memory else "")
    feedback = ""
    attempts: list[dict[str, Any]] = []
    verifier_calls = 0
    verifier_ms = 0.0
    generated_tokens = 0
    output_chars = 0
    token_metric_available = True

    with tempfile.TemporaryDirectory(prefix=f"v159-{task['project']}-{arm}-{seed}-") as td:
        try:
            work = base.checkout_buggy(bugsinpy, task["project"], task["bug_id"], Path(td))
            _assert_clean_identity(work, task)
        except Exception as exc:
            return {
                "arm": arm, "seed": seed, "status": "R10",
                "reason": f"initial checkout identity: {exc.__class__.__name__}: {exc}",
                "attempts": [], "model_calls": 0, "verifier_calls": 0,
                "verifier_ms": 0.0, "wall_ms": round((time.perf_counter() - started) * 1000, 3),
            }

        prior_payload = ""
        source_sync_for_next = ""
        for call_idx in range(1, MAX_CALLS + 1):
            prompt = prompt0 + feedback
            if source_sync_for_next:
                prompt += source_sync_for_next
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

            cost = _response_cost(rr, text)
            output_chars += cost["output_chars_proxy"]
            if cost["generated_tokens"] is None:
                token_metric_available = False
            else:
                generated_tokens += cost["generated_tokens"]
            row: dict[str, Any] = {
                "call": call_idx,
                "prompt_sha256": sha_text(prompt),
                "response_sha256": sha_text(text),
                "response_cost": cost,
                "response": rr,
                "persistent_workspace": True,
                "fresh_cell_checkout": True,
                "full_exact_verifier": True,
                "source_sync_injected": bool(source_sync_for_next),
            }

            try:
                payload = sed.extract_edits(text)
                payload_sha = sha_text(payload)
                row["edit_payload_sha256"] = payload_sha
                row["changed_files"] = sed.changed_files(payload)
                if call_idx > 1 and prior_payload and payload_sha == sha_text(prior_payload):
                    row["duplicate_prior_payload"] = True
            except Exception as exc:
                row["transport_error"] = f"extract: {exc.__class__.__name__}: {exc}"
                attempts.append(row)
                feedback = (
                    "\n\nTRANSPORT FEEDBACK FROM PRIOR ATTEMPT:\n"
                    "Return ONLY the required structured-edit JSON. Each `old` string must be copied exactly from the CURRENT source and occur exactly once."
                )
                source_sync_for_next = ""
                continue

            try:
                sed.apply_edits(work, payload)
            except Exception as exc:
                row["transport_error"] = f"apply: {exc.__class__.__name__}: {exc}"
                attempts.append(row)
                feedback = (
                    "\n\nTRANSPORT FEEDBACK FROM PRIOR ATTEMPT:\n"
                    "The edit did not apply to the CURRENT working tree. Return a smaller structured edit grounded only in source shown in this task."
                )
                source_sync_for_next = ""
                continue

            verdict = exact_runtime.native_test(bugsinpy, work)
            verifier_calls += 1
            verifier_ms += float(verdict.get("duration_ms") or 0)
            row["verdict"] = verdict
            attempts.append(row)
            prior_payload = payload

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

            if call_idx < MAX_CALLS:
                try:
                    snapshot, hashes = _current_snapshot(work, payload)
                    row["post_failure_source_sha256"] = hashes
                    source_sync_for_next = (
                        "\n\nCURRENT POST-ATTEMPT SOURCE STATE:\n" + snapshot +
                        "\n\nYour next structured edit will be applied to this CURRENT source, not the original source. "
                        "Every `old` field must occur exactly once in the current source."
                    )
                except Exception as exc:
                    return {
                        "arm": arm, "seed": seed, "status": "R10",
                        "reason": f"source synchronization failed: {exc.__class__.__name__}: {exc}",
                        "attempts": attempts, "model_calls": call_idx, "verifier_calls": verifier_calls,
                        "verifier_ms": verifier_ms, "wall_ms": round((time.perf_counter() - started) * 1000, 3),
                    }
                feedback = (
                    "\n\nNATIVE VERIFIER FEEDBACK FROM PRIOR ATTEMPT:\n"
                    "The applied candidate did not pass. Diagnose the residual and return revised structured-edit JSON only.\n" +
                    verdict.get("test_output", "")[-7000:]
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
    return {
        "n_total": len(rows),
        "n_comparable": len(comparable),
        "n_r10": len(rows) - len(comparable),
        "solved_n": len(solved),
        "median_calls_to_solve": sorted(calls)[len(calls) // 2] if calls else None,
        "model_calls": sum(int(r.get("model_calls") or 0) for r in rows),
        "verifier_calls": sum(int(r.get("verifier_calls") or 0) for r in rows),
        "verifier_ms": round(sum(float(r.get("verifier_ms") or 0) for r in rows), 3),
        "output_chars_proxy": sum(int(r.get("output_chars_proxy") or 0) for r in rows),
        "transport_failures": sum(1 for r in rows for a in r.get("attempts", []) if a.get("transport_error")),
        "source_sync_failures": sum(1 for r in rows if "source synchronization failed" in str(r.get("reason", ""))),
    }


def strict_advantage(target: dict[str, Any], controls: list[dict[str, Any]], *, n: int) -> str:
    if target.get("n_comparable") != n or any(c.get("n_comparable") != n for c in controls):
        return "R10_INSUFFICIENT_COMPARABLE"
    if target.get("solved_n", 0) > max(c.get("solved_n", 0) for c in controls):
        return "REACHABILITY"
    if target.get("solved_n", 0) == max(c.get("solved_n", 0) for c in controls) and target.get("solved_n", 0) > 0:
        tc = target.get("median_calls_to_solve")
        ccs = [c.get("median_calls_to_solve") for c in controls]
        if tc is not None and all(x is not None and tc < x for x in ccs):
            return "EFFICIENCY"
    return "NULL"
