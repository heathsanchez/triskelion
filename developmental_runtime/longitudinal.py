from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class LongitudinalVerdict:
    verdict: str
    developmental_pass: bool
    practical_advantage: bool | None
    reasons: tuple[str, ...]


def _bool(record: Mapping[str, Any], key: str) -> bool:
    return bool(record.get(key, False))


def classify_longitudinal_result(record: Mapping[str, Any]) -> LongitudinalVerdict:
    """Apply the frozen V159 decision table to one completed result record.

    This function does not infer scientific facts from raw model text. Its input
    must already contain native-verifier/apparatus measurements produced by the
    execution harness.
    """
    reasons: list[str] = []

    apparatus = record.get("apparatus", {})
    required_apparatus = (
        "same_task_order",
        "matched_model_budget",
        "matched_verifier_access",
        "protected_boundary_clean",
        "fresh_arm_state",
    )
    apparatus_ok = all(_bool(apparatus, key) for key in required_apparatus)
    if not apparatus_ok:
        missing = [key for key in required_apparatus if not _bool(apparatus, key)]
        reasons.append("apparatus invalid: " + ",".join(missing))
        return LongitudinalVerdict("OBSTRUCTED", False, None, tuple(reasons))

    gate = record.get("developmental_gate", {})
    if not _bool(gate, "reached"):
        reasons.append("developmental gate not reached: " + str(gate.get("obstruction", "unspecified")))
        return LongitudinalVerdict("OBSTRUCTED", False, None, tuple(reasons))

    required_pass = (
        "prospective_ancestor_fixed",
        "ancestor_acquisition_native_verified",
        "ancestor_acquisition_ablation_causal",
        "downstream_source_distinct",
        "downstream_native_verified",
        "downstream_not_discoverable_ancestor_minus",
        "downstream_discoverable_dev",
        "frontier_shift_preanswer",
        "restart_exact",
    )
    developmental_pass = all(_bool(gate, key) for key in required_pass)
    if developmental_pass:
        reasons.append("all frozen natural developmental predicates passed")
        verdict = "PASS_NATURAL_LONGITUDINAL_DEVELOPMENT"
    else:
        failed = [key for key in required_pass if not _bool(gate, key)]
        reasons.append("valid developmental execution without full causal pass: " + ",".join(failed))
        verdict = "NEGATIVE"

    practical = record.get("practical", {})
    if practical.get("reached") is not True:
        practical_advantage: bool | None = None
        reasons.append("practical comparison not reached")
    else:
        practical_advantage = bool(
            practical.get("dev_beats_strongest_comparator", False)
            and practical.get("matched_total_budget", False)
            and practical.get("no_extra_verifier_access", False)
        )
        reasons.append("practical advantage passed" if practical_advantage else "practical advantage did not pass")

    return LongitudinalVerdict(verdict, developmental_pass, practical_advantage, tuple(reasons))
