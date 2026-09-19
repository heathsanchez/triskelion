#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
import copy
import hashlib
import json
from typing import Hashable

from experiments.cross_world_nucleus_invariance_v1 import (
    ARMS,
    Feature,
    WorldConfig,
    differentiate,
    fit_finite_relation,
    generated_target,
    initial_state,
    relabel_config,
    relabel_map,
    solve_episode,
    stable,
    world_configs,
)

PROTOCOL = "WHAKAPAPA_CAUSALITY_V1"
PRECOMMIT_COMMIT = "ad5e8349c24f82db8fbe917288e2cd2beefed1aa"
ADDENDUM_COMMIT = "8dcb5858ca6a0b7add988b2bc4298b15e4dd4ec1"

CAP_ORDER = ("G1", "G2", "L3", "L4", "R3", "R4", "X5", "X6")
TOPOLOGY = (
    ("G1", "q0", "q1"),
    ("G2", "G1", "q2"),
    ("L3", "G2", "q3"),
    ("L4", "L3", "q0"),
    ("R3", "G2", "q0"),
    ("R4", "R3", "q1"),
    ("X5", "L4", "R4"),
    ("X6", "X5", "q2"),
)
PRIMITIVE_IDS = ("q0", "q1", "q2", "q3")

WORLD_SEEDS = {
    "binary": "TRISKELION_WHAKAPAPA_V1_BINARY",
    "ternary": "TRISKELION_WHAKAPAPA_V1_TERNARY",
    "symbolic": "TRISKELION_WHAKAPAPA_V1_SYMBOLIC",
    "temporal": "TRISKELION_WHAKAPAPA_V1_TEMPORAL",
    "graph": "TRISKELION_WHAKAPAPA_V1_GRAPH",
}

ANCESTRY_ARMS = (
    "TRUE_MIN",
    "FULL_CLOSURE",
    "FLAT",
    "SEVERED",
    "SHAM",
    "RECONSTRUCT",
    "COLD",
)


@dataclass(frozen=True)
class LineageEpisode:
    index: int
    node_id: str
    target: tuple[Hashable, ...]
    declared_parents: tuple[str, str]
    counter: int


@dataclass(frozen=True)
class Scenario:
    config: WorldConfig
    seed: str
    episodes: tuple[LineageEpisode, ...]
    hidden_graph: dict[str, tuple[str, ...]]
    future_f1: tuple[Hashable, ...]
    future_f1_parents: tuple[str, str]
    future_f2: tuple[Hashable, ...]
    future_f2_parents: tuple[str, str]


def sha(*parts: object) -> str:
    return hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest()


def feature_state_with_hidden_lineage(
    config: WorldConfig,
    episodes: tuple[LineageEpisode, ...],
) -> dict[str, Feature]:
    state = initial_state(config)
    for episode in episodes:
        state[episode.node_id] = Feature(
            feature_id=episode.node_id,
            values=episode.target,
            dependencies=episode.declared_parents,
            provenance=f"hidden:{episode.node_id}",
        )
    return state


def generate_exact_parent_target(
    *,
    config: WorldConfig,
    active: dict[str, Feature],
    left_id: str,
    right_id: str,
    seed: str,
    stage: str,
    index: int,
) -> tuple[tuple[Hashable, ...], int]:
    wanted = frozenset((left_id, right_id))
    left = active[left_id].values
    right = active[right_id].values

    for counter in range(65536):
        target = generated_target(
            left=left,
            right=right,
            alphabet=config.alphabet,
            seed=f"{seed}:{stage}",
            generation=index,
            counter=counter,
        )
        if any(feature.values == target for feature in active.values()):
            continue

        declared = fit_finite_relation(target, (left, right))
        if declared is None:
            continue

        selected, relation, _ = differentiate(target, active)
        if selected is None or relation is None or len(selected) != 2:
            continue
        if frozenset(selected) != wanted:
            continue

        return target, counter

    raise RuntimeError(
        f"unable to generate exact-parent target {config.world_id} {stage} "
        f"{left_id},{right_id}"
    )


