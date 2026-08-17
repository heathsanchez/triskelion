#!/usr/bin/env python3
"""Evidence-only recovery crawler for lost V134–V144 primary artifacts.

This script DOES NOT run scientific experiments. It queries this repository's
GitHub Actions archive for 2026-08-16, enumerates workflow runs/artifacts, and
records any run/artifact metadata whose names, branch names, display titles,
or artifact file names mention V134..V144 (case-insensitive). It may download
existing artifact ZIPs to inspect filenames/text metadata only.

Usage in Actions requires GITHUB_TOKEN and GITHUB_REPOSITORY.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path

import requests

REPO = os.environ.get("GITHUB_REPOSITORY", "heathsanchez/triskelion")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = Path(os.environ.get("RECOVERY_OUT", "recovered_v134_v144"))
TARGET_RE = re.compile(r"(?i)\bv1(?:3[4-9]|4[0-4])\b|v1(?:3[4-9]|4[0-4])[_-]")
TEXT_EXTS = {".json", ".md", ".txt", ".csv", ".log", ".yml", ".yaml"}

session = requests.Session()
session.headers.update({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
if TOKEN:
    session.headers["Authorization"] = f"Bearer {TOKEN}"


def api(path: str, **params):
    url = f"https://api.github.com/repos/{REPO}/{path.lstrip('/')}"
    r = session.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def text_hit(*parts) -> bool:
    return bool(TARGET_RE.search(" ".join(str(p or "") for p in parts)))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ledger = {
        "purpose": "recover existing V134-V144 primary evidence only; no scientific rerun",
        "repository": REPO,
        "created_filter": "2026-08-16",
        "runs_scanned": 0,
        "artifact_records_scanned": 0,
        "candidate_runs": [],
        "candidate_artifacts": [],
        "candidate_files": [],
        "errors": [],
    }

    runs = api("actions/runs", created="2026-08-16", per_page=100).get("workflow_runs", [])
    ledger["runs_scanned"] = len(runs)

    for run in runs:
        rid = run["id"]
        run_fields = [run.get("name"), run.get("head_branch"), run.get("display_title"), run.get("path"), (run.get("head_commit") or {}).get("message")]
        if text_hit(*run_fields):
            ledger["candidate_runs"].append({k: run.get(k) for k in ["id", "name", "head_branch", "head_sha", "path", "display_title", "status", "conclusion", "created_at", "html_url"]})

        try:
            arts = api(f"actions/runs/{rid}/artifacts", per_page=100).get("artifacts", [])
        except Exception as e:
            ledger["errors"].append({"run_id": rid, "stage": "list_artifacts", "error": repr(e)})
            continue
        ledger["artifact_records_scanned"] += len(arts)

        for art in arts:
            aname = art.get("name", "")
            candidate_by_name = text_hit(*run_fields, aname)
            # Inspect every surviving artifact filename because old workflows may have generic names.
            try:
                url = f"https://api.github.com/repos/{REPO}/actions/artifacts/{art['id']}/zip"
                rr = session.get(url, timeout=120)
                rr.raise_for_status()
                z = zipfile.ZipFile(io.BytesIO(rr.content))
                names = z.namelist()
            except Exception as e:
                ledger["errors"].append({"run_id": rid, "artifact_id": art.get("id"), "stage": "download_or_zip", "error": repr(e)})
                continue

            name_hits = [n for n in names if text_hit(n)]
            if candidate_by_name or name_hits:
                ledger["candidate_artifacts"].append({
                    "run_id": rid,
                    "run_name": run.get("name"),
                    "head_branch": run.get("head_branch"),
                    "head_sha": run.get("head_sha"),
                    "artifact_id": art.get("id"),
                    "artifact_name": aname,
                    "files": names,
                    "filename_hits": name_hits,
                })

            # Search text files for explicit V134..V144 markers without interpreting semantics.
            for n in names:
                suffix = Path(n).suffix.lower()
                if suffix not in TEXT_EXTS:
                    continue
                try:
                    raw = z.read(n)
                    txt = raw.decode("utf-8", errors="replace")
                except Exception:
                    continue
                if TARGET_RE.search(txt) or text_hit(n):
                    dest = OUT / f"run_{rid}" / f"artifact_{art['id']}" / n
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(raw)
                    ledger["candidate_files"].append({
                        "run_id": rid,
                        "run_name": run.get("name"),
                        "head_branch": run.get("head_branch"),
                        "head_sha": run.get("head_sha"),
                        "artifact_id": art.get("id"),
                        "artifact_name": aname,
                        "path": n,
                        "saved_path": str(dest),
                    })

    (OUT / "RECOVERY_LEDGER.json").write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "runs_scanned": ledger["runs_scanned"],
        "artifact_records_scanned": ledger["artifact_records_scanned"],
        "candidate_runs": len(ledger["candidate_runs"]),
        "candidate_artifacts": len(ledger["candidate_artifacts"]),
        "candidate_files": len(ledger["candidate_files"]),
        "errors": len(ledger["errors"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
