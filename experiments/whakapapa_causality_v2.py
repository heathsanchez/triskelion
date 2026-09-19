#!/usr/bin/env python3
from __future__ import annotations

from itertools import combinations
from pathlib import Path
import hashlib
import json

from experiments.whakapapa_causality_v1 import (
    ARMS,
    CAP_ORDER,
    PRIMITIVE_IDS,
    ancestry_edge_count,
    build_scenario,
    capability_digest,
    descendants,
    flat_t1_candidates,
    flat_t2_candidates,
    full_closure_graph,
    pair_search,
    reconstruct_graph,
    relabel_scenario,
    run_nucleus_arm,
    severed_graph,
    t1_future_discovery,
    t2_recombination,
    t4_regeneration,
    world_configs,
)

PROTOCOL = "WHAKAPAPA_CAUSALITY_V2"
PRECOMMIT_COMMIT = "6331b2eb8bf4e1fcb015d019c11176e230af5cff"

WORLD_BASE_SEEDS = {
    "binary": "TRISKELION_WHAKAPAPA_V2_BINARY",
    "ternary": "TRISKELION_WHAKAPAPA_V2_TERNARY",
    "symbolic": "TRISKELION_WHAKAPAPA_V2_SYMBOLIC",
    "temporal": "TRISKELION_WHAKAPAPA_V2_TEMPORAL",
    "graph": "TRISKELION_WHAKAPAPA_V2_GRAPH",
}

ANCESTRY_ARMS = (
    "TRUE_MIN",
    "FULL_CLOSURE",
    "FLAT",
    "SEVERED",
    "SHAM_V2",
    "RECONSTRUCT",
    "COLD",
)

ANCHOR_ORDER = ("G2", "L3", "R3", "L4", "R4")


def sha(*parts: object) -> str:
    return hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest()


def select_admissible_scenario(config, base_seed: str):
    errors = []
    for index in range(256):
        candidate_seed = f"{base_seed}:WORLD:{index:03d}"
        try:
            scenario = build_scenario(config, candidate_seed)
            return {
                "scenario": scenario,
                "selected_seed": candidate_seed,
                "rejected_worlds": index,
                "rejection_examples": errors[:8],
            }
        except RuntimeError as exc:
            errors.append(str(exc))
    return {
        "scenario": None,
        "selected_seed": None,
        "rejected_worlds": 256,
        "rejection_examples": errors[:8],
    }


def topological_parent_choices(node: str) -> list[tuple[str, ...]]:
    available = list(PRIMITIVE_IDS)
    for candidate in CAP_ORDER:
        if candidate == node:
            break
        available.append(candidate)
    return [
        tuple(sorted(pair))
        for pair in combinations(sorted(available), 2)
    ]


def sham_v2_graph(
    true_graph: dict[str, tuple[str, ...]],
    seed: str,
) -> tuple[dict[str, tuple[str, ...]] | None, str | None, int]:
    """Return a same-in-degree, acyclic, causally distinct false ancestry.

    Candidate graphs are generated deterministically from SHA-ranked legal
    parent-set choices. The chosen graph is the first candidate that differs
    from TRUE_MIN and changes at least one frozen revocation-anchor descendant
    cone.
    """
    for attempt in range(4096):
        graph: dict[str, tuple[str, ...]] = {}
        for node in CAP_ORDER:
            choices = topological_parent_choices(node)
            width = len(true_graph[node])
            choices = [pair for pair in choices if len(pair) == width]
            choices.sort(
                key=lambda pair: sha(seed, "SHAM_V2", attempt, node, pair)
            )
            if not choices:
                graph[node] = true_graph[node]
                continue
            graph[node] = choices[0]

        if graph == true_graph:
            continue

        for anchor in ANCHOR_ORDER:
            true_desc = descendants(true_graph, anchor)
            if not true_desc:
                continue
            sham_desc = descendants(graph, anchor)
            if sham_desc != true_desc:
                return graph, anchor, attempt

    return None, None, 4096


