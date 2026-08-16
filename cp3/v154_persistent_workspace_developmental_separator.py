#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path
from typing import Any

import v153_set_valued_rival_search as prev

exp = prev.exp
base = prev.base
exact_runtime = prev.exact_runtime
sed = prev.sed
sha_text = prev.sha_text
response_cost = prev.response_cost
parse_ranked_rivals = prev.parse_ranked_rivals


def run_seed_arm_persistent(provider, bugsinpy: Path, task: dict[str, Any],
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
    prior_sha: str | None = None

    with tempfile.TemporaryDirectory(prefix=f"v154-{arm}-{seed}-") as td:
        try:
            work = base.checkout_buggy(bugsinpy, exp.T2[0], exp.T2[1], Path(td))
        except Exception as exc:
            return {
                "arm": arm, "seed": seed, "status": "R10",
                "reason": f"initial checkout: {exc.__class__.__name__}: {exc}",
                "attempts": [], "model_calls": 0, "verifier_calls": 0,
                "verifier_ms": 0.0,
                "wall_ms": round((time.perf_counter()-started)*1000,3),
            }

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
                    "wall_ms": round((time.perf_counter()-started)*1000,3),
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
                "persistent_workspace": True,
            }

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
                row["alternatives_distinct_from_call1"] = sum(
                    1 for x in rival_audit if x.get("status") == "VALID" and not x.get("duplicates_falsified_call1")
                )
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

            try:
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
                prior_sha = payload_sha

            if verdict.get("infrastructure_error"):
                return {
                    "arm": arm, "seed": seed, "status": "R10",
                    "reason": verdict["infrastructure_error"],
                    "attempts": attempts, "model_calls": call_idx,
                    "verifier_calls": verifier_calls, "verifier_ms": verifier_ms,
                    "wall_ms": round((time.perf_counter()-started)*1000,3),
                }
            if verdict.get("passed"):
                return {
                    "arm": arm, "seed": seed, "status": "VERIFIED_SOLVED", "solved": True,
                    "calls_to_solve": call_idx,
                    "successful_edit_payload": payload,
                    "successful_edit_payload_sha256": payload_sha,
                    "changed_files": sed.changed_files(payload),
                    "attempts": attempts, "model_calls": call_idx,
                    "generated_tokens": generated_tokens if token_metric_available else None,
                    "output_chars_proxy": output_chars,
                    "verifier_calls": verifier_calls, "verifier_ms": verifier_ms,
                    "retained_state_chars": len(memory),
                    "wall_ms": round((time.perf_counter()-started)*1000,3),
                }

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

    return {
        "arm": arm, "seed": seed, "status": "UNSOLVED", "solved": False,
        "attempts": attempts, "model_calls": exp.MAX_CALLS,
        "generated_tokens": generated_tokens if token_metric_available else None,
        "output_chars_proxy": output_chars,
        "verifier_calls": verifier_calls, "verifier_ms": verifier_ms,
        "retained_state_chars": len(memory),
        "wall_ms": round((time.perf_counter()-started)*1000,3),
    }


def postprocess(out: Path) -> None:
    src = out / "V151_RESULT.json"
    r = json.loads(src.read_text())
    r["canonical_id"] = "V154_PERSISTENT_WORKSPACE_DEVELOPMENTAL_SEPARATOR"
    r["protocol"] = "protocols/V154_PERSISTENT_WORKSPACE_DEVELOPMENTAL_SEPARATOR_PRECOMMIT.md"
    r["persistent_workspace"] = True

    comparable = all(v.get("n_comparable") == len(exp.SEEDS) for v in r.get("summary", {}).values())
    o1adv = r.get("compiled_o1_advantage")
    rawadv = r.get("raw_t1_advantage")
    positive = {"REACHABILITY", "EFFICIENCY"}
    raw_solved = r.get("summary", {}).get("D_PLUS_RAW_T1", {}).get("solved_n", 0)

    reach: dict[str, Any] = {}
    for arm, rows in r.get("rows", {}).items():
        c2 = [a for rr in rows for a in rr.get("attempts", []) if a.get("call") == 2]
        reach[arm] = {
            "call2_selected_reaching_verifier": sum(1 for a in c2 if a.get("selected_rank") is not None and isinstance(a.get("verdict"), dict)),
            "call2_transport_failures": sum(1 for a in c2 if a.get("transport_error")),
            "call2_selected_payloads": [a.get("selected_payload_sha256") for a in c2 if a.get("selected_payload_sha256")],
        }
    r["persistent_state_audit"] = reach

    if not comparable:
        verdict = "R10_INCONCLUSIVE_V154"
    elif o1adv in positive and rawadv in positive:
        verdict = "PASS_V154_BOTH_REPRESENTATIONS_SIGNAL_PERSISTENT_STATE"
    elif o1adv in positive:
        verdict = "PASS_V154_COMPILED_O1_CAUSAL_SIGNAL_PERSISTENT_STATE"
    elif rawadv in positive and raw_solved > 0:
        verdict = "PASS_V154_RAW_T1_CAUSAL_SIGNAL_PERSISTENT_STATE"
    else:
        verdict = "NEGATIVE_V154_NO_T1_DEVELOPMENTAL_SIGNAL_PERSISTENT_STATE"
    r["verdict"] = verdict

    dst = out / "V154_RESULT.json"
    dst.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "compiled_o1_advantage": o1adv,
        "raw_t1_advantage": rawadv,
        "summary": r.get("summary"),
        "persistent_state_audit": reach,
    }, indent=2, sort_keys=True))


def main() -> None:
    exp.run_seed_arm = run_seed_arm_persistent
    exp.main()
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--out", type=Path, required=True)
    args, _ = ap.parse_known_args()
    postprocess(args.out)


if __name__ == "__main__":
    main()
