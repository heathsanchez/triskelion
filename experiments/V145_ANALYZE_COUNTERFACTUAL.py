#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PROTOCOL_ID = "V145_NATURAL_THREE_EPISODE_COUNTERFACTUAL"
ARMS = ["COLD", "O1_ONLY", "FULL", "ANCESTOR_MINUS", "SHAM", "ORACLE_O2"]
CORE_ARMS = ["COLD", "O1_ONLY", "FULL", "ANCESTOR_MINUS", "SHAM"]
EXPECTED_CASES = {"E1": "httpie/5", "E2": "youtube-dl/32", "E3": "pandas/66"}
CORPUS_LOCK = "760b73f87bbe79b76c970c1b2ac4cdd83e5eb18ee3f4b9f2304a915fddbbd5ad"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        x = json.load(f)
    if not isinstance(x, dict):
        raise ValueError(f"{path}: top level must be an object")
    return x


def require(cond: bool, msg: str, errors: list[str]) -> None:
    if not cond:
        errors.append(msg)


def episode_admitted(r: dict[str, Any], e: str) -> bool:
    return bool(r.get("episodes", {}).get(e, {}).get("operator_admitted", False))


def episode_verified(r: dict[str, Any], e: str) -> bool:
    return bool(r.get("episodes", {}).get(e, {}).get("verified_solution", False))