def t3_revocation_v2(
    graph: dict[str, tuple[str, ...]] | None,
    *,
    conservative_flat: bool,
    true_graph: dict[str, tuple[str, ...]],
    anchor: str,
) -> dict[str, object]:
    true_invalid = {anchor} | descendants(true_graph, anchor)

    if conservative_flat:
        proposed = set(CAP_ORDER)
    else:
        if graph is None:
            return {
                "anchor": anchor,
                "true_invalid": sorted(true_invalid),
                "safe": False,
                "unsafe_before_repair": sorted(true_invalid),
                "unsafe_after_repair": sorted(true_invalid),
                "initial_requalified": 0,
                "repair_checks": 0,
                "total_requalification_checks": 0,
                "unnecessary_before_repair": [],
            }
        proposed = {anchor} | descendants(graph, anchor)

    unsafe_before = sorted(true_invalid - proposed)
    unnecessary_before = sorted(proposed - true_invalid)
    initial_checks = len(proposed)

    repair_checks = 0
    if unsafe_before:
        repair_checks = len(set(CAP_ORDER) - proposed)
        proposed = set(CAP_ORDER)

    unsafe_after = sorted(true_invalid - proposed)

    return {
        "anchor": anchor,
        "true_invalid": sorted(true_invalid),
        "safe": not unsafe_after,
        "unsafe_before_repair": unsafe_before,
        "unsafe_after_repair": unsafe_after,
        "initial_requalified": initial_checks,
        "repair_checks": repair_checks,
        "total_requalification_checks": initial_checks + repair_checks,
        "unnecessary_before_repair": unnecessary_before,
    }


def ancestry_variants_v2(scenario, frozen_state, generated_graph):
    reconstruction, subset_tests, verifier_checks = reconstruct_graph(
        scenario.config,
        frozen_state,
    )
    sham, anchor, sham_attempt = sham_v2_graph(
        generated_graph,
        scenario.seed,
    )

    variants = {
        "TRUE_MIN": dict(generated_graph),
        "FULL_CLOSURE": full_closure_graph(generated_graph),
        "FLAT": {node: () for node in CAP_ORDER},
        "SEVERED": severed_graph(generated_graph, scenario.seed),
        "SHAM_V2": sham,
        "RECONSTRUCT": reconstruction,
        "COLD": None,
    }

    return variants, {
        "reconstruction": {
            "graph": reconstruction,
            "exact_graph_recovery": reconstruction == generated_graph,
            "parent_subset_tests": subset_tests,
            "verifier_checks": verifier_checks,
        },
        "sham": {
            "identified": sham is not None and anchor is not None,
            "anchor": anchor,
            "attempt": sham_attempt,
            "graph": sham,
            "true_descendants": (
                None if anchor is None
                else sorted(descendants(generated_graph, anchor))
            ),
            "sham_descendants": (
                None if sham is None or anchor is None
                else sorted(descendants(sham, anchor))
            ),
        },
    }


def evaluate_ancestry_v2(scenario, frozen_state, generated_graph):
    variants, metadata = ancestry_variants_v2(
        scenario,
        frozen_state,
        generated_graph,
    )
    anchor = metadata["sham"]["anchor"] or "G2"
    digest = capability_digest(frozen_state)
    arms = {}

    for arm in ANCESTRY_ARMS:
        graph = variants[arm]

        if arm == "COLD":
            arms[arm] = {
                "content_digest": None,
                "edge_count": 0,
                "T1_future_discovery": {
                    "ok": False, "checks": 0, "parents": []
                },
                "T2_recombination": {
                    "ok": False, "checks": 0, "parents": []
                },
                "T3_revocation": {
                    "anchor": anchor,
                    "safe": True,
                    "unsafe_before_repair": [],
                    "unsafe_after_repair": [],
                    "total_requalification_checks": 0,
                },
                "T4_regeneration": {
                    "ok": False, "checks": 0, "parents": []
                },
            }
            continue

        state = frozen_state

        if arm == "FLAT":
            t1 = pair_search(
                target=scenario.future_f1,
                state=state,
                candidate_pairs=flat_t1_candidates(),
                budget=None,
            )
            t2 = pair_search(
                target=scenario.future_f2,
                state=state,
                candidate_pairs=flat_t2_candidates(),
                budget=8,
            )
            t3 = t3_revocation_v2(
                None,
                conservative_flat=True,
                true_graph=generated_graph,
                anchor=anchor,
            )
        else:
            if graph is None:
                t1 = {"ok": False, "checks": 0, "parents": []}
                t2 = {"ok": False, "checks": 0, "parents": []}
                t3 = t3_revocation_v2(
                    None,
                    conservative_flat=False,
                    true_graph=generated_graph,
                    anchor=anchor,
                )
            else:
                t1 = t1_future_discovery(scenario, state, graph)
                t2 = t2_recombination(scenario, state, graph)
                t3 = t3_revocation_v2(
                    graph,
                    conservative_flat=False,
                    true_graph=generated_graph,
                    anchor=anchor,
                )

        t4_arm = "SHAM" if arm == "SHAM_V2" else arm
        t4 = t4_regeneration(
            scenario,
            state,
            graph,
            t4_arm,
        )

        arms[arm] = {
            "content_digest": digest,
            "edge_count": (
                0 if graph is None else ancestry_edge_count(graph)
            ),
            "T1_future_discovery": t1,
            "T2_recombination": t2,
            "T3_revocation": t3,
            "T4_regeneration": t4,
        }

    same_content = len({
        arms[arm]["content_digest"]
        for arm in ANCESTRY_ARMS
        if arm != "COLD"
    }) == 1

    return {
        "arms": arms,
        "reconstruction": metadata["reconstruction"],
        "sham": metadata["sham"],
        "same_capability_content_non_cold": same_content,
    }


