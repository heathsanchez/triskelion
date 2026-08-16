from __future__ import annotations

import hashlib
import json
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

import bugsinpy_four_arm as base
import bugsinpy_exact_runtime as exact_runtime
from river_qwen35_provider import Qwen35ChatRiverProvider
from structured_edit_protocol_v2 import _json_object

MODEL = "Qwen/Qwen3.5-9B"
MAX_TOKENS = 2048
SEEDS = [202608161, 202608162, 202608163]
MAX_CALLS = 2
STREAM = [("httpie", 5), ("youtube-dl", 32), ("pandas", 66)]

# Force the frozen exact historical verifier for all uses in this runner.
base.native_test = exact_runtime.native_test


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def patch_path(bugsinpy: Path, project: str, bug_id: int) -> Path:
    return bugsinpy / "projects" / project / "bugs" / str(bug_id) / "bug_patch.txt"


def changed_files(diff: str) -> list[str]:
    out: list[str] = []
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            p = line[6:]
            if p != "/dev/null" and p not in out:
                out.append(p)
    return out


def rejects_tests(paths: list[str]) -> bool:
    for raw in paths:
        p = Path(raw)
        low = [x.lower() for x in p.parts]
        n = p.name.lower()
        if "test" in low or "tests" in low or n.startswith("test_") or n.endswith("_test.py"):
            return True
    return False


def response_cost(row: dict[str, Any] | None, text: str) -> dict[str, Any]:
    completion_tokens = None
    if isinstance(row, dict):
        candidates = [row.get("usage"), row.get("metadata"), row]
        for c in candidates:
            if not isinstance(c, dict):
                continue
            for key in ("completion_tokens", "output_tokens", "generated_tokens"):
                v = c.get(key)
                if isinstance(v, int):
                    completion_tokens = v
                    break
            if completion_tokens is not None:
                break
    return {
        "generated_tokens": completion_tokens,
        "output_chars_proxy": len(text),
        "token_metric": "provider_generated_tokens" if completion_tokens is not None else "output_chars_proxy",
    }


def capability_memory(caps: list[dict[str, Any]]) -> str:
    if not caps:
        return ""
    payload = [{
        "capability_id": c["capability_id"],
        "instruction": c["instruction"],
        "preconditions": c["preconditions"],
        "postconditions": c["postconditions"],
        "applicability_test": c["applicability_test"],
    } for c in caps]
    return "RETAINED VERIFIED CAPABILITIES:\n" + json.dumps(payload, sort_keys=True)


def sham_for(n: int) -> str:
    # Capability-shaped but deliberately semantically empty. Exact character length is matched.
    seed = 'RETAINED CONTROL STATE: {"capability_id":"SHAM","instruction":"neutral placeholder only; no repair guidance","preconditions":[],"postconditions":[],"applicability_test":"none"}'
    filler = "|neutral-control-token"
    s = seed
    while len(s) < n:
        s += filler
    return s[:n]


def prepare_visible_task(bugsinpy: Path, project: str, bug_id: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"v145-prep-{project}-") as td:
        work = base.checkout_buggy(bugsinpy, project, bug_id, Path(td))
        baseline = exact_runtime.native_test(bugsinpy, work)
        if baseline.get("infrastructure_error"):
            return {"status": "R10", "reason": baseline["infrastructure_error"], "baseline": baseline}
        if baseline.get("passed"):
            return {"status": "REPRODUCTION_NEGATIVE", "baseline": baseline}
        context, files = base.collect_context(work, baseline.get("test_output", ""))
        prompt = base.visible_request(project, bug_id, baseline.get("test_output", ""), context)
        return {
            "status": "READY",
            "project": project,
            "bug_id": bug_id,
            "baseline": baseline,
            "context_files": files,
            "context_sha256": sha_text(context),
            "visible_prompt": prompt,
            "visible_prompt_sha256": sha_text(prompt),
            "baseline_verifier_calls": 1,
            "baseline_verifier_ms": baseline.get("duration_ms"),
        }


