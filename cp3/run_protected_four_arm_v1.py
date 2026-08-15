#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROTOCOL = "TRISKELION_CP3_FOUR_ARM_V1"
MODEL = "Qwen/Qwen3.5-9B"
MODEL_LABEL = "Qwen3.5-9B"
BASE_SEED = 20260815
MAX_TOKENS = 2048
MAX_CALLS = 2
EXPECTED_CAPABILITY_SHA256 = "b59ec323ef03138319c0ae440586ab0d9bf19ff46a054826d9b82b11d9ddd5d7"
EXPECTED_RUNTIME_SHA256 = "aef1cd1f5b6ba27ba8f869909e49eb059e3128504aaca012a43a6e01a1e6daef"
EXPECTED_BUGSINPY_HEAD = "11c5f1eea954a42132cfd06bf257766a7963e0fd"
PROTECTED = ["thefuck/32", "keras/32", "spacy/2", "fastapi/5", "black/18"]
ARMS = ["COLD", "RAW_MEMORY", "ALWAYS_ON", "VERIFIED"]
ACQUISITION = ["httpie/5", "youtube-dl/32"]

EXCLUDED_PARTS = {
    ".git", "env", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    "vendor", "vendors", "generated", "dist", "build", "node_modules", "site-packages",
}


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode())


def run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 1800) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=timeout)


def must_run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 1800) -> str:
    p = run(cmd, cwd=cwd, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}\n{p.stdout[-12000:]}")
    return p.stdout


def docker_exec(container: str, shell: str, *, timeout: int = 1800) -> subprocess.CompletedProcess[str]:
    return run(["docker", "exec", container, "bash", "-lc", shell], timeout=timeout)


def is_production_py(rel: Path) -> bool:
    if rel.suffix != ".py" or rel.is_absolute():
        return False
    low_parts = [p.lower() for p in rel.parts]
    if any(p in EXCLUDED_PARTS for p in low_parts):
        return False
    if any(p in {"test", "tests", "testing"} for p in low_parts):
        return False
    if rel.name.lower().startswith("test_") or rel.name.lower().endswith("_test.py"):
        return False
    if rel.name.startswith("bugsinpy_"):
        return False
    return True


def normalize_candidate_path(raw: str, work: Path) -> Path | None:
    raw = raw.strip().strip("'\"()[]{}:,;")
    raw = raw.replace("\\", "/")
    p = Path(raw)
    if p.is_absolute():
        try:
            rel = p.resolve().relative_to(work.resolve())
        except Exception:
            # Tracebacks inside the BugsInPy container use /home/workspace/<project>/...
            marker = f"/home/workspace/{work.name}/"
            if marker in raw:
                rel = Path(raw.split(marker, 1)[1])
            else:
                return None
    else:
        rel = p
    if not is_production_py(rel):
        return None
    target = work / rel
    return rel if target.is_file() else None