def evaluate_scenario_v2(scenario):
    nucleus_runs = {
        arm: run_nucleus_arm(scenario, arm)
        for arm in ARMS
    }
    dmi = nucleus_runs["DMI"]
    full = dmi["depth"] == len(CAP_ORDER)
    graph_exact = (
        full
        and dmi["generated_graph"] == scenario.hidden_graph
    )

    ancestry = None
    if full:
        ancestry = evaluate_ancestry_v2(
            scenario,
            dmi["_state"],
            dmi["generated_graph"],
        )

    return {
        "world_id": scenario.config.world_id,
        "surface": scenario.config.surface,
        "nucleus": {
            arm: {
                key: value
                for key, value in run.items()
                if not key.startswith("_")
            }
            for arm, run in nucleus_runs.items()
        },
        "generated_graph_exact": graph_exact,
        "ancestry": ancestry,
    }


def metamorphic_signature_v2(result):
    ancestry = result["ancestry"]
    true = ancestry["arms"]["TRUE_MIN"]
    flat = ancestry["arms"]["FLAT"]
    sham = ancestry["arms"]["SHAM_V2"]

    return {
        "dmi_depth": result["nucleus"]["DMI"]["depth"],
        "graph_exact": result["generated_graph_exact"],
        "true_t1_ok": true["T1_future_discovery"]["ok"],
        "true_t1_beats_flat": (
            true["T1_future_discovery"]["checks"]
            < flat["T1_future_discovery"]["checks"]
        ),
        "true_t2_ok": true["T2_recombination"]["ok"],
        "true_t3_safe": true["T3_revocation"]["safe"],
        "sham_unsafe_or_more_expensive": (
            bool(sham["T3_revocation"]["unsafe_before_repair"])
            or sham["T3_revocation"]["total_requalification_checks"]
            > true["T3_revocation"]["total_requalification_checks"]
        ),
        "true_t4_ok": true["T4_regeneration"]["ok"],
        "true_t4_beats_flat": (
            not flat["T4_regeneration"]["ok"]
            or true["T4_regeneration"]["checks"]
            < flat["T4_regeneration"]["checks"]
        ),
    }


def evaluate_selected_world(config, base_seed: str, do_relabel: bool):
    selected = select_admissible_scenario(config, base_seed)
    scenario = selected["scenario"]

    if scenario is None:
        return {
            "selected": {
                key: value
                for key, value in selected.items()
                if key != "scenario"
            },
            "base": None,
            "relabelled": None,
            "metamorphic_pass": None,
        }

    base = evaluate_scenario_v2(scenario)
    relabelled = None
    metamorphic_pass = None

    if do_relabel:
        relabelled = evaluate_scenario_v2(
            relabel_scenario(scenario)
        )
        metamorphic_pass = (
            metamorphic_signature_v2(base)
            == metamorphic_signature_v2(relabelled)
        )

    return {
        "selected": {
            key: value
            for key, value in selected.items()
            if key != "scenario"
        },
        "base": base,
        "relabelled": relabelled,
        "metamorphic_pass": metamorphic_pass,
    }


