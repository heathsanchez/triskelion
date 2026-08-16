#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import v156_format_matched_raw_t1_semantic_separator as v156

v155 = v156.v155
exp = v156.exp
SEEDS = exp.SEEDS
MODEL = exp.MODEL
MAX_TOKENS = exp.MAX_TOKENS
PREFIX = "RETAINED VERIFIED ACQUISITION TRACE:\n"


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def prf_letter(ch: str, tag: str, i: int) -> str:
    h = hashlib.sha256(f"V157|{tag}|{i}|{ord(ch)}".encode()).digest()[0]
    alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if ch.isupper() else "abcdefghijklmnopqrstuvwxyz"
    return alpha[h % 26]


def opaque_string(s: str, tag: str) -> str:
    out = []
    for i, ch in enumerate(s):
        if ch.isascii() and ch.isalpha():
            out.append(prf_letter(ch, tag, i))
        else:
            out.append(ch)
    return "".join(out)


def opaque_obj(x: Any, path: str = "$" ) -> Any:
    if isinstance(x, str):
        return opaque_string(x, path)
    if isinstance(x, list):
        return [opaque_obj(v, f"{path}[{i}]") for i, v in enumerate(x)]
    if isinstance(x, dict):
        # Preserve the exact ordering used by json.dumps(..., sort_keys=True) on the source object.
        out = {}
        for i, key in enumerate(sorted(x.keys())):
            new_key = opaque_string(str(key), f"{path}.key[{i}]")
            out[new_key] = opaque_obj(x[key], f"{path}.{key}")
        return out
    return x


def make_memories(t1: dict[str, Any]) -> tuple[str, str, str, dict[str, Any]]:
    raw, evidence = exp.raw_t1_memory(t1)
    matched_evidence = v156.scrub_value(evidence)
    labelled = PREFIX + json.dumps(matched_evidence, sort_keys=True)

    opaque_evidence = opaque_obj(matched_evidence)
    opaque_prefix = opaque_string(PREFIX, "prefix")
    opaque = opaque_prefix + json.dumps(opaque_evidence, sort_keys=False)

    # Opaque prefix has identical punctuation/newline positions; transformed evidence preserves
    # key/value lengths and insertion order, so total serialized length must be identical.
    construction = {
        "raw_chars": len(raw),
        "labelled_chars": len(labelled),
        "opaque_chars": len(opaque),
        "raw_sha256": sha_text(raw),
        "labelled_sha256": sha_text(labelled),
        "opaque_sha256": sha_text(opaque),
        "labelled_json_parses": False,
        "opaque_json_parses": False,
        "same_length": len(labelled) == len(opaque),
    }
    try:
        json.loads(labelled.split("\n", 1)[1])
        construction["labelled_json_parses"] = True
    except Exception:
        pass
    try:
        json.loads(opaque.split("\n", 1)[1])
        construction["opaque_json_parses"] = True
    except Exception:
        pass
    return raw, labelled, opaque, construction


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("output directory exists; refusing to overwrite evidence")
    args.out.mkdir(parents=True)

    result: dict[str, Any] = {
        "canonical_id": "V157_OPAQUE_ENVELOPE_LABEL_SEMANTICS_SEPARATOR",
        "protocol": "protocols/V157_OPAQUE_ENVELOPE_LABEL_SEMANTICS_SEPARATOR_PRECOMMIT.md",
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "max_calls": exp.MAX_CALLS,
        "seeds": SEEDS,
        "T1": "httpie/5",
        "T2": "youtube-dl/32",
    }

    try:
        exp.verify_o1_identity()
        t1 = exp.v145.verify_acquisition_intervention(args.bugsinpy, *exp.T1)
        if t1.get("status") != "VERIFIED" or t1.get("diff_sha256") != exp.EXPECTED_T1_DIFF_SHA256:
            raise RuntimeError("T1 intervention identity/replay mismatch")
        task = exp.prepare_t2(args.bugsinpy)
        if task.get("status") != "READY":
            raise RuntimeError(f"T2 not READY: {task.get('status')}")
        _raw, labelled, opaque, construction = make_memories(t1)
        result["control_construction"] = construction
        construction_ok = (
            construction["same_length"]
            and construction["labelled_json_parses"]
            and construction["opaque_json_parses"]
        )
        if not construction_ok:
            result["verdict"] = "R10_INCONCLUSIVE_V157_CONTROL_CONSTRUCTION"
            args.out.joinpath("V157_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            print(json.dumps(result, indent=2, sort_keys=True))
            return
    except Exception as exc:
        result.update(verdict="R10_INCONCLUSIVE_V157_CONTROL_CONSTRUCTION", reason=f"{exc.__class__.__name__}: {exc}")
        args.out.joinpath("V157_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    provider = exp.Qwen35ChatRiverProvider(MODEL)
    memories = {
        "COLD": "",
        "MATCHED_LABELLED": labelled,
        "OPAQUE_ENVELOPE": opaque,
    }
    rows: dict[str, list[dict[str, Any]]] = {k: [] for k in memories}
    for seed in SEEDS:
        for arm in ["COLD", "MATCHED_LABELLED", "OPAQUE_ENVELOPE"]:
            rows[arm].append(v155.run_seed_arm_synced(provider, args.bugsinpy, task, arm, seed, memories[arm]))

    result["rows"] = rows
    result["summary"] = {k: exp.arm_summary(v) for k, v in rows.items()}
    per_arm: dict[str, Any] = {}
    for arm, arm_rows in rows.items():
        details = []
        success_n = 0
        for rr in arm_rows:
            ok, detail = v156.rival_execution_success(rr)
            success_n += int(ok)
            details.append({"seed": rr.get("seed"), "success": ok, **detail})
        per_arm[arm] = {"success_n": success_n, "n": len(arm_rows), "details": details}
    result["rival_execution_capability"] = per_arm

    comparable = all(s.get("n_comparable") == len(SEEDS) for s in result["summary"].values())
    L = per_arm["MATCHED_LABELLED"]["success_n"]
    O = per_arm["OPAQUE_ENVELOPE"]["success_n"]
    C = per_arm["COLD"]["success_n"]

    if not comparable:
        verdict = "R10_INCONCLUSIVE_V157"
    elif L < 2:
        verdict = "OBSTRUCTED_V157_V156_EFFECT_NOT_REPLICATED"
    elif (L - O) >= 2 and (L - C) >= 2:
        verdict = "PASS_V157_SEMANTIC_LABELS_CAUSAL_FOR_RIVAL_EXECUTION"
    elif O >= 2 and abs(L - O) <= 1 and (O - C) >= 2:
        verdict = "NEGATIVE_V157_LABEL_SEMANTICS_NOT_REQUIRED_OPAQUE_ENVELOPE_SUFFICIENT"
    else:
        verdict = "OBSTRUCTED_V157_INTERMEDIATE_SEPARATION"

    result["primary"] = {
        "labelled_success_n": L,
        "opaque_success_n": O,
        "cold_success_n": C,
        "labelled_minus_opaque": L - O,
        "opaque_minus_cold": O - C,
        "task_solved_n": {a: s.get("solved_n") for a, s in result["summary"].items()},
    }
    result["verdict"] = verdict
    args.out.joinpath("V157_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": verdict, "control_construction": result["control_construction"], "primary": result["primary"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
