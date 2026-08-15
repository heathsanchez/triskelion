from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any

from bugsinpy_four_arm import (
    MODEL, SEED, MAX_TOKENS, RiverProvider, Task,
    apply_diff, checkout_buggy, collect_context, failure_class,
    native_test, visible_request,
)

HERE = Path(__file__).resolve().parent
ALLOWED_SCOPE_FIELDS = {"metadata.failure_class", "metadata.project", "source", "task_id"}


def parse_case(value: str) -> tuple[str, int]:
    project, raw = value.rsplit("/", 1)
    return project, int(raw)


def extract_diff(text: str) -> str:
    blocks = re.findall(r"```(?:diff)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    candidate = blocks[0] if len(blocks) == 1 else text
    candidate = candidate.strip() + "\n"
    if "diff --git " not in candidate and not candidate.startswith("--- "):
        raise ValueError("model output is not a unified diff")
    return candidate


def extract_json(text: str) -> dict[str, Any]:
    blocks = re.findall(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    candidate = blocks[0] if len(blocks) == 1 else text
    return json.loads(candidate.strip())


def validate_scope(scope: dict[str, Any]) -> None:
    if not isinstance(scope, dict) or not scope:
        raise ValueError("scope must be a non-empty object")
    if "all" in scope:
        for item in scope["all"]: validate_scope(item)
        return
    if "any" in scope:
        for item in scope["any"]: validate_scope(item)
        return
    if "not" in scope:
        validate_scope(scope["not"]); return
    field = scope.get("field")
    if field not in ALLOWED_SCOPE_FIELDS:
        raise ValueError(f"scope field not allowed: {field!r}")
    predicates = [k for k in ("equals", "contains", "in") if k in scope]
    if len(predicates) != 1:
        raise ValueError("scope leaf must contain exactly one predicate")


def changed_files(diff: str) -> list[str]:
    out = []
    for path in re.findall(r"^\+\+\+ b/(.+)$", diff, flags=re.MULTILINE):
        if path != "/dev/null" and path not in out:
            out.append(path)
    return out


def acquire_case(provider: RiverProvider, bugsinpy: Path, project: str, bug_id: int, case_index: int) -> dict[str, Any]:
    attempts = []
    feedback = ""
    for attempt in range(2):
        with tempfile.TemporaryDirectory(prefix="cp3-acquire-") as raw:
            root = Path(raw)
            work = checkout_buggy(bugsinpy, project, bug_id, root)
            baseline = native_test(bugsinpy, work)
            if baseline.get("infrastructure_error"):
                return {"case": f"{project}/{bug_id}", "status": "INFRASTRUCTURE_NEGATIVE", "baseline": baseline, "attempts": attempts}
            if baseline.get("passed"):
                return {"case": f"{project}/{bug_id}", "status": "REPRODUCTION_NEGATIVE", "baseline": baseline, "attempts": attempts}
            context, files = collect_context(work, baseline["test_output"])
            prompt = visible_request(project, bug_id, baseline["test_output"], context)
            if feedback:
                prompt += "\n\nPREVIOUS VERIFIED ATTEMPT FAILED. Use this verifier feedback only to revise the repair:\n" + feedback[-8000:]
            response = provider.sample(prompt, seed=SEED + case_index * 10 + attempt, max_tokens=MAX_TOKENS)
            row: dict[str, Any] = {"attempt": attempt + 1, "response": response.to_dict(), "context_files": files}
            try:
                diff = extract_diff(response.text)
                row["diff"] = diff
                row["diff_sha256"] = hashlib.sha256(diff.encode()).hexdigest()
                apply_diff(work, diff)
            except Exception as exc:
                row["patch_error"] = f"{exc.__class__.__name__}: {exc}"
                attempts.append(row)
                feedback = row["patch_error"]
                continue
            verdict = native_test(bugsinpy, work)
            row["verdict"] = verdict
            attempts.append(row)
            if verdict.get("passed"):
                return {
                    "case": f"{project}/{bug_id}", "status": "VERIFIED_REPAIR",
                    "failure_class": failure_class(baseline["test_output"]),
                    "context_files": files, "baseline": baseline,
                    "successful_diff": diff, "changed_files": changed_files(diff),
                    "attempts": attempts,
                }
            feedback = verdict.get("test_output", "")
    return {"case": f"{project}/{bug_id}", "status": "NO_VERIFIED_REPAIR", "attempts": attempts}


def synthesize(provider: RiverProvider, episodes: list[dict[str, Any]]) -> dict[str, Any]:
    payload = []
    for e in episodes:
        payload.append({
            "case": e["case"], "failure_class": e["failure_class"],
            "context_files": e["context_files"], "changed_files": e["changed_files"],
            "successful_diff": e["successful_diff"],
        })
    prompt = (
        "You are compressing ONLY two verified acquisition repairs into one portable repair capability. "
        "Do not use or infer any protected task. Return ONLY JSON with keys: name, instruction, preconditions, "
        "postconditions, applicability_test, scope. The instruction must be a concise reusable repair policy, not a case-specific patch. "
        "scope must use only this DSL: leaves {field: one of metadata.failure_class, metadata.project, source, task_id; "
        "and exactly one of equals, contains, in}; combine with all/any/not. Prefer source-distinct semantic scope over exact project/task IDs "
        "when justified by both acquisition cases. Do not invent evidence not present below.\n\nACQUISITION EVIDENCE:\n" + json.dumps(payload, indent=2, sort_keys=True)
    )
    response = provider.sample(prompt, seed=SEED + 9000, max_tokens=MAX_TOKENS)
    value = extract_json(response.text)
    validate_scope(value["scope"])
    return {"manifest": value, "response": response.to_dict(), "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--known", type=Path, default=HERE / "KNOWN_QUALIFIED.json")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("output exists; refusing to overwrite acquisition freeze")
    args.out.mkdir(parents=True)

    known = json.loads(args.known.read_text())
    acquisition = [x["case"] for x in known["acquisition"] if x.get("status") == "QUALIFIED"]
    if acquisition != ["httpie/5", "youtube-dl/32"]:
        raise SystemExit(f"unexpected frozen acquisition set: {acquisition!r}")

    provider = RiverProvider(MODEL)
    episodes = []
    for i, case in enumerate(acquisition):
        project, bug_id = parse_case(case)
        episode = acquire_case(provider, args.bugsinpy, project, bug_id, i)
        episodes.append(episode)
        (args.out / f"{project}_{bug_id}.json").write_text(json.dumps(episode, indent=2, sort_keys=True) + "\n")

    if not all(x.get("status") == "VERIFIED_REPAIR" for x in episodes):
        summary = {"status": "ACQUISITION_INCOMPLETE", "cases": [{"case": x["case"], "status": x["status"]} for x in episodes]}
        (args.out / "ACQUISITION_STATUS.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        raise SystemExit("both frozen acquisition cases must yield a verified repair before capability freeze")

    synthesis = synthesize(provider, episodes)
    m = synthesis["manifest"]
    artifact = {"name": "prompt_module", "instruction": m["instruction"], "execution_order": 100}
    artifact_sha = hashlib.sha256(json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    capability = {
        "capability_id": "CP3.BUGSINPY.ACQUIRED.V1",
        "name": m["name"], "version": "1", "type": "verified_prompt_module",
        "artifact": artifact, "interface": {"input": "buggy repository context", "output": "repair-policy prompt module"},
        "preconditions": m["preconditions"], "postconditions": m["postconditions"],
        "scope": m["scope"], "applicability_test": m["applicability_test"],
        "dependencies": [], "composes_with": [], "conflicts_with": [],
        "acquired_from": acquisition,
        "evidence": [{"case": x["case"], "status": x["status"], "diff_sha256": hashlib.sha256(x["successful_diff"].encode()).hexdigest()} for x in episodes],
        "verifier": "bugsinpy-native-test-v1", "protected_tests": [], "source_distinct_transfer": [],
        "ablation_status": "pending_protected_eval", "counterexamples": [], "revocation_conditions": [],
        "discovery_cost": {"max_model_calls_per_case": 2, "synthesis_calls": 1}, "execution_cost": {}, "token_cost": {},
        "status": "verified", "enabled": True, "artifact_sha256": artifact_sha,
    }
    raw_lines = ["Unstructured acquisition memory; no executable patch or scoped capability follows."]
    for x in episodes:
        raw_lines.append(f"- {x['case']}: failure class {x['failure_class']}; a repair touching {', '.join(x['changed_files'])} passed the native verifier.")
    raw_memory = "\n".join(raw_lines) + "\n"

    (args.out / "CAPABILITY.json").write_text(json.dumps(capability, indent=2, sort_keys=True) + "\n")
    (args.out / "RAW_MEMORY.txt").write_text(raw_memory)
    (args.out / "SYNTHESIS.json").write_text(json.dumps(synthesis, indent=2, sort_keys=True) + "\n")
    freeze = {
        "status": "CAPABILITY_FROZEN", "acquisition": acquisition,
        "capability_sha256": hashlib.sha256((args.out / "CAPABILITY.json").read_bytes()).hexdigest(),
        "raw_memory_sha256": hashlib.sha256(raw_memory.encode()).hexdigest(),
        "protected_information_used": False,
    }
    (args.out / "ACQUISITION_STATUS.json").write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    print(json.dumps(freeze, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