def build_scenario(config: WorldConfig, seed: str) -> Scenario:
    active = initial_state(config)
    episodes: list[LineageEpisode] = []
    hidden_graph: dict[str, tuple[str, ...]] = {}

    for index, (node_id, left_id, right_id) in enumerate(TOPOLOGY, 1):
        target, counter = generate_exact_parent_target(
            config=config,
            active=active,
            left_id=left_id,
            right_id=right_id,
            seed=seed,
            stage=node_id,
            index=index,
        )
        episode = LineageEpisode(
            index=index,
            node_id=node_id,
            target=target,
            declared_parents=(left_id, right_id),
            counter=counter,
        )
        episodes.append(episode)
        hidden_graph[node_id] = tuple(sorted((left_id, right_id)))
        active[node_id] = Feature(
            feature_id=node_id,
            values=target,
            dependencies=tuple(sorted((left_id, right_id))),
            provenance=f"hidden:{seed}:{node_id}:{counter}",
        )

    f1, _ = generate_exact_parent_target(
        config=config,
        active=active,
        left_id="X6",
        right_id="q3",
        seed=seed,
        stage="F1",
        index=101,
    )
    f2, _ = generate_exact_parent_target(
        config=config,
        active=active,
        left_id="L4",
        right_id="R4",
        seed=seed,
        stage="F2",
        index=102,
    )

    return Scenario(
        config=config,
        seed=seed,
        episodes=tuple(episodes),
        hidden_graph=hidden_graph,
        future_f1=f1,
        future_f1_parents=("X6", "q3"),
        future_f2=f2,
        future_f2_parents=("L4", "R4"),
    )


def relabel_scenario(scenario: Scenario) -> Scenario:
    mapping = relabel_map(scenario.config.alphabet)
    config = relabel_config(scenario.config)

    def rv(values: tuple[Hashable, ...]) -> tuple[Hashable, ...]:
        return tuple(mapping[value] for value in values)

    episodes = tuple(
        LineageEpisode(
            index=episode.index,
            node_id=episode.node_id,
            target=rv(episode.target),
            declared_parents=episode.declared_parents,
            counter=episode.counter,
        )
        for episode in scenario.episodes
    )
    return Scenario(
        config=config,
        seed=scenario.seed + ":RELABEL",
        episodes=episodes,
        hidden_graph=dict(scenario.hidden_graph),
        future_f1=rv(scenario.future_f1),
        future_f1_parents=scenario.future_f1_parents,
        future_f2=rv(scenario.future_f2),
        future_f2_parents=scenario.future_f2_parents,
    )


def run_nucleus_arm(scenario: Scenario, arm: str) -> dict[str, object]:
    active = initial_state(scenario.config)
    records = []

    for episode in scenario.episodes:
        if arm == "DMI_COLD":
            active = initial_state(scenario.config)

        result, active = solve_episode(
            target=episode.target,
            episode_id=episode.node_id,
            active=active,
            arm=arm,
            provenance=(
                f"{PRECOMMIT_COMMIT}:{scenario.config.world_id}:"
                f"{scenario.seed}:{episode.node_id}"
            ),
            oracle_parents=(
                episode.declared_parents if arm == "ORACLE_STACK" else None
            ),
        )
        selected = tuple(sorted(result.get("selected_parents", ())))
        result.update(
            {
                "node_id": episode.node_id,
                "declared_parents": list(sorted(episode.declared_parents)),
                "generated_parents": list(selected),
                "parent_match": (
                    bool(result.get("ok"))
                    and selected == tuple(sorted(episode.declared_parents))
                ),
            }
        )
        records.append(result)
        if not result["ok"]:
            break

    generated_graph = {}
    for node_id in CAP_ORDER:
        if node_id in active:
            generated_graph[node_id] = tuple(sorted(active[node_id].dependencies))

    return {
        "arm": arm,
        "depth": sum(1 for row in records if row["ok"]),
        "records": records,
        "generated_graph": generated_graph,
        "distinction_tests": sum(
            int(row.get("distinction_tests", 0)) for row in records
        ),
        "verifier_candidate_checks": sum(
            int(row.get("verifier_candidate_checks", 0)) for row in records
        ),
        "_state": active,
    }


def direct_children(graph: dict[str, tuple[str, ...]]) -> dict[str, set[str]]:
    children: dict[str, set[str]] = {}
    for child, parents in graph.items():
        for parent in parents:
            children.setdefault(parent, set()).add(child)
    return children


def ancestors(
    graph: dict[str, tuple[str, ...]],
    node: str,
) -> set[str]:
    seen: set[str] = set()
    frontier = list(graph.get(node, ()))
    while frontier:
        current = frontier.pop()
        if current in seen:
            continue
        seen.add(current)
        frontier.extend(graph.get(current, ()))
    return seen


def descendants(
    graph: dict[str, tuple[str, ...]],
    node: str,
) -> set[str]:
    children = direct_children(graph)
    seen: set[str] = set()
    frontier = list(children.get(node, ()))
    while frontier:
        current = frontier.pop()
        if current in seen:
            continue
        seen.add(current)
        frontier.extend(children.get(current, ()))
    return seen


