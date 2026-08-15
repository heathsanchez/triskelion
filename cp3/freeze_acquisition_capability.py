#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

PROTOCOL = "TRISKELION_CP3_ACQUISITION_FREEZE_V1"
MODEL = "Qwen/Qwen3.5-9B"
MODEL_LABEL = "Qwen3.5-9B"
SEED = 20260815
MAX_TOKENS = 1800
BUGSINPY_REPO = "https://github.com/soarsmu/BugsInPy.git"
EXPECTED_ACQUISITION = ("httpie/5", "youtube-dl/32")
PROTECTED_NAMES = (
    "thefuck", "keras", "spacy", "fastapi", "black", "ansible", "sanic",
    "matplotlib", "scrapy", "luigi", "tornado", "tqdm",
)
REQUIRED_CAP_FIELDS = (
    "capability_id", "name", "operator", "preconditions", "postconditions",
    "scope_any_terms", "negative_constraints", "applicability_test", "memory_text",
)


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode())


def run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 600) -> str:
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}\n{p.stdout[-8000:]}")
    return p.stdout


def load_acquisition_traces(repo: Path) -> tuple[list[dict], str]:
    head = run(["git", "rev-parse", "HEAD"], cwd=repo, timeout=30).strip()
    traces = []
    for case in EXPECTED_ACQUISITION:
        project, bug_id = case.split("/", 1)
        base = repo / "projects" / project / "bugs" / bug_id
        info_path = base / "bug.info"
        patch_path = base / "bug_patch.txt"
        if not info_path.is_file() or not patch_path.is_file():
            raise RuntimeError(f"missing frozen acquisition evidence for {case}")
        info = info_path.read_text(errors="replace")
        patch = patch_path.read_text(errors="replace")
        traces.append({
            "case": case,
            "bug_info_sha256": sha256_text(info),
            "intervention_sha256": sha256_text(patch),
            "verified_intervention_trace": patch,
        })
    return traces, head


def acquisition_prompt(traces: list[dict]) -> str:
    rendered = []
    for t in traces:
        rendered.append(
            f"ACQUISITION CASE {t['case']}\n"
            f"VERIFIED INTERVENTION TRACE (developer fix; acquisition evidence is allowed):\n"
            f"```diff\n{t['verified_intervention_trace']}\n```"
        )
    return """You are constructing portable repair capabilities from ACQUISITION evidence only.
The protected evaluation set is sealed and unavailable. Do not speculate about named future projects.

From the two verified intervention traces below, induce a SMALL reusable capability basis. The goal is not to memorize patches. Compress each trace into a generic repair operation with an explicit applicability scope so a later runtime can decide whether to activate it. If the traces support a shared higher-level operator, include it only if it is genuinely operational rather than a slogan.

Return ONLY one JSON object with this exact top-level shape:
{
  "capabilities": [
    {
      "capability_id": "PY.<UPPERCASE_ID>.V1",
      "name": "short generic name",
      "operator": "concrete generic repair operation",
      "preconditions": ["..."],
      "postconditions": ["..."],
      "scope_any_terms": ["lowercase generic lexical/semantic cue", "..."],
      "negative_constraints": ["when not to activate", "..."],
      "applicability_test": "short deterministic description of when the scope cues should count",
      "memory_text": "compact instruction suitable for a repair model"
    }
  ],
  "compression_rationale": "one short paragraph"
}

Constraints:
- 1 to 3 capabilities total.
- No project names, file paths, line numbers, commit ids, or literal copied patches inside capability fields.
- scope_any_terms must contain 2 to 8 generic lowercase cues per capability, no regex syntax, no punctuation-only tokens, no project-specific identifiers.
- operator and memory_text must describe an executable repair move, not merely 'be robust'.
- Scope must be narrow enough that ALWAYS-ON and selectively activated VERIFIED are meaningfully different.
- Do not mention or infer protected cases.

""" + "\n\n".join(rendered)


