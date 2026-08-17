#!/usr/bin/env python3
import hashlib
import json
import os
import re
from pathlib import Path

import river_client as river

BASE = "Qwen/Qwen3.5-9B"
SEED = 20260818
N = 8
MAX_TOKENS = 1800
TEMPERATURE = 0.8
ROOT = Path("checker")
EXPOSED = Path("blind-di/exposed.ndjson")
BASELINE = Path("blind-di/exposed_baseline.json")
OUT = Path("blind-di/candidates.json")


def bundle_source():
    files = sorted((ROOT / "kernel").rglob("*.vow"))
    rows = []
    total = 0
    for p in files:
        txt = p.read_text(errors="replace")
        rel = str(p.relative_to(ROOT))
        chunk = f"\n===== FILE {rel} =====\n{txt}\n"
        # The selection rule is purely lexical/size based, frozen in code, not semantic.
        if total + len(chunk) > 100_000:
            break
        rows.append(chunk)
        total += len(chunk)
    if not rows:
        raise SystemExit("no allowed source files")
    return "".join(rows), [str(p.relative_to(ROOT)) for p in files[:len(rows)]]


def extract_json(text):
    text = text.strip()
    blocks = [text]
    blocks += re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S | re.I)
    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        blocks.append(text[first:last+1])
    for b in blocks:
        try:
            obj = json.loads(b)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
    return None


def admissible(obj, allowed):
    if not isinstance(obj, dict):
        return False, "not_object"
    if set(["path", "old", "new"]) - set(obj):
        return False, "missing_fields"
    path = str(obj.get("path", ""))
    old = str(obj.get("old", ""))
    new = str(obj.get("new", ""))
    if path not in allowed:
        return False, "path_outside_allowed_surface"
    if not old or old == new:
        return False, "empty_or_noop_edit"
    src = (ROOT / path).read_text(errors="replace")
    if src.count(old) != 1:
        return False, f"old_occurs_{src.count(old)}_times"
    return True, "ok"


def main():
    api_key = os.environ.get("RIVER_API_KEY")
    if not api_key:
        raise SystemExit("RIVER_API_KEY is required")
    source, allowed = bundle_source()
    case = EXPOSED.read_text(errors="replace")
    baseline = json.loads(BASELINE.read_text())
    prompt = f"""You are the autonomous repair proposer in a preregistered blind software experiment.

You are given ONE naturally selected failing case and the frozen source of an independent Lean proof checker. Protected later cases exist but are unavailable to you. Diagnose from the supplied evidence only.

Your job is to propose ONE minimal source edit that is likely to make the checker handle the exposed case correctly without damaging other behavior.

Rules:
- You may edit exactly one of the listed kernel/*.vow files.
- You may make exactly one exact string replacement.
- Do not edit tests, the harness, build scripts, or the exposed input.
- No target-specific repair rule has been supplied to you.
- Return STRICT JSON only, with keys: hypothesis, path, old, new.
- `old` must be an exact substring occurring once in the supplied file.
- Prefer a principled semantic/representation correction over special-casing this testcase.

ALLOWED FILES:
{json.dumps(allowed)}

BASELINE RESULT:
{json.dumps(baseline, indent=2)}

EXPOSED CASE:
{case}

FROZEN SOURCE:
{source}
"""
    prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()
    client = river.Client(api_key=api_key, timeout=240.0)
    if not client.health_check():
        raise SystemExit("River health check failed")
    prompts = [prompt + f"\nCandidate generation index: {i+1}/{N}. Produce an independent best hypothesis.\n" for i in range(N)]
    with client.session(project="di-blind-v1-autonomous-constructor") as s:
        model = s.create_model(base_model=BASE, lora=river.LoraConfig(rank=8, seed=SEED))
        generations = model.sample(prompts=prompts, max_tokens=MAX_TOKENS, temperature=TEMPERATURE)
    rows = []
    for i, gs in enumerate(generations):
        text = gs[0].text if gs else ""
        obj = extract_json(text)
        ok, reason = admissible(obj, set(allowed))
        rows.append({
            "index": i,
            "raw_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "raw": text,
            "parsed": obj,
            "admissible": ok,
            "admissibility_reason": reason,
        })
    result = {
        "protocol": "DI_BLIND_V1_AUTONOMOUS_CONSTRUCTION",
        "base_model": BASE,
        "base_weight_updates": 0,
        "seed": SEED,
        "candidate_count": N,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "prompt_sha256": prompt_sha,
        "allowed_files": allowed,
        "admissible_count": sum(r["admissible"] for r in rows),
        "candidates": rows,
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k:v for k,v in result.items() if k != "candidates"}, indent=2))
    for r in rows:
        print("CANDIDATE", r["index"], "ADMISSIBLE", r["admissible"], r["admissibility_reason"], r["raw_sha256"])


if __name__ == "__main__":
    main()