def source_excerpt(path: Path, line_no: int | None, max_chars: int = 8000) -> str:
    text = path.read_text(errors="replace")
    if len(text) <= max_chars:
        return text
    if line_no is None:
        return text[:max_chars]
    lines = text.splitlines(keepends=True)
    idx = max(0, min(len(lines) - 1, line_no - 1))
    prefix_chars = sum(len(x) for x in lines[:idx])
    start = max(0, prefix_chars - max_chars // 2)
    end = min(len(text), start + max_chars)
    start = max(0, end - max_chars)
    return text[start:end]


def sanitize(work: Path, failing_output: str) -> tuple[str, list[str]]:
    tail = failing_output[-12000:]
    # Capture Python paths and optional traceback line numbers in occurrence order.
    path_pat = re.compile(r"(?P<path>(?:[A-Za-z]:)?[^\s\"'<>|]+?\.py)(?:[:\", ]+line\s+(?P<line>\d+)|:(?P<lineno>\d+))?")
    chosen: list[tuple[Path, int | None]] = []
    seen: set[str] = set()
    for m in path_pat.finditer(tail):
        rel = normalize_candidate_path(m.group("path"), work)
        if rel is None:
            continue
        key = rel.as_posix()
        if key in seen:
            continue
        seen.add(key)
        ln_raw = m.group("line") or m.group("lineno")
        chosen.append((rel, int(ln_raw) if ln_raw else None))
        if len(chosen) == 3:
            break

    if not chosen:
        for p in sorted(work.rglob("*.py")):
            try:
                rel = p.relative_to(work)
            except Exception:
                continue
            if is_production_py(rel):
                chosen.append((rel, None))
                if len(chosen) == 3:
                    break

    # Strip absolute temporary/workspace prefixes from verifier output.
    cleaned_tail = tail.replace(str(work.resolve()), f"<WORK>/{work.name}")
    cleaned_tail = re.sub(r"/home/workspace/[^/]+", "<WORK>", cleaned_tail)
    sections = ["NATIVE FAILING VERIFIER OUTPUT (tail):\n" + cleaned_tail]
    included = []
    for rel, line_no in chosen:
        included.append(rel.as_posix())
        excerpt = source_excerpt(work / rel, line_no)
        sections.append(f"PRODUCTION SOURCE: {rel.as_posix()}\n```python\n{excerpt}\n```")
    return "\n\n".join(sections), included


def parse_first_json_object(text: str) -> dict:
    first = text.find("{")
    if first < 0:
        raise ValueError("no JSON object")
    obj, _ = json.JSONDecoder().raw_decode(text[first:])
    if not isinstance(obj, dict):
        raise ValueError("decoded JSON is not object")
    return obj


def proposal_prompt(context: str, memory: str) -> str:
    memory_block = "" if not memory else f"\nACQUIRED REPAIR CAPABILITY MEMORY:\n{memory}\n"
    return f"""You are repairing one Python bug from a sealed protected evaluation. You see only the buggy code context and its failing native verifier output. Do not ask for or infer a developer patch. Propose the smallest concrete source edit that makes the failing behavior correct.
{memory_block}
Return ONLY one JSON object with this exact shape:
{{
  "edits": [
    {{"path": "relative/production.py", "search": "exact old text", "replace": "new text"}}
  ],
  "rationale": "short explanation"
}}

Rules:
- 1 to 4 edits.
- Edit existing production Python files only; never tests.
- `search` must be exact text copied from the provided production source and identify one occurrence.
- No shell commands, dependency changes, new files, deletions, or network actions.
- Do not include Markdown fences around the JSON.

PROTECTED BUG CONTEXT:\n{context}
"""


def retry_prompt(original: str, invalid_text: str, error: str) -> str:
    return original + f"\n\nYour previous response could not be parsed/applied mechanically. You receive NO verifier feedback. Error: {error}\nPREVIOUS RESPONSE:\n{invalid_text}\nReturn only a corrected JSON object under the identical edit contract."


def validate_and_apply(proposal: dict, work: Path) -> tuple[list[dict], str]:
    edits = proposal.get("edits")
    if not isinstance(edits, list) or not (1 <= len(edits) <= 4):
        raise ValueError("edits must contain 1..4 entries")
    normalized: list[dict] = []
    for e in edits:
        if not isinstance(e, dict):
            raise ValueError("edit is not object")
        path, search, replace = e.get("path"), e.get("search"), e.get("replace")
        if not all(isinstance(x, str) for x in (path, search, replace)):
            raise ValueError("path/search/replace must be strings")
        rel = Path(path)
        if not is_production_py(rel):
            raise ValueError(f"disallowed path: {path}")
        target = (work / rel)
        if not target.is_file():
            raise ValueError(f"nonexistent path: {path}")
        if not search:
            raise ValueError("empty search")
        text = target.read_text(errors="replace")
        count = text.count(search)
        if count != 1:
            raise ValueError(f"search occurrence count for {path}: {count}")
        target.write_text(text.replace(search, replace, 1))
        normalized.append({"path": rel.as_posix(), "search": search, "replace": replace})
    patch_text = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return normalized, sha256_text(patch_text)


def activate(capabilities: list[dict], context: str) -> tuple[list[dict], list[dict]]:
    low = context.lower()
    active = []
    matches = []
    for cap in capabilities:
        terms = list(cap.get("scope", {}).get("any_terms", []))
        hit = [t for t in terms if isinstance(t, str) and t.lower() in low]
        matches.append({"capability_id": cap.get("capability_id"), "matched_terms": hit})
        if hit:
            active.append(cap)
    return active, matches


def arm_memory(arm: str, capabilities: list[dict], acquisition_diffs: list[str], context: str) -> tuple[str, dict]:
    if arm == "COLD":
        return "", {"requested": False, "activated": False, "reason": "cold arm", "matched": []}
    if arm == "RAW_MEMORY":
        return "\n\n".join(acquisition_diffs), {"requested": False, "activated": True, "reason": "raw acquisition traces supplied", "matched": []}
    if arm == "ALWAYS_ON":
        mem = "\n\n".join(c["artifact"]["memory_text"] for c in capabilities)
        return mem, {"requested": True, "activated": bool(capabilities), "reason": "all frozen capabilities forced on", "matched": [{"capability_id": c["capability_id"], "matched_terms": ["FORCED"]} for c in capabilities]}
    if arm == "VERIFIED":
        active, matches = activate(capabilities, context)
        mem = "\n\n".join(c["artifact"]["memory_text"] for c in active)
        return mem, {"requested": True, "activated": bool(active), "reason": "literal frozen scope.any_terms routing", "matched": matches, "activated_ids": [c["capability_id"] for c in active]}
    raise ValueError(arm)


def native_test(container: str, work_container: str, *, timeout: int = 1200) -> tuple[bool, str]:
    # BugsInPy's native test wrapper records failed relevant commands in bugsinpy_fail.txt.
    cmd = (
        f"export PATH=$PATH:/home/bugsinpy/framework/bin; "
        f"rm -f {work_container}/bugsinpy_fail.txt; "
        f"bugsinpy-test -r -w {work_container}; rc=$?; "
        f"echo __BUGSINPY_WRAPPER_RC__=$rc; "
        f"if [ -s {work_container}/bugsinpy_fail.txt ]; then echo __BUGSINPY_RESULT__=FAIL; cat {work_container}/bugsinpy_fail.txt; "
        f"else echo __BUGSINPY_RESULT__=PASS; fi"
    )
    p = docker_exec(container, cmd, timeout=timeout)
    out = p.stdout
    passed = "__BUGSINPY_RESULT__=PASS" in out and "__BUGSINPY_RESULT__=FAIL" not in out
    return passed, out


def provider_client():
    key = os.environ.get("RIVER_API_KEY")
    if not key:
        raise RuntimeError("RIVER_API_KEY missing")
    import river_client as river
    client = river.Client(api_key=key)
    if not client.health_check():
        raise RuntimeError("River health check failed")
    if MODEL not in list(client.get_capabilities()):
        raise RuntimeError(f"frozen model unavailable: {MODEL}")
    return client


def sample(client, prompt: str, seed: int) -> tuple[str, float]:
    t0 = time.perf_counter()
    samples = client.sample(prompt, base_model=MODEL, max_tokens=MAX_TOKENS,
                            temperature=0.0, seed=seed)
    if not samples:
        raise RuntimeError("River returned no samples")
    return samples[0].text, round((time.perf_counter() - t0) * 1000, 3)


def setup_bugsinpy(root: Path, project: str, bug_id: str, container: str) -> tuple[Path, str]:
    repo = root / "BugsInPy"
    must_run(["git", "clone", "https://github.com/soarsmu/BugsInPy.git", str(repo)], timeout=600)
    must_run(["git", "checkout", EXPECTED_BUGSINPY_HEAD], cwd=repo, timeout=60)
    head = must_run(["git", "rev-parse", "HEAD"], cwd=repo, timeout=30).strip()
    if head != EXPECTED_BUGSINPY_HEAD:
        raise RuntimeError(f"BugsInPy head mismatch: {head}")
    must_run(["docker", "build", "-t", "cp3-protected-bugsinpy", "."], cwd=repo, timeout=1800)
    framework = str((repo / "framework").resolve())
    projects = str((repo / "projects").resolve())
    workspace = repo / "workspace"
    workspace.mkdir()
    start = run([
        "docker", "run", "-d", "--name", container,
        "-v", f"{framework}:/home/bugsinpy/framework",
        "-v", f"{projects}:/home/bugsinpy/projects",
        "-v", f"{workspace.resolve()}:/home/workspace",
        "cp3-protected-bugsinpy", "bash", "-lc", "sleep infinity",
    ])
    if start.returncode != 0:
        raise RuntimeError("container start failed\n" + start.stdout)
    work_container = f"/home/workspace/{project}"
    prep = docker_exec(container,
        "export PATH=$PATH:/home/bugsinpy/framework/bin; "
        f"bugsinpy-checkout -p {project} -i {bug_id} -v 0 -w /home/workspace && "
        f"bugsinpy-compile -w {work_container} && chmod -R a+rwX {work_container}",
        timeout=3600)
    if prep.returncode != 0 or "This is not a checkout project folder" in prep.stdout:
        raise RuntimeError("protected provisioning failed\n" + prep.stdout[-12000:])
    work = workspace / project
    if not (work / "bugsinpy_compile_flag").is_file():
        raise RuntimeError("compile flag missing after provisioning")
    return work, work_container


def load_frozen_payload(path: Path) -> tuple[dict, str]:
    blob = path.read_bytes()
    sha = sha256_bytes(blob)
    if sha != EXPECTED_CAPABILITY_SHA256:
        raise RuntimeError(f"capability payload hash mismatch: {sha}")
    payload = json.loads(blob)
    if payload.get("protected_evidence_used") is not False or payload.get("status") != "FROZEN":
        raise RuntimeError("capability payload not cleanly frozen")
    return payload, sha


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, choices=PROTECTED)
    ap.add_argument("--capability", required=True)
    ap.add_argument("--runtime-sha-file", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    case_index = PROTECTED.index(args.case)
    seed = BASE_SEED + case_index
    project, bug_id = args.case.split("/", 1)
    out = Path(args.out)
    if out.exists():
        raise SystemExit("output exists; refusing overwrite")
    out.mkdir(parents=True)

    payload, capability_sha = load_frozen_payload(Path(args.capability))
    runtime_sha = Path(args.runtime_sha_file).read_text().strip()
    if runtime_sha != EXPECTED_RUNTIME_SHA256:
        raise SystemExit(f"runtime source hash mismatch: {runtime_sha}")
    capabilities = payload["capabilities"]

    container = f"cp3-protected-{project.lower().replace('_','-')}-{os.getpid()}"
    root = out / "_infra"
    root.mkdir()
    results = []
    summary: dict = {"case": args.case, "status": "RUNNING"}
    try:
        work, work_container = setup_bugsinpy(root, project, bug_id, container)
        baseline_pass, baseline_log = native_test(container, work_container)
        (out / "BASELINE_FAILING_VERIFIER.log").write_text(baseline_log)
        if baseline_pass:
            raise RuntimeError("qualified protected case unexpectedly passes before model scoring")
        context, included_files = sanitize(work, baseline_log)
        input_sha = sha256_text(context)
        (out / "SANITIZED_INPUT.txt").write_text(context)
        (out / "SANITIZED_INPUT_SHA256.txt").write_text(input_sha + "\n")

        # Acquisition raw memory is read only from the two frozen acquisition traces.
        acquisition_diffs = []
        bugs_repo = root / "BugsInPy"
        for acq in ACQUISITION:
            apj, aid = acq.split("/", 1)
            acquisition_diffs.append((bugs_repo / "projects" / apj / "bugs" / aid / "bug_patch.txt").read_text(errors="replace"))

        client = provider_client()
        for arm in ARMS:
            # Same compiled buggy checkout, reset production source after prior arm.
            reset = docker_exec(container, f"cd {work_container} && git reset --hard HEAD", timeout=120)
            if reset.returncode != 0:
                raise RuntimeError("git reset failed between arms\n" + reset.stdout)

            memory, activation = arm_memory(arm, capabilities, acquisition_diffs, context)
            prompt = proposal_prompt(context, memory)
            calls = []
            applied = False
            patch_sha = None
            edit_records = None
            mechanical_error = None
            for call_index in range(MAX_CALLS):
                call_prompt = prompt if call_index == 0 else retry_prompt(prompt, calls[-1]["text"], mechanical_error or "unknown mechanical error")
                raw_text, latency_ms = sample(client, call_prompt, seed)
                call_rec = {"index": call_index + 1, "text": raw_text, "sha256": sha256_text(raw_text), "latency_ms": latency_ms}
                calls.append(call_rec)
                try:
                    proposal = parse_first_json_object(raw_text)
                    edit_records, patch_sha = validate_and_apply(proposal, work)
                    applied = True
                    mechanical_error = None
                    break
                except Exception as exc:
                    # Restore source before optional formatting/application retry.
                    docker_exec(container, f"cd {work_container} && git reset --hard HEAD", timeout=120)
                    mechanical_error = f"{type(exc).__name__}: {exc}"

            if applied:
                passed, verifier_log = native_test(container, work_container)
                verifier_ran = True
                terminal = "PASS" if passed else "FAIL"
                verifier_sha = sha256_text(verifier_log)
                (out / f"{arm}_NATIVE_VERIFIER.log").write_text(verifier_log)
            else:
                passed = None
                verifier_ran = False
                terminal = "FAIL"
                verifier_sha = None

            # Do not persist full protected source. Persist hashes/proposals/results.
            clean_calls = [{k: v for k, v in c.items() if k != "text"} | {"response": c["text"]} for c in calls]
            result = {
                "protocol": PROTOCOL,
                "case": args.case,
                "arm": arm,
                "model": MODEL_LABEL,
                "seed": seed,
                "input_sha256": input_sha,
                "capability_sha256": None if arm in {"COLD", "RAW_MEMORY"} else capability_sha,
                "runtime_source_sha256": runtime_sha,
                "calls": clean_calls,
                "activation": activation,
                "verifier": {"consulted": verifier_ran, "decision": terminal if verifier_ran else None},
                "patch_sha256": patch_sha,
                "edits": edit_records,
                "native_verifier": {"ran": verifier_ran, "passed": passed, "log_sha256": verifier_sha},
                "terminal_status": terminal,
                "mechanical_error": mechanical_error,
                "included_production_files": included_files,
                "baseline_failing_verifier_sha256": sha256_text(baseline_log),
            }
            (out / f"{arm}.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            results.append(result)

        summary = {
            "protocol": PROTOCOL,
            "case": args.case,
            "seed": seed,
            "input_sha256": input_sha,
            "capability_sha256": capability_sha,
            "runtime_source_sha256": runtime_sha,
            "arms": {r["arm"]: r["terminal_status"] for r in results},
            "verified_activated_ids": next((r["activation"].get("activated_ids", []) for r in results if r["arm"] == "VERIFIED"), []),
            "status": "COMPLETE",
        }
    except Exception as exc:
        summary = {
            "protocol": PROTOCOL,
            "case": args.case,
            "status": "INFRASTRUCTURE_FAILURE",
            "error": f"{type(exc).__name__}: {exc}",
            "capability_sha256": capability_sha,
            "runtime_source_sha256": runtime_sha,
        }
    finally:
        run(["docker", "rm", "-f", container], timeout=120)
        shutil.rmtree(root, ignore_errors=True)
        (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
