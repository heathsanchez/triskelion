#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path
from typing import Any

import v152_attempt_state_threading_separator as prev

# Reuse the exact V152 substrate, including the immutable V149 O1 binding.
exp = prev.exp
base = prev.base
exact_runtime = prev.exact_runtime
sed = prev.sed
sha_text = prev.sha_text
response_cost = prev.response_cost


def parse_ranked_rivals(text: str, prior_sha: str | None) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    audit: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None
    try:
        obj = sed._json_object(text)
    except Exception as exc:
        return [{"rank": None, "status": "OBJECT_PARSE_ERROR", "error": f"{exc.__class__.__name__}: {exc}"}], None

    alternatives = obj.get("alternatives")
    if not isinstance(alternatives, list) or len(alternatives) != 3:
        return [{"rank": None, "status": "BAD_ALTERNATIVES_CARDINALITY", "observed_type": type(alternatives).__name__, "observed_n": len(alternatives) if isinstance(alternatives, list) else None}], None

    seen: set[str] = set()
    for idx, alt in enumerate(alternatives, start=1):
        row: dict[str, Any] = {"rank": idx}
        if not isinstance(alt, dict):
            row.update(status="INVALID_ALT_OBJECT")
            audit.append(row)
            continue
        row["diagnosis"] = alt.get("diagnosis") if isinstance(alt.get("diagnosis"), str) else None
        edits = alt.get("edits")
        try:
            payload = sed.extract_edits(json.dumps({"edits": edits}, ensure_ascii=False))
            h = sha_text(payload)
            row.update(status="VALID", payload_sha256=h, changed_files=sed.changed_files(payload))
            row["duplicates_falsified_call1"] = prior_sha is not None and h == prior_sha
            row["duplicates_earlier_rival"] = h in seen
            seen.add(h)
            if selected is None and not row["duplicates_falsified_call1"] and not row["duplicates_earlier_rival"]:
                selected = {"rank": idx, "payload": payload, "payload_sha256": h, "diagnosis": row["diagnosis"]}
                row["selected"] = True
            else:
                row["selected"] = False
        except Exception as exc:
            row.update(status="INVALID_EDITS", error=f"{exc.__class__.__name__}: {exc}")
        audit.append(row)
    return audit, selected


