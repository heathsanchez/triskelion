from __future__ import annotations

import json
import re
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "v102_boundary_compression"
OUT.mkdir(parents=True, exist_ok=True)

V51 = ROOT / "results" / "attested" / "V51_OPERATOR_INVENTION" / "PRIMARY_ARTIFACT_SNAPSHOT.md"
V101P = ROOT / "results" / "V101P_DEPTH2_CLOSURE_DIAGNOSTIC_20260814.md"
V101F = ROOT / "results" / "V101F_CLOSURE_INVARIANT_AUDIT_20260814.md"


def parse_fenced_json_by_heading(text: str, heading: str) -> dict:
    m = re.search(rf"## `{re.escape(heading)}`\s*```json\s*(\{{.*?\}})\s*```", text, re.S)
    if not m:
        raise RuntimeError(f"Could not parse {heading}")
    return json.loads(m.group(1))


def canonical_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def mdl_lengths(obj) -> dict:
    raw = canonical_bytes(obj)
    return {
        "canonical_json_bytes": len(raw),
        "zlib9_bytes": len(zlib.compress(raw, 9)),
    }


v51_text = V51.read_text()
phase_a = parse_fenced_json_by_heading(v51_text, "PHASE_A.json")
phase_b = parse_fenced_json_by_heading(v51_text, "PHASE_B.json")
v101p_text = V101P.read_text()
v101f_text = V101F.read_text()

assert phase_a["old_closure_obstruction"] is True
assert phase_a["constructed_operator"]["src_posthoc"] == "<"
assert phase_a["constructed_operator"]["dst_posthoc"] == "<="
assert phase_b["decision"] == "REVOKE"
assert phase_b["later_counterevidence"]["member"] is True
assert phase_b["refined_scope_candidates"] == []
assert "depth 1 reachable: 0/4" in v101p_text
assert "depth 2 reachable: 1/4" in v101p_text
assert "sieve" in v101p_text and "CMP_OP -> NEGATE_GUARD" in v101p_text

# -----------------------------------------------------------------------------
# TEST 1: Boundary robustness
# -----------------------------------------------------------------------------
# V51's old generators are all token-position rearrangements. Any composition of
# rearrangements preserves the token multiset. We perturb granularity and
# composition power while preserving that semantic invariant, then include a
# positive-control boundary that explicitly admits token substitution.

boundary_models = [
    {
        "name": "original_generators_depth1",
        "allows_reordering": True,
        "unbounded_composition": False,
        "allows_token_identity_change": False,
        "interpretation": "original named structural generators, shallow",
    },
    {
        "name": "original_generators_unbounded_closure",
        "allows_reordering": True,
        "unbounded_composition": True,
        "allows_token_identity_change": False,
        "interpretation": "same generators, arbitrary lawful composition depth",
    },
    {
        "name": "coarse_arbitrary_permutation_primitive",
        "allows_reordering": True,
        "unbounded_composition": True,
        "allows_token_identity_change": False,
        "interpretation": "collapse all reorder operations into one maximally coarse permutation primitive",
    },
    {
        "name": "fine_adjacent_swap_basis",
        "allows_reordering": True,
        "unbounded_composition": True,
        "allows_token_identity_change": False,
        "interpretation": "refine structural language to a minimal adjacent-swap generating basis",
    },
    {
        "name": "token_substitution_positive_control",
        "allows_reordering": True,
        "unbounded_composition": True,
        "allows_token_identity_change": True,
        "interpretation": "semantic boundary expansion that explicitly admits token identity substitution",
    },
]

src, dst = "<", "<="
for b in boundary_models:
    # The relevant certified invariant is token-identity/multiset preservation.
    b["operator_inside_closure"] = bool(b["allows_token_identity_change"])
    b["obstruction_survives"] = not b["operator_inside_closure"]

structural_models = [b for b in boundary_models if not b["allows_token_identity_change"]]
semantic_positive = [b for b in boundary_models if b["allows_token_identity_change"]]