def verify_acquisition_intervention(bugsinpy: Path, project: str, bug_id: int) -> dict[str, Any]:
    """Replay an acquisition-only developer intervention; never expose it to later task prompts."""
    p = patch_path(bugsinpy, project, bug_id)
    if not p.is_file():
        return {"status": "R10", "reason": "developer intervention patch missing"}
    diff = p.read_text(encoding="utf-8", errors="strict")
    files = changed_files(diff)
    if rejects_tests(files):
        return {"status": "INVALID_INTERVENTION", "reason": "developer patch edits tests", "changed_files": files}
    with tempfile.TemporaryDirectory(prefix=f"v145-trace-{project}-") as td:
        work = base.checkout_buggy(bugsinpy, project, bug_id, Path(td))
        baseline = exact_runtime.native_test(bugsinpy, work)
        if baseline.get("infrastructure_error"):
            return {"status": "R10", "reason": baseline["infrastructure_error"], "baseline": baseline}
        if baseline.get("passed"):
            return {"status": "REPRODUCTION_NEGATIVE", "baseline": baseline}
        try:
            base.apply_diff(work, diff)
        except Exception as exc:
            return {"status": "R10", "reason": f"developer intervention apply failed: {exc}"}
        verdict = exact_runtime.native_test(bugsinpy, work)
        if verdict.get("infrastructure_error"):
            return {"status": "R10", "reason": verdict["infrastructure_error"], "verdict": verdict}
        return {
            "status": "VERIFIED" if verdict.get("passed") else "INTERVENTION_FAILED",
            "project": project,
            "bug_id": bug_id,
            "failure_class": base.failure_class(baseline.get("test_output", "")),
            "baseline_failure_tail": baseline.get("test_output", "")[-6000:],
            "diff": diff,
            "diff_sha256": sha_text(diff),
            "changed_files": files,
            "baseline": baseline,
            "verdict": verdict,
            "verifier_calls": 2,
            "verifier_ms": (baseline.get("duration_ms") or 0) + (verdict.get("duration_ms") or 0),
        }