def run_seed_arm_rivals(provider, bugsinpy: Path, task: dict[str, Any],
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
    prior_payload: str | None = None
    prior_sha: str | None = None

    for call_idx in range(1, exp.MAX_CALLS + 1):
        prompt = prompt0 + feedback
        try:
            response = provider.sample(prompt, seed=seed + call_idx - 1, max_tokens=exp.MAX_TOKENS)
            text = response.text
            rr = response.to_dict()
        except Exception as exc:
            return {"arm": arm, "seed": seed, "status": "R10", "reason": f"provider error: {exc.__class__.__name__}: {exc}", "attempts": attempts, "model_calls": call_idx - 1, "verifier_calls": verifier_calls, "verifier_ms": verifier_ms, "wall_ms": round((time.perf_counter()-started)*1000,3)}

        c = response_cost(rr, text)
        output_chars += c["output_chars_proxy"]
        if c["generated_tokens"] is None:
            token_metric_available = False
        else:
            generated_tokens += c["generated_tokens"]
        row: dict[str, Any] = {"call": call_idx, "prompt_sha256": sha_text(prompt), "response_sha256": sha_text(text), "response_cost": c, "response": rr}

        if call_idx == 1:
            try:
                payload = sed.extract_edits(text)
                payload_sha = sha_text(payload)
                row["edit_payload_sha256"] = payload_sha
                row["changed_files"] = sed.changed_files(payload)
            except Exception as exc:
                row["transport_error"] = f"extract: {exc.__class__.__name__}: {exc}"
                attempts.append(row)
                feedback = (
                    "\n\nATTEMPT STATE FROM PRIOR CALL:\nThe prior raw response was:\n" + text[-6000:] +
                    "\n\nThat action was not executable. Your final call must return ONLY JSON with exactly three ranked rivals in this schema: "
                    '{"alternatives":[{"diagnosis":"...","edits":[{"path":"...","old":"...","new":"..."}]},{"diagnosis":"...","edits":[...]},{"diagnosis":"...","edits":[...]}]}. '
                    "Make the three repair mechanisms substantively different."
                )
                continue
        else:
            rival_audit, selected = parse_ranked_rivals(text, prior_sha)
            row["rivals"] = rival_audit
            row["alternatives_emitted"] = 3 if rival_audit and rival_audit[0].get("rank") is not None else 0
            row["alternatives_valid"] = sum(1 for x in rival_audit if x.get("status") == "VALID")
            row["alternatives_distinct_from_call1"] = sum(1 for x in rival_audit if x.get("status") == "VALID" and not x.get("duplicates_falsified_call1"))
            row["selected_rank"] = selected.get("rank") if selected else None
            row["selected_payload_sha256"] = selected.get("payload_sha256") if selected else None
            if selected is None:
                row["rival_error"] = "NO_DISTINCT_VALID_RIVAL"
                attempts.append(row)
                continue
            payload = selected["payload"]
            payload_sha = selected["payload_sha256"]
            row["edit_payload_sha256"] = payload_sha
            row["changed_files"] = sed.changed_files(payload)

        with tempfile.TemporaryDirectory(prefix=f"v153-{arm}-{seed}-") as td:
            try:
                work = base.checkout_buggy(bugsinpy, exp.T2[0], exp.T2[1], Path(td))
                sed.apply_edits(work, payload)
            except Exception as exc:
                row["transport_error"] = f"apply: {exc.__class__.__name__}: {exc}"
                attempts.append(row)
                if call_idx == 1:
                    feedback = (
                        "\n\nATTEMPT STATE FROM PRIOR CALL:\nThe prior normalized structured edit was:\n" + payload +
                        "\nSHA256: " + payload_sha +
                        "\n\nIt did not apply. Your final call must return ONLY JSON with exactly three ranked, substantively different repair alternatives in schema "
                        '{"alternatives":[{"diagnosis":"...","edits":[...]},{"diagnosis":"...","edits":[...]},{"diagnosis":"...","edits":[...]}]}. '
                        "Do not repeat the failed edit."
                    )
                continue

            verdict = exact_runtime.native_test(bugsinpy, work)
            verifier_calls += 1
            verifier_ms += float(verdict.get("duration_ms") or 0)
            row["verdict"] = verdict
            attempts.append(row)
            if call_idx == 1:
                prior_payload, prior_sha = payload, payload_sha

            if verdict.get("infrastructure_error"):
                return {"arm": arm, "seed": seed, "status": "R10", "reason": verdict["infrastructure_error"], "attempts": attempts, "model_calls": call_idx, "verifier_calls": verifier_calls, "verifier_ms": verifier_ms, "wall_ms": round((time.perf_counter()-started)*1000,3)}
            if verdict.get("passed"):
                return {"arm": arm, "seed": seed, "status": "VERIFIED_SOLVED", "solved": True, "calls_to_solve": call_idx, "successful_edit_payload": payload, "successful_edit_payload_sha256": payload_sha, "changed_files": sed.changed_files(payload), "attempts": attempts, "model_calls": call_idx, "generated_tokens": generated_tokens if token_metric_available else None, "output_chars_proxy": output_chars, "verifier_calls": verifier_calls, "verifier_ms": verifier_ms, "retained_state_chars": len(memory), "wall_ms": round((time.perf_counter()-started)*1000,3)}

            if call_idx == 1:
                fail_tail = verdict.get("test_output", "")[-7000:]
                feedback = (
                    "\n\nATTEMPT STATE FROM PRIOR CALL:\nThe following normalized edit was executed and is VERIFIER-DISPROVED:\n" + payload +
                    "\nSHA256: " + payload_sha +
                    "\n\nNATIVE VERIFIER FEEDBACK:\n" + fail_tail +
                    "\nGenerate a RANKED SET OF RIVALS rather than another single best guess. Return ONLY JSON with exactly three alternatives: "
                    '{"alternatives":[{"diagnosis":"short mechanism","edits":[{"path":"relative/path.py","old":"exact source","new":"replacement"}]},{"diagnosis":"different mechanism","edits":[...]},{"diagnosis":"third different mechanism","edits":[...]}]}. '
                    "Each alternative must be substantively different from the falsified edit and from the other alternatives. The controller will deterministically test only the first valid distinct alternative."
                )

    return {"arm": arm, "seed": seed, "status": "UNSOLVED", "solved": False, "attempts": attempts, "model_calls": exp.MAX_CALLS, "generated_tokens": generated_tokens if token_metric_available else None, "output_chars_proxy": output_chars, "verifier_calls": verifier_calls, "verifier_ms": verifier_ms, "retained_state_chars": len(memory), "wall_ms": round((time.perf_counter()-started)*1000,3)}


def postprocess(out: Path) -> None:
    src = out / "V151_RESULT.json"
    if not src.is_file():
        raise RuntimeError("V151 base result missing")
    r = json.loads(src.read_text())
    raw_rows = r.get("rows", {}).get("D_PLUS_RAW_T1", [])
    rival_seeds = 0
    rival_verified = 0
    selected_ranks: list[int] = []
    for rr in raw_rows:
        for a in rr.get("attempts", []):
            if a.get("call") != 2:
                continue
            if int(a.get("alternatives_distinct_from_call1") or 0) >= 1:
                rival_seeds += 1
            if a.get("selected_rank") is not None:
                selected_ranks.append(int(a["selected_rank"]))
                if isinstance(a.get("verdict"), dict):
                    rival_verified += 1
            break

    r1 = rival_seeds >= 2
    r2 = rival_verified >= 1
    compiled = r.get("compiled_o1_advantage") in {"REACHABILITY", "EFFICIENCY"}
    raw = r.get("raw_t1_advantage") in {"REACHABILITY", "EFFICIENCY"}
    all_comparable = all(v.get("n_comparable") == len(exp.SEEDS) for v in r.get("summary", {}).values())

    if not r1:
        verdict = "OBSTRUCTED_V153_NO_RIVAL_HYPOTHESIS_GENERATION"
    elif not r2:
        verdict = "OBSTRUCTED_V153_RIVALS_DO_NOT_REACH_VERIFIER"
    elif raw and not compiled:
        verdict = "PASS_V153_CAPABILITY_COMPILATION_LOSS"
    elif compiled:
        verdict = "PASS_V153_COMPILED_DEVELOPMENTAL_SIGNAL"
    elif raw:
        verdict = "PASS_V153_RAW_DEVELOPMENTAL_SIGNAL"
    elif all_comparable:
        verdict = "NEGATIVE_V153_NO_T1_DEVELOPMENTAL_SIGNAL_UNDER_RIVAL_SEARCH"
    else:
        verdict = "R10_OR_INSUFFICIENT_RIVAL_EVIDENCE"

    r["canonical_id"] = "V153_SET_VALUED_RIVAL_SEARCH"
    r["protocol"] = "protocols/V153_SET_VALUED_RIVAL_SEARCH_PRECOMMIT.md"
    r["rival_search"] = {"raw_rival_generating_seeds": rival_seeds, "raw_distinct_selected_reaching_verifier": rival_verified, "selected_ranks": selected_ranks, "R1_rival_generation": r1, "R2_rival_execution": r2, "v152_raw_distinct_baseline": 0}
    r["verdict"] = verdict
    (out / "V153_RESULT.json").write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")


def main() -> None:
    exp.run_seed_arm = run_seed_arm_rivals
    exp.main()
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--out", type=Path, required=True)
    args, _ = ap.parse_known_args()
    postprocess(args.out)
    print((args.out / "V153_RESULT.json").read_text())


if __name__ == "__main__":
    main()