boundary_result = {
    "question": "Does the V51 new operator remain outside old closure under reasonable changes in operator granularity/composition rules?",
    "operator": f"{src} -> {dst}",
    "certified_invariant": "token identity / token multiset preservation under reordering-only closure",
    "models": boundary_models,
    "all_structural_redescriptions_preserve_obstruction": all(x["obstruction_survives"] for x in structural_models),
    "positive_control_boundary_expansion_removes_obstruction": all(not x["obstruction_survives"] for x in semantic_positive),
    "empirical_depth_perturbation": {
        "source": "V101P nonclaim diagnostic",
        "depth1_reachable": "0/4",
        "depth2_reachable": "1/4",
        "obstruction_removed": "sieve",
        "lawful_composition": "CMP_OP -> NEGATE_GUARD",
        "remaining_depth2_residuals": ["breadth_first_search", "subsequences", "find_in_sorted"],
        "status": "diagnostic_only_posthoc",
    },
    "structural_invariant_followup": {
        "source": "V101F post-hoc nonclaim audit",
        "remaining_missing_class": "typed expression / value construction at an operational slot",
        "claim_status": "posthoc_nonclaim_requires_fresh_split",
    },
}

boundary_result["verdict"] = (
    "PASS_PARTIAL_BOUNDARY_ROBUSTNESS"
    if boundary_result["all_structural_redescriptions_preserve_obstruction"]
    and boundary_result["positive_control_boundary_expansion_removes_obstruction"]
    else "FAIL_BOUNDARY_ROBUSTNESS"
)

# -----------------------------------------------------------------------------
# TEST 2: Compression vs displaced complexity
# -----------------------------------------------------------------------------
# Charge the operator AND activation predicate. Compare with explicit one-off
# repairs using multiple encodings. Then evaluate the full governed class after
# the later harmful in-scope counterexample. A persistent abstraction cannot be
# credited with compression if it is invalid on the full evidence class and no
# admissible scope refinement survives.

operator_scope_package = {
    "operation": {"kind": "replace_token", "from": "<", "to": "<="},
    "scope": {"ancestor_kind": "if"},
}

# Minimal normalized identifiers; deliberately do not copy long file paths or
# source lines into the baseline, so the one-off baseline is not artificially
# inflated.
positive_cases = ["p1", "p2", "sealed_transfer"]
case_table = {
    "repairs": [{"case": c, "from": "<", "to": "<="} for c in positive_cases]
}
training_case_table = {
    "repairs": [{"case": c, "from": "<", "to": "<="} for c in positive_cases[:2]]
}

mdl = {
    "operator_plus_scope": mdl_lengths(operator_scope_package),
    "two_training_oneoffs": mdl_lengths(training_case_table),
    "three_positive_oneoffs": mdl_lengths(case_table),
}

# Search/reconstruction accounting from frozen artifact: 42 possible constructor
# destinations were available. This is a conservative candidate-count proxy, not
# wall-clock compute. Warm use is charged one scope decision + one operator use.
constructor_destination_count = int(phase_a["constructor_destination_count"])
search_proxy = {
    "cold_candidate_menu_per_site": constructor_destination_count,
    "positive_sites": len(positive_cases),
    "cold_upper_menu_exposures": constructor_destination_count * len(positive_cases),
    "warm_decisions_per_site": 2,
    "warm_total_decisions": 2 * len(positive_cases),
    "note": "candidate-count proxy only; not a measured runtime ratio",
}

helpful_class_compression = {
    metric: mdl["operator_plus_scope"][metric] < mdl["three_positive_oneoffs"][metric]
    for metric in mdl["operator_plus_scope"]
}

full_class_validity = {
    "later_harm_inside_learned_scope": bool(phase_b["later_counterevidence"]["member"]),
    "scope_refinement_candidates": len(phase_b["refined_scope_candidates"]),
    "ratchet_decision": phase_b["decision"],
    "persistent_operator_valid_on_full_observed_class": phase_b["decision"] != "REVOKE",
}

compression_result = {
    "question": "Does V51 unify a problem class at lower description/search cost without hiding complexity in its definition or activation condition?",
    "mdl_normalization": "canonical minimal semantic JSON; operator and scope both charged; one-off baseline uses short case IDs rather than source paths",
    "mdl": mdl,
    "helpful_positive_class": {
        "n": len(positive_cases),
        "operator_beats_oneoff_by_metric": helpful_class_compression,
        "all_mdl_encodings_agree": all(helpful_class_compression.values()),
    },
    "search_reconstruction_proxy": search_proxy,
    "full_governed_class": full_class_validity,
}

