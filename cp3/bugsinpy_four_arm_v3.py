from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

import bugsinpy_four_arm as base


def _python_version(work: Path) -> str:
    info = work / "bugsinpy_bug.info"
    if not info.exists():
        raise RuntimeError("bugsinpy_bug.info missing after checkout")
    text = info.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'^python_version="([^"]+)"', text, flags=re.MULTILINE)
    if not m:
        raise RuntimeError("python_version missing from bugsinpy_bug.info")
    return m.group(1)


def _uv() -> str:
    for candidate in [shutil.which("uv"), "/root/.local/bin/uv"]:
        if candidate and Path(candidate).exists():
            return str(candidate)
    raise RuntimeError("uv unavailable in official BugsInPy image")


def _exact_python(version: str) -> str:
    uv = _uv()
    install = base.run([uv, "python", "install", version], timeout=1800)
    if install.returncode != 0:
        raise RuntimeError(f"uv could not install exact Python {version}: {install.stdout[-10000:]}")
    found = base.run([uv, "python", "find", version], timeout=120)
    if found.returncode != 0:
        raise RuntimeError(f"uv could not resolve exact Python {version}: {found.stdout[-6000:]}")
    path = found.stdout.strip().splitlines()[-1].strip()
    if not path or not Path(path).exists():
        raise RuntimeError(f"uv returned invalid Python path for {version}: {path!r}")
    probe = base.run([path, "-c", "import platform; print(platform.python_version())"], timeout=60)
    actual = probe.stdout.strip().splitlines()[-1] if probe.returncode == 0 and probe.stdout.strip() else ""
    if actual != version:
        raise RuntimeError(f"exact Python mismatch: requested {version}, resolved {actual or 'unknown'}")
    return path


def _official_env(bugsinpy: Path, work: Path) -> tuple[dict[str, str], str]:
    version = _python_version(work)
    python = _exact_python(version)
    shim = Path(tempfile.mkdtemp(prefix="cp3-python-shim-"))
    (shim / "python3").symlink_to(python)
    (shim / "python").symlink_to(python)
    env = os.environ.copy()
    env["PATH"] = str(shim) + os.pathsep + str((bugsinpy / "framework" / "bin").resolve()) + os.pathsep + env.get("PATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env, version


def native_test(bugsinpy: Path, work: Path) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        env, version = _official_env(bugsinpy, work)
    except Exception as exc:
        return {
            "passed": False,
            "infrastructure_error": f"environment_setup_failed: {exc}",
            "python_version": _python_version(work) if (work / "bugsinpy_bug.info").exists() else None,
            "compile_output": "",
            "test_output": "",
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        }

    comp = base.run(["bugsinpy-compile", "-w", str(work)], cwd=work, timeout=2400, env=env)
    if comp.returncode != 0 or not (work / "bugsinpy_compile_flag").exists():
        return {
            "passed": False,
            "infrastructure_error": "compile_failed",
            "python_version": version,
            "compile_output": comp.stdout[-20000:],
            "test_output": "",
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        }

    test = base.run(["bugsinpy-test", "-w", str(work)], cwd=work, timeout=900, env=env)
    text = test.stdout
    fail_file = work / "bugsinpy_fail.txt"
    failures = fail_file.read_text(encoding="utf-8", errors="replace") if fail_file.exists() else ""
    combined = (text + "\n" + failures)[-40000:]
    hard_error_markers = [
        "ImportError while loading", "ModuleNotFoundError", "command not found",
        "No module named", "could not find a version that satisfies", "subprocess-exited-with-error",
    ]
    hard_error = any(x.lower() in combined.lower() for x in hard_error_markers)
    # Official bugsinpy-test records every relevant failing command in bugsinpy_fail.txt.
    passed = test.returncode == 0 and not failures.strip() and not hard_error
    return {
        "passed": passed,
        "infrastructure_error": "test_environment_error" if hard_error else None,
        "python_version": version,
        "compile_output": comp.stdout[-20000:],
        "test_output": combined,
        "returncode": test.returncode,
        "duration_ms": round((time.perf_counter() - started) * 1000, 3),
    }


base.native_test = native_test

if __name__ == "__main__":
    base.main()