def headline_nucleus_gates(headline):
    selected_all = all(
        world["base"] is not None
        for world in headline.values()
    )

    if not selected_all:
        return {
            "N1_same_imported_nucleus_all_worlds": True,
            "N2_admissible_world_selected_all_headlines": False,
            "N3_dmi_full_lineage_all_worlds": False,
            "N4_generated_graph_exact_all_worlds": False,
            "N5_cold_not_full_all_worlds": False,
            "N6_remove_i_reduces_reach_all_worlds": False,
            "N7_remove_m_reduces_reach_all_worlds": False,
            "N8_remove_d_reach_or_cost_penalty_all_worlds": False,
            "N9_no_proper_subset_matches_full_all_worlds": False,
        }

    def n(world):
        return world["base"]["nucleus"]

    n3 = all(n(world)["DMI"]["depth"] == 8 for world in headline.values())
    n4 = all(
        world["base"]["generated_graph_exact"]
        for world in headline.values()
    )
    n5 = all(
        n(world)["DMI_COLD"]["depth"] < 8
        for world in headline.values()
    )
    n6 = all(
        n(world)["DM"]["depth"] < n(world)["DMI"]["depth"]
        for world in headline.values()
    )
    n7 = all(
        n(world)["DI"]["depth"] < n(world)["DMI"]["depth"]
        for world in headline.values()
    )
    n8 = all(
        (
            n(world)["MI"]["depth"] < n(world)["DMI"]["depth"]
        )
        or (
            n(world)["MI"]["depth"] == n(world)["DMI"]["depth"]
            and n(world)["MI"]["verifier_candidate_checks"]
            > n(world)["DMI"]["verifier_candidate_checks"]
        )
        for world in headline.values()
    )

    proper = ("NONE", "D", "M", "I", "DM", "DI", "MI")
    n9 = all(
        all(
            n(world)[arm]["depth"] < 8
            or n(world)[arm]["verifier_candidate_checks"]
            > n(world)["DMI"]["verifier_candidate_checks"]
            for arm in proper
        )
        for world in headline.values()
    )

    return {
        "N1_same_imported_nucleus_all_worlds": True,
        "N2_admissible_world_selected_all_headlines": True,
        "N3_dmi_full_lineage_all_worlds": n3,
        "N4_generated_graph_exact_all_worlds": n4,
        "N5_cold_not_full_all_worlds": n5,
        "N6_remove_i_reduces_reach_all_worlds": n6,
        "N7_remove_m_reduces_reach_all_worlds": n7,
        "N8_remove_d_reach_or_cost_penalty_all_worlds": n8,
        "N9_no_proper_subset_matches_full_all_worlds": n9,
    }


