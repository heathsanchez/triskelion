from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import bugsinpy_four_arm as base
import bugsinpy_exact_runtime as exact
import v145_natural_third_rung_causal as experiment

TEMPLATE_ROOT = Path(os.environ.get("V145_TEMPLATE_ROOT", "/tmp/v145_precompiled_templates"))
TEMPLATE_ROOT.mkdir(parents=True, exist_ok=True)

_original_checkout = base.checkout_buggy
_original_native = exact.native_test
_original_apply = base.apply_diff


def _key(project: str, bug_id: int) -> str:
    return f"{project}__{bug_id}"


def _template(project: str, bug_id: int) -> Path:
    return TEMPLATE_ROOT / _key(project, bug_id)


def checkout_reusing_precompiled(bugsinpy: Path, project: str, bug_id: int, root: Path) -> Path:
    tpl = _template(project, bug_id)
    if tpl.is_dir() and (tpl / ".v145_precompiled").exists():
        root.mkdir(parents=True, exist_ok=True)
        dst = root / project
        shutil.copytree(tpl, dst, symlinks=True)
        return dst
    work = _original_checkout(bugsinpy, project, bug_id, root)
    (work / ".v145_case").write_text(f"{project}\n{bug_id}\n")
    return work


def _case_from(work: Path) -> tuple[str, int] | None:
    p = work / ".v145_case"
    if not p.exists():
        return None
    lines = p.read_text().splitlines()
    if len(lines) != 2:
        return None
    try:
        return lines[0], int(lines[1])
    except Exception:
        return None


def _build_sensitive(paths: list[str]) -> bool:
    for raw in paths:
        p = Path(raw)
        low = raw.lower()
        if p.suffix.lower() != ".py":
            return True
        if p.name.lower() in {"setup.py", "setup.cfg", "pyproject.toml"}:
            return True
        if "requirements" in p.name.lower() or "build" in [x.lower() for x in p.parts]:
            return True
    return False


def apply_with_policy(work: Path, diff: str) -> None:
    paths = experiment.changed_files(diff)
    if experiment.rejects_tests(paths):
        raise ValueError("candidate edits a test path; forbidden by frozen V145 protocol")
    _original_apply(work, diff)
    if _build_sensitive(paths):
        (work / ".v145_force_full_compile").write_text("1\n")


def _test_only(bugsinpy: Path, work: Path) -> dict[str, Any]:
    import time
    started = time.perf_counter()
    try:
        version, image = exact._image_for(work)
    except Exception as exc:
        return {"passed":False,"infrastructure_error":f"environment_setup_failed: {exc}","compile_output":"","test_output":"","duration_ms":round((time.perf_counter()-started)*1000,3),"v145_precompiled":True}
    probe = exact._docker_shell(bugsinpy, work, image, "python --version", 180)
    if probe.returncode != 0 or version not in probe.stdout:
        return {"passed":False,"infrastructure_error":"exact_python_probe_failed","python_version":version,"python_image":image,"compile_output":probe.stdout[-8000:],"test_output":"","duration_ms":round((time.perf_counter()-started)*1000,3),"v145_precompiled":True}
    fail_file = work / "bugsinpy_fail.txt"
    if fail_file.exists():
        fail_file.unlink()
    test = exact._docker_shell(bugsinpy, work, image, "bugsinpy-test", 900)
    failures = fail_file.read_text(encoding="utf-8", errors="replace") if fail_file.exists() else ""
    combined = (test.stdout + "\n" + failures)[-40000:]
    lower = combined.lower()
    hard_error_markers = [
        "importerror while loading", "modulenotfounderror", "command not found",
        "no module named", "could not find a version that satisfies",
        "subprocess-exited-with-error", "you have not compile this project",
    ]
    hard_error = any(x in lower for x in hard_error_markers)
    passed = test.returncode == 0 and not failures.strip() and not hard_error
    return {
        "passed":passed,
        "infrastructure_error":"test_environment_error" if hard_error else None,
        "python_version":version,"python_image":image,
        "compile_output":"PRECOMPILED_TEMPLATE_REUSE_V145A",
        "test_output":combined,"returncode":test.returncode,
        "duration_ms":round((time.perf_counter()-started)*1000,3),"v145_precompiled":True,
    }


def native_with_template(bugsinpy: Path, work: Path) -> dict[str, Any]:
    if (work / ".v145_precompiled").exists() and not (work / ".v145_force_full_compile").exists():
        return _test_only(bugsinpy, work)
    result = _original_native(bugsinpy, work)
    case = _case_from(work)
    # Freeze a reusable template only after a successful full compile/test invocation
    # whose environment itself is valid. The semantic test is expected to fail on buggy checkout.
    if case is not None and not result.get("infrastructure_error") and (work / "bugsinpy_compile_flag").exists():
        project, bug_id = case
        tpl = _template(project, bug_id)
        if not tpl.exists():
            shutil.copytree(work, tpl, symlinks=True)
            (tpl / ".v145_precompiled").write_text("1\n")
    return result


base.checkout_buggy = checkout_reusing_precompiled
base.apply_diff = apply_with_policy
exact.native_test = native_with_template
base.native_test = native_with_template
# The experiment module imported function globals by module reference, so its
# calls to base/exact now use the patched apparatus.

if __name__ == "__main__":
    experiment.main()
