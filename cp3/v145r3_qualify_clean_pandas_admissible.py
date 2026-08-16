#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import v145r1_qualify_clean_pandas_exact as base

PROTOCOL = "V145R3_CLEAN_THIRD_RUNG_ADMISSIBILITY"
DENYLIST_PATH = Path("protocols/V145R3_EXPOSURE_DENYLIST.json")

base.PROTOCOL = PROTOCOL
base.DENYLIST_PATH = DENYLIST_PATH

_original_classify_pair = base.classify_pair


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


def classify_pair(bugsinpy: Path, project: str, bug_id: int) -> dict:
    rec = _original_classify_pair(bugsinpy, project, bug_id)
    if rec.get("qualified") is not True or rec.get("status") != "QUALIFIED":
        return rec

    patch = bugsinpy / "projects" / project / "bugs" / str(bug_id) / "bug_patch.txt"
    if not patch.is_file():
        rec.update(
            qualified=None,
            status="INTERVENTION_PATH_APPARATUS_INELIGIBLE",
            reason="developer_patch_missing_for_path_audit",
        )
        return rec
    try:
        diff = patch.read_text(encoding="utf-8", errors="strict")
        files = changed_files(diff)
    except Exception as exc:
        rec.update(
            qualified=None,
            status="INTERVENTION_PATH_APPARATUS_INELIGIBLE",
            reason=f"developer_patch_path_parse_failed:{exc.__class__.__name__}:{exc}",
        )
        return rec

    rec["reference_changed_files"] = files
    rec["reference_path_audit_only"] = True
    if not files:
        rec.update(
            qualified=None,
            status="INTERVENTION_PATH_APPARATUS_INELIGIBLE",
            reason="developer_patch_has_no_parseable_changed_paths",
        )
    elif rejects_tests(files):
        rec.update(
            qualified=False,
            status="REFERENCE_INTERVENTION_INELIGIBLE_TEST_PATH",
            reason="developer_patch_edits_test_path_under_inherited_v145_rule",
        )
    else:
        rec.update(
            qualified=True,
            status="QUALIFIED",
            reason="fixed_pass_buggy_fail_and_reference_paths_pass_no_test_edit_law",
        )
    return rec


base.classify_pair = classify_pair

if __name__ == "__main__":
    base.main()
