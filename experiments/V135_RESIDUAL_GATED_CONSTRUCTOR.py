#!/usr/bin/env python3
"""
V135 residual-gated constructor evaluator.

This script is intentionally small and boring. It does not implement K6.
It freezes the constructibility criterion used by the Daniel experiment:
K6 is constructible iff the normalized residual record contains the full
specialization-before-instance-synthesis schema.

Usage:
  python3 experiments/V135_RESIDUAL_GATED_CONSTRUCTOR.py \
    --cold cold_residual.json \
    --developed developed_residual.json \
    --out result.json
"""

import argparse
import hashlib
import json
from pathlib import Path

REQUIRED_R2 = {
    "residual_family": "specialization_before_instance_synthesis",
    "fixed_top_level_parameter": True,
    "constructor_local_symbolic_parameter": True,
    "downstream_instance_requested_over_symbolic_parameter": True,
    "specialized_concrete_type_has_available_instance": True,
    "failure_is_not_universe_mismatch": True,
    "failure_is_not_constructor_overapplication": True,
    "failure_is_not_parser_or_build_error": True,
}

K6 = {
    "repair_family": "SpecializeBeforeInstanceSynthesis",
    "description": (
        "Before synthesizing field-generation/typeclass evidence for a constructor "
        "field whose type depends on a constructor-local family parameter, propagate "
        "any already-fixed top-level relation/target parameter equality into the field "
        "type and request the instance for the specialized concrete field type rather "
        "than the symbolic local family projection."
    ),
    "forbidden": [
        "target_specific_instance",
        "strata_specific_name",
        "p0_unit_special_case",
        "verifier_contract_change",
        "accept_failed_instance_synthesis",
        "replace_k2_k5_wholesale",
    ],
}


def stable_sha(obj):
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def residual_record(obj):
    """Allow either a direct residual object or {"normalized_residual": {...}}."""
    if isinstance(obj, dict) and isinstance(obj.get("normalized_residual"), dict):
        return obj["normalized_residual"]
    return obj


def missing_requirements(residual):
    missing = {}
    for key, expected in REQUIRED_R2.items():
        actual = residual.get(key, None) if isinstance(residual, dict) else None
        if actual != expected:
            missing[key] = {"expected": expected, "actual": actual}
    return missing


def construct(residual):
    missing = missing_requirements(residual)
    if missing:
        return {
            "constructible": False,
            "reason": "required_R2_schema_absent",
            "missing_or_mismatched": missing,
            "emitted": None,
        }
    return {
        "constructible": True,
        "reason": "required_R2_schema_present",
        "missing_or_mismatched": {},
        "emitted": K6,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cold", required=True)
    ap.add_argument("--developed", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cold_raw = load(args.cold)
    dev_raw = load(args.developed)
    cold_residual = residual_record(cold_raw)
    dev_residual = residual_record(dev_raw)

    cold = construct(cold_residual)
    developed = construct(dev_residual)

    if (not cold["constructible"]) and developed["constructible"]:
        verdict = "PASS_CONSTRUCTIBILITY_DIFFERENCE"
    elif cold["constructible"] and developed["constructible"]:
        verdict = "NO_CONSTRUCTIBILITY_DIFFERENCE_BOTH_EMIT_K6"
    elif (not cold["constructible"]) and (not developed["constructible"]):
        verdict = "NO_CONSTRUCTIBILITY_DIFFERENCE_NEITHER_EMITS_K6"
    else:
        verdict = "REVERSE_OR_ANOMALOUS"

    out = {
        "protocol": "V135_RESIDUAL_GATED_CONSTRUCTOR",
        "required_R2_schema": REQUIRED_R2,
        "candidate_repair_family": "SpecializeBeforeInstanceSynthesis",
        "cold_input_sha256": hashlib.sha256(Path(args.cold).read_bytes()).hexdigest(),
        "developed_input_sha256": hashlib.sha256(Path(args.developed).read_bytes()).hexdigest(),
        "cold_residual_sha256": stable_sha(cold_residual),
        "developed_residual_sha256": stable_sha(dev_residual),
        "cold": cold,
        "developed": developed,
        "verdict": verdict,
        "claim_boundary": (
            "This script decides residual-gated constructibility only. It does not "
            "implement K6, verify K6, or prove semantic correctness of a future repair."
        ),
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
