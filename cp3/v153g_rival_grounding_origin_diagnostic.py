#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import bugsinpy_four_arm as base
import structured_edit_protocol_v2 as sed

T2 = ("youtube-dl", 32)
RAW_ARM = "D_PLUS_RAW_T1"
CALL1_SHA = "69002ebf51a2842e41639dd21d1d5c196ee65feac42470bdbef24067264f40bb"


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def project_edit_payloads(text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    dec = json.JSONDecoder()
    pos = 0
    accepted: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    ordinal = 0
    needle = '"edits":'
    while True:
        k = text.find(needle, pos)
        if k < 0:
            break
        ordinal += 1
        start = k + len(needle)
        row: dict[str, Any] = {"ordinal": ordinal, "key_offset": k}
        try:
            value, end = dec.raw_decode(text, start)
            row["decoded_end"] = end
            if not isinstance(value, list):
                raise ValueError("edits field did not decode to array")
            payload = sed.extract_edits(json.dumps({"edits": value}, ensure_ascii=False))
            h = sha_text(payload)
            row.update(status="VALID", payload_sha256=h, changed_files=sed.changed_files(payload))
            accepted.append({"ordinal": ordinal, "payload": payload, "payload_sha256": h})
            pos = end
        except Exception as exc:
            row.update(status="INVALID", error=f"{exc.__class__.__name__}: {exc}")
            pos = start + 1
        audit.append(row)
    return accepted, audit


def referenced_paths(payloads: list[str]) -> set[str]:
    out: set[str] = set()
    for payload in payloads:
        for e in json.loads(payload)["edits"]:
            out.add(e["path"])
    return out


def load_state(work: Path, paths: set[str]) -> dict[str, str | None]:
    state: dict[str, str | None] = {}
    for raw in paths:
        p = work / raw
        state[raw] = p.read_text(encoding="utf-8", errors="strict") if p.is_file() else None
    return state


def simulate(state0: dict[str, str | None], payload: str) -> tuple[bool, dict[str, str | None], dict[str, Any] | None]:
    state = dict(state0)
    for idx, edit in enumerate(json.loads(payload)["edits"], start=1):
        path = edit["path"]
        text = state.get(path)
        if text is None:
            return False, state, {"edit_index": idx, "path": path, "reason": "MISSING_FILE", "old_count": None}
        count = text.count(edit["old"])
        if count != 1:
            return False, state, {"edit_index": idx, "path": path, "reason": "OLD_COUNT_NOT_ONE", "old_count": count, "old_sha256": sha_text(edit["old"])}
        state[path] = text.replace(edit["old"], edit["new"], 1)
    return True, state, None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v153-result", type=Path, required=True)
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("output exists; refusing overwrite")
    args.out.mkdir(parents=True)

    source_bytes = args.v153_result.read_bytes()
    source = json.loads(source_bytes)
    raw_rows = source.get("rows", {}).get(RAW_ARM, [])

    result: dict[str, Any] = {
        "canonical_id": "V153G_RIVAL_GROUNDING_ORIGIN_DIAGNOSTIC",
        "protocol": "protocols/V153G_RIVAL_GROUNDING_ORIGIN_DIAGNOSTIC.md",
        "source_v153_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "source_v153_verdict": source.get("verdict"),
        "model_calls": 0,
        "verifier_calls": 0,
        "call1_payload_sha256_expected": CALL1_SHA,
        "rows": [],
    }

    if not raw_rows:
        result["verdict"] = "R10_DIAGNOSTIC_INCONCLUSIVE"
        result["reason"] = "no raw-T1 rows"
        (args.out / "V153G_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print((args.out / "V153G_RESULT.json").read_text())
        return

    call1_payloads: list[str] = []
    projected_by_seed: list[tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]] = []
    all_payloads: list[str] = []

    for rr in raw_rows:
        attempts = rr.get("attempts", [])
        call1 = next((a for a in attempts if a.get("call") == 1), None)
        call2 = next((a for a in attempts if a.get("call") == 2), None)
        if not call1 or not isinstance((call1.get("response") or {}).get("text"), str):
            result["verdict"] = "R10_DIAGNOSTIC_INCONCLUSIVE"
            result["reason"] = f"missing call1 text for seed {rr.get('seed')}"
            (args.out / "V153G_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            print((args.out / "V153G_RESULT.json").read_text())
            return
        try:
            c1p = sed.extract_edits(call1["response"]["text"])
        except Exception as exc:
            result["verdict"] = "R10_DIAGNOSTIC_INCONCLUSIVE"
            result["reason"] = f"call1 extraction failed for seed {rr.get('seed')}: {exc}"
            (args.out / "V153G_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            print((args.out / "V153G_RESULT.json").read_text())
            return
        if sha_text(c1p) != CALL1_SHA:
            result["verdict"] = "R10_DIAGNOSTIC_INCONCLUSIVE"
            result["reason"] = f"call1 hash mismatch for seed {rr.get('seed')}: {sha_text(c1p)}"
            (args.out / "V153G_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            print((args.out / "V153G_RESULT.json").read_text())
            return
        call1_payloads.append(c1p)
        all_payloads.append(c1p)

        if not call2 or not isinstance((call2.get("response") or {}).get("text"), str):
            accepted, audit = [], []
        else:
            accepted, audit = project_edit_payloads(call2["response"]["text"])
        projected_by_seed.append((rr, accepted, audit))
        all_payloads.extend(p["payload"] for p in accepted)

    call1_payload = call1_payloads[0]
    paths = referenced_paths(all_payloads)

    try:
        with tempfile.TemporaryDirectory(prefix="v153g-clean-") as td:
            work = base.checkout_buggy(args.bugsinpy, T2[0], T2[1], Path(td))
            clean = load_state(work, paths)
    except Exception as exc:
        result["verdict"] = "R10_DIAGNOSTIC_INCONCLUSIVE"
        result["reason"] = f"clean checkout failed: {exc.__class__.__name__}: {exc}"
        (args.out / "V153G_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print((args.out / "V153G_RESULT.json").read_text())
        return

    c1_ok, post_call1, c1_fail = simulate(clean, call1_payload)
    result["call1_applies_clean"] = c1_ok
    result["call1_failure"] = c1_fail
    result["referenced_paths"] = sorted(paths)
    if not c1_ok:
        result["verdict"] = "R10_DIAGNOSTIC_INCONCLUSIVE"
        result["reason"] = "frozen call1 payload does not ground in clean state"
        (args.out / "V153G_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print((args.out / "V153G_RESULT.json").read_text())
        return

    counts = {"GROUND_BOTH": 0, "GROUND_CLEAN_ONLY": 0, "GROUND_POST_CALL1_ONLY": 0, "UNGROUNDED_BOTH": 0}
    nonclean = 0

    for rr, accepted, audit in projected_by_seed:
        row: dict[str, Any] = {"seed": rr.get("seed"), "projection_audit": audit, "rivals": []}
        seen: set[str] = set()
        for p in accepted:
            h = p["payload_sha256"]
            if h == CALL1_SHA or h in seen:
                continue
            seen.add(h)
            clean_ok, _, clean_fail = simulate(clean, p["payload"])
            post_ok, _, post_fail = simulate(post_call1, p["payload"])
            if clean_ok and post_ok:
                klass = "GROUND_BOTH"
            elif clean_ok:
                klass = "GROUND_CLEAN_ONLY"
            elif post_ok:
                klass = "GROUND_POST_CALL1_ONLY"
            else:
                klass = "UNGROUNDED_BOTH"
            counts[klass] += 1
            if not clean_ok:
                nonclean += 1
            row["rivals"].append({
                "ordinal": p["ordinal"],
                "payload_sha256": h,
                "grounding_class": klass,
                "clean_applies": clean_ok,
                "clean_failure": clean_fail,
                "post_call1_applies": post_ok,
                "post_call1_failure": post_fail,
            })
        result["rows"].append(row)

    post_only = counts["GROUND_POST_CALL1_ONLY"]
    result["summary"] = {
        "distinct_rivals": sum(counts.values()),
        "non_clean_grounded_rivals": nonclean,
        **counts,
    }

    if nonclean > 0 and post_only * 2 >= nonclean:
        verdict = "DIAGNOSTIC_V153_STATE_SEMANTICS_MISMATCH"
    elif post_only >= 1:
        verdict = "DIAGNOSTIC_V153_MIXED_STATE_GROUNDING"
    elif nonclean > 0:
        verdict = "DIAGNOSTIC_V153_SOURCE_GROUNDING_FAILURE"
    else:
        verdict = "DIAGNOSTIC_V153_ALL_RIVALS_CLEAN_GROUNDED"
    result["verdict"] = verdict

    p = args.out / "V153G_RESULT.json"
    p.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(p.read_text())


if __name__ == "__main__":
    main()