def headline_whakapapa_gates(headline):
    if any(world["base"] is None for world in headline.values()):
        return {
            "W1_true_min_success_t1_t4_all_worlds": False,
            "W2_true_min_t1_cheaper_than_flat_all_worlds": False,
            "W3_true_min_t2_beats_flat_all_worlds": False,
            "W4_true_min_exact_safe_revocation_all_worlds": False,
            "W5_sham_v2_identified_and_causally_separates_all_worlds": False,
            "W6_true_min_regeneration_beats_flat_all_worlds": False,
            "W7_true_min_equals_full_closure_with_fewer_edges": False,
            "W8_reconstruction_positive_work_all_worlds": False,
            "W9_representation_metamorphism": False,
            "W10_same_capability_content_non_cold": False,
        }

    ancestry = [
        world["base"]["ancestry"]
        for world in headline.values()
    ]

    def arm(a, name):
        return a["arms"][name]

    w1 = all(
        arm(a, "TRUE_MIN")["T1_future_discovery"]["ok"]
        and arm(a, "TRUE_MIN")["T2_recombination"]["ok"]
        and arm(a, "TRUE_MIN")["T3_revocation"]["safe"]
        and arm(a, "TRUE_MIN")["T4_regeneration"]["ok"]
        for a in ancestry
    )
    w2 = all(
        arm(a, "TRUE_MIN")["T1_future_discovery"]["checks"]
        < arm(a, "FLAT")["T1_future_discovery"]["checks"]
        for a in ancestry
    )
    w3 = all(
        arm(a, "TRUE_MIN")["T2_recombination"]["ok"]
        and (
            not arm(a, "FLAT")["T2_recombination"]["ok"]
            or arm(a, "TRUE_MIN")["T2_recombination"]["checks"]
            < arm(a, "FLAT")["T2_recombination"]["checks"]
        )
        for a in ancestry
    )
    w4 = all(
        arm(a, "TRUE_MIN")["T3_revocation"]["safe"]
        and not arm(a, "TRUE_MIN")["T3_revocation"]["unsafe_before_repair"]
        for a in ancestry
    )
    w5 = all(
        a["sham"]["identified"]
        and (
            bool(arm(a, "SHAM_V2")["T3_revocation"]["unsafe_before_repair"])
            or arm(a, "SHAM_V2")["T3_revocation"]["total_requalification_checks"]
            > arm(a, "TRUE_MIN")["T3_revocation"]["total_requalification_checks"]
        )
        for a in ancestry
    )
    w6 = all(
        arm(a, "TRUE_MIN")["T4_regeneration"]["ok"]
        and (
            not arm(a, "FLAT")["T4_regeneration"]["ok"]
            or arm(a, "TRUE_MIN")["T4_regeneration"]["checks"]
            < arm(a, "FLAT")["T4_regeneration"]["checks"]
        )
        for a in ancestry
    )
    w7 = all(
        arm(a, "TRUE_MIN")["T1_future_discovery"]["ok"]
        == arm(a, "FULL_CLOSURE")["T1_future_discovery"]["ok"]
        and arm(a, "TRUE_MIN")["T2_recombination"]["ok"]
        == arm(a, "FULL_CLOSURE")["T2_recombination"]["ok"]
        and arm(a, "TRUE_MIN")["T3_revocation"]["safe"]
        == arm(a, "FULL_CLOSURE")["T3_revocation"]["safe"]
        and arm(a, "TRUE_MIN")["T4_regeneration"]["ok"]
        == arm(a, "FULL_CLOSURE")["T4_regeneration"]["ok"]
        and arm(a, "TRUE_MIN")["edge_count"]
        < arm(a, "FULL_CLOSURE")["edge_count"]
        for a in ancestry
    )
    w8 = all(
        a["reconstruction"]["parent_subset_tests"] > 0
        for a in ancestry
    )
    w9 = all(
        world["metamorphic_pass"] is True
        for world_id, world in headline.items()
        if world_id != "graph"
    )
    w10 = all(
        a["same_capability_content_non_cold"]
        for a in ancestry
    )

    return {
        "W1_true_min_success_t1_t4_all_worlds": w1,
        "W2_true_min_t1_cheaper_than_flat_all_worlds": w2,
        "W3_true_min_t2_beats_flat_all_worlds": w3,
        "W4_true_min_exact_safe_revocation_all_worlds": w4,
        "W5_sham_v2_identified_and_causally_separates_all_worlds": w5,
        "W6_true_min_regeneration_beats_flat_all_worlds": w6,
        "W7_true_min_equals_full_closure_with_fewer_edges": w7,
        "W8_reconstruction_positive_work_all_worlds": w8,
        "W9_representation_metamorphism": w9,
        "W10_same_capability_content_non_cold": w10,
    }


