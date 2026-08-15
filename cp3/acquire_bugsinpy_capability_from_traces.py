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


acquisition.acquire_case = acquire_case

if __name__ == "__main__":
    acquisition.main()
