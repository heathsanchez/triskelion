from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any

import bugsinpy_four_arm as base

# Immutable official CPython image digests established before protected semantic
# evaluation. 3.7.3 was already frozen during acquisition; the other three were
# established by protected runtime probe run 31895706375.
PYTHON_IMAGES = {
    "3.7.0": "python:3.7.0@sha256:10608fb357a18383f792efbf7472ec6d2e166dad62efc0d7c409ef2777aaafd0",
    "3.7.3": "python:3.7.3@sha256:9e0b4f32487ca1863b45383420b8db77990debae748e2e875d2f86fa9510d4a5",
    "3.7.7": "python:3.7.7@sha256:c1e36afba1c3c230a6846801fb284cf4383a8a0080fcf32c2ec625c066c56361",
    "3.8.3": "python:3.8.3@sha256:dd6cd8191ccbced2a6af5d0ddb51e6057c1444df14e14bcfd5c7b3ef78738050",
}


def _python_version(work: Path) -> str:
    info = work / "bugsinpy_bug.info"
    if not info.exists():
        raise RuntimeError("bugsinpy_bug.info missing after checkout")
    text = info.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'^python_version="([^"]+)"', text, flags=re.MULTILINE)
    if not m:
        raise RuntimeError("python_version missing from bugsinpy_bug.info")
    return m.group(1)


def _ensure_tools(work: Path) -> Path:
    tools = work / ".cp3_tools"
    tools.mkdir(exist_ok=True)
    dos2unix = tools / "dos2unix"
    dos2unix.write_text(
        "#!/bin/sh\n"
        "if [ \"${1:-}\" = \"--version\" ]; then echo 'dos2unix CP3 deterministic shim 1'; exit 0; fi\n"
        "for f in \"$@\"; do sed -i 's/\\r$//' \"$f\" || exit $?; done\n"
    )
    dos2unix.chmod(0o755)
    return tools


def _docker_shell(bugsinpy: Path, work: Path, image: str, script: str, timeout: int):
    _ensure_tools(work)
    cmd = [
        "docker", "run", "--rm",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "-e", "HOME=/tmp", "-e", "PYTHONDONTWRITEBYTECODE=1",
        "-v", f"{work.resolve()}:/work",
        "-v", f"{bugsinpy.resolve()}:/bugsinpy:ro",
        "-w", "/work", image, "bash", "-lc",
        "export PATH=/work/.cp3_tools:/bugsinpy/framework/bin:$PATH; " + script,
    ]
    return base.run(cmd, timeout=timeout)


def native_test(bugsinpy: Path, work: Path) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        version = _python_version(work)
        image = PYTHON_IMAGES[version]
    except Exception as exc:
        return {"passed": False, "infrastructure_error": f"environment_setup_failed: {exc}", "duration_ms": round((time.perf_counter()-started)*1000, 3)}

    probe = _docker_shell(bugsinpy, work, image, "python --version", 180)
    if probe.returncode != 0 or version not in probe.stdout:
        return {"passed": False, "infrastructure_error": "exact_python_probe_failed", "python_version": version, "python_image": image, "compile_output": probe.stdout[-8000:], "test_output": "", "duration_ms": round((time.perf_counter()-started)*1000, 3)}

    comp = _docker_shell(bugsinpy, work, image, "bugsinpy-compile", 2400)
    if comp.returncode != 0 or not (work / "bugsinpy_compile_flag").exists():
        return {"passed": False, "infrastructure_error": "compile_failed", "python_version": version, "python_image": image, "compile_output": comp.stdout[-20000:], "test_output": "", "duration_ms": round((time.perf_counter()-started)*1000, 3)}

    test = _docker_shell(bugsinpy, work, image, "bugsinpy-test", 1200)
    fail_file = work / "bugsinpy_fail.txt"
    failures = fail_file.read_text(encoding="utf-8", errors="replace") if fail_file.exists() else ""
    combined = (test.stdout + "\n" + failures)[-40000:]
    lower = combined.lower()
    hard_markers = ["importerror while loading", "modulenotfounderror", "command not found", "no module named", "could not find a version that satisfies", "subprocess-exited-with-error", "you have not compile this project"]
    hard_error = any(x in lower for x in hard_markers)
    passed = test.returncode == 0 and not failures.strip() and not hard_error
    return {
        "passed": passed,
        "infrastructure_error": "test_environment_error" if hard_error else None,
        "python_version": version, "python_image": image,
        "compile_output": comp.stdout[-20000:], "test_output": combined,
        "returncode": test.returncode,
        "duration_ms": round((time.perf_counter()-started)*1000, 3),
    }
