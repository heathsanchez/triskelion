from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
VENDOR = HERE / "vendor" / "cp1"
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from triskelion.models import Capability, Task
from triskelion.providers import RiverProvider
from triskelion.scope import matches_scope

MODEL = "Qwen/Qwen3.5-9B"
SEED = 20260815
MAX_TOKENS = 2048
ARMS = ["cold", "raw_memory", "always_on", "verified"]


def run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 1800, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)


def framework_env(bugsinpy: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = str(bugsinpy / "framework" / "bin") + os.pathsep + env.get("PATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def checkout_buggy(bugsinpy: Path, project: str, bug_id: int, root: Path) -> Path:
    env = framework_env(bugsinpy)
    root.mkdir(parents=True, exist_ok=True)
    proc = run([
        "bugsinpy-checkout", "-p", project, "-v", "0", "-i", str(bug_id), "-w", str(root)
    ], timeout=1800, env=env)
    if proc.returncode != 0:
        raise RuntimeError(f"checkout failed: {proc.stdout[-8000:]}")
    work = root / project
    if not work.is_dir():
        raise RuntimeError(f"checkout did not create {work}")
    return work


def native_test(bugsinpy: Path, work: Path) -> dict[str, Any]:
    env = framework_env(bugsinpy)
    started = time.perf_counter()
    comp = run(["bugsinpy-compile"], cwd=work, timeout=2400, env=env)
    if comp.returncode != 0:
        return {"passed": False, "infrastructure_error": "compile_failed", "compile_output": comp.stdout[-12000:], "test_output": "", "duration_ms": round((time.perf_counter()-started)*1000, 3)}
    test = run(["bugsinpy-test"], cwd=work, timeout=900, env=env)
    text = test.stdout
    lower = text.lower()
    passed = test.returncode == 0 and (" passed" in lower or "ok" in lower) and " failures " not in lower and " failed" not in lower
    return {
        "passed": passed,
        "infrastructure_error": None,
        "compile_output": comp.stdout[-12000:],
        "test_output": text[-24000:],
        "returncode": test.returncode,
        "duration_ms": round((time.perf_counter()-started)*1000, 3),
    }


def failure_class(text: str) -> str:
    for name in ["AssertionError", "TypeError", "ValueError", "KeyError", "AttributeError", "IndexError", "ImportError", "RuntimeError"]:
        if name in text:
            return name
    if "FAILURES" in text or "FAILED" in text:
        return "TEST_FAILURE"
    return "UNKNOWN_FAILURE"


def collect_context(work: Path, baseline_output: str, *, max_files: int = 6, max_chars: int = 36000) -> tuple[str, list[str]]:
    paths: list[Path] = []
    for raw in re.findall(r'File ["\']([^"\']+\.py)["\']', baseline_output):
        p = Path(raw)
        if not p.is_absolute():
            p = work / p
        try:
            p = p.resolve()
            p.relative_to(work.resolve())
        except Exception:
            continue
        if p.is_file() and p not in paths:
            paths.append(p)
    if not paths:
        for p in sorted(work.rglob("*.py")):
            if ".git" not in p.parts and p.stat().st_size <= 20000:
                paths.append(p)
                if len(paths) >= max_files:
                    break
    chunks: list[str] = []
    used: list[str] = []
    remaining = max_chars
    for p in paths[:max_files]:
        text = p.read_text(encoding="utf-8", errors="replace")
        rel = str(p.relative_to(work))
        chunk = f"\n### FILE {rel}\n```python\n{text}\n```\n"
        if len(chunk) > remaining:
            break
        chunks.append(chunk); used.append(rel); remaining -= len(chunk)
    return "".join(chunks), used


def visible_request(project: str, bug_id: int, failure: str, context: str) -> str:
    return (
        "Repair this independently authored Python repository bug. Return ONLY a unified git diff. "
        "Do not edit tests. Use only the buggy source and failing native-test evidence below.\n\n"
        f"CASE: {project}/{bug_id}\n"
        f"NATIVE FAILURE:\n{failure[-12000:]}\n"
        f"BUGGY SOURCE CONTEXT:\n{context}"
    )


def load_capability(path: Path) -> Capability:
    value = json.loads(path.read_text())
    cap = Capability.from_dict(value)
    blob = json.dumps(cap.artifact, sort_keys=True, separators=(",", ":"))
    expected = hashlib.sha256(blob.encode()).hexdigest()
    if cap.artifact_sha256 and cap.artifact_sha256 != expected:
        raise ValueError("capability artifact hash mismatch")
    return cap


def memory_view(arm: str, cap: Capability | None, raw_memory: str, task: Task) -> tuple[list[str], str]:
    if arm == "cold":
        return [], ""
    if arm == "raw_memory":
        return [], raw_memory
    if cap is None:
        raise RuntimeError("capability required for always_on/verified")
    active = arm == "always_on" or (arm == "verified" and matches_scope(cap.scope, task))
    if not active:
        return [], ""
    payload = {
        "id": cap.capability_id,
        "preconditions": cap.preconditions,
        "postconditions": cap.postconditions,
        "scope": cap.scope,
        "artifact": cap.artifact,
    }
    return [cap.capability_id], "Installed verified capability manifest:\n" + json.dumps(payload, sort_keys=True)


def extract_diff(text: str) -> str:
    blocks = re.findall(r"```(?:diff)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    candidate = blocks[0] if len(blocks) == 1 else text
    candidate = candidate.strip() + "\n"
    if "diff --git " not in candidate and not candidate.startswith("--- "):
        raise ValueError("model output is not a unified diff")
    return candidate


def apply_diff(work: Path, diff: str) -> None:
    patch = work / ".cp3_candidate.diff"
    patch.write_text(diff)
    check = run(["git", "apply", "--check", str(patch)], cwd=work, timeout=60)
    if check.returncode != 0:
        raise ValueError(f"git apply --check failed: {check.stdout[-6000:]}")
    applied = run(["git", "apply", str(patch)], cwd=work, timeout=60)
    if applied.returncode != 0:
        raise ValueError(f"git apply failed: {applied.stdout[-6000:]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--bug-id", type=int, required=True)
    ap.add_argument("--arm", choices=ARMS, required=True)
    ap.add_argument("--case-index", type=int, required=True)
    ap.add_argument("--capability", type=Path)
    ap.add_argument("--raw-memory", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    if args.out.exists():
        raise SystemExit("output exists; refusing to overwrite frozen evidence")
    args.out.parent.mkdir(parents=True, exist_ok=True)

    cap = load_capability(args.capability) if args.capability else None
    raw_memory = args.raw_memory.read_text() if args.raw_memory else ""

    with tempfile.TemporaryDirectory(prefix="cp3-bugsinpy-") as raw:
        root = Path(raw)
        work = checkout_buggy(args.bugsinpy, args.project, args.bug_id, root)
        baseline = native_test(args.bugsinpy, work)
        if baseline["infrastructure_error"]:
            result = {"status": "INFRASTRUCTURE_NEGATIVE", "baseline": baseline, "project": args.project, "bug_id": args.bug_id, "arm": args.arm}
            args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n"); return
        if baseline["passed"]:
            result = {"status": "REPRODUCTION_NEGATIVE", "baseline": baseline, "project": args.project, "bug_id": args.bug_id, "arm": args.arm}
            args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n"); return

        context, files = collect_context(work, baseline["test_output"])
        task = Task(
            task_id=f"{args.project}/{args.bug_id}", source=context, tests=[], split="protected", source_group=args.project,
            metadata={"project": args.project, "bug_id": args.bug_id, "failure_class": failure_class(baseline["test_output"]), "context_files": files},
        )
        selected, memory = memory_view(args.arm, cap, raw_memory, task)
        prompt = visible_request(args.project, args.bug_id, baseline["test_output"], context)
        if memory:
            prompt += "\n\n" + memory

        provider = RiverProvider(MODEL)
        seed = SEED + args.case_index
        infrastructure_error = None
        output_error = None
        patch_error = None
        response_row = None
        diff = ""
        try:
            response = provider.sample(prompt, seed=seed, max_tokens=MAX_TOKENS)
            response_row = response.to_dict()
            response_row["text_sha256"] = hashlib.sha256(response.text.encode()).hexdigest()
        except Exception as exc:
            infrastructure_error = f"{exc.__class__.__name__}: {exc}"
        if infrastructure_error is None:
            try:
                diff = extract_diff(response.text)
                apply_diff(work, diff)
            except Exception as exc:
                patch_error = f"{exc.__class__.__name__}: {exc}"
        verdict = None
        if infrastructure_error is None and patch_error is None:
            verdict = native_test(args.bugsinpy, work)
        result = {
            "protocol": "TRISKELION_CP3_FOUR_ARM_V1",
            "model": MODEL,
            "temperature": 0.0,
            "max_tokens": MAX_TOKENS,
            "seed": seed,
            "project": args.project,
            "bug_id": args.bug_id,
            "arm": args.arm,
            "selected": selected,
            "scope_matched": bool(cap and matches_scope(cap.scope, task)),
            "context_files": files,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "response": response_row,
            "diff_sha256": hashlib.sha256(diff.encode()).hexdigest() if diff else None,
            "infrastructure_error": infrastructure_error,
            "output_error": output_error,
            "patch_error": patch_error,
            "baseline": baseline,
            "verdict": verdict,
        }
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({k: result[k] for k in ["project", "bug_id", "arm", "selected", "scope_matched", "infrastructure_error", "patch_error", "verdict"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
