#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import bugsinpy_four_arm as base
import bugsinpy_exact_runtime as exact_runtime
import structured_edit_protocol_v2 as sed

T2 = ("youtube-dl", 32)
RAW_ARM = "D_PLUS_RAW_T1"
CALL1_SHA = "69002ebf51a2842e41639dd21d1d5c196ee65feac42470bdbef24067264f40bb"
EXPECTED_CLASS = {
    "583c8807e3546d8b5f1bef66691b6579c7819a2b2a32d065f4ade79cd57c876b": "GROUND_CLEAN_ONLY",
    "66836a81c4c370f95e354d6f6cc5c0daeaa7b4cd3046f59bc81b9b486c6dfd2e": "GROUND_CLEAN_ONLY",
    "e2412752d6ac269675bb75b704b06a809898b1c653655b9bd010ec12662fdb2b": "GROUND_POST_CALL1_ONLY",
    "da977ac0351961e7210a39b157e4905329e72034af5de75da63a562e8267f7f7": "GROUND_POST_CALL1_ONLY",
}


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def source_hash(work: Path, rel: str = "youtube_dl/utils.py") -> str:
    return hashlib.sha256((work / rel).read_bytes()).hexdigest()


def project_edit_payloads(text: str) -> list[dict[str, Any]]:
    dec = json.JSONDecoder()
    pos = 0
    accepted: list[dict[str, Any]] = []
    ordinal = 0
    needle = '"edits":'
    while True:
        k = text.find(needle, pos)
        if k < 0:
            break
        ordinal += 1
        start = k + len(needle)
        try:
            value, end = dec.raw_decode(text, start)
            if not isinstance(value, list):
                raise ValueError("edits field did not decode to array")
            payload = sed.extract_edits(json.dumps({"edits": value}, ensure_ascii=False))
            accepted.append({"ordinal": ordinal, "payload": payload, "payload_sha256": sha_text(payload)})
            pos = end
        except Exception:
            pos = start + 1
    return accepted


def extract_call1(rr: dict[str, Any]) -> str:
    a = next(x for x in rr.get("attempts", []) if x.get("call") == 1)
    payload = sed.extract_edits(a["response"]["text"])
    if sha_text(payload) != CALL1_SHA:
        raise RuntimeError(f"call1 hash mismatch: {sha_text(payload)}")
    return payload


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v153-result", type=Path, required=True)
    ap.add_argument("--bugsinpy", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("output exists; refusing overwrite")
    args.out.mkdir(parents=True)

    src_bytes = args.v153_result.read_bytes()
    src = json.loads(src_bytes)
    result: dict[str, Any] = {
        "canonical_id": "V153H_IMMUTABLE_STATE_ALIGNED_RIVAL_REPLAY",
        "protocol": "protocols/V153H_IMMUTABLE_STATE_ALIGNED_RIVAL_REPLAY.md",
        "source_v153_sha256": hashlib.sha256(src_bytes).hexdigest(),
        "model_calls": 0,
        "rows": [],
    }

    raw_rows = src.get("rows", {}).get(RAW_ARM, [])
    seed_instances: list[dict[str, Any]] = []
    for rr in raw_rows:
        call1 = extract_call1(rr)
        a2 = next((x for x in rr.get("attempts", []) if x.get("call") == 2), None)
        if not a2:
            continue
        seen: set[str] = set()
        for p in project_edit_payloads(a2["response"]["text"]):
            h = p["payload_sha256"]
            if h == CALL1_SHA or h in seen:
                continue
            seen.add(h)
            if h not in EXPECTED_CLASS:
                raise RuntimeError(f"unexpected rival payload {h}")
            seed_instances.append({"seed": rr.get("seed"), "ordinal": p["ordinal"], "payload": p["payload"], "payload_sha256": h, "grounding_class": EXPECTED_CLASS[h], "call1": call1})

    if len(seed_instances) != 6:
        result.update(verdict="R10_STATE_ALIGNMENT_INCONSISTENT", reason=f"expected 6 seed-level rivals, got {len(seed_instances)}")
        p=args.out/"V153H_RESULT.json"; p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(p.read_text()); return

    clean_hash_ref: str | None = None
    post_hash_ref: str | None = None
    infra = 0
    transport = 0
    solved = 0
    reached = 0

    for inst in seed_instances:
        row = {k:v for k,v in inst.items() if k not in {"payload","call1"}}
        with tempfile.TemporaryDirectory(prefix=f"v153h-{inst['seed']}-{inst['ordinal']}-") as td:
            try:
                work = base.checkout_buggy(args.bugsinpy, T2[0], T2[1], Path(td))
                ch = source_hash(work)
                row["clean_source_sha256"] = ch
                if clean_hash_ref is None:
                    clean_hash_ref = ch
                elif ch != clean_hash_ref:
                    raise RuntimeError(f"clean source hash drift: {ch} != {clean_hash_ref}")

                if inst["grounding_class"] == "GROUND_POST_CALL1_ONLY":
                    sed.apply_edits(work, inst["call1"])
                    ph = source_hash(work)
                    row["post_call1_source_sha256"] = ph
                    if post_hash_ref is None:
                        post_hash_ref = ph
                    elif ph != post_hash_ref:
                        raise RuntimeError(f"post-call1 source hash drift: {ph} != {post_hash_ref}")

                sed.apply_edits(work, inst["payload"])
                row["state_aligned_transport"] = True
            except Exception as exc:
                transport += 1
                row.update(status="TRANSPORT_OR_STATE_ASSERTION_FAILURE", error=f"{exc.__class__.__name__}: {exc}")
                result["rows"].append(row)
                continue

            verdict = exact_runtime.native_test(args.bugsinpy, work)
            row["native_verdict"] = verdict
            if verdict.get("infrastructure_error"):
                infra += 1
                row.update(status="R10", error=verdict["infrastructure_error"])
            else:
                reached += 1
                if verdict.get("passed"):
                    solved += 1
                    row["status"] = "VERIFIED_SOLVED"
                else:
                    row["status"] = "VERIFIED_FAILED"
            result["rows"].append(row)

    unique: dict[str, dict[str, Any]] = {}
    for r in result["rows"]:
        h=r["payload_sha256"]
        u=unique.setdefault(h,{"payload_sha256":h,"grounding_class":r["grounding_class"],"instances":0,"statuses":[]})
        u["instances"] += 1
        u["statuses"].append(r.get("status"))

    result["clean_source_sha256"] = clean_hash_ref
    result["post_call1_source_sha256"] = post_hash_ref
    result["unique_payloads"] = list(unique.values())
    result["summary"] = {
        "seed_level_rivals": len(seed_instances),
        "unique_payloads": len(unique),
        "state_aligned_transport_failures": transport,
        "native_infrastructure_errors": infra,
        "rivals_reaching_verifier": reached,
        "verified_solved": solved,
    }

    if infra:
        verdict="R10_DIAGNOSTIC_INCONCLUSIVE"
    elif transport:
        verdict="R10_STATE_ALIGNMENT_INCONSISTENT"
    elif solved:
        verdict="DIAGNOSTIC_V153_STATE_ALIGNED_RIVAL_SOLVES_T2"
    elif reached == 6:
        verdict="DIAGNOSTIC_V153_STATE_ALIGNED_CANDIDATE_SET_SEMANTIC_TRAP"
    else:
        verdict="R10_DIAGNOSTIC_INCONCLUSIVE"
    result["verdict"] = verdict
    p=args.out/"V153H_RESULT.json"; p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(p.read_text())


if __name__ == "__main__":
    main()
