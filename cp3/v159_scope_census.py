from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import bugsinpy_four_arm as base
import bugsinpy_exact_runtime as exact_runtime
import structured_edit_protocol_v2 as sed
from v149_context_resolver import resolve_context

HERE = Path(__file__).resolve().parent
VENDOR = HERE / "vendor" / "cp1"
import sys
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))
from triskelion.models import Capability, Task
from triskelion.scope import matches_scope


DOWNSTREAM = [
    ("thefuck", 32),
    ("keras", 32),
    ("spacy", 2),
    ("fastapi", 5),
    ("black", 18),
    ("pandas", 66),
]

base.native_test = exact_runtime.native_test


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def load_capability(path: Path) -> Capability:
    return Capability.from_dict(json.loads(path.read_text()))


def inspect_case(bugsinpy: Path, cap: Capability, project: str, bug_id: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"v159-scope-{project}-") as td:
        try:
            work = base.checkout_buggy(bugsinpy, project, bug_id, Path(td))
            baseline = exact_runtime.native_test(bugsinpy, work)
        except Exception as exc:
            return {"status": "R10", "reason": f"{exc.__class__.__name__}: {exc}"}
        if baseline.get("infrastructure_error"):
            return {"status": "R10", "reason": baseline["infrastructure_error"], "baseline": baseline}
        if baseline.get("passed"):
            return {"status": "REPRODUCTION_NEGATIVE", "baseline": baseline}
        context, files, audit = resolve_context(work, baseline.get("test_output", ""), max_files=6, max_chars=36000)
        task = Task(
            task_id=f"{project}/{bug_id}",
            source=context,
            tests=[],
            split="protected",
            source_group=project,
            metadata={
                "project": project,
                "bug_id": bug_id,
                "failure_class": base.failure_class(baseline.get("test_output", "")),
                "context_files": files,
            },
        )
        prompt = sed.visible_request(project, bug_id, baseline.get("test_output", ""), context)
        return {
            "status": "READY",
            "scope_matched": matches_scope(cap.scope, task),
            "failure_class": task.metadata["failure_class"],
            "context_files": files,
            "context_sha256": sha_text(context),
            "visible_prompt_sha256": sha_text(prompt),
            "python_version": baseline.get("python_version"),
            "python_image": baseline.get("python_image"),
        }


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--capability", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("output exists; refusing overwrite")
    args.out.mkdir(parents=True)
    cap = load_capability(args.capability)
    rows = {f"{p}/{b}": inspect_case(args.bugsinpy, cap, p, b) for p, b in DOWNSTREAM}
    ready = [k for k, v in rows.items() if v.get("status") == "READY"]
    matched = [k for k, v in rows.items() if v.get("status") == "READY" and v.get("scope_matched")]
    result = {
        "canonical_id": "V159_DOWNSTREAM_SCOPE_CENSUS",
        "scientific_outcome": False,
        "capability_id": cap.capability_id,
        "capability_scope": cap.scope,
        "frozen_downstream_order": [f"{p}/{b}" for p, b in DOWNSTREAM],
        "rows": rows,
        "ready": ready,
        "scope_matched": matched,
        "eligible_downstream_exists": bool(matched),
        "verdict": "PASS_V159_SCOPE_FRONTIER_EXISTS" if matched else "OBSTRUCTED_V159_NO_NATURAL_SCOPE_MATCH",
    }
    (args.out / "V159_SCOPE_CENSUS.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if matched else 2)


if __name__ == "__main__":
    main()
