#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import bugsinpy_four_arm as base
import bugsinpy_exact_runtime as exact_runtime
import structured_edit_protocol_v2 as sed

TASK_PROJECT = "thefuck"
TASK_BUG = 32

FIRST = json.dumps({"edits":[{"path":"thefuck/rules/ls_lah.py","old":"def match(command, settings):\n    return 'ls' in command.script","new":"def match(command, settings):\n    return 'ls' in command.script and '-lah' not in command.script"}]}, separators=(",", ":"))
RIGHT = json.dumps({"edits":[{"path":"thefuck/rules/ls_lah.py","old":"def match(command, settings):\n    return 'ls' in command.script and '-lah' not in command.script","new":"def match(command, settings):\n    return command.script.startswith('ls ') and '-lah' not in command.script"}]}, separators=(",", ":"))
WRONG = json.dumps({"edits":[{"path":"thefuck/rules/ls_lah.py","old":"def match(command, settings):\n    return 'ls' in command.script and '-lah' not in command.script","new":"def match(command, settings):\n    return 'ls' in command.script and '-lah' not in command.script and 'pacman' not in command.script"}]}, separators=(",", ":"))

base.native_test = exact_runtime.native_test


def replay(bugsinpy: Path, second: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="v161a-") as td:
        work = base.checkout_buggy(bugsinpy, TASK_PROJECT, TASK_BUG, Path(td))
        baseline = exact_runtime.native_test(bugsinpy, work)
        if baseline.get("infrastructure_error") or baseline.get("passed"):
            return {"status":"R10","stage":"baseline","baseline":baseline}
        try:
            sed.apply_edits(work, FIRST)
        except Exception as exc:
            return {"status":"R10","stage":"first_apply","error":f"{type(exc).__name__}: {exc}"}
        first_verdict = exact_runtime.native_test(bugsinpy, work)
        if first_verdict.get("infrastructure_error"):
            return {"status":"R10","stage":"first_verify","first_verdict":first_verdict}
        try:
            sed.apply_edits(work, second)
            second_applied = True
            apply_error = None
        except Exception as exc:
            second_applied = False
            apply_error = f"{type(exc).__name__}: {exc}"
        if not second_applied:
            return {
                "status":"OK",
                "first_verdict":first_verdict,
                "second_applied":False,
                "second_apply_error":apply_error,
                "second_verdict":None,
            }
        second_verdict = exact_runtime.native_test(bugsinpy, work)
        return {
            "status":"R10" if second_verdict.get("infrastructure_error") else "OK",
            "first_verdict":first_verdict,
            "second_applied":True,
            "second_apply_error":None,
            "second_verdict":second_verdict,
        }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    right = replay(args.bugsinpy, RIGHT)
    wrong = replay(args.bugsinpy, WRONG)

    if right.get("status") == "R10":
        verdict = "R10_V161A_REPLAY_INVALID"
    elif not right.get("second_applied"):
        verdict = "DIAGNOSTIC_V161_BINDING_CANDIDATE_UNGROUNDED"
    elif (right.get("second_verdict") or {}).get("passed"):
        verdict = "DIAGNOSTIC_V161_STATE_ALIGNED_RIGHT_BIND_VERIFIED"
    else:
        verdict = "DIAGNOSTIC_V161_STATE_ALIGNMENT_CONFIRMED"

    result = {
        "canonical_id":"V161A_STATE_ALIGNED_BINDING_REPLAY",
        "task":"thefuck/32",
        "model_calls":0,
        "right":right,
        "wrong":wrong,
        "verdict":verdict,
    }
    args.out.joinpath("V161A_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
