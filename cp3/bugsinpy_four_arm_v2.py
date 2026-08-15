from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
from pathlib import Path
from typing import Any

import bugsinpy_four_arm as base


def _conda() -> str:
    value = shutil.which("conda")
    if value:
        return value
    fallback = Path("/opt/conda/bin/conda")
    if fallback.exists():
        return str(fallback)
    raise RuntimeError("conda is unavailable in BugsInPy environment")


def _python_version(work: Path) -> str:
    info = work / "bugsinpy_bug.info"
    if not info.exists():
        raise RuntimeError("bugsinpy_bug.info missing after checkout")
    text = info.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"\b(3\.\d+\.\d+)\b", text)
    if not match:
        raise RuntimeError("could not determine exact Python version from bugsinpy_bug.info")
    return match.group(1)


def _env_name(work: Path, python_version: str) -> str:
    req = work / "bugsinpy_requirements.txt"
    raw = req.read_bytes() if req.exists() else b""
    digest = hashlib.sha256(python_version.encode() + b"\0" + raw).hexdigest()[:20]
    return "cp3_" + digest


def _ensure_env(work: Path) -> tuple[str, str]:
    conda = _conda()
    version = _python_version(work)
    name = _env_name(work, version)
    listed = base.run([conda, "env", "list", "--json"], timeout=120)
    if listed.returncode != 0:
        raise RuntimeError(f"conda env list failed: {listed.stdout[-6000:]}")
    payload = json.loads(listed.stdout)
    exists = any(Path(p).name == name for p in payload.get("envs", []))
    if not exists:
        made = base.run([conda, "create", "-y", "-n", name, f"python={version}", "pytest", "pip"], timeout=1800)
        if made.returncode != 0:
            raise RuntimeError(f"conda create failed: {made.stdout[-10000:]}")
    return conda, name


def native_test(bugsinpy: Path, work: Path) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        conda, env_name = _ensure_env(work)
    except Exception as exc:
        return {
            "passed": False,
            "infrastructure_error": f"environment_setup_failed: {exc}",
            "compile_output": "",
            "test_output": "",
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        }
    framework = str((bugsinpy / "framework" / "bin").resolve())
    shell_prefix = f"export PATH={framework}:$PATH; export PYTHONDONTWRITEBYTECODE=1; "
    comp = base.run(
        [conda, "run", "--no-capture-output", "-n", env_name, "bash", "-lc", shell_prefix + "bugsinpy-compile"],
        cwd=work, timeout=2400,
    )
    if comp.returncode != 0:
        return {
            "passed": False,
            "infrastructure_error": "compile_failed",
            "conda_env": env_name,
            "compile_output": comp.stdout[-16000:],
            "test_output": "",
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        }
    test = base.run(
        [conda, "run", "--no-capture-output", "-n", env_name, "bash", "-lc", shell_prefix + "bugsinpy-test"],
        cwd=work, timeout=900,
    )
    text = test.stdout
    lower = text.lower()
    hard_error = any(x in text for x in ["= ERRORS =", "ImportError while loading", ": command not found", "You have not compile this project"])
    explicit_failure = "= FAILURES =" in text or "FAILED (" in text or " failed" in lower
    explicit_pass = bool(re.search(r"\bpassed\b|\bOK\b", text, flags=re.IGNORECASE))
    passed = test.returncode == 0 and explicit_pass and not explicit_failure and not hard_error
    infrastructure_error = "test_environment_error" if hard_error else None
    return {
        "passed": passed,
        "infrastructure_error": infrastructure_error,
        "conda_env": env_name,
        "compile_output": comp.stdout[-16000:],
        "test_output": text[-32000:],
        "returncode": test.returncode,
        "duration_ms": round((time.perf_counter() - started) * 1000, 3),
    }


base.native_test = native_test

if __name__ == "__main__":
    base.main()