def tips(
    graph: dict[str, tuple[str, ...]],
    nodes: tuple[str, ...] = CAP_ORDER,
) -> list[str]:
    children = direct_children(graph)
    active = set(nodes)
    return sorted(
        node
        for node in nodes
        if not any(child in active for child in children.get(node, ()))
    )


def full_closure_graph(
    graph: dict[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    return {
        node: tuple(sorted(ancestors(graph, node)))
        for node in CAP_ORDER
    }


def severed_graph(
    graph: dict[str, tuple[str, ...]],
    seed: str,
) -> dict[str, tuple[str, ...]]:
    out = {}
    for node in CAP_ORDER:
        parents = list(graph[node])
        if len(parents) >= 2:
            drop = int(sha(seed, "SEVER", node)[:8], 16) % len(parents)
            parents.pop(drop)
        out[node] = tuple(sorted(parents))
    return out


def sham_graph(
    graph: dict[str, tuple[str, ...]],
    seed: str,
) -> dict[str, tuple[str, ...]]:
    out: dict[str, tuple[str, ...]] = {}
    available = list(PRIMITIVE_IDS)

    for node in CAP_ORDER:
        true = frozenset(graph[node])
        width = len(graph[node])
        candidates = [
            tuple(sorted(pair))
            for pair in combinations(sorted(available), width)
            if frozenset(pair) != true
        ]
        if not candidates:
            candidates = [tuple(sorted(graph[node]))]
        candidates.sort(key=lambda pair: sha(seed, "SHAM", node, pair))
        out[node] = candidates[0]
        available.append(node)

    return out


def reconstruct_graph(
    config: WorldConfig,
    frozen_state: dict[str, Feature],
) -> tuple[dict[str, tuple[str, ...]], int, int]:
    state = initial_state(config)
    graph = {}
    subset_tests = 0
    verifier_checks = 0

    for node in CAP_ORDER:
        target = frozen_state[node].values
        parent_ids, relation, tested = differentiate(target, state)
        subset_tests += tested
        if parent_ids is None or relation is None:
            graph[node] = ()
            continue

        proposal_ok = all(
            relation.get(
                tuple(state[parent].values[row] for parent in parent_ids)
            )
            == target[row]
            for row in range(len(target))
        )
        verifier_checks += 1
        if not proposal_ok:
            graph[node] = ()
            continue

        graph[node] = tuple(sorted(parent_ids))
        state[node] = Feature(
            feature_id=node,
            values=target,
            dependencies=tuple(sorted(parent_ids)),
            provenance="reconstructed",
        )

    return graph, subset_tests, verifier_checks


def capability_digest(state: dict[str, Feature]) -> str:
    payload = [
        [node, list(state[node].values)]
        for node in CAP_ORDER
        if node in state
    ]
    return hashlib.sha256(
        json.dumps(payload, default=str, separators=(",", ":")).encode()
    ).hexdigest()


def ancestry_edge_count(graph: dict[str, tuple[str, ...]]) -> int:
    return sum(len(graph.get(node, ())) for node in CAP_ORDER)


def pair_search(
    *,
    target: tuple[Hashable, ...],
    state: dict[str, Feature],
    candidate_pairs: list[tuple[str, str]],
    budget: int | None = None,
) -> dict[str, object]:
    checked = 0
    for left_id, right_id in candidate_pairs:
        if budget is not None and checked >= budget:
            break
        if left_id not in state or right_id not in state:
            continue
        checked += 1
        relation = fit_finite_relation(
            target,
            (state[left_id].values, state[right_id].values),
        )
        if relation is None:
            continue

        proposal_ok = all(
            relation[
                (state[left_id].values[row], state[right_id].values[row])
            ]
            == target[row]
            for row in range(len(target))
        )
        if proposal_ok:
            return {
                "ok": True,
                "checks": checked,
                "parents": list(sorted((left_id, right_id))),
            }

    return {
        "ok": False,
        "checks": checked,
        "parents": [],
    }


def t1_future_discovery(
    scenario: Scenario,
    state: dict[str, Feature],
    graph: dict[str, tuple[str, ...]],
) -> dict[str, object]:
    lineage_tips = tips(graph)
    candidates = [
        tuple(sorted((tip, primitive)))
        for tip in lineage_tips
        for primitive in PRIMITIVE_IDS
        if tip != primitive
    ]
    candidates = sorted(set(candidates))
    return pair_search(
        target=scenario.future_f1,
        state=state,
        candidate_pairs=candidates,
        budget=None,
    )


def t2_recombination(
    scenario: Scenario,
    state: dict[str, Feature],
    graph: dict[str, tuple[str, ...]],
) -> dict[str, object]:
    cut_nodes = ("G1", "G2", "L3", "L4", "R3", "R4")
    branch_tips = tips(graph, cut_nodes)
    candidates = [
        tuple(sorted(pair))
        for pair in combinations(branch_tips, 2)
    ]
    candidates = sorted(set(candidates))
    return pair_search(
        target=scenario.future_f2,
        state=state,
        candidate_pairs=candidates,
        budget=8,
    )


def flat_t1_candidates() -> list[tuple[str, str]]:
    return sorted(
        set(
            tuple(sorted((node, primitive)))
            for node in CAP_ORDER
            for primitive in PRIMITIVE_IDS
        )
    )


def flat_t2_candidates() -> list[tuple[str, str]]:
    cut_nodes = ("G1", "G2", "L3", "L4", "R3", "R4")
    return sorted(
        tuple(sorted(pair))
        for pair in combinations(cut_nodes, 2)
    )


def t3_revocation(
    graph: dict[str, tuple[str, ...]] | None,
    *,
    conservative_flat: bool,
    true_graph: dict[str, tuple[str, ...]],
) -> dict[str, object]:
    true_invalid = {"G2"} | descendants(true_graph, "G2")

    if conservative_flat:
        proposed = set(CAP_ORDER)
    else:
        assert graph is not None
        proposed = {"G2"} | descendants(graph, "G2")

    unsafe_before_repair = sorted(true_invalid - proposed)
    unnecessary_before_repair = sorted(proposed - true_invalid)
    initial_checks = len(proposed)

    # External safety audit detects any missed true descendant. A sham/severed
    # lineage must then conservatively requalify every capability not already checked.
    repair_checks = 0
    if unsafe_before_repair:
        repair_checks = len(set(CAP_ORDER) - proposed)
        proposed = set(CAP_ORDER)

    unsafe_after_repair = sorted(true_invalid - proposed)

    return {
        "true_invalid": sorted(true_invalid),
        "initial_requalified": initial_checks,
        "repair_checks": repair_checks,
        "total_requalification_checks": initial_checks + repair_checks,
        "unsafe_before_repair": unsafe_before_repair,
        "unsafe_after_repair": unsafe_after_repair,
        "unnecessary_before_repair": unnecessary_before_repair,
        "safe": not unsafe_after_repair,
    }


def parent_subset_search(
    *,
    target: tuple[Hashable, ...],
    state: dict[str, Feature],
    candidate_ids: list[str],
    preferred_pairs: list[tuple[str, str]] | None,
    budget: int,
) -> dict[str, object]:
    seen = set()
    ordered: list[tuple[str, str]] = []

    for pair in preferred_pairs or []:
        pair = tuple(sorted(pair))
        if pair not in seen:
            ordered.append(pair)
            seen.add(pair)

    for pair in combinations(sorted(candidate_ids), 2):
        pair = tuple(sorted(pair))
        if pair not in seen:
            ordered.append(pair)
            seen.add(pair)

    return pair_search(
        target=target,
        state=state,
        candidate_pairs=ordered,
        budget=budget,
    )


def t4_regeneration(
    scenario: Scenario,
    state: dict[str, Feature],
    graph: dict[str, tuple[str, ...]] | None,
    arm: str,
) -> dict[str, object]:
    working = {
        feature_id: feature
        for feature_id, feature in state.items()
        if feature_id != "L3"
    }
    target = state["L3"].values

    if arm == "COLD":
        return {"ok": False, "checks": 0, "parents": []}

    preferred = None
    candidate_ids = sorted(working)

    if arm == "TRUE_MIN":
        preferred = [
            tuple(sorted(graph["L3"]))
        ] if graph else None
    elif arm == "FULL_CLOSURE":
        anc = sorted(graph["L3"]) if graph else []
        candidate_ids = [node for node in anc if node in working]
    elif arm in {"SEVERED", "SHAM", "RECONSTRUCT"}:
        preferred = [
            tuple(sorted(graph["L3"]))
        ] if graph and len(graph["L3"]) == 2 else None
    elif arm == "FLAT":
        preferred = None

    return parent_subset_search(
        target=target,
        state=working,
        candidate_ids=candidate_ids,
        preferred_pairs=preferred,
        budget=12,
    )


def ancestry_variants(
    scenario: Scenario,
    frozen_state: dict[str, Feature],
    generated_graph: dict[str, tuple[str, ...]],
) -> tuple[
    dict[str, dict[str, tuple[str, ...]] | None],
    dict[str, object],
]:
    reconstruction, subset_tests, verifier_checks = reconstruct_graph(
        scenario.config,
        frozen_state,
    )
    variants: dict[str, dict[str, tuple[str, ...]] | None] = {
        "TRUE_MIN": dict(generated_graph),
        "FULL_CLOSURE": full_closure_graph(generated_graph),
        "FLAT": {node: () for node in CAP_ORDER},
        "SEVERED": severed_graph(generated_graph, scenario.seed),
        "SHAM": sham_graph(generated_graph, scenario.seed),
        "RECONSTRUCT": reconstruction,
        "COLD": None,
    }
    reconstruction_result = {
        "graph": reconstruction,
        "exact_graph_recovery": reconstruction == generated_graph,
        "parent_subset_tests": subset_tests,
        "verifier_checks": verifier_checks,
    }
    return variants, reconstruction_result


def evaluate_ancestry(
    scenario: Scenario,
    frozen_state: dict[str, Feature],
    generated_graph: dict[str, tuple[str, ...]],
) -> dict[str, object]:
    variants, reconstruction = ancestry_variants(
        scenario,
        frozen_state,
        generated_graph,
    )

    content_digest = capability_digest(frozen_state)
    arms = {}

    for arm in ANCESTRY_ARMS:
        graph = variants[arm]

        if arm == "COLD":
            state = initial_state(scenario.config)
            t1 = {"ok": False, "checks": 0, "parents": []}
            t2 = {"ok": False, "checks": 0, "parents": []}
            t3 = {
                "safe": True,
                "total_requalification_checks": 0,
                "unsafe_before_repair": [],
                "unsafe_after_repair": [],
            }
            t4 = {"ok": False, "checks": 0, "parents": []}
            edge_count = 0
        else:
            state = frozen_state
            assert graph is not None

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
                t3 = t3_revocation(
                    None,
                    conservative_flat=True,
                    true_graph=generated_graph,
                )
            else:
                t1 = t1_future_discovery(
                    scenario,
                    state,
                    graph,
                )
                t2 = t2_recombination(
                    scenario,
                    state,
                    graph,
                )
                t3 = t3_revocation(
                    graph,
                    conservative_flat=False,
                    true_graph=generated_graph,
                )

            t4 = t4_regeneration(
                scenario,
                state,
                graph,
                arm,
            )
            edge_count = ancestry_edge_count(graph)

        arms[arm] = {
            "content_digest": content_digest if arm != "COLD" else None,
            "edge_count": edge_count,
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
        "reconstruction": reconstruction,
        "same_capability_content_non_cold": same_content,
    }


def evaluate_scenario(scenario: Scenario) -> dict[str, object]:
    nucleus_runs = {
        arm: run_nucleus_arm(scenario, arm)
        for arm in ARMS
    }
    dmi = nucleus_runs["DMI"]
    full_lineage = dmi["depth"] == len(CAP_ORDER)

    generated_graph = dmi["generated_graph"]
    graph_exact = full_lineage and generated_graph == scenario.hidden_graph

    ancestry = None
    if full_lineage:
        ancestry = evaluate_ancestry(
            scenario,
            dmi["_state"],
            generated_graph,
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


def headline_nucleus_gates(
    headline: dict[str, dict[str, object]],
) -> dict[str, bool]:
    def n(world: dict[str, object]) -> dict[str, object]:
        return world["base"]["nucleus"]

    n2 = all(n(world)["DMI"]["depth"] == 8 for world in headline.values())
    n3 = all(world["base"]["generated_graph_exact"] for world in headline.values())
    n4 = all(n(world)["DMI_COLD"]["depth"] < 8 for world in headline.values())
    n5 = all(n(world)["DM"]["depth"] < 8 for world in headline.values())
    n6 = all(n(world)["DI"]["depth"] < 8 for world in headline.values())
    n7 = all(
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
    n8 = all(
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
        "N2_dmi_full_lineage_all_worlds": n2,
        "N3_generated_graph_exact_all_worlds": n3,
        "N4_cold_not_full_all_worlds": n4,
        "N5_remove_i_reduces_reach_all_worlds": n5,
        "N6_remove_m_reduces_reach_all_worlds": n6,
        "N7_remove_d_reach_or_cost_penalty_all_worlds": n7,
        "N8_no_proper_subset_matches_full_all_worlds": n8,
    }


def headline_whakapapa_gates(
    headline: dict[str, dict[str, object]],
) -> dict[str, bool]:
    ancestry = [
        world["base"]["ancestry"]
        for world in headline.values()
    ]

    def arm(a: dict[str, object], name: str) -> dict[str, object]:
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
        bool(arm(a, "SHAM")["T3_revocation"]["unsafe_before_repair"])
        or (
            arm(a, "SHAM")["T3_revocation"]["total_requalification_checks"]
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
        "W5_sham_unsafe_or_more_repair_all_worlds": w5,
        "W6_true_min_regeneration_beats_flat_all_worlds": w6,
        "W7_true_min_equals_full_closure_with_fewer_edges": w7,
        "W8_reconstruction_positive_work_all_worlds": w8,
        "W9_representation_metamorphism": w9,
        "W10_same_capability_content_non_cold": w10,
    }


def metamorphic_signature(result: dict[str, object]) -> dict[str, object]:
    ancestry = result["ancestry"]
    true = ancestry["arms"]["TRUE_MIN"]
    flat = ancestry["arms"]["FLAT"]

    return {
        "dmi_depth": result["nucleus"]["DMI"]["depth"],
        "graph_exact": result["generated_graph_exact"],
        "true_t1_ok": true["T1_future_discovery"]["ok"],
        "flat_t1_ok": flat["T1_future_discovery"]["ok"],
        "true_t1_beats_flat": (
            true["T1_future_discovery"]["checks"]
            < flat["T1_future_discovery"]["checks"]
        ),
        "true_t2_ok": true["T2_recombination"]["ok"],
        "true_t3_safe": true["T3_revocation"]["safe"],
        "true_t4_ok": true["T4_regeneration"]["ok"],
        "true_t4_beats_flat": (
            not flat["T4_regeneration"]["ok"]
            or true["T4_regeneration"]["checks"]
            < flat["T4_regeneration"]["checks"]
        ),
    }


def evaluate_headline(config: WorldConfig, seed: str) -> dict[str, object]:
    scenario = build_scenario(config, seed)
    base = evaluate_scenario(scenario)

    if config.world_id == "graph":
        return {
            "base": base,
            "relabelled": None,
            "metamorphic_pass": None,
        }

    relabelled = evaluate_scenario(relabel_scenario(scenario))
    return {
        "base": base,
        "relabelled": relabelled,
        "metamorphic_pass": (
            metamorphic_signature(base)
            == metamorphic_signature(relabelled)
        ),
    }


def compact_headline(world: dict[str, object]) -> dict[str, object]:
    base = world["base"]
    ancestry = base["ancestry"]
    return {
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
        "ancestry": {
            "same_capability_content_non_cold": ancestry[
                "same_capability_content_non_cold"
            ],
            "reconstruction": ancestry["reconstruction"],
            "arms": {
                arm: ancestry["arms"][arm]
                for arm in ANCESTRY_ARMS
            },
        },
        "metamorphic_pass": world["metamorphic_pass"],
    }


def sweep_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    total = len(rows)

    def base(row: dict[str, object]) -> dict[str, object]:
        return row["result"]

    dmi_full = sum(base(row)["nucleus"]["DMI"]["depth"] == 8 for row in rows)
    graph_exact = sum(base(row)["generated_graph_exact"] for row in rows)
    cold_full = sum(
        base(row)["nucleus"]["DMI_COLD"]["depth"] == 8
        for row in rows
    )
    dm_loss = sum(
        base(row)["nucleus"]["DM"]["depth"]
        < base(row)["nucleus"]["DMI"]["depth"]
        for row in rows
    )
    di_loss = sum(
        base(row)["nucleus"]["DI"]["depth"]
        < base(row)["nucleus"]["DMI"]["depth"]
        for row in rows
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
        for row in rows
    )

    true_t1_success = 0
    true_t1_cheaper = 0
    true_t2_success = 0
    true_t3_safe = 0
    true_t4_success = 0
    true_t4_cheaper = 0
    sham_bad_or_expensive = 0
    true_full_equiv = 0

    for row in rows:
        result = base(row)
        a = result["ancestry"]
        if a is None:
            continue
        true = a["arms"]["TRUE_MIN"]
        flat = a["arms"]["FLAT"]
        sham = a["arms"]["SHAM"]
        full = a["arms"]["FULL_CLOSURE"]

        true_t1_success += int(true["T1_future_discovery"]["ok"])
        true_t1_cheaper += int(
            true["T1_future_discovery"]["ok"]
            and true["T1_future_discovery"]["checks"]
            < flat["T1_future_discovery"]["checks"]
        )
        true_t2_success += int(true["T2_recombination"]["ok"])
        true_t3_safe += int(true["T3_revocation"]["safe"])
        true_t4_success += int(true["T4_regeneration"]["ok"])
        true_t4_cheaper += int(
            true["T4_regeneration"]["ok"]
            and (
                not flat["T4_regeneration"]["ok"]
                or true["T4_regeneration"]["checks"]
                < flat["T4_regeneration"]["checks"]
            )
        )
        sham_bad_or_expensive += int(
            bool(sham["T3_revocation"]["unsafe_before_repair"])
            or sham["T3_revocation"]["total_requalification_checks"]
            > true["T3_revocation"]["total_requalification_checks"]
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
        "S_N1_dmi_full_ge_120": dmi_full >= 120,
        "S_N2_graph_exact_ge_120": graph_exact >= 120,
        "S_N3_cold_full_le_10": cold_full <= 10,
        "S_N4_dm_loss_ge_115": dm_loss >= 115,
        "S_N5_di_loss_ge_115": di_loss >= 115,
        "S_N6_mi_penalty_ge_115": mi_penalty >= 115,
    }
    whakapapa_criteria = {
        "S_W1_true_t1_success_ge_120": true_t1_success >= 120,
        "S_W2_true_t1_cheaper_ge_115": true_t1_cheaper >= 115,
        "S_W3_true_t2_success_ge_115": true_t2_success >= 115,
        "S_W4_true_t3_safe_ge_120": true_t3_safe >= 120,
        "S_W5_true_t4_success_ge_120": true_t4_success >= 120,
        "S_W6_true_t4_cheaper_ge_115": true_t4_cheaper >= 115,
        "S_W7_sham_bad_or_expensive_ge_115": sham_bad_or_expensive >= 115,
        "S_W8_true_full_equiv_ge_120": true_full_equiv >= 120,
    }

    return {
        "worlds": total,
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
        "true_t4_success": true_t4_success,
        "true_t4_cheaper_than_flat": true_t4_cheaper,
        "sham_unsafe_or_more_expensive": sham_bad_or_expensive,
        "true_full_closure_correctness_equiv": true_full_equiv,
        "nucleus_criteria": nucleus_criteria,
        "whakapapa_criteria": whakapapa_criteria,
        "nucleus_strong_pass": all(nucleus_criteria.values()),
        "whakapapa_strong_pass": all(whakapapa_criteria.values()),
    }


def classify(
    nucleus_gates: dict[str, bool],
    whakapapa_gates: dict[str, bool],
    sweep: dict[str, object],
) -> str:
    nucleus_headline = all(nucleus_gates.values())
    whakapapa_headline = all(whakapapa_gates.values())
    nucleus_strong = bool(sweep["nucleus_strong_pass"])
    whakapapa_strong = bool(sweep["whakapapa_strong_pass"])

    if nucleus_headline and whakapapa_headline and nucleus_strong and whakapapa_strong:
        return "PASS_WHAKAPAPA_CAUSALITY_AND_IRREDUCIBLE_NUCLEUS_V1"

    nucleus_core = all(
        value
        for key, value in nucleus_gates.items()
        if key not in {
            "N7_remove_d_reach_or_cost_penalty_all_worlds",
            "N8_no_proper_subset_matches_full_all_worlds",
        }
    )
    role_reduced = not (
        nucleus_gates["N7_remove_d_reach_or_cost_penalty_all_worlds"]
        and nucleus_gates["N8_no_proper_subset_matches_full_all_worlds"]
    )

    if whakapapa_headline and whakapapa_strong and nucleus_core and role_reduced:
        return "PASS_WHAKAPAPA_CAUSALITY_REDUCED_NUCLEUS_V1"
    if nucleus_headline and nucleus_strong and not (whakapapa_headline and whakapapa_strong):
        return "NUCLEUS_PASS_WHAKAPAPA_NEGATIVE_V1"
    if whakapapa_headline and whakapapa_strong:
        return "WHAKAPAPA_PASS_NUCLEUS_PARTIAL_V1"
    if any(whakapapa_gates.values()) or any(nucleus_gates.values()):
        return "PARTIAL_WHAKAPAPA_CAUSALITY_V1"
    return "VALID_NEGATIVE_WHAKAPAPA_CAUSALITY_V1"


def main() -> int:
    configs = world_configs()

    headline = {
        world_id: evaluate_headline(configs[world_id], WORLD_SEEDS[world_id])
        for world_id in WORLD_SEEDS
    }

    nucleus_gates = headline_nucleus_gates(headline)
    whakapapa_gates = headline_whakapapa_gates(headline)

    sweep_rows = []
    for world_id in WORLD_SEEDS:
        config = configs[world_id]
        for index in range(25):
            seed = f"{WORLD_SEEDS[world_id]}:SWEEP:{index:03d}"
            scenario = build_scenario(config, seed)
            result = evaluate_scenario(scenario)
            sweep_rows.append(
                {
                    "world_id": world_id,
                    "seed": seed,
                    "result": result,
                }
            )

    sweep = sweep_summary(sweep_rows)
    verdict = classify(nucleus_gates, whakapapa_gates, sweep)

    result = {
        "protocol": PROTOCOL,
        "precommit_commit": PRECOMMIT_COMMIT,
        "addendum_commit": ADDENDUM_COMMIT,
        "headline": {
            world_id: compact_headline(world)
            for world_id, world in headline.items()
        },
        "headline_nucleus_gates": nucleus_gates,
        "headline_whakapapa_gates": whakapapa_gates,
        "sweep": sweep,
        "verdict": verdict,
        "claim_boundary": (
            "Bounded finite cross-world test of generated capability ancestry "
            "and D/M/I irreducibility under five frozen adapters and fixed "
            "search policies. The engineering use of whakapapa is deliberately "
            "narrow and does not exhaust the Māori concept. A PASS does not "
            "establish metaphysical inevitability, unique minimality over all "
            "possible algorithms, or unrestricted open-world intelligence."
        ),
    }

    outdir = Path("results/whakapapa_causality_v1")
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str) + "\n"
    )

    compact_sweep = []
    for row in sweep_rows:
        r = row["result"]
        a = r["ancestry"]
        compact_sweep.append(
            {
                "world_id": row["world_id"],
                "seed": row["seed"],
                "nucleus_depths": {
                    arm: r["nucleus"][arm]["depth"]
                    for arm in ARMS
                },
                "graph_exact": r["generated_graph_exact"],
                "true_t1": (
                    None if a is None else a["arms"]["TRUE_MIN"]["T1_future_discovery"]
                ),
                "flat_t1": (
                    None if a is None else a["arms"]["FLAT"]["T1_future_discovery"]
                ),
                "true_t2": (
                    None if a is None else a["arms"]["TRUE_MIN"]["T2_recombination"]
                ),
                "true_t3": (
                    None if a is None else a["arms"]["TRUE_MIN"]["T3_revocation"]
                ),
                "sham_t3": (
                    None if a is None else a["arms"]["SHAM"]["T3_revocation"]
                ),
                "true_t4": (
                    None if a is None else a["arms"]["TRUE_MIN"]["T4_regeneration"]
                ),
                "flat_t4": (
                    None if a is None else a["arms"]["FLAT"]["T4_regeneration"]
                ),
            }
        )

    (outdir / "sweep.json").write_text(
        json.dumps(compact_sweep, indent=2, sort_keys=True, default=str) + "\n"
    )

    print("=" * 100)
    print("WHAKAPAPA CAUSALITY V1")
    print("=" * 100)
    for world_id, world in result["headline"].items():
        print(world_id)
        print("  nucleus", json.dumps(world["nucleus_depths"], sort_keys=True))
        print("  graph_exact", world["generated_graph_exact"])
        print("  metamorphic", world["metamorphic_pass"])
        true = world["ancestry"]["arms"]["TRUE_MIN"]
        flat = world["ancestry"]["arms"]["FLAT"]
        sham = world["ancestry"]["arms"]["SHAM"]
        print("  T1 true/flat", true["T1_future_discovery"], flat["T1_future_discovery"])
        print("  T2 true/flat", true["T2_recombination"], flat["T2_recombination"])
        print("  T3 true/sham", true["T3_revocation"], sham["T3_revocation"])
        print("  T4 true/flat", true["T4_regeneration"], flat["T4_regeneration"])
    print("-" * 100)
    print("NUCLEUS GATES")
    for key, value in nucleus_gates.items():
        print(key, "PASS" if value else "FAIL")
    print("WHAKAPAPA GATES")
    for key, value in whakapapa_gates.items():
        print(key, "PASS" if value else "FAIL")
    print("-" * 100)
    print(json.dumps(sweep, indent=2, sort_keys=True))
    print(verdict)

    # Any scientific verdict is a completed experiment. Infrastructure errors raise.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