def validate_arm(r: dict[str, Any], arm: str, protocol_sha: str) -> list[str]:
    errors: list[str] = []
    require(r.get("protocol") == PROTOCOL_ID, f"{arm}: wrong protocol", errors)
    require(r.get("protocol_sha256") == protocol_sha, f"{arm}: protocol hash mismatch", errors)
    require(r.get("arm") == arm, f"{arm}: arm label mismatch", errors)
    require(r.get("corpus_lock_sha256") == CORPUS_LOCK, f"{arm}: corpus lock mismatch", errors)
    require(r.get("semantic_rescue") is False, f"{arm}: semantic_rescue must be false", errors)

    episodes = r.get("episodes")
    require(isinstance(episodes, dict), f"{arm}: episodes missing", errors)
    if isinstance(episodes, dict):
        for e, case in EXPECTED_CASES.items():
            rec = episodes.get(e)
            require(isinstance(rec, dict), f"{arm}: missing {e}", errors)
            if isinstance(rec, dict):
                require(rec.get("case") == case, f"{arm}: {e} case changed", errors)

    return errors


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--protocol", default="protocols/V145_NATURAL_THREE_EPISODE_COUNTERFACTUAL_PRECOMMIT.md")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    results_dir = Path(args.results_dir)
    protocol_path = Path(args.protocol)
    out_path = Path(args.out)

    if not protocol_path.exists():
        raise SystemExit(f"missing protocol: {protocol_path}")
    protocol_sha = sha256_bytes(protocol_path.read_bytes())

    records: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    validation_errors: list[str] = []

    for arm in ARMS:
        p = results_dir / f"{arm}.json"
        if not p.exists():
            missing.append(arm)
            continue
        r = load_json(p)
        records[arm] = r
        validation_errors.extend(validate_arm(r, arm, protocol_sha))

    # ORACLE_O2 is diagnostic and may be absent/unrealizable. The five core arms are mandatory.
    missing_core = [a for a in CORE_ARMS if a not in records]
    core_infra_invalid = [
        a for a in CORE_ARMS
        if a in records and (
            records[a].get("apparatus_valid") is not True
            or records[a].get("terminal_status") == "INFRASTRUCTURE_NULL"
        )
    ]

    full = records.get("FULL", {})
    cold = records.get("COLD", {})
    o1_only = records.get("O1_ONLY", {})
    ancestor = records.get("ANCESTOR_MINUS", {})
    sham = records.get("SHAM", {})
    oracle = records.get("ORACLE_O2")

    full_chain = (
        episode_admitted(full, "E1")
        and episode_admitted(full, "E2")
        and episode_admitted(full, "E3")
        and episode_verified(full, "E3")
        and full.get("o3_ablation_pass") is True
    )

    controls_block_o3 = (
        not episode_admitted(cold, "E3")
        and not episode_admitted(o1_only, "E3")
        and not episode_admitted(sham, "E3")
    )

    ancestor_chain_broken = (
        not episode_admitted(ancestor, "E2")
        or not episode_admitted(ancestor, "E3")
        or ancestor.get("ancestor_primary_criterion_worse") is True
    )

    core_causal = full_chain and controls_block_o3 and ancestor_chain_broken

    frontier = full.get("frontier", {}) if isinstance(full.get("frontier"), dict) else {}
    strongest_frontier_signature = (
        frontier.get("O2_reachable_from_A0") is False
        and frontier.get("O2_reachable_after_O1") is True
        and frontier.get("O3_reachable_from_A0") is False
        and frontier.get("O3_reachable_after_O1") is False
        and frontier.get("O3_reachable_after_O1_O2") is True
    )

    oracle_realizable = bool(
        oracle
        and oracle.get("arm_realizable", True) is True
        and oracle.get("terminal_status") != "ARM_NOT_REALIZABLE"
    )
    oracle_valid = bool(
        oracle_realizable
        and oracle.get("apparatus_valid") is True
        and oracle.get("semantic_rescue") is False
        and oracle.get("protocol_sha256") == protocol_sha
    )
    oracle_o3 = bool(oracle_valid and episode_admitted(oracle, "E3") and episode_verified(oracle, "E3"))

    if missing_core or core_infra_invalid or validation_errors:
        primary = "INFRASTRUCTURE_NULL_V145"
    elif core_causal:
        primary = "PASS_V145_THREE_GENERATION_CAUSAL"
    elif episode_admitted(full, "E1") and episode_admitted(full, "E2"):
        primary = "PARTIAL_V145_TWO_GENERATION_ONLY"
    else:
        primary = "NO_V145_DEVELOPMENTAL_EFFECT"

    subtype = None
    if primary == "PASS_V145_THREE_GENERATION_CAUSAL" and oracle_valid:
        if oracle_o3:
            subtype = "PASS_V145_O2_SUFFICIENCY_AND_ANCESTRY"
        else:
            subtype = "PASS_V145_TRAJECTORY_STATE_EXCEEDS_O2"
    elif primary == "PASS_V145_THREE_GENERATION_CAUSAL" and oracle and not oracle_realizable:
        subtype = "ORACLE_O2_NOT_REALIZABLE"

    analysis = {
        "protocol": PROTOCOL_ID,
        "protocol_sha256": protocol_sha,
        "results_dir": str(results_dir),
        "arms_found": sorted(records),
        "missing_arms": missing,
        "missing_core_arms": missing_core,
        "core_infrastructure_invalid": core_infra_invalid,
        "validation_errors": validation_errors,
        "gates": {
            "full_natural_O1": episode_admitted(full, "E1"),
            "full_natural_O2": episode_admitted(full, "E2"),
            "full_verified_O3": episode_admitted(full, "E3") and episode_verified(full, "E3"),
            "o3_ablation": full.get("o3_ablation_pass") is True,
            "cold_blocks_O3": not episode_admitted(cold, "E3"),
            "o1_only_blocks_O3": not episode_admitted(o1_only, "E3"),
            "sham_blocks_O3": not episode_admitted(sham, "E3"),
            "ancestor_chain_broken": ancestor_chain_broken,
            "strongest_frontier_signature": strongest_frontier_signature,
            "oracle_realizable": oracle_realizable,
            "oracle_valid": oracle_valid,
            "oracle_O2_sufficient_for_O3": oracle_o3,
            "protected_O3_transfer": full.get("o3_protected_transfer_pass")
        },
        "primary_verdict": primary,
        "diagnostic_subtype": subtype,
        "allowed_claim": None,
        "forbidden_claim": "No open-ended self-improvement, AGI, universal transfer, or unbounded recursive development claim is licensed by V145."
    }

    if primary == "PASS_V145_THREE_GENERATION_CAUSAL":
        analysis["allowed_claim"] = (
            "Under the frozen bounded natural BugsInPy protocol, verified developmental inheritance "
            "causally enabled a three-episode acquisition chain; removing the first ancestor or limiting "
            "inheritance prevented the full O3 acquisition pattern."
        )
        if strongest_frontier_signature:
            analysis["allowed_claim"] += (
                " The FULL arm also exhibited the preregistered frontier signature in which O1 made O2 "
                "reachable and O1+O2 made O3 reachable under the same frozen discovery budget."
            )
    elif primary == "PARTIAL_V145_TWO_GENERATION_ONLY":
        analysis["allowed_claim"] = "The run supports at most a narrower two-generation developmental result; a causal O3 staircase was not established."
    elif primary == "NO_V145_DEVELOPMENTAL_EFFECT":
        analysis["allowed_claim"] = "Under valid frozen apparatus, the intended natural three-generation developmental effect was not established."
    else:
        analysis["allowed_claim"] = "No semantic developmental conclusion is permitted because a mandatory core arm or protocol-validity gate failed."

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(analysis, indent=2, sort_keys=True))

    if primary == "INFRASTRUCTURE_NULL_V145":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
