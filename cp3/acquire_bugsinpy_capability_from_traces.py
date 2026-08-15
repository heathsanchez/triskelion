from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import acquire_bugsinpy_capability as acquisition
import bugsinpy_four_arm_v4 as env_adapter
import structured_edit_protocol_v2 as json_transport
from river_qwen35_provider import Qwen35ChatRiverProvider

acquisition.native_test = env_adapter.native_test
acquisition.RiverProvider = Qwen35ChatRiverProvider
acquisition.extract_json = json_transport._json_object


def _patch_path(bugsinpy: Path, project: str, bug_id: int) -> Path:
    return bugsinpy / "projects" / project / "bugs" / str(bug_id) / "bug_patch.txt"


def _changed_files_from_diff(diff: str) -> list[str]:
    out: list[str] = []
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
            if path != "/dev/null" and path not in out:
                out.append(path)
    return out


def _reject_test_patch(paths: list[str]) -> None:
    for raw in paths:
        parts = [p.lower() for p in Path(raw).parts]
        name = Path(raw).name.lower()
        if "test" in parts or "tests" in parts or name.startswith("test_") or name.endswith("_test.py"):
            raise ValueError(f"acquisition intervention edits tests: {raw}")


def acquire_case(provider, bugsinpy: Path, project: str, bug_id: int, case_index: int) -> dict[str, Any]:
    del provider, case_index
    case = f"{project}/{bug_id}"
    with tempfile.TemporaryDirectory(prefix="cp3-trace-acquire-") as raw:
        root = Path(raw)
        work = acquisition.checkout_buggy(bugsinpy, project, bug_id, root)
        baseline = acquisition.native_test(bugsinpy, work)
        if baseline.get("infrastructure_error"):
            return {"case": case, "status": "INFRASTRUCTURE_NEGATIVE", "baseline": baseline, "attempts": []}
        if baseline.get("passed"):
            return {"case": case, "status": "REPRODUCTION_NEGATIVE", "baseline": baseline, "attempts": []}

        path = _patch_path(bugsinpy, project, bug_id)
        if not path.is_file():
            return {"case": case, "status": "INFRASTRUCTURE_NEGATIVE", "baseline": baseline, "attempts": [], "error": "acquisition intervention patch missing"}
        diff = path.read_text(encoding="utf-8", errors="strict")
        changed = _changed_files_from_diff(diff)
        _reject_test_patch(changed)
        patch_sha = hashlib.sha256(diff.encode()).hexdigest()

        try:
            acquisition.apply_diff(work, diff)
        except Exception as exc:
            return {
                "case": case,
                "status": "INFRASTRUCTURE_NEGATIVE",
                "baseline": baseline,
                "attempts": [],
                "error": f"acquisition intervention apply failed: {exc}",
                "intervention_sha256": patch_sha,
                "changed_files": changed,
            }

        verdict = acquisition.native_test(bugsinpy, work)
        trace = {
            "source": "BugsInPy acquisition-only successful intervention trace",
            "intervention_sha256": patch_sha,
            "changed_files": changed,
            "verdict": verdict,
        }
        if verdict.get("infrastructure_error"):
            return {"case": case, "status": "INFRASTRUCTURE_NEGATIVE", "baseline": baseline, "attempts": [trace]}
        if not verdict.get("passed"):
            return {"case": case, "status": "INTERVENTION_NOT_VERIFIED", "baseline": baseline, "attempts": [trace]}

        return {
            "case": case,
            "status": "VERIFIED_REPAIR",
            "failure_class": acquisition.failure_class(baseline.get("test_output", "")),
            "context_files": changed,
            "baseline": baseline,
            "successful_diff": diff,
            "changed_files": changed,
            "attempts": [trace],
            "acquisition_mode": "verified_successful_intervention_trace",
        }


def _scope_properties(scope: dict[str, Any]) -> tuple[set[str], bool]:
    fields: set[str] = set()
    has_source_contains = False
    def walk(node: Any) -> None:
        nonlocal has_source_contains
        if not isinstance(node, dict):
            return
        for key in ("all", "any"):
            if key in node and isinstance(node[key], list):
                for child in node[key]:
                    walk(child)
                return
        if "not" in node:
            walk(node["not"]); return
        field = node.get("field")
        if isinstance(field, str):
            fields.add(field)
            if field == "source" and "contains" in node:
                has_source_contains = True
    walk(scope)
    return fields, has_source_contains


def synthesize(provider, episodes: list[dict[str, Any]]) -> dict[str, Any]:
    payload = []
    for e in episodes:
        payload.append({
            "case": e["case"],
            "failure_class": e["failure_class"],
            "changed_files": e["changed_files"],
            "failing_test_tail": e["baseline"].get("test_output", "")[-6000:],
            "successful_intervention": e["successful_diff"],
        })
    prompt = (
        "Compress ONLY the two independently replayed, native-verified acquisition interventions below into one portable repair capability. "
        "Return ONLY JSON with exactly these keys: name, instruction, preconditions, postconditions, applicability_test, scope. "
        "The instruction must be a concise reusable repair policy, not either case-specific patch. "
        "The scope MUST be a non-empty source-distinct applicability rule derived only from observable acquisition evidence. "
        "Scope leaves may use ONLY fields `source` and `metadata.failure_class`; `metadata.project` and `task_id` are forbidden. "
        "Scope must contain at least one leaf of the form {\"field\":\"source\",\"contains\":\"...\"}. "
        "Combine leaves only with all/any/not. Do not name HTTPie, youtube-dl, acquisition case IDs, protected tasks, or any unseen project. "
        "Choose lexical/semantic source indicators that reflect the shared repair mechanism, and keep the scope selective rather than universal. "
        "Do not invent protected evidence.\n\nACQUISITION EVIDENCE:\n" + json.dumps(payload, indent=2, sort_keys=True)
    )
    response = provider.sample(prompt, seed=acquisition.SEED + 9000, max_tokens=acquisition.MAX_TOKENS)
    value = json_transport._json_object(response.text)
    required = {"name", "instruction", "preconditions", "postconditions", "applicability_test", "scope"}
    if set(value) != required:
        raise ValueError(f"synthesis keys must be exactly {sorted(required)}; got {sorted(value)}")
    acquisition.validate_scope(value["scope"])
    fields, has_source_contains = _scope_properties(value["scope"])
    if not fields or not fields.issubset({"source", "metadata.failure_class"}):
        raise ValueError(f"scope uses forbidden fields: {sorted(fields)}")
    if not has_source_contains:
        raise ValueError("scope must contain at least one source-contains predicate")
    lowered = json.dumps(value["scope"], sort_keys=True).lower()
    for forbidden in ("httpie", "youtube-dl", "youtube_dl", "httpie/5", "youtube-dl/32"):
        if forbidden in lowered:
            raise ValueError(f"scope contains acquisition identity {forbidden!r}")
    return {
        "manifest": value,
        "response": response.to_dict(),
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
    }


acquisition.acquire_case = acquire_case
acquisition.synthesize = synthesize

if __name__ == "__main__":
    acquisition.main()