def sweep_summary(rows):
    total = len(rows)
    selected = [row for row in rows if row["result"]["base"] is not None]

    def base(row):
        return row["result"]["base"]

    admissible = len(selected)
    dmi_full = sum(
        base(row)["nucleus"]["DMI"]["depth"] == 8
        for row in selected
    )
    graph_exact = sum(
        base(row)["generated_graph_exact"]
        for row in selected
    )
    cold_full = sum(
        base(row)["nucleus"]["DMI_COLD"]["depth"] == 8
        for row in selected
    )
    dm_loss = sum(
        base(row)["nucleus"]["DM"]["depth"]
        < base(row)["nucleus"]["DMI"]["depth"]
        for row in selected
    )
    di_loss = sum(
        base(row)["nucleus"]["DI"]["depth"]
        < base(row)["nucleus"]["DMI"]["depth"]
        for row in selected
    )
    mi_penalty = sum(
        (
            base(row)["nucleus"]["MI"]["depth"]
            < base(row)["nucleus"]["DMI"]["depth"]
        )
        or (
            base(row)["nucleus"]["MI"]["depth"]
            == base(row)["nucleus"]["DMI"]["depth"]
            and base(row)["nucleus"]["MI"]["verifier_candidate_checks"]
            > base(row)["nucleus"]["DMI"]["verifier_candidate_checks"]
        )
        for row in selected
    )

    true_t1_success = 0
    true_t1_cheaper = 0
    true_t2_success = 0
    true_t3_safe = 0
    sham_sep = 0
    true_t4_success = 0
    true_t4_cheaper = 0
    true_full_equiv = 0
    sham_identified = 0

    for row in selected:
        a = base(row)["ancestry"]
        true = a["arms"]["TRUE_MIN"]
        flat = a["arms"]["FLAT"]
        sham = a["arms"]["SHAM_V2"]
        full = a["arms"]["FULL_CLOSURE"]

        true_t1_success += int(true["T1_future_discovery"]["ok"])
        true_t1_cheaper += int(
            true["T1_future_discovery"]["ok"]
            and true["T1_future_discovery"]["checks"]
            < flat["T1_future_discovery"]["checks"]
        )
        true_t2_success += int(true["T2_recombination"]["ok"])
        true_t3_safe += int(true["T3_revocation"]["safe"])
        sham_identified += int(a["sham"]["identified"])
        sham_sep += int(
            a["sham"]["identified"]
            and (
                bool(sham["T3_revocation"]["unsafe_before_repair"])
                or sham["T3_revocation"]["total_requalification_checks"]
                > true["T3_revocation"]["total_requalification_checks"]
            )
        )
        true_t4_success += int(true["T4_regeneration"]["ok"])
        true_t4_cheaper += int(
            true["T4_regeneration"]["ok"]
            and (
                not flat["T4_regeneration"]["ok"]
                or true["T4_regeneration"]["checks"]
                < flat["T4_regeneration"]["checks"]
            )
        )
        true_full_equiv += int(
            true["T1_future_discovery"]["ok"]
            == full["T1_future_discovery"]["ok"]
            and true["T2_recombination"]["ok"]
            == full["T2_recombination"]["ok"]
            and true["T3_revocation"]["safe"]
            == full["T3_revocation"]["safe"]
            and true["T4_regeneration"]["ok"]
            == full["T4_regeneration"]["ok"]
        )

    nucleus_criteria = {
        "S_N1_admissible_ge_124": admissible >= 124,
        "S_N2_dmi_full_ge_120": dmi_full >= 120,
        "S_N3_graph_exact_ge_120": graph_exact >= 120,
        "S_N4_cold_full_le_5": cold_full <= 5,
        "S_N5_dm_loss_ge_115": dm_loss >= 115,
        "S_N6_di_loss_ge_115": di_loss >= 115,
        "S_N7_mi_penalty_ge_115": mi_penalty >= 115,
    }
    whakapapa_criteria = {
        "S_W1_true_t1_success_ge_120": true_t1_success >= 120,
        "S_W2_true_t1_cheaper_ge_115": true_t1_cheaper >= 115,
        "S_W3_true_t2_success_ge_115": true_t2_success >= 115,
        "S_W4_true_t3_safe_ge_120": true_t3_safe >= 120,
        "S_W5_sham_identified_and_separates_ge_115": sham_sep >= 115,
        "S_W6_true_t4_success_ge_120": true_t4_success >= 120,
        "S_W7_true_t4_cheaper_ge_115": true_t4_cheaper >= 115,
        "S_W8_true_full_equiv_ge_120": true_full_equiv >= 120,
    }

    return {
        "worlds": total,
        "admissible_worlds": admissible,
        "failed_world_selection": total - admissible,
        "dmi_full_lineage": dmi_full,
        "generated_graph_exact": graph_exact,
        "cold_full_lineage": cold_full,
        "dm_reach_loss": dm_loss,
        "di_reach_loss": di_loss,
        "mi_reach_or_cost_penalty": mi_penalty,
        "true_t1_success": true_t1_success,
        "true_t1_cheaper_than_flat": true_t1_cheaper,
        "true_t2_success": true_t2_success,
        "true_t3_safe": true_t3_safe,
        "sham_identified": sham_identified,
        "sham_identified_and_causal_separator": sham_sep,
        "true_t4_success": true_t4_success,
        "true_t4_cheaper_than_flat": true_t4_cheaper,
        "true_full_closure_correctness_equiv": true_full_equiv,
        "nucleus_criteria": nucleus_criteria,
        "whakapapa_criteria": whakapapa_criteria,
        "nucleus_strong_pass": all(nucleus_criteria.values()),
        "whakapapa_strong_pass": all(whakapapa_criteria.values()),
    }