def synthesize_capability(provider: Qwen35ChatRiverProvider, *, generation: str,
                          episode: dict[str, Any], ancestors: list[dict[str, Any]]) -> dict[str, Any]:
    ancestor_payload = [{k: a[k] for k in ("capability_id", "instruction", "preconditions", "postconditions", "applicability_test")} for a in ancestors]
    evidence = {
        "failure_class": episode.get("failure_class"),
        "failing_test_tail": episode.get("baseline_failure_tail", "")[-5000:],
        "changed_files": episode.get("changed_files", []),
        "verified_intervention": episode.get("diff", ""),
        "ancestors": ancestor_payload,
    }
    prompt = (
        f"Construct generation {generation} of a portable repair capability from ONLY the verified natural episode evidence below. "
        "Return ONLY JSON with exactly: instruction, preconditions, postconditions, applicability_test. "
        "Do not name any repository, project, bug id, task id, protected case, or unseen source. "
        "Generalize the mechanism rather than copying the patch. If ancestors are supplied, make this an incremental policy: "
        "do not restate ancestor instructions and do not assume an unseen future task.\n\nEVIDENCE:\n" + json.dumps(evidence, indent=2, sort_keys=True)
    )
    attempts = []
    for j in range(2):
        try:
            r = provider.sample(prompt, seed=202608160 + (1 if generation == "O1" else 2) + j * 100, max_tokens=MAX_TOKENS)
        except Exception as exc:
            return {"status": "R10", "reason": f"provider synthesis error: {exc.__class__.__name__}: {exc}", "attempts": attempts}
        text = r.text
        rr = r.to_dict()
        attempts.append({"response": rr, "text_sha256": sha_text(text), **response_cost(rr, text)})
        try:
            v = _json_object(text)
            required = {"instruction", "preconditions", "postconditions", "applicability_test"}
            if set(v) != required:
                raise ValueError(f"keys {sorted(v)} != {sorted(required)}")
            low = json.dumps(v, sort_keys=True).lower()
            forbidden = ["httpie", "youtube-dl", "youtube_dl", "pandas", "/5", "/32", "/66"]
            if any(x in low for x in forbidden):
                raise ValueError("identity leakage in synthesized capability")
            cap = {
                "capability_id": f"V145.{generation}",
                "generation": generation,
                **v,
                "ancestor_ids": [a["capability_id"] for a in ancestors],
                "source_intervention_sha256": episode.get("diff_sha256"),
            }
            cap["artifact_sha256"] = hashlib.sha256(json.dumps(cap, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            return {"status": "FROZEN", "capability": cap, "prompt_sha256": sha_text(prompt), "attempts": attempts}
        except Exception as exc:
            prompt += f"\n\nPrevious output was invalid ({exc}). Return only the required JSON object."
    return {"status": "CONSTRUCTION_FAILURE", "reason": "two malformed capability outputs", "attempts": attempts}


def run_seed_arm(provider: Qwen35ChatRiverProvider, bugsinpy: Path, task: dict[str, Any],
                 arm: str, seed: int, memory: str) -> dict[str, Any]:
    started = time.perf_counter()
    prompt0 = task["visible_prompt"]
    if memory:
        prompt0 += "\n\n" + memory
    feedback = ""
    attempts = []
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
                "arm": arm, "seed": seed, "status": "R10", "reason": f"provider error: {exc.__class__.__name__}: {exc}",
                "attempts": attempts, "model_calls": call_idx - 1, "verifier_calls": verifier_calls,
                "verifier_ms": verifier_ms, "wall_ms": round((time.perf_counter()-started)*1000,3),
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
            diff = base.extract_diff(text)
            row["diff_sha256"] = sha_text(diff)
        except Exception as exc:
            row["patch_error"] = f"extract: {exc.__class__.__name__}: {exc}"
            attempts.append(row)
            feedback = "\n\nVERIFIER/TRANSPORT FEEDBACK FROM PRIOR ATTEMPT:\nYour previous answer was not an applicable unified diff. Return only a valid unified git diff."
            continue

        with tempfile.TemporaryDirectory(prefix=f"v145-{task['project']}-{arm}-") as td:
            try:
                work = base.checkout_buggy(bugsinpy, task["project"], task["bug_id"], Path(td))
                base.apply_diff(work, diff)
            except Exception as exc:
                row["patch_error"] = f"apply: {exc.__class__.__name__}: {exc}"
                attempts.append(row)
                feedback = "\n\nVERIFIER/TRANSPORT FEEDBACK FROM PRIOR ATTEMPT:\nThe previous diff did not apply cleanly to the unchanged buggy checkout. Produce a smaller valid diff against the shown source."
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
                    "verifier_ms": verifier_ms, "wall_ms": round((time.perf_counter()-started)*1000,3),
                }
            if verdict.get("passed"):
                return {
                    "arm": arm, "seed": seed, "status": "VERIFIED_SOLVED", "solved": True,
                    "calls_to_solve": call_idx, "successful_diff": diff, "successful_diff_sha256": sha_text(diff),
                    "changed_files": changed_files(diff), "attempts": attempts, "model_calls": call_idx,
                    "generated_tokens": generated_tokens if token_metric_available else None,
                    "output_chars_proxy": output_chars, "verifier_calls": verifier_calls, "verifier_ms": verifier_ms,
                    "retained_state_chars": len(memory), "wall_ms": round((time.perf_counter()-started)*1000,3),
                }
            fail_tail = verdict.get("test_output", "")[-7000:]
            feedback = "\n\nVERIFIER FEEDBACK FROM PRIOR ATTEMPT:\nThe candidate did not pass the native verifier. Diagnose this residual and return a revised unified diff.\n" + fail_tail

    return {
        "arm": arm, "seed": seed, "status": "UNSOLVED", "solved": False, "attempts": attempts,
        "model_calls": MAX_CALLS, "generated_tokens": generated_tokens if token_metric_available else None,
        "output_chars_proxy": output_chars, "verifier_calls": verifier_calls, "verifier_ms": verifier_ms,
        "retained_state_chars": len(memory), "wall_ms": round((time.perf_counter()-started)*1000,3),
    }


def comparable(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in rows if r.get("status") != "R10"]


def arm_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    good = comparable(rows)
    solved = [r for r in good if r.get("solved")]
    calls = [r["calls_to_solve"] for r in solved if r.get("calls_to_solve") is not None]
    toks = [r["generated_tokens"] for r in solved if r.get("generated_tokens") is not None]
    chars = [r["output_chars_proxy"] for r in solved if r.get("output_chars_proxy") is not None]
    return {
        "n_total": len(rows), "n_comparable": len(good), "n_r10": len(rows)-len(good),
        "solved_n": len(solved),
        "median_calls_to_solve": statistics.median(calls) if calls else None,
        "median_generated_tokens": statistics.median(toks) if toks else None,
        "median_output_chars_proxy": statistics.median(chars) if chars else None,
        "verifier_calls": sum(int(r.get("verifier_calls") or 0) for r in rows),
        "verifier_ms": round(sum(float(r.get("verifier_ms") or 0) for r in rows),3),
        "wall_ms": round(sum(float(r.get("wall_ms") or 0) for r in rows),3),
    }


def strictly_cheaper(a: dict[str, Any], bs: list[dict[str, Any]]) -> bool:
    # Only compare controls tied on solve count. Calls first, then provider tokens if exposed for all, else chars proxy.
    tied = [b for b in bs if b["solved_n"] == a["solved_n"]]
    if not tied:
        return False
    ac = a.get("median_calls_to_solve")
    if ac is not None and all(b.get("median_calls_to_solve") is not None for b in tied):
        if all(ac < b["median_calls_to_solve"] for b in tied):
            return True
        if any(ac != b["median_calls_to_solve"] for b in tied):
            return False
    at = a.get("median_generated_tokens")
    if at is not None and all(b.get("median_generated_tokens") is not None for b in tied):
        return all(at < b["median_generated_tokens"] for b in tied)
    ach = a.get("median_output_chars_proxy")
    return ach is not None and all(b.get("median_output_chars_proxy") is not None and ach < b["median_output_chars_proxy"] for b in tied)


def classify_advantage(target: dict[str, Any], controls: list[dict[str, Any]]) -> str:
    if not controls:
        return "NULL"
    if target["n_comparable"] == 0 or any(c["n_comparable"] == 0 for c in controls):
        return "R10_INSUFFICIENT_COMPARABLE"
    # Require the same full three-seed denominator for a strong label.
    if target["n_comparable"] != len(SEEDS) or any(c["n_comparable"] != len(SEEDS) for c in controls):
        return "R10_INSUFFICIENT_COMPARABLE"
    if all(target["solved_n"] > c["solved_n"] for c in controls):
        return "REACHABILITY"
    if all(target["solved_n"] >= c["solved_n"] for c in controls) and strictly_cheaper(target, controls):
        return "EFFICIENCY"
    return "NULL"


def first_verified(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    for r in sorted(rows, key=lambda x: (x["seed"], x.get("calls_to_solve") or 99)):
        if r.get("status") == "VERIFIED_SOLVED":
            return r
    return None


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("output directory exists; refusing to overwrite frozen evidence")
    args.out.mkdir(parents=True)
    provider = Qwen35ChatRiverProvider(MODEL)
    result: dict[str, Any] = {
        "canonical_id": "V145_NATURAL_THIRD_RUNG_CAUSAL",
        "protocol": "protocols/V145_NATURAL_THIRD_RUNG_CAUSAL_PRECOMMIT.md",
        "model": MODEL, "max_tokens": MAX_TOKENS, "max_calls": MAX_CALLS,
        "seeds": SEEDS, "stream": [f"{p}/{b}" for p,b in STREAM],
    }

    # Freeze visible evidence for all tasks before any repair-arm outcome.
    prepared = {}
    for p,b in STREAM:
        prepared[f"{p}/{b}"] = prepare_visible_task(args.bugsinpy, p, b)
    result["prepared"] = {k: {kk:vv for kk,vv in v.items() if kk != "visible_prompt"} for k,v in prepared.items()}
    if any(v.get("status") != "READY" for v in prepared.values()):
        result["verdict"] = "R10_OR_REPRODUCTION_INCONCLUSIVE"
        args.out.joinpath("V145_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
        print(json.dumps(result, indent=2, sort_keys=True)); return

    # O1 from T1 acquisition-only verified intervention, before T2 outcomes.
    t1 = verify_acquisition_intervention(args.bugsinpy, *STREAM[0])
    result["T1_intervention"] = {k:v for k,v in t1.items() if k != "diff"}
    if t1.get("status") != "VERIFIED":
        result["verdict"] = "R10_OR_T1_INTERVENTION_FAILURE"
        args.out.joinpath("V145_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n"); print(json.dumps(result,indent=2,sort_keys=True)); return
    o1s = synthesize_capability(provider, generation="O1", episode=t1, ancestors=[])
    result["O1_synthesis"] = o1s
    if o1s.get("status") != "FROZEN":
        result["verdict"] = "O1_CONSTRUCTION_INCONCLUSIVE"
        args.out.joinpath("V145_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n"); print(json.dumps(result,indent=2,sort_keys=True)); return
    o1 = o1s["capability"]
    o1mem = capability_memory([o1])
    sham1 = sham_for(len(o1mem))
    assert len(sham1) == len(o1mem)

    # T2 matched arms.
    t2task = prepared[f"{STREAM[1][0]}/{STREAM[1][1]}"]
    t2rows: dict[str, list[dict[str, Any]]] = {"D_COLD":[], "D_PLUS_O1":[], "D_PLUS_SHAM":[]}
    for seed in SEEDS:
        t2rows["D_COLD"].append(run_seed_arm(provider,args.bugsinpy,t2task,"D_COLD",seed,""))
        t2rows["D_PLUS_O1"].append(run_seed_arm(provider,args.bugsinpy,t2task,"D_PLUS_O1",seed,o1mem))
        t2rows["D_PLUS_SHAM"].append(run_seed_arm(provider,args.bugsinpy,t2task,"D_PLUS_SHAM",seed,sham1))
    t2sum = {k:arm_summary(v) for k,v in t2rows.items()}
    t2adv = classify_advantage(t2sum["D_PLUS_O1"],[t2sum["D_COLD"],t2sum["D_PLUS_SHAM"]])
    result["T2"] = {"rows":t2rows,"summary":t2sum,"advantage":t2adv,"sham_chars":len(sham1),"o1_memory_chars":len(o1mem)}

    t2winner = first_verified(t2rows["D_PLUS_O1"])
    if t2winner is None:
        result["verdict"] = "NEGATIVE_O1_CANNOT_ACQUIRE_O2_WITHIN_BUDGET"
        args.out.joinpath("V145_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n"); print(json.dumps(result,indent=2,sort_keys=True)); return

    # O2 is frozen from the first deterministic verified O1-assisted repair, before T3 outcomes.
    t2episode = {
        "failure_class": base.failure_class(t2task["baseline"].get("test_output", "")),
        "baseline_failure_tail": t2task["baseline"].get("test_output", "")[-6000:],
        "changed_files": t2winner.get("changed_files", []),
        "diff": t2winner["successful_diff"],
        "diff_sha256": t2winner["successful_diff_sha256"],
    }
    o2s = synthesize_capability(provider,generation="O2",episode=t2episode,ancestors=[o1])
    result["O2_synthesis"] = o2s
    if o2s.get("status") != "FROZEN":
        result["verdict"] = "O2_CONSTRUCTION_INCONCLUSIVE"
        args.out.joinpath("V145_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n"); print(json.dumps(result,indent=2,sort_keys=True)); return
    o2 = o2s["capability"]

    # T3 full matched causal arms.
    t3task = prepared[f"{STREAM[2][0]}/{STREAM[2][1]}"]
    mem_o1 = capability_memory([o1])
    mem_o12 = capability_memory([o1,o2])
    mem_o2 = capability_memory([o2])
    sham12 = sham_for(len(mem_o12)); assert len(sham12)==len(mem_o12)
    t3rows: dict[str,list[dict[str,Any]]] = {k:[] for k in ["D_COLD","D_PLUS_O1","D_PLUS_O1_O2","D_PLUS_O2_ANCESTOR_ABLATED","D_PLUS_SHAM"]}
    for seed in SEEDS:
        t3rows["D_COLD"].append(run_seed_arm(provider,args.bugsinpy,t3task,"D_COLD",seed,""))
        t3rows["D_PLUS_O1"].append(run_seed_arm(provider,args.bugsinpy,t3task,"D_PLUS_O1",seed,mem_o1))
        t3rows["D_PLUS_O1_O2"].append(run_seed_arm(provider,args.bugsinpy,t3task,"D_PLUS_O1_O2",seed,mem_o12))
        t3rows["D_PLUS_O2_ANCESTOR_ABLATED"].append(run_seed_arm(provider,args.bugsinpy,t3task,"D_PLUS_O2_ANCESTOR_ABLATED",seed,mem_o2))
        t3rows["D_PLUS_SHAM"].append(run_seed_arm(provider,args.bugsinpy,t3task,"D_PLUS_SHAM",seed,sham12))
    t3sum={k:arm_summary(v) for k,v in t3rows.items()}
    t3adv=classify_advantage(t3sum["D_PLUS_O1_O2"],[t3sum["D_COLD"],t3sum["D_PLUS_O1"],t3sum["D_PLUS_O2_ANCESTOR_ABLATED"],t3sum["D_PLUS_SHAM"]])
    result["T3"]={"rows":t3rows,"summary":t3sum,"advantage":t3adv,"o1_o2_memory_chars":len(mem_o12),"sham_chars":len(sham12)}

    ancestor_worse = False
    dev=t3sum["D_PLUS_O1_O2"]; abl=t3sum["D_PLUS_O2_ANCESTOR_ABLATED"]
    if dev["n_comparable"]==len(SEEDS) and abl["n_comparable"]==len(SEEDS):
        ancestor_worse = dev["solved_n"] > abl["solved_n"] or (dev["solved_n"]==abl["solved_n"] and strictly_cheaper(dev,[abl]))
    sham_not_reproduce = t3adv in {"REACHABILITY","EFFICIENCY"}
    strong = t2adv in {"REACHABILITY","EFFICIENCY"} and t3adv in {"REACHABILITY","EFFICIENCY"} and ancestor_worse and sham_not_reproduce
    result["gates"]={
        "G1_T1_verified_O1_frozen":True,
        "G2_T2_O1_causal_advantage":t2adv in {"REACHABILITY","EFFICIENCY"},
        "G3_O2_frozen_before_T3":True,
        "G4_T3_developmental_advantage":t3adv in {"REACHABILITY","EFFICIENCY"},
        "G5_ancestor_ablation_worse":ancestor_worse,
        "G6_sham_not_reproduce":sham_not_reproduce,
        "G7_source_distinct":len({p for p,_ in STREAM})==3,
        "G8_full_comparable_denominators":all(s["n_comparable"]==len(SEEDS) for s in list(t2sum.values())+list(t3sum.values())),
    }
    if strong and result["gates"]["G8_full_comparable_denominators"]:
        if t2adv=="REACHABILITY" and t3adv=="REACHABILITY":
            result["verdict"]="PASS_V145_CAUSAL_THREE_RUNG_DEVELOPMENT_REACHABILITY"
        else:
            result["verdict"]="PASS_V145_CAUSAL_THREE_RUNG_FRONTIER_EFFICIENCY"
    elif not result["gates"]["G8_full_comparable_denominators"]:
        result["verdict"]="R10_INCONCLUSIVE_MATCHED_DENOMINATOR"
    else:
        result["verdict"]="NEGATIVE_OR_NULL_V145_NO_CAUSAL_THREE_RUNG_DEVELOPMENT"
    result["claim_boundary"]="Bounded three-episode BugsInPy/Qwen causal test only; no unrestricted recursive or open-ended development claim."
    args.out.joinpath("V145_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"verdict":result["verdict"],"T2_advantage":t2adv,"T3_advantage":t3adv,"gates":result["gates"],"T2_summary":t2sum,"T3_summary":t3sum},indent=2,sort_keys=True))


if __name__ == "__main__":
    main()
