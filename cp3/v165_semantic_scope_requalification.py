#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import v159_safe_persistent_runner as runner

PROTOCOL = "protocols/V165_SEMANTIC_SCOPE_REQUALIFICATION_PRECOMMIT.md"
FROZEN_MATRIX = "cp3/FROZEN_EVAL_MATRIX.json"

# Frozen directly from the capability's preconditions/applicability language.
# All three families are required. `re.` alone is explicitly insufficient.
STRUCTURED = re.compile(r"\b(pars(?:e|er|ing)|extract(?:ion|ing)?|structured|json(?:p)?|key[-_ ]?value|cli arguments?|string splitting)\b", re.I)
SEPARATOR = re.compile(r"\b(separator|delimiter|split(?:ting)?|key[-_ ]?value boundar(?:y|ies)|separator matching)\b", re.I)
PROTECTION = re.compile(r"\b(escap(?:e|ed|ing)|backslash|quoted?|protected syntax|premature split(?:ting)?)\b", re.I)


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def snippets(text: str, rx: re.Pattern[str], radius: int = 180) -> list[str]:
    out: list[str] = []
    for m in rx.finditer(text):
        lo, hi = max(0, m.start() - radius), min(len(text), m.end() + radius)
        s = " ".join(text[lo:hi].split())
        if s not in out:
            out.append(s)
        if len(out) >= 4:
            break
    return out


def semantic_evidence(task: dict[str, Any]) -> dict[str, Any]:
    baseline = task.get("baseline", {}).get("test_output", "")
    context = task.get("context", "")
    visible = baseline + "\n\n" + context
    structured = bool(STRUCTURED.search(visible))
    separator = bool(SEPARATOR.search(visible))
    protection = bool(PROTECTION.search(visible))
    return {
        "structured_parsing": structured,
        "separator_operation": separator,
        "escape_or_protection": protection,
        "semantically_eligible": structured and separator and protection,
        "visible_evidence_sha256": sha_text(visible),
        "structured_snippets": snippets(visible, STRUCTURED),
        "separator_snippets": snippets(visible, SEPARATOR),
        "protection_snippets": snippets(visible, PROTECTION),
    }


def frozen_cases() -> list[tuple[str, int]]:
    matrix = json.loads(Path(FROZEN_MATRIX).read_text())
    out: list[tuple[str, int]] = []
    for cell in matrix["cells"]:
        case = cell["case"]
        project, bug = case.rsplit("/", 1)
        pair = (project, int(bug))
        if pair not in out:
            out.append(pair)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("output exists; refusing overwrite")
    args.out.mkdir(parents=True)

    rows: list[dict[str, Any]] = []
    eligible: list[str] = []
    for project, bug_id in frozen_cases():
        case = f"{project}/{bug_id}"
        task = runner.prepare_task(args.bugsinpy, project, bug_id)
        row: dict[str, Any] = {"case": case, "task_status": task.get("status")}
        if task.get("status") == "READY":
            row.update(semantic_evidence(task))
            row["failure_class"] = task.get("failure_class")
            row["context_files"] = task.get("context_files")
            row["context_sha256"] = task.get("context_sha256")
            if row["semantically_eligible"]:
                eligible.append(case)
        else:
            row["reason"] = task.get("reason")
        rows.append(row)

    verdict = "PASS_V165_LAWFUL_NATURAL_SCOPE_FRONTIER_EXISTS" if eligible else "OBSTRUCTED_V165_NO_LAWFUL_NATURAL_SCOPE_FRONTIER"
    result = {
        "canonical_id": "V165_SEMANTIC_SCOPE_REQUALIFICATION",
        "phase": "A_ZERO_MODEL_CENSUS",
        "protocol": PROTOCOL,
        "matrix": FROZEN_MATRIX,
        "matrix_sha256": sha_text(Path(FROZEN_MATRIX).read_text()),
        "model_calls": 0,
        "frozen_case_order": [f"{p}/{b}" for p,b in frozen_cases()],
        "eligible_cases": eligible,
        "selected_case_if_any": eligible[0] if eligible else None,
        "rows": rows,
        "verdict": verdict,
        "scientific_outcome": "PASS" if verdict.startswith("PASS_") else "OBSTRUCTED",
    }
    args.out.joinpath("V165_SCOPE_CENSUS.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": verdict, "eligible_cases": eligible, "rows": rows}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