def classify(nucleus_gates, whakapapa_gates, sweep):
    nucleus_headline = all(nucleus_gates.values())
    whakapapa_headline = all(whakapapa_gates.values())
    nucleus_strong = bool(sweep["nucleus_strong_pass"])
    whakapapa_strong = bool(sweep["whakapapa_strong_pass"])

    if nucleus_headline and whakapapa_headline and nucleus_strong and whakapapa_strong:
        return "PASS_WHAKAPAPA_CAUSALITY_AND_BOUNDED_IRREDUCIBLE_NUCLEUS_V2"

    nucleus_core = all(
        value
        for key, value in nucleus_gates.items()
        if key not in {
            "N8_remove_d_reach_or_cost_penalty_all_worlds",
            "N9_no_proper_subset_matches_full_all_worlds",
        }
    )
    role_reduced = not (
        nucleus_gates["N8_remove_d_reach_or_cost_penalty_all_worlds"]
        and nucleus_gates["N9_no_proper_subset_matches_full_all_worlds"]
    )

    if whakapapa_headline and whakapapa_strong and nucleus_core and role_reduced:
        return "PASS_WHAKAPAPA_CAUSALITY_REDUCED_NUCLEUS_V2"
    if nucleus_headline and nucleus_strong and not (whakapapa_headline and whakapapa_strong):
        return "NUCLEUS_PASS_WHAKAPAPA_NEGATIVE_V2"
    if whakapapa_headline and whakapapa_strong:
        return "WHAKAPAPA_PASS_NUCLEUS_PARTIAL_V2"
    if any(nucleus_gates.values()) or any(whakapapa_gates.values()):
        return "PARTIAL_WHAKAPAPA_CAUSALITY_V2"
    return "VALID_NEGATIVE_WHAKAPAPA_CAUSALITY_V2"


def compact_world(world):
    if world["base"] is None:
        return {
            "selected": world["selected"],
            "base": None,
            "metamorphic_pass": world["metamorphic_pass"],
        }

    base = world["base"]
    ancestry = base["ancestry"]
    return {
        "selected": world["selected"],
        "nucleus_depths": {
            arm: base["nucleus"][arm]["depth"]
            for arm in ARMS
        },
        "nucleus_typed_cost": {
            arm: {
                "distinction_tests": base["nucleus"][arm]["distinction_tests"],
                "verifier_candidate_checks": base["nucleus"][arm][
                    "verifier_candidate_checks"
                ],
            }
            for arm in ("MI", "DMI", "ORACLE_STACK")
        },
        "generated_graph_exact": base["generated_graph_exact"],
        "generated_graph": base["nucleus"]["DMI"]["generated_graph"],
        "ancestry": ancestry,
        "metamorphic_pass": world["metamorphic_pass"],
    }