# Strict criterion: a durable compression claim requires the governed operator to
# remain valid after later in-scope evidence (or admit a valid refinement). V51
# was correctly revoked, so it cannot close Bao's compression challenge.
compression_result["verdict"] = (
    "PASS_DURABLE_COMPRESSION"
    if full_class_validity["persistent_operator_valid_on_full_observed_class"]
    and all(helpful_class_compression.values())
    else "FAIL_DURABLE_COMPRESSION_V51_REVOKED"
)

# -----------------------------------------------------------------------------
# Joint interpretation
# -----------------------------------------------------------------------------
result = {
    "protocol": "V102_BOUNDARY_COMPRESSION_AUDIT_20260815",
    "inputs": {
        "v51_snapshot": str(V51.relative_to(ROOT)),
        "v101p": str(V101P.relative_to(ROOT)),
        "v101f": str(V101F.relative_to(ROOT)),
    },
    "test_1_boundary_robustness": boundary_result,
    "test_2_compression_displacement": compression_result,
    "joint_verdict": "MIXED_BOUNDARY_PARTIAL_COMPRESSION_NOT_CLOSED",
    "claim": (
        "The operator-construction claim is robust to multiple structural granularity/composition "
        "redescriptions that preserve the certified token-identity invariant, while a deliberate "
        "semantic boundary expansion removes the obstruction as expected. The separate V101P "
        "diagnostic also shows that widening lawful composition can eliminate an apparent obstruction. "
        "However V51 does not establish durable compression once activation/scope is charged over the "
        "full observed class: later in-scope counterevidence admitted no refinement and the ratchet "
        "correctly revoked the operator. Search reuse remains suggestive but is not a substitute for "
        "a prospective full-class MDL/computational-cost test."
    ),
    "next_required_test": (
        "Prospectively freeze several reasonable effective-language boundaries and an encoding/cost "
        "scheme; learn an operator on acquisition cases; charge operator+scope+withdrawal logic; then "
        "measure held-out description and verifier-search cost against old-language search and an "
        "equal-budget case-table dispatcher."
    ),
}

(OUT / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")

md = f"""# V102 Boundary Robustness + Compression Audit\n\n## Joint verdict\n\n**{result['joint_verdict']}**\n\n## 1. Boundary robustness\n\n**{boundary_result['verdict']}**\n\nThe V51 `< -> <=` operator remains outside every tested reordering-only redescription of the old language, including unbounded composition, a maximally coarse arbitrary-permutation primitive, and a minimal adjacent-swap basis. All preserve token identity/multiset, so none can synthesize the new token identity.\n\nAs a positive control, explicitly adding token substitution makes the operator reachable. The result is therefore **relative to an effective-language boundary**, not representation-independent invention.\n\nThe independent V101P diagnostic gives empirical sensitivity in the other direction: widening lawful composition from depth 1 to depth 2 changed reachability from 0/4 to 1/4 and killed the `sieve` obstruction (`CMP_OP -> NEGATE_GUARD`). The other three remained residuals; V101F characterizes structural invariants, but both are post-hoc/nonclaim evidence.\n\n## 2. Compression vs displacement\n\n**{compression_result['verdict']}**\n\nNormalized MDL (operator **plus scope** is charged):\n\n- operator+scope: {mdl['operator_plus_scope']}\n- two training one-offs: {mdl['two_training_oneoffs']}\n- three positive one-offs incl. sealed transfer: {mdl['three_positive_oneoffs']}\n\nHelpful-only MDL agreement across encodings: **{compression_result['helpful_positive_class']['all_mdl_encodings_agree']}**.\n\nThe candidate-menu search proxy favors reuse ({search_proxy['cold_upper_menu_exposures']} cold menu exposures vs {search_proxy['warm_total_decisions']} warm scope/application decisions across three positive sites), but this is **not measured runtime**.\n\nThe decisive full-class result is negative: the later harmful case was inside the learned scope, there were zero admissible refinement candidates, and V51 correctly chose **REVOKE**. Therefore this experiment does **not** establish durable class compression after scope/activation complexity and counterevidence are charged.\n\n## What this answers\n\nBao boundary test: **partially passed**. The obstruction survives reasonable structural granularity/composition changes, but deliberately disappears when the boundary is semantically expanded enough to include substitution.\n\nBao compression test: **not closed by V51**. There is helpful-class/search compression signal, but the governed abstraction does not survive the full observed evidence class.\n\n## Next clean test\n\n{result['next_required_test']}\n"""
(OUT / "REPORT.md").write_text(md)
print(md)
print("RESULT", OUT / "RESULT.json")
