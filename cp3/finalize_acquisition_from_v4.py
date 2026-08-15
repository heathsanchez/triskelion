#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import freeze_acquisition_capability as v1

EXPECTED_RAW_SHA256 = "4e404604af6fd76839a932fe85273c9b2568ef20ff639e27633e87850fb30970"
EXPECTED_PARSED_SHA256 = "b3f97180eb47376382a1f2303a61fb3d8457e5f5b360d1d28b4169ac4c98d409"
BUGSINPY_HEAD = "11c5f1eea954a42132cfd06bf257766a7963e0fd"
EXPECTED_IDS = ["PY.PARSER_ESCAPE.V1", "PY.JSONP_STRIP.V1"]
JSONP_SCOPE = ["callback", "function", "response", "json", "wrapper", "payload"]
JSONP_NEGATIVE = [
    "do not activate if the response is not a JSONP string",
    "do not activate if the response is already plain JSON",
]
EVIDENCE = [
    {
        "case": "httpie/5",
        "qualification": "fixed_pass_and_buggy_fail",
        "bug_info_sha256": "2dd5363740eca8808fa82cb8c10ff8cacb39a79d5a602eef2375f1bb65819535",
        "verified_intervention_sha256": "b7f419e7993e92164969b7a99689f01dfa279ce2d1615e25fce0bb21486f472d",
    },
    {
        "case": "youtube-dl/32",
        "qualification": "fixed_pass_and_buggy_fail",
        "bug_info_sha256": "6fcf34b5b6920211c06ca66f70127f922ac493709870a2c5b79aee60988ee1ff",
        "verified_intervention_sha256": "8f5e4ab591494840d5adfebd31981892ab1cd2cd6e59cf040b1894d7cb18c878",
    },
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: object) -> str:
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: finalize_acquisition_from_v4.py RAW PARSED OUT_DIR")
    raw_path, parsed_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    if out.exists():
        raise SystemExit("output exists; refusing to overwrite frozen evidence")
    out.mkdir(parents=True)

    raw_bytes = raw_path.read_bytes()
    parsed_bytes = parsed_path.read_bytes()
    if sha256_bytes(raw_bytes) != EXPECTED_RAW_SHA256:
        raise SystemExit("raw response hash mismatch; refusing normalization")
    if sha256_bytes(parsed_bytes) != EXPECTED_PARSED_SHA256:
        raise SystemExit("parsed response hash mismatch; refusing normalization")

    raw = raw_bytes.decode()
    proposal = json.loads(parsed_bytes)
    caps = proposal.get("capabilities")
    if not isinstance(caps, list) or [c.get("capability_id") for c in caps] != EXPECTED_IDS:
        raise SystemExit("unexpected capability identity/order")

    jsonp = caps[1]
    if jsonp.get("single_line_comments") != JSONP_NEGATIVE:
        raise SystemExit("unexpected JSONP alias field; refusing recovery")
    if "negative_constraints" in jsonp or "scope_any_terms" in jsonp:
        raise SystemExit("expected missing JSONP fields are not missing")

    # Recovery is permitted only because the SAME frozen raw model response
    # explicitly self-checks these exact field values after the first JSON object.
    required_literals = [
        '2. `PY.JSONP_STRIP.V1`:',
        '`scope_any_terms`: ["callback", "function", "response", "json", "wrapper", "payload"]',
        '`negative_constraints`: ["do not activate if the response is not a JSONP string", "do not activate if the response is already plain JSON"]',
    ]
    for literal in required_literals:
        if literal not in raw:
            raise SystemExit(f"raw response does not attest recovery literal: {literal}")

    jsonp.pop("single_line_comments")
    jsonp["scope_any_terms"] = list(JSONP_SCOPE)
    jsonp["negative_constraints"] = list(JSONP_NEGATIVE)

    # No other semantic fields are changed. Run the original frozen validator.
    validated = v1.validate_payload(proposal)
    cp1_caps = [v1.to_cp1_compatible(cap, EVIDENCE) for cap in validated]

    frozen = {
        "canonical_id": "TRISKELION_CP3_ACQUISITION_CAPABILITY_V1",
        "protocol": v1.PROTOCOL,
        "status": "FROZEN",
        "model": v1.MODEL_LABEL,
        "provider_model": v1.MODEL,
        "temperature": 0.0,
        "seed": v1.SEED,
        "max_tokens": v1.MAX_TOKENS,
        "acquisition_cases": list(v1.EXPECTED_ACQUISITION),
        "protected_evidence_used": False,
        "bugsinpy_head": BUGSINPY_HEAD,
        "model_response_sha256": EXPECTED_RAW_SHA256,
        "prevalidation_parsed_sha256": EXPECTED_PARSED_SHA256,
        "normalization": "hash-locked same-response schema recovery only",
        "capabilities": cp1_caps,
        "compression_rationale": proposal.get("compression_rationale", ""),
        "freeze_rule": "No semantic changes after this artifact before protected four-arm evaluation.",
    }
    payload_text = canonical_json(frozen)
    payload_sha = sha256_bytes(payload_text.encode())
    (out / "CAPABILITY_PAYLOAD.json").write_text(payload_text)
    (out / "CAPABILITY_SHA256.txt").write_text(payload_sha + "\n")
    (out / "ACQUISITION_EVIDENCE.json").write_text(canonical_json(EVIDENCE))
    normalization = {
        "canonical_id": "TRISKELION_CP3_ACQUISITION_NORMALIZATION_V1",
        "source_artifact_id": 9246154368,
        "source_workflow_run_id": 31881546140,
        "raw_response_sha256": EXPECTED_RAW_SHA256,
        "prevalidation_parsed_sha256": EXPECTED_PARSED_SHA256,
        "recovered_capability_id": "PY.JSONP_STRIP.V1",
        "changes": {
            "single_line_comments_to_negative_constraints": JSONP_NEGATIVE,
            "scope_any_terms_from_same_response_self_check": JSONP_SCOPE,
        },
        "protected_evidence_used": False,
    }
    (out / "NORMALIZATION_RECORD.json").write_text(canonical_json(normalization))
    print(canonical_json({
        "status": "FROZEN",
        "capability_count": len(cp1_caps),
        "capability_ids": [c["capability_id"] for c in cp1_caps],
        "capability_sha256": payload_sha,
        "protected_evidence_used": False,
        "normalization": "hash-locked same-response schema recovery only",
    }), end="")


if __name__ == "__main__":
    main()