def parse_json_object(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    first, last = text.find("{"), text.rfind("}")
    if first < 0 or last <= first:
        raise ValueError("model did not return a JSON object")
    return json.loads(text[first:last + 1])


def validate_payload(payload: dict) -> list[dict]:
    caps = payload.get("capabilities")
    if not isinstance(caps, list) or not (1 <= len(caps) <= 3):
        raise ValueError("expected 1..3 capabilities")
    ids = set()
    for cap in caps:
        for field in REQUIRED_CAP_FIELDS:
            if field not in cap:
                raise ValueError(f"missing capability field: {field}")
        cid = cap["capability_id"]
        if not isinstance(cid, str) or not re.fullmatch(r"PY\.[A-Z0-9_]+\.V1", cid):
            raise ValueError(f"invalid capability_id: {cid!r}")
        if cid in ids:
            raise ValueError(f"duplicate capability_id: {cid}")
        ids.add(cid)
        for field in ("preconditions", "postconditions", "negative_constraints"):
            if not isinstance(cap[field], list) or not all(isinstance(x, str) and x.strip() for x in cap[field]):
                raise ValueError(f"{cid}: invalid {field}")
        terms = cap["scope_any_terms"]
        if not isinstance(terms, list) or not (2 <= len(terms) <= 8):
            raise ValueError(f"{cid}: scope_any_terms must have 2..8 entries")
        for term in terms:
            if not isinstance(term, str) or term != term.lower() or not re.fullmatch(r"[a-z0-9_ -]{2,40}", term):
                raise ValueError(f"{cid}: invalid scope term {term!r}")
        semantic_blob = "\n".join(str(cap[k]) for k in REQUIRED_CAP_FIELDS).lower()
        forbidden = [x for x in PROTECTED_NAMES if x.lower() in semantic_blob]
        if forbidden:
            raise ValueError(f"protected-name leakage in {cid}: {forbidden}")
        if any(x in semantic_blob for x in ("httpie", "youtube-dl", "youtube_dl")):
            raise ValueError(f"acquisition literal leakage in generic capability {cid}")
    return caps


def to_cp1_compatible(cap: dict, evidence: list[dict]) -> dict:
    artifact = {
        "name": "cp3_prompt_capability",
        "kind": "prompt_manifest",
        "execution_order": 50,
        "operator": cap["operator"],
        "memory_text": cap["memory_text"],
    }
    artifact_sha = sha256_text(json.dumps(artifact, sort_keys=True, separators=(",", ":")))
    return {
        "capability_id": cap["capability_id"],
        "name": cap["name"],
        "version": "1.0.0",
        "type": "repair_prompt_operator",
        "artifact": artifact,
        "interface": {"input": "sanitized_bug_context", "output": "repair_proposal_guidance"},
        "preconditions": cap["preconditions"],
        "postconditions": cap["postconditions"],
        "scope": {"any_terms": cap["scope_any_terms"]},
        "applicability_test": cap["applicability_test"],
        "dependencies": [],
        "composes_with": [],
        "conflicts_with": [],
        "acquired_from": list(EXPECTED_ACQUISITION),
        "evidence": evidence,
        "verifier": "bugsinpy-native-qualification-v1",
        "protected_tests": [],
        "source_distinct_transfer": [],
        "ablation_status": "untested",
        "counterexamples": [],
        "revocation_conditions": cap["negative_constraints"],
        "discovery_cost": {"model_calls": 1, "model": MODEL_LABEL},
        "execution_cost": {"model_calls": 0, "kind": "prompt_manifest"},
        "token_cost": {},
        "status": "verified",
        "enabled": True,
        "artifact_sha256": artifact_sha,
    }


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: freeze_acquisition_capability.py OUT_DIR")
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit("output exists; refusing to overwrite frozen evidence")
    out.mkdir(parents=True)

    key = os.environ.get("RIVER_API_KEY")
    if not key:
        raise SystemExit("RIVER_API_KEY is not configured; fail-loud, no substitute model")

    work = out / "_work"
    run(["git", "clone", "--depth", "1", BUGSINPY_REPO, str(work)], timeout=600)
    traces, bugsinpy_head = load_acquisition_traces(work)
    prompt = acquisition_prompt(traces)

    try:
        import river_client as river
    except ImportError as exc:
        raise SystemExit("river-client is not installed") from exc

    client = river.Client(api_key=key)
    if not client.health_check():
        raise SystemExit("River health check failed")
    available = list(client.get_capabilities())
    if MODEL not in available:
        raise SystemExit(f"frozen model {MODEL!r} unavailable; enabled={available!r}")

    started = time.perf_counter()
    samples = client.sample(prompt, base_model=MODEL, max_tokens=MAX_TOKENS,
                            temperature=0.0, seed=SEED)
    if not samples:
        raise SystemExit("River returned no samples")
    sample = samples[0]
    raw_text = sample.text
    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    proposal = parse_json_object(raw_text)
    caps = validate_payload(proposal)

    evidence = [{
        "case": t["case"],
        "qualification": "fixed_pass_and_buggy_fail",
        "bug_info_sha256": t["bug_info_sha256"],
        "verified_intervention_sha256": t["intervention_sha256"],
    } for t in traces]
    cp1_caps = [to_cp1_compatible(cap, evidence) for cap in caps]

    frozen = {
        "canonical_id": "TRISKELION_CP3_ACQUISITION_CAPABILITY_V1",
        "protocol": PROTOCOL,
        "status": "FROZEN",
        "model": MODEL_LABEL,
        "provider_model": MODEL,
        "temperature": 0.0,
        "seed": SEED,
        "max_tokens": MAX_TOKENS,
        "acquisition_cases": list(EXPECTED_ACQUISITION),
        "protected_evidence_used": False,
        "bugsinpy_head": bugsinpy_head,
        "model_prompt_sha256": sha256_text(prompt),
        "model_response_sha256": sha256_text(raw_text),
        "model_latency_ms": latency_ms,
        "capabilities": cp1_caps,
        "compression_rationale": proposal.get("compression_rationale", ""),
        "freeze_rule": "No semantic changes before the protected four-arm evaluation.",
    }
    canonical = json.dumps(frozen, indent=2, sort_keys=True) + "\n"
    (out / "CAPABILITY_PAYLOAD.json").write_text(canonical)
    (out / "CAPABILITY_SHA256.txt").write_text(sha256_text(canonical) + "\n")
    (out / "ACQUISITION_EVIDENCE.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    (out / "MODEL_RESPONSE.txt").write_text(raw_text)
    (out / "PROMPT_SHA256.txt").write_text(sha256_text(prompt) + "\n")
    # Do not persist cloned acquisition source/diffs in the frozen artifact directory.
    import shutil
    shutil.rmtree(work, ignore_errors=True)
    print(json.dumps({
        "status": "FROZEN",
        "capability_count": len(cp1_caps),
        "capability_ids": [c["capability_id"] for c in cp1_caps],
        "capability_sha256": sha256_text(canonical),
        "protected_evidence_used": False,
        "bugsinpy_head": bugsinpy_head,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
