from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .models import Task, Verdict


def _purge_pycache(root: Path) -> None:
    for path in root.rglob("__pycache__"):
        shutil.rmtree(path, ignore_errors=True)
    for path in root.rglob("*.pyc"):
        path.unlink(missing_ok=True)


class PythonSubprocessVerifier:
    verifier_id = "python-subprocess-v1"

    def _once(self, task: Task, source: str) -> tuple[bool, list[str], str | None]:
        with tempfile.TemporaryDirectory(prefix="triskelion-verify-") as raw:
            root = Path(raw)
            candidate = root / "candidate.py"
            harness = root / "harness.py"
            candidate.write_text(source)
            harness.write_text(
                "import importlib.util,json\n"
                "spec=importlib.util.spec_from_file_location('candidate','candidate.py')\n"
                "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)\n"
                f"tests=json.loads({json.dumps(json.dumps(task.tests))})\n"
                "fails=[]\n"
                "for i,t in enumerate(tests):\n"
                "  fn=getattr(m,t['function'])\n"
                "  try:\n"
                "    got=fn(*t.get('args',[]))\n"
                "    if 'raises' in t: fails.append(f'{i}: expected {t[\"raises\"]}, returned {got!r}')\n"
                "    elif got != t.get('expected'): fails.append(f'{i}: {got!r} != {t.get(\"expected\")!r}')\n"
                "  except Exception as e:\n"
                "    if e.__class__.__name__ != t.get('raises'): fails.append(f'{i}: unexpected {e.__class__.__name__}: {e}')\n"
                "print(json.dumps({'failures':fails}))\n"
            )
            _purge_pycache(root)
            env = os.environ.copy()
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            try:
                proc = subprocess.run(
                    [sys.executable, "-B", "harness.py"], cwd=root, env=env,
                    text=True, capture_output=True, timeout=10,
                )
            except subprocess.TimeoutExpired:
                return False, [], "verifier timeout"
            finally:
                _purge_pycache(root)
            if proc.returncode != 0:
                return False, [], f"verifier process failed: {proc.stderr.strip()}"
            try:
                failures = json.loads(proc.stdout.strip())["failures"]
            except Exception as exc:
                return False, [], f"invalid verifier output: {exc}"
            return not failures, failures, None

    def verify(self, task: Task, source: str) -> Verdict:
        started = time.perf_counter()
        passed, failures, error = self._once(task, source)
        replay_passed = False
        if passed and error is None:
            replay_passed, replay_failures, replay_error = self._once(task, source)
            if not replay_passed:
                failures.extend([f"replay: {x}" for x in replay_failures])
                error = replay_error
                passed = False
        return Verdict(
            passed=passed, task_id=task.task_id,
            candidate_sha256=hashlib.sha256(source.encode()).hexdigest(),
            tests_run=len(task.tests), failures=failures,
            duration_ms=round((time.perf_counter() - started) * 1000, 3),
            replay_passed=replay_passed, infrastructure_error=error,
        )
