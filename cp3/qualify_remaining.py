#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

EXPECTED_PROJECTS = [
    "pandas", "youtube-dl", "httpie", "PySnooper", "cookiecutter",
    "ansible", "spacy", "sanic", "keras", "matplotlib", "thefuck",
    "black", "scrapy", "luigi", "fastapi", "tornado", "tqdm",
]
EXPECTED_BUG_COUNT = 501
EXPECTED_CORPUS_LOCK = "760b73f87bbe79b76c970c1b2ac4cdd83e5eb18ee3f4b9f2304a915fddbbd5ad"
ALLOWED_REMAINING = {"pandas", "scrapy", "luigi"}


def run(cmd, *, cwd=None, check=False, timeout=None):
    p = subprocess.run(
        cmd, cwd=cwd, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=timeout
    )
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}\n{p.stdout}")
    return p


def candidate_rank(project: str, bug_id: int) -> str:
    # Frozen CP3 merger treated rank as a hexadecimal ordering key.
    # Preserve the original SHA256(project/id) lexical-hex ordering.
    return hashlib.sha256(f"{project}/{bug_id}".encode()).hexdigest()


def enumerate_manifest(repo: Path):
    manifest = []
    projects_dir = repo / "projects"
    for project in EXPECTED_PROJECTS:
        bugs_dir = projects_dir / project / "bugs"
        if not bugs_dir.is_dir():
            raise RuntimeError(f"missing frozen project: {project}")
        for p in bugs_dir.iterdir():
            if p.is_dir() and p.name.isdigit():
                manifest.append((project, int(p.name)))
    manifest.sort(key=lambda x: (EXPECTED_PROJECTS.index(x[0]), candidate_rank(x[0], x[1])))
    return manifest


def canonical_manifest_hash(manifest):
    # Recorded for provenance. The historical corpus lock's serializer is not
    # reconstructed here, so the frozen lock itself remains authoritative.
    payload = "\n".join(f"{p}/{i}" for p, i in manifest) + "\n"
    return hashlib.sha256(payload.encode()).hexdigest()


def docker_ready(repo: Path, name: str):
    run(["docker", "rm", "-f", name])
    build = run(["docker", "build", "-t", "cp3-bugsinpy", "."], cwd=repo, timeout=1800)
    if build.returncode != 0:
        raise RuntimeError("BugsInPy Docker build failed\n" + build.stdout[-12000:])
    framework = str((repo / "framework").resolve())
    projects = str((repo / "projects").resolve())
    workspace = str((repo / "workspace").resolve())
    Path(workspace).mkdir(parents=True, exist_ok=True)
    start = run([
        "docker", "run", "-d", "--name", name,
        "-v", f"{framework}:/home/bugsinpy/framework",
        "-v", f"{projects}:/home/bugsinpy/projects",
        "-v", f"{workspace}:/home/workspace",
        "cp3-bugsinpy", "bash", "-lc", "sleep infinity",
    ])
    if start.returncode != 0:
        raise RuntimeError("BugsInPy container start failed\n" + start.stdout)
    probe = run([
        "docker", "exec", name, "bash", "-lc",
        "export PATH=$PATH:/home/bugsinpy/framework/bin; command -v bugsinpy-testall || true"
    ])
    if "bugsinpy-testall" not in probe.stdout:
        raise RuntimeError("current BugsInPy image does not expose bugsinpy-testall")


def classify_index(index_path: Path, project: str, bug_id: int):
    if not index_path.exists():
        return None, "no_index"
    rows = []
    with index_path.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if row.get("repo") == project and row.get("bugid") == str(bug_id):
                rows.append(row)
    by_ver = {r.get("version"): r.get("result") for r in rows}
    if by_ver.get("buggy") == "fail" and by_ver.get("fixed") == "pass":
        return True, "fixed_pass_buggy_fail"
    if by_ver.get("fixed") == "pass" and by_ver.get("buggy") not in {None, "fail"}:
        return False, f"semantic_nonqualification:{by_ver}"
    return None, f"infrastructure_or_reproduction_negative:{by_ver}"


