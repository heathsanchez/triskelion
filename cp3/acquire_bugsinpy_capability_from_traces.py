from __future__ import annotations

import hashlib
import json
import re
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


def _added_lines(diff: str) -> list[str]:
    return [
        line[1:] for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]


def _api_prefixes(diff: str) -> set[str]:
    text = "\n".join(_added_lines(diff))
    return set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\.[A-Za-z_][A-Za-z0-9_]*\b", text))


def induce_scope(episodes: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Induce applicability from acquisition evidence only, with no model choice.

    Rule frozen here before protected exposure:
    1. Extract API/module prefixes used in ADDED lines of each verified intervention.
    2. Intersect across all acquisition episodes.
    3. Remove generic pseudo-prefixes that cannot identify a mechanism.
    4. Select the lexicographically first remaining shared prefix.
    5. Scope is exactly `source contains <prefix>.`.

    This intentionally does not inspect protected source or outcomes and does not
    use project/task identities. For the current acquisition traces the derived
    shared prefix is expected to be `re`, reflecting regex-based boundary parsing.
    """
    if not episodes:
        raise ValueError("cannot induce scope without acquisition episodes")
    per_episode = [_api_prefixes(e["successful_diff"]) for e in episodes]
    shared = set.intersection(*per_episode) if per_episode else set()
    shared -= {"self", "str", "dict", "list", "set", "tuple", "os", "sys"}
    if not shared:
        raise ValueError(f"no shared added-line API prefix across acquisition traces: {per_episode!r}")
    chosen = sorted(shared)[0]
    scope = {"field": "source", "contains": chosen + "."}
    provenance = {
        "method": "intersection_of_added_line_api_prefixes_v1",
        "per_episode_api_prefixes": [sorted(x) for x in per_episode],
        "shared_api_prefixes": sorted(shared),
        "chosen_prefix": chosen,
        "scope": scope,
        "protected_information_used": False,
    }
    return scope, provenance


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
    scope, scope_provenance = induce_scope(episodes)
    prompt = (
        "Compress ONLY the two independently replayed, native-verified acquisition interventions below into one portable repair capability. "
        "Return ONLY JSON with exactly these five keys: name, instruction, preconditions, postconditions, applicability_test. "
        "The instruction must be a concise reusable repair policy, not either case-specific patch. "
        "Do not name acquisition projects/case IDs, protected tasks, or any unseen project. "
        "Do not invent protected evidence. Applicability scope is induced separately by a deterministic verifier-side rule and must NOT be proposed here.\n\n"
        "ACQUISITION EVIDENCE:\n" + json.dumps(payload, indent=2, sort_keys=True)
    )
    response = provider.sample(prompt, seed=acquisition.SEED + 9000, max_tokens=acquisition.MAX_TOKENS)
    value = json_transport._json_object(response.text)
    required = {"name", "instruction", "preconditions", "postconditions", "applicability_test"}
    if set(value) != required:
        raise ValueError(f"synthesis keys must be exactly {sorted(required)}; got {sorted(value)}")
    serialized = json.dumps(value, sort_keys=True).lower()
    for forbidden in ("httpie", "youtube-dl", "youtube_dl", "httpie/5", "youtube-dl/32"):
        if forbidden in serialized:
            raise ValueError(f"capability synthesis contains acquisition identity {forbidden!r}")
    value["scope"] = scope
    acquisition.validate_scope(value["scope"])
    return {
        "manifest": value,
        "response": response.to_dict(),
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "scope_provenance": scope_provenance,
    }


acquisition.acquire_case = acquire_case
acquisition.synthesize = synthesize

if __name__ == "__main__":
    acquisition.main()
