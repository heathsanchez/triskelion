from developmental_runtime.longitudinal import classify_longitudinal_result


def base_record():
    return {
        "apparatus": {
            "same_task_order": True,
            "matched_model_budget": True,
            "matched_verifier_access": True,
            "protected_boundary_clean": True,
            "fresh_arm_state": True,
        },
        "developmental_gate": {
            "reached": True,
            "prospective_ancestor_fixed": True,
            "ancestor_acquisition_native_verified": True,
            "ancestor_acquisition_ablation_causal": True,
            "downstream_source_distinct": True,
            "downstream_native_verified": True,
            "downstream_not_discoverable_ancestor_minus": True,
            "downstream_discoverable_dev": True,
            "frontier_shift_preanswer": True,
            "restart_exact": True,
        },
        "practical": {
            "reached": True,
            "dev_beats_strongest_comparator": True,
            "matched_total_budget": True,
            "no_extra_verifier_access": True,
        },
    }


def test_pass_requires_every_frozen_causal_predicate():
    verdict = classify_longitudinal_result(base_record())
    assert verdict.verdict == "PASS_NATURAL_LONGITUDINAL_DEVELOPMENT"
    assert verdict.developmental_pass is True
    assert verdict.practical_advantage is True


def test_valid_no_separation_is_negative_not_obstructed():
    record = base_record()
    record["developmental_gate"]["downstream_not_discoverable_ancestor_minus"] = False
    verdict = classify_longitudinal_result(record)
    assert verdict.verdict == "NEGATIVE"
    assert verdict.developmental_pass is False


def test_gate_not_reached_is_obstructed_not_negative():
    record = base_record()
    record["developmental_gate"] = {"reached": False, "obstruction": "constructor ceiling"}
    verdict = classify_longitudinal_result(record)
    assert verdict.verdict == "OBSTRUCTED"
    assert verdict.developmental_pass is False


def test_bad_apparatus_is_obstructed_even_if_scientific_fields_claim_pass():
    record = base_record()
    record["apparatus"]["protected_boundary_clean"] = False
    verdict = classify_longitudinal_result(record)
    assert verdict.verdict == "OBSTRUCTED"
    assert verdict.developmental_pass is False