def main() -> int:
    configs = world_configs()

    headline = {
        world_id: evaluate_selected_world(
            configs[world_id],
            WORLD_BASE_SEEDS[world_id],
            do_relabel=(world_id != "graph"),
        )
        for world_id in WORLD_BASE_SEEDS
    }

    nucleus_gates = headline_nucleus_gates(headline)
    whakapapa_gates = headline_whakapapa_gates(headline)

    sweep_rows = []
    for world_id in WORLD_BASE_SEEDS:
        config = configs[world_id]
        for index in range(25):
            base_seed = f"{WORLD_BASE_SEEDS[world_id]}:SWEEP:{index:03d}"
            result = evaluate_selected_world(
                config,
                base_seed,
                do_relabel=False,
            )
            sweep_rows.append(
                {
                    "world_id": world_id,
                    "base_seed": base_seed,
                    "result": result,
                }
            )

    sweep = sweep_summary(sweep_rows)
    verdict = classify(nucleus_gates, whakapapa_gates, sweep)

    result = {
        "protocol": PROTOCOL,
        "precommit_commit": PRECOMMIT_COMMIT,
        "headline": {
            world_id: compact_world(world)
            for world_id, world in headline.items()
        },
        "headline_nucleus_gates": nucleus_gates,
        "headline_whakapapa_gates": whakapapa_gates,
        "sweep": sweep,
        "verdict": verdict,
        "claim_boundary": (
            "Bounded finite cross-world test conditioned on mechanically "
            "selected admissible synthetic worlds. Supports only the frozen "
            "D/M/I and verified-ancestry causal claims under this experimental "
            "family. It does not establish metaphysical inevitability, unique "
            "minimality over all algorithms, unrestricted intelligence, or the "
            "full cultural meaning of whakapapa."
        ),
    }

    outdir = Path("results/whakapapa_causality_v2")
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str) + "\n"
    )

    compact_sweep = []
    for row in sweep_rows:
        r = row["result"]
        base = r["base"]
        if base is None:
            compact_sweep.append(
                {
                    "world_id": row["world_id"],
                    "base_seed": row["base_seed"],
                    "selected": r["selected"],
                    "world_selection_failed": True,
                }
            )
            continue

        a = base["ancestry"]
        compact_sweep.append(
            {
                "world_id": row["world_id"],
                "base_seed": row["base_seed"],
                "selected": r["selected"],
                "nucleus_depths": {
                    arm: base["nucleus"][arm]["depth"]
                    for arm in ARMS
                },
                "graph_exact": base["generated_graph_exact"],
                "sham": a["sham"],
                "true_t1": a["arms"]["TRUE_MIN"]["T1_future_discovery"],
                "flat_t1": a["arms"]["FLAT"]["T1_future_discovery"],
                "true_t2": a["arms"]["TRUE_MIN"]["T2_recombination"],
                "true_t3": a["arms"]["TRUE_MIN"]["T3_revocation"],
                "sham_t3": a["arms"]["SHAM_V2"]["T3_revocation"],
                "true_t4": a["arms"]["TRUE_MIN"]["T4_regeneration"],
                "flat_t4": a["arms"]["FLAT"]["T4_regeneration"],
            }
        )

    (outdir / "sweep.json").write_text(
        json.dumps(compact_sweep, indent=2, sort_keys=True, default=str) + "\n"
    )

    print("=" * 104)
    print("WHAKAPAPA CAUSALITY V2")
    print("=" * 104)
    for world_id, world in result["headline"].items():
        print(world_id, "selected=", world["selected"])
        if world.get("base") is None and "nucleus_depths" not in world:
            print("  WORLD_SELECTION_FAILED")
            continue
        print("  nucleus", json.dumps(world["nucleus_depths"], sort_keys=True))
        print("  graph_exact", world["generated_graph_exact"])
        print("  metamorphic", world["metamorphic_pass"])
        true = world["ancestry"]["arms"]["TRUE_MIN"]
        flat = world["ancestry"]["arms"]["FLAT"]
        sham = world["ancestry"]["arms"]["SHAM_V2"]
        print("  sham", world["ancestry"]["sham"])
        print("  T1 true/flat", true["T1_future_discovery"], flat["T1_future_discovery"])
        print("  T2 true/flat", true["T2_recombination"], flat["T2_recombination"])
        print("  T3 true/sham", true["T3_revocation"], sham["T3_revocation"])
        print("  T4 true/flat", true["T4_regeneration"], flat["T4_regeneration"])

    print("-" * 104)
    print("NUCLEUS GATES")
    for key, value in nucleus_gates.items():
        print(key, "PASS" if value else "FAIL")
    print("WHAKAPAPA GATES")
    for key, value in whakapapa_gates.items():
        print(key, "PASS" if value else "FAIL")
    print("-" * 104)
    print(json.dumps(sweep, indent=2, sort_keys=True))
    print(verdict)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