def qualify_one(container: str, repo: Path, project: str, bug_id: int, timeout: int):
    index = repo / "projects" / "bugsinpy-index.csv"
    if index.exists():
        index.unlink()
    temp_dir = repo / "temp" / "projects"
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
    cmd = [
        "docker", "exec", container, "bash", "-lc",
        "export PATH=$PATH:/home/bugsinpy/framework/bin; "
        "rm -f /home/bugsinpy/projects/bugsinpy-index.csv; "
        f"bugsinpy-testall -p {project}:{bug_id}"
    ]
    t0 = time.time()
    try:
        p = run(cmd, timeout=timeout)
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        p = None
        timed_out = True
        output = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
    elapsed = time.time() - t0
    q, reason = classify_index(index, project, bug_id)
    if timed_out:
        q, reason = None, "infrastructure_timeout"
    return {
        "project": project,
        "bug_id": bug_id,
        "rank": candidate_rank(project, bug_id),
        "qualified": q,
        "reason": reason,
        "elapsed_seconds": round(elapsed, 3),
        "returncode": None if p is None else p.returncode,
        "log_tail": (output if timed_out else p.stdout)[-12000:],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, choices=sorted(ALLOWED_REMAINING))
    ap.add_argument("--out", required=True)
    ap.add_argument("--candidate-timeout", type=int, default=3600)
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cp3_qualify_") as td:
        root = Path(td)
        repo = root / "BugsInPy"
        clone = run(["git", "clone", "--depth", "1", "https://github.com/soarsmu/BugsInPy.git", str(repo)], timeout=600)
        if clone.returncode != 0:
            raise RuntimeError("BugsInPy clone failed\n" + clone.stdout)

        head = run(["git", "rev-parse", "HEAD"], cwd=repo, check=True).stdout.strip()
        manifest = enumerate_manifest(repo)
        count_ok = len(manifest) == EXPECTED_BUG_COUNT
        project_set_ok = sorted({p for p, _ in manifest}) == sorted(EXPECTED_PROJECTS)
        if not count_ok or not project_set_ok:
            result = {
                "status": "CORPUS_MISMATCH",
                "expected_bug_count": EXPECTED_BUG_COUNT,
                "observed_bug_count": len(manifest),
                "expected_corpus_lock": EXPECTED_CORPUS_LOCK,
                "observed_manifest_sha256": canonical_manifest_hash(manifest),
                "bugsinpy_head": head,
            }
            out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            raise SystemExit(2)

        ids = [i for p, i in manifest if p == args.project]
        ids.sort(key=lambda i: candidate_rank(args.project, i))
        container = f"cp3-{args.project.lower().replace('_','-')}-{os.getpid()}"
        attempts = []
        selected = None
        try:
            docker_ready(repo, container)
            for bug_id in ids:
                rec = qualify_one(container, repo, args.project, bug_id, args.candidate_timeout)
                attempts.append(rec)
                print(json.dumps({k: rec[k] for k in ["project","bug_id","rank","qualified","reason","elapsed_seconds"]}), flush=True)
                if rec["qualified"] is True:
                    selected = f"{args.project}/{bug_id}"
                    break
        finally:
            run(["docker", "rm", "-f", container])

        result = {
            "status": "QUALIFIED" if selected else "EXHAUSTED",
            "project": args.project,
            "selected": selected,
            "attempts": attempts,
            "candidate_order": "SHA256(project/id) lexical hexadecimal ascending",
            "admission": "fixed_pass_and_buggy_fail",
            "semantic_skipping": False,
            "expected_corpus_lock": EXPECTED_CORPUS_LOCK,
            "observed_manifest_sha256": canonical_manifest_hash(manifest),
            "observed_bug_count": len(manifest),
            "bugsinpy_head": head,
        }
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": result["status"], "project": args.project, "selected": selected, "attempt_count": len(attempts)}, indent=2))


if __name__ == "__main__":
    main()
