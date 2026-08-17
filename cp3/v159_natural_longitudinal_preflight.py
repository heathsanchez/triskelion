from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from developmental_runtime import Decision, DevelopmentalState, EvidenceRef

import v145_natural_third_rung_causal as v145


STREAM = [("httpie", 5), ("youtube-dl", 32), ("pandas", 66)]
PROTOCOL = "protocols/V159_NATURAL_LONGITUDINAL_DEVELOPMENT_PRECOMMIT.md"


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head(repo: Path) -> str:
    return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()


def evidence(name: str, artifact: str, digest: str) -> EvidenceRef:
    return EvidenceRef(
        verifier="v159-apparatus-preflight",
        decision=Decision.VERIFIED,
        artifact=artifact,
        digest=digest,
        scope="apparatus-only",
        metadata={"scientific_outcome": False},
    )


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    if args.out.exists():
        raise SystemExit("output directory exists; refusing to overwrite frozen preflight")
    args.out.mkdir(parents=True)

    protocol_path = Path(PROTOCOL)
    corpus_head = git_head(args.bugsinpy)
    protocol_sha = sha_file(protocol_path)

    state = DevelopmentalState()
    state.set_verifier_config(
        "bugsinpy-native-exact-runtime-v1",
        {
            "adapter": "cp3.bugsinpy_exact_runtime.native_test",
            "corpus": "soarsmu/BugsInPy",
            "corpus_head": corpus_head,
            "terminal": "native test suite pass",
        },
        evidence("verifier", f"git://soarsmu/BugsInPy@{corpus_head}", corpus_head),
    )
    state.set_discovery_policy(
        "v159-closure-first",
        {
            "task_order": [f"{p}/{b}" for p, b in STREAM],
            "closure_before_invention": True,
            "max_model_calls_per_task": 2,
            "prospective_first_qualifying_ancestor": True,
            "protocol_sha256": protocol_sha,
        },
        evidence("policy", PROTOCOL, protocol_sha),
    )

    tasks: dict[str, Any] = {}
    for project, bug_id in STREAM:
        key = f"{project}/{bug_id}"
        task = v145.prepare_visible_task(args.bugsinpy, project, bug_id)
        tasks[key] = {k: v for k, v in task.items() if k != "visible_prompt"}

    ready = all(row.get("status") == "READY" for row in tasks.values())
    source_distinct = len({p for p, _ in STREAM}) == len(STREAM)
    exact_runtime = all(
        row.get("baseline", {}).get("python_image")
        and row.get("baseline", {}).get("infrastructure_error") is None
        for row in tasks.values()
    )
    baselines_fail = all(not row.get("baseline", {}).get("passed", True) for row in tasks.values())

    snapshot = state.snapshot()
    replayed = DevelopmentalState.replay(snapshot["events"])
    restart_exact = replayed.state_hash() == state.state_hash()

    result = {
        "canonical_id": "V159_NATURAL_LONGITUDINAL_PREFLIGHT",
        "scientific_outcome": False,
        "protocol": PROTOCOL,
        "protocol_sha256": protocol_sha,
        "bugsinpy_head": corpus_head,
        "stream": [f"{p}/{b}" for p, b in STREAM],
        "tasks": tasks,
        "apparatus": {
            "all_tasks_ready": ready,
            "source_distinct": source_distinct,
            "exact_runtime_resolved": exact_runtime,
            "buggy_baselines_fail": baselines_fail,
            "event_chain_valid": state.verify_event_chain(),
            "restart_exact": restart_exact,
        },
    }
    result["pass"] = all(result["apparatus"].values())
    result["verdict"] = "PASS_V159_APPARATUS_PREFLIGHT" if result["pass"] else "OBSTRUCTED_V159_APPARATUS_PREFLIGHT"

    (args.out / "V159_PREFLIGHT_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (args.out / "V159_INITIAL_STATE.json").write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
