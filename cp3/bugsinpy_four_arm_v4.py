from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any

import bugsinpy_four_arm as base

# Immutable official CPython image digests verified in Actions run 31877656442.
PYTHON_IMAGES = {
    "3.7.3": "python:3.7.3@sha256:9e0b4f32487ca1863b45383420b8db77990debae748e2e875d2f86fa9510d4a5",
    "3.7.4": "python:3.7.4@sha256:fc0a398e1987fb1e58909053c11630e06adb3df265fe693391779020b9253f5e",
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


def _image_for(work: Path) -> tuple[str, str]:
    version = _python_version(work)
    image = PYTHON_IMAGES.get(version)
    if image is None:
        raise RuntimeError(f"no frozen exact CPython image for {version}")
    return version, image


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
    # The model/provider remains on the host. Only the native verifier executes
    # inside the exact historical interpreter image. Run as the host uid/gid so
    # temporary checkout artifacts remain removable by the host controller.
    tools = _ensure_tools(work)
    cmd = [
        "docker", "run", "--rm",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "-e", "HOME=/tmp",
        "-e", "PYTHONDONTWRITEBYTECODE=1",
        "-v", f"{work.resolve()}:/work",
        "-v", f"{bugsinpy.resolve()}:/bugsinpy:ro",
        "-w", "/work",
        image,
        "bash", "-lc",
        "export PATH=/work/.cp3_tools:/bugsinpy/framework/bin:$PATH; " + script,
    ]
    return base.run(cmd, timeout=timeout)


def native_test(bugsinpy: Path, work: Path) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        version, image = _image_for(work)
    except Exception as exc:
        return {
            "passed": False,
            "infrastructure_error": f"environment_setup_failed: {exc}",
            "python_version": _python_version(work) if (work / "bugsinpy_bug.info").exists() else None,
            "compile_output": "",
            "test_output": "",
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        }

    probe = _docker_shell(bugsinpy, work, image, "python --version", 180)
    if probe.returncode != 0 or version not in probe.stdout:
        return {
            "passed": False,
            "infrastructure_error": "exact_python_probe_failed",
            "python_version": version,
            "python_image": image,
            "compile_output": probe.stdout[-8000:],
            "test_output": "",
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        }

    comp = _docker_shell(bugsinpy, work, image, "bugsinpy-compile", 2400)
    if comp.returncode != 0 or not (work / "bugsinpy_compile_flag").exists():
        return {
            "passed": False,
            "infrastructure_error": "compile_failed",
            "python_version": version,
            "python_image": image,
            "compile_output": comp.stdout[-20000:],
            "test_output": "",
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        }

    test = _docker_shell(bugsinpy, work, image, "bugsinpy-test", 900)
    fail_file = work / "bugsinpy_fail.txt"
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
        "passed": passed,
        "infrastructure_error": "test_environment_error" if hard_error else None,
        "python_version": version,
        "python_image": image,
        "compile_output": comp.stdout[-20000:],
        "test_output": combined,
        "returncode": test.returncode,
        "duration_ms": round((time.perf_counter() - started) * 1000, 3),
    }


base.native_test = native_test

if __name__ == "__main__":
    base.main()
