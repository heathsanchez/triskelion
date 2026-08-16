#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import v154_persistent_workspace_developmental_separator as prev

exp = prev.exp
base = prev.base
exact_runtime = prev.exact_runtime
sed = prev.sed
sha_text = prev.sha_text
CRITICAL_ARMS = ("D_COLD", "D_PLUS_RAW_T1", "D_PLUS_SHAM_RAW")
WINDOW = 40


def snapshot(work: Path, payload: str) -> tuple[str, dict[str, str]]:
    blocks: list[str] = []
    hashes: dict[str, str] = {}
    for rel in sed.changed_files(payload):
        p = work / rel
        raw = p.read_bytes()
        hashes[rel] = hashlib.sha256(raw).hexdigest()
        lines = raw.decode("utf-8").splitlines()
        cp = subprocess.run(["git", "diff", "--unified=0", "--", rel], cwd=work,
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        if cp.returncode:
            raise RuntimeError(f"git diff failed for {rel}: {cp.stderr[-500:]}")
        spans = []
        for m in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", cp.stdout, re.MULTILINE):
            start, count = int(m.group(1)), int(m.group(2) or "1")
            anchor = max(1, start)
            spans.append([max(1, anchor-WINDOW),
                          min(len(lines), anchor+max(count, 1)-1+WINDOW)])
        if not spans:
            raise RuntimeError(f"no current-side hunk for {rel}")
        spans.sort()
        merged = []
        for lo, hi in spans:
            if not merged or lo > merged[-1][1] + 1:
                merged.append([lo, hi])
            else:
                merged[-1][1] = max(merged[-1][1], hi)
        blocks.append(f"FILE {rel} CURRENT_SHA256 {hashes[rel]}")
        for lo, hi in merged:
            blocks.append(f"CURRENT LINES {lo}-{hi}")
            blocks.extend(f"{n:05d}: {lines[n-1]}" for n in range(lo, hi+1))
    if not blocks:
        raise RuntimeError("empty source snapshot")
    return "\n".join(blocks), hashes


class WrappedResponse:
    def __init__(self, inner, audit: dict[str, Any]):
        self._inner = inner
        self._audit = audit

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def to_dict(self):
        d = self._inner.to_dict()
        d["v155_source_sync"] = self._audit
        return d


def run_seed_arm_synced(provider, bugsinpy: Path, task: dict[str, Any],
                        arm: str, seed: int, memory: str) -> dict[str, Any]:
    state: dict[str, Any] = {"apply_count": 0, "failed_call1": False}
    orig_apply = sed.apply_edits
    orig_test = exact_runtime.native_test

    def apply_wrap(work: Path, payload: str):
        out = orig_apply(work, payload)
        state["apply_count"] += 1
        if state["apply_count"] == 1:
            state["work"] = work
            state["payload"] = payload
        return out

    def test_wrap(bugsinpy_arg: Path, work: Path):
        v = orig_test(bugsinpy_arg, work)
        if state.get("apply_count") == 1 and not v.get("passed") and not v.get("infrastructure_error"):
            state["failed_call1"] = True
        return v

    class ProviderProxy:
        def sample(self, prompt: str, *args, **kwargs):
            actual = prompt
            audit: dict[str, Any] = {"injected": False}
            if state.get("failed_call1"):
                try:
                    src, hashes = snapshot(state["work"], state["payload"])
                except Exception as exc:
                    raise RuntimeError(f"V155_SOURCE_SNAPSHOT: {exc.__class__.__name__}: {exc}")
                actual = (
                    prompt +
                    "\n\nCURRENT POST-CALL-1 SOURCE STATE:\n" + src +
                    "\n\nYour next edit will be applied to the CURRENT post-call-1 source above, not the original source. "
                    "Every `old` field must occur exactly once in that CURRENT source. "
                    "Ground all three rival edits only in this current source."
                )
                audit = {
                    "injected": True,
                    "pre_sync_prompt_sha256": sha_text(prompt),
                    "actual_prompt_sha256": sha_text(actual),
                    "snapshot_sha256": sha_text(src),
                    "snapshot_chars": len(src),
                    "current_file_sha256": hashes,
                }
                state["failed_call1"] = False
            return WrappedResponse(provider.sample(actual, *args, **kwargs), audit)

    sed.apply_edits = apply_wrap
    exact_runtime.native_test = test_wrap
    try:
        return prev.run_seed_arm_persistent(ProviderProxy(), bugsinpy, task, arm, seed, memory)
    finally:
        sed.apply_edits = orig_apply
        exact_runtime.native_test = orig_test


def postprocess(out: Path) -> None:
    prev.postprocess(out)
    r = json.loads((out / "V154_RESULT.json").read_text())
    r["canonical_id"] = "V155_SOURCE_STATE_SYNCHRONIZATION_SEPARATOR"
    r["protocol"] = "protocols/V155_SOURCE_STATE_SYNCHRONIZATION_SEPARATOR_PRECOMMIT.md"

    snapshot_failures = 0
    reach: dict[str, int] = {}
    injected: dict[str, int] = {}
    for arm, rows in r.get("rows", {}).items():
        reach[arm] = 0
        injected[arm] = 0
        for rr in rows:
            if "V155_SOURCE_SNAPSHOT" in str(rr.get("reason", "")):
                snapshot_failures += 1
            for a in rr.get("attempts", []):
                if a.get("call") != 2:
                    continue
                sync = (a.get("response") or {}).get("v155_source_sync") or {}
                if sync.get("injected"):
                    injected[arm] += 1
                if a.get("selected_rank") is not None and isinstance(a.get("verdict"), dict):
                    reach[arm] += 1
                break

    sync_gate = all(reach.get(a, 0) >= 2 for a in CRITICAL_ARMS)
    comparable = all(v.get("n_comparable") == len(exp.SEEDS)
                     for v in r.get("summary", {}).values())
    positive = {"REACHABILITY", "EFFICIENCY"}
    raw_pos = r.get("raw_t1_advantage") in positive
    compiled_pos = r.get("compiled_o1_advantage") in positive

    if snapshot_failures:
        verdict = "R10_INCONCLUSIVE_V155_SOURCE_SNAPSHOT"
    elif not comparable:
        verdict = "R10_INCONCLUSIVE_V155"
    elif not sync_gate:
        verdict = "OBSTRUCTED_V155_SOURCE_SYNC_DID_NOT_RESTORE_EXECUTION"
    elif raw_pos and compiled_pos:
        verdict = "PASS_V155_BOTH_REPRESENTATIONS_SIGNAL_AFTER_SOURCE_SYNC"
    elif compiled_pos:
        verdict = "PASS_V155_COMPILED_O1_SIGNAL_AFTER_SOURCE_SYNC"
    elif raw_pos:
        verdict = "PASS_V155_RAW_T1_SIGNAL_AFTER_SOURCE_SYNC"
    else:
        verdict = "NEGATIVE_V155_NO_T1_DEVELOPMENTAL_SIGNAL_AFTER_SOURCE_SYNC"

    r["source_sync_audit"] = {
        "critical_arms": list(CRITICAL_ARMS),
        "required_reaching_verifier_per_critical_arm": 2,
        "call2_sync_prompt_injected": injected,
        "call2_selected_reaching_verifier": reach,
        "source_snapshot_failures": snapshot_failures,
        "sync_gate": sync_gate,
        "note": "V154 prompt_sha256 remains the pre-sync prompt hash; response.v155_source_sync.actual_prompt_sha256 is the executed call-2 prompt hash.",
    }
    r["verdict"] = verdict
    (out / "V155_RESULT.json").write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "compiled_o1_advantage": r.get("compiled_o1_advantage"),
        "raw_t1_advantage": r.get("raw_t1_advantage"),
        "source_sync_audit": r["source_sync_audit"],
        "summary": r.get("summary"),
    }, indent=2, sort_keys=True))


def main() -> None:
    exp.run_seed_arm = run_seed_arm_synced
    exp.main()
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--out", type=Path, required=True)
    args, _ = ap.parse_known_args()
    postprocess(args.out)


if __name__ == "__main__":
    main()
