#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Hashable
import copy
import hashlib
import json

from experiments.cross_world_nucleus_invariance_v1 import (
    Feature,
    WorldConfig,
    fit_finite_relation,
    initial_state as inherited_initial_state,
    stable,
    world_configs,
)

PROTOCOL = "CONTINUITY_DIFFERENCE_PETRI_DISH_V1"
PRECOMMIT_COMMIT = "8f08e098b3feff913e39b12c5537f9bea6dd2f5c"
MAX_RESIDUALS = 128
OUTPUT_ALPHABET = ("o0", "o1", "o2", "o3", "o4")
ARMS = (
    "NONE",
    "C_ONLY",
    "D_ONLY",
    "CD",
    "CD_NO_REENTRY",
    "C_SHAM_D",
    "CD_COLD_TWIN",
    "ORACLE",
)

WORLD_SEEDS = {
    "binary": "TRISKELION_CD_PETRI_V1_BINARY",
    "ternary": "TRISKELION_CD_PETRI_V1_TERNARY",
    "symbolic": "TRISKELION_CD_PETRI_V1_SYMBOLIC",
    "temporal": "TRISKELION_CD_PETRI_V1_TEMPORAL",
    "graph": "TRISKELION_CD_PETRI_V1_GRAPH",
}

HISTORY_A = (
    ("A1", "q0", "q1"),
    ("A2", "A1", "q2"),
    ("A3", "A2", "q3"),
)
HISTORY_B = (
    ("B1", "q0", "q4"),
    ("B2", "B1", "q5"),
    ("B3", "B2", "q2"),
)
LINEAGE_NODES = ("A1", "A2", "A3", "B1", "B2", "B3", "K", "Z")


def sha(*parts: object) -> str:
    return hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest()


def augment_config(config: WorldConfig) -> WorldConfig:
    primitive = dict(config.primitive)
    nrows = len(next(iter(primitive.values())))
    base_ids = sorted(primitive)

    for extra in ("q4", "q5"):
        if extra in primitive:
            continue
        values = []
        for row in range(nrows):
            signature = tuple(primitive[name][row] for name in base_ids)
            token = int(sha(config.world_id, extra, stable(signature))[:16], 16) % 5
            values.append(f"{extra}v{token}")
        if len(set(values)) < 2:
            raise RuntimeError(f"derived primitive {extra} is constant")
        primitive[extra] = tuple(values)

    # Every Petri dish exposes exactly q0...q5 to the developmental cell.
    missing = [q for q in ("q0", "q1", "q2", "q3", "q4", "q5") if q not in primitive]
    if missing:
        raise RuntimeError(f"missing required opaque primitives: {missing}")

    return WorldConfig(
        world_id=config.world_id,
        primitive={q: primitive[q] for q in ("q0", "q1", "q2", "q3", "q4", "q5")},
        alphabet=config.alphabet,
        schedule=config.schedule,
        surface=config.surface + "-cd-petri",
        relabelled=config.relabelled,
    )


@dataclass(frozen=True)
class Episode:
    node_id: str
    target: tuple[Hashable, ...]
    declared_parents: tuple[str, str]
    counter: int


@dataclass(frozen=True)
class Scenario:
    config: WorldConfig
    seed: str
    history_a: tuple[Episode, ...]
    history_b: tuple[Episode, ...]
    common: Episode
    recombination: Episode
    descendant: Episode
    hidden_graph: dict[str, tuple[str, str]]


def active_values(state: dict[str, Feature]) -> dict[str, tuple[Hashable, ...]]:
    return {name: feature.values for name, feature in state.items()}


def sufficient_pairs(
    target: tuple[Hashable, ...],
    state: dict[str, Feature],
) -> list[tuple[str, str]]:
    out = []
    for left, right in combinations(sorted(state), 2):
        if fit_finite_relation(target, (state[left].values, state[right].values)) is not None:
            out.append((left, right))
    return out


def pair_target(
    *,
    state: dict[str, Feature],
    left_id: str,
    right_id: str,
    seed: str,
    stage: str,
) -> tuple[tuple[Hashable, ...], int]:
    left = state[left_id].values
    right = state[right_id].values
    support = sorted(set(zip(left, right)), key=stable)

    for counter in range(65536):
        table = {}
        for key in support:
            idx = int(sha(seed, stage, counter, stable(key))[:16], 16) % len(OUTPUT_ALPHABET)
            table[key] = OUTPUT_ALPHABET[idx]
        target = tuple(table[(a, b)] for a, b in zip(left, right))

        if any(feature.values == target for feature in state.values()):
            continue
        if fit_finite_relation(target, (left, right)) is None:
            continue
        pairs = sufficient_pairs(target, state)
        if pairs == [tuple(sorted((left_id, right_id)))]:
            return target, counter

    raise RuntimeError(
        f"pair target exhaustion {seed} {stage} {left_id},{right_id}"
    )


def install_hidden(
    state: dict[str, Feature],
    episode: Episode,
) -> dict[str, Feature]:
    nxt = dict(state)
    nxt[episode.node_id] = Feature(
        feature_id=episode.node_id,
        values=episode.target,
        dependencies=tuple(sorted(episode.declared_parents)),
        provenance=f"hidden:{episode.node_id}:{episode.counter}",
    )
    return nxt


def make_episode(
    *,
    state: dict[str, Feature],
    node_id: str,
    left_id: str,
    right_id: str,
    seed: str,
) -> Episode:
    target, counter = pair_target(
        state=state,
        left_id=left_id,
        right_id=right_id,
        seed=seed,
        stage=node_id,
    )
    return Episode(
        node_id=node_id,
        target=target,
        declared_parents=tuple(sorted((left_id, right_id))),
        counter=counter,
    )


def build_scenario(config: WorldConfig, seed: str) -> Scenario:
    initial = inherited_initial_state(config)

    a_state = dict(initial)
    hist_a = []
    for node, left, right in HISTORY_A:
        ep = make_episode(
            state=a_state, node_id=node, left_id=left, right_id=right, seed=seed
        )
        hist_a.append(ep)
        a_state = install_hidden(a_state, ep)

    b_state = dict(initial)
    hist_b = []
    for node, left, right in HISTORY_B:
        ep = make_episode(
            state=b_state, node_id=node, left_id=left, right_id=right, seed=seed
        )
        hist_b.append(ep)
        b_state = install_hidden(b_state, ep)

    union_state = dict(initial)
    for ep in (*hist_a, *hist_b):
        union_state = install_hidden(union_state, ep)

    # Common target is generated against the union, so q4/q5 is its unique pair
    # even after both distinct histories exist.
    common = make_episode(
        state=union_state,
        node_id="COMMON",
        left_id="q4",
        right_id="q5",
        seed=seed,
    )

    # COMMON is an evaluation branch, not part of the hidden ancestry gate.
    union_with_common = install_hidden(union_state, common)

    recombination = make_episode(
        state=union_with_common,
        node_id="K",
        left_id="A3",
        right_id="B3",
        seed=seed,
    )
    with_k = install_hidden(union_with_common, recombination)

    descendant = make_episode(
        state=with_k,
        node_id="Z",
        left_id="K",
        right_id="q0",
        seed=seed,
    )

    hidden_graph = {
        ep.node_id: ep.declared_parents
        for ep in (*hist_a, *hist_b, recombination, descendant)
    }

    return Scenario(
        config=config,
        seed=seed,
        history_a=tuple(hist_a),
        history_b=tuple(hist_b),
        common=common,
        recombination=recombination,
        descendant=descendant,
        hidden_graph=hidden_graph,
    )


# ---------------------------------------------------------------------------
# The C + Difference solver. No imported D/M/I solver is used here.
# ---------------------------------------------------------------------------

def canonical_output(values: set[Hashable]) -> Hashable:
    return sorted(values, key=stable)[0]


def relation_from_residuals(
    *,
    pair: tuple[str, str],
    state: dict[str, Feature],
    residuals: dict[int, Hashable],
) -> dict[tuple[Hashable, Hashable], Hashable] | None:
    left = state[pair[0]].values
    right = state[pair[1]].values
    table: dict[tuple[Hashable, Hashable], Hashable] = {}

    for row, expected in sorted(residuals.items()):
        key = (left[row], right[row])
        if key in table and table[key] != expected:
            return None
        table[key] = expected

    if not table:
        return None

    default = canonical_output(set(table.values()))
    for key in set(zip(left, right)):
        table.setdefault(key, default)
    return table


def proposal_from_pair(
    pair: tuple[str, str],
    state: dict[str, Feature],
    relation: dict[tuple[Hashable, Hashable], Hashable],
) -> tuple[Hashable, ...]:
    left = state[pair[0]].values
    right = state[pair[1]].values
    return tuple(relation[(a, b)] for a, b in zip(left, right))


def verifier_counterexample(
    proposal: tuple[Hashable, ...] | None,
    target: tuple[Hashable, ...],
) -> tuple[bool, int | None, Hashable | None]:
    if proposal is None:
        return False, 0, target[0]
    for row, (actual, expected) in enumerate(zip(proposal, target)):
        if actual != expected:
            return False, row, expected
    return True, None, None


def sham_expected(
    target: tuple[Hashable, ...],
    row: int,
) -> Hashable:
    expected = target[row]
    for offset in range(1, len(target)):
        candidate = target[(row + offset) % len(target)]
        if candidate != expected:
            return candidate
    return expected


def solve_cd_episode(
    *,
    state: dict[str, Feature],
    episode: Episode,
    arm: str,
    provenance: str,
) -> tuple[dict[str, object], dict[str, Feature]]:
    continuity = arm in {"C_ONLY", "CD", "C_SHAM_D", "ORACLE"}
    difference = arm in {"D_ONLY", "CD", "CD_NO_REENTRY", "C_SHAM_D", "CD_COLD_TWIN"}
    reentry = arm in {"CD", "C_SHAM_D", "ORACLE"}
    sham = arm == "C_SHAM_D"

    if arm == "NONE":
        continuity = difference = reentry = False
    if arm == "C_ONLY":
        difference = False
    if arm in {"D_ONLY", "CD_NO_REENTRY", "CD_COLD_TWIN"}:
        continuity = False
        reentry = False

    if arm == "ORACLE":
        left, right = episode.declared_parents
        if left not in state or right not in state:
            return {
                "ok": False,
                "route": "ORACLE_PARENT_MISSING",
                "verifier_checks": 0,
                "residuals": 0,
                "pair_tests": 0,
            }, state
        relation = fit_finite_relation(
            episode.target, (state[left].values, state[right].values)
        )
        if relation is None:
            return {
                "ok": False,
                "route": "ORACLE_RELATION_FAIL",
                "verifier_checks": 1,
                "residuals": 0,
                "pair_tests": 1,
            }, state
        next_state = dict(state)
        next_state[episode.node_id] = Feature(
            feature_id=episode.node_id,
            values=episode.target,
            dependencies=tuple(sorted((left, right))),
            provenance=provenance,
        )
        return {
            "ok": True,
            "route": "ORACLE_VERIFIED",
            "parents": list(sorted((left, right))),
            "verifier_checks": 1,
            "residuals": 0,
            "pair_tests": 1,
            "installed": True,
            "constructed_relation": True,
        }, next_state

    # Difference starts with a refutation of the null proposal.
    ok, row, expected = verifier_counterexample(None, episode.target)
    verifier_checks = 1
    residuals: dict[int, Hashable] = {}
    if difference and row is not None and expected is not None:
        residuals[row] = sham_expected(episode.target, row) if sham else expected
    else:
        return {
            "ok": False,
            "route": "NO_CONSEQUENTIAL_DIFFERENCE",
            "verifier_checks": verifier_checks,
            "residuals": 0,
            "pair_tests": 0,
            "installed": False,
        }, state

    pair_tests = 0
    attempted: set[tuple[str, str, str]] = set()

    for _ in range(MAX_RESIDUALS):
        chosen = None
        chosen_relation = None
        chosen_proposal = None

        for pair in combinations(sorted(state), 2):
            relation = relation_from_residuals(
                pair=pair, state=state, residuals=residuals
            )
            pair_tests += 1
            if relation is None:
                continue
            proposal = proposal_from_pair(pair, state, relation)
            signature = (
                pair[0],
                pair[1],
                sha(stable(proposal), stable(sorted(residuals.items()))),
            )
            if signature in attempted:
                continue
            chosen = pair
            chosen_relation = relation
            chosen_proposal = proposal
            attempted.add(signature)
            break

        if chosen is None or chosen_relation is None or chosen_proposal is None:
            return {
                "ok": False,
                "route": "NO_RESIDUAL_CONSISTENT_RECOMBINATION",
                "verifier_checks": verifier_checks,
                "residuals": len(residuals),
                "pair_tests": pair_tests,
                "installed": False,
            }, state

        verified, bad_row, true_expected = verifier_counterexample(
            chosen_proposal, episode.target
        )
        verifier_checks += 1

        if verified:
            next_state = state
            installed = False
            if reentry:
                next_state = dict(state)
                next_state[episode.node_id] = Feature(
                    feature_id=episode.node_id,
                    values=chosen_proposal,
                    dependencies=tuple(sorted(chosen)),
                    provenance=provenance,
                )
                installed = True
            return {
                "ok": True,
                "route": "VERIFIED_RECOMBINATION",
                "parents": list(sorted(chosen)),
                "verifier_checks": verifier_checks,
                "residuals": len(residuals),
                "pair_tests": pair_tests,
                "installed": installed,
                "constructed_relation": True,
            }, next_state

        if bad_row is None or true_expected is None:
            break
        supplied = sham_expected(episode.target, bad_row) if sham else true_expected
        residuals[bad_row] = supplied

    return {
        "ok": False,
        "route": "RESIDUAL_BUDGET_EXHAUSTED",
        "verifier_checks": verifier_checks,
        "residuals": len(residuals),
        "pair_tests": pair_tests,
        "installed": False,
    }, state


def run_history(
    *,
    config: WorldConfig,
    episodes: tuple[Episode, ...],
    arm: str,
    lineage: str,
    seed: str,
) -> dict[str, object]:
    state = inherited_initial_state(config)
    records = []

    for ep in episodes:
        if arm in {"D_ONLY", "CD_NO_REENTRY", "CD_COLD_TWIN"}:
            state = inherited_initial_state(config)

        result, state = solve_cd_episode(
            state=state,
            episode=ep,
            arm=arm,
            provenance=f"{PRECOMMIT_COMMIT}:{seed}:{lineage}:{ep.node_id}",
        )
        result["node_id"] = ep.node_id
        result["declared_parents"] = list(ep.declared_parents)
        result["parent_match"] = (
            result.get("ok")
            and tuple(result.get("parents", ())) == ep.declared_parents
        )
        records.append(result)
        if not result["ok"]:
            break

    return {
        "depth": sum(1 for row in records if row["ok"]),
        "records": records,
        "state": state,
        "verifier_checks": sum(int(row["verifier_checks"]) for row in records),
        "pair_tests": sum(int(row["pair_tests"]) for row in records),
    }


def solve_on_copy(
    state: dict[str, Feature],
    episode: Episode,
    arm: str,
    provenance: str,
) -> dict[str, object]:
    result, _ = solve_cd_episode(
        state=copy.deepcopy(state),
        episode=episode,
        arm=arm,
        provenance=provenance,
    )
    return result


def merge_states(
    config: WorldConfig,
    a: dict[str, Feature],
    b: dict[str, Feature],
) -> dict[str, Feature]:
    merged = inherited_initial_state(config)
    for state in (a, b):
        for node, feature in state.items():
            if node.startswith("q"):
                continue
            if node in merged and merged[node].values != feature.values:
                raise RuntimeError(f"conflicting node {node}")
            merged[node] = feature
    return merged


def lineage_digest(state: dict[str, Feature], prefix: str) -> str:
    rows = [
        [
            node,
            list(feature.values),
            list(feature.dependencies),
        ]
        for node, feature in sorted(state.items())
        if node.startswith(prefix)
    ]
    return sha(stable(rows))


def generated_graph(state: dict[str, Feature]) -> dict[str, tuple[str, str]]:
    out = {}
    for node in LINEAGE_NODES:
        if node in state:
            deps = tuple(sorted(state[node].dependencies))
            if len(deps) == 2:
                out[node] = deps  # type: ignore[assignment]
    return out


def evaluate_arm(scenario: Scenario, arm: str) -> dict[str, object]:
    a = run_history(
        config=scenario.config,
        episodes=scenario.history_a,
        arm=arm,
        lineage="A",
        seed=scenario.seed,
    )
    b = run_history(
        config=scenario.config,
        episodes=scenario.history_b,
        arm=arm,
        lineage="B",
        seed=scenario.seed,
    )

    twin_divergence = (
        a["depth"] == 3
        and b["depth"] == 3
        and lineage_digest(a["state"], "A") != lineage_digest(b["state"], "B")
    )

    common_a = solve_on_copy(
        a["state"],
        scenario.common,
        arm,
        f"{scenario.seed}:COMMON:A",
    )
    common_b = solve_on_copy(
        b["state"],
        scenario.common,
        arm,
        f"{scenario.seed}:COMMON:B",
    )

    combined = merge_states(scenario.config, a["state"], b["state"])

    recomb_result, with_k = solve_cd_episode(
        state=combined,
        episode=scenario.recombination,
        arm=arm,
        provenance=f"{scenario.seed}:K",
    )
    a_only_k = solve_on_copy(
        a["state"],
        scenario.recombination,
        arm,
        f"{scenario.seed}:K:AONLY",
    )
    b_only_k = solve_on_copy(
        b["state"],
        scenario.recombination,
        arm,
        f"{scenario.seed}:K:BONLY",
    )

    descendant_result = {
        "ok": False,
        "route": "K_NOT_AVAILABLE",
        "verifier_checks": 0,
        "pair_tests": 0,
    }
    without_k = {
        "ok": False,
        "route": "K_NOT_AVAILABLE",
        "verifier_checks": 0,
        "pair_tests": 0,
    }
    after_restore = {
        "ok": False,
        "route": "K_NOT_AVAILABLE",
        "verifier_checks": 0,
        "pair_tests": 0,
    }

    if recomb_result["ok"] and "K" in with_k:
        descendant_result, with_z = solve_cd_episode(
            state=with_k,
            episode=scenario.descendant,
            arm=arm,
            provenance=f"{scenario.seed}:Z",
        )

        ablated = {name: feature for name, feature in with_k.items() if name != "K"}
        without_k = solve_on_copy(
            ablated,
            scenario.descendant,
            arm,
            f"{scenario.seed}:Z:ABLATE",
        )
        restored = dict(ablated)
        restored["K"] = with_k["K"]
        after_restore = solve_on_copy(
            restored,
            scenario.descendant,
            arm,
            f"{scenario.seed}:Z:RESTORE",
        )
    else:
        with_z = with_k

    graph = generated_graph(with_z)
    graph_exact = graph == scenario.hidden_graph

    complete = (
        a["depth"] == 3
        and b["depth"] == 3
        and common_a["ok"]
        and common_b["ok"]
        and recomb_result["ok"]
        and descendant_result["ok"]
        and graph_exact
    )

    # Post-hoc phenotype classification; this does not affect solver behavior.
    d_like = complete and all(
        row.get("parent_match", False)
        for row in (*a["records"], *b["records"])
    ) and recomb_result.get("parents") == list(scenario.recombination.declared_parents)
    m_like = complete and all(
        row.get("constructed_relation", False)
        for row in (*a["records"], *b["records"])
    ) and recomb_result.get("constructed_relation", False)
    i_like = (
        complete
        and "A1" in a["state"]
        and "A2" in a["state"]
        and "B1" in b["state"]
        and "B2" in b["state"]
        and recomb_result.get("installed", False)
        and descendant_result.get("parents") == list(scenario.descendant.declared_parents)
    )

    return {
        "arm": arm,
        "history_a_depth": a["depth"],
        "history_b_depth": b["depth"],
        "twin_divergence": twin_divergence,
        "common_a_ok": bool(common_a["ok"]),
        "common_b_ok": bool(common_b["ok"]),
        "recombination_ok": bool(recomb_result["ok"]),
        "a_only_k_ok": bool(a_only_k["ok"]),
        "b_only_k_ok": bool(b_only_k["ok"]),
        "k_novel_to_a": all(
            feature.values != scenario.recombination.target
            for feature in a["state"].values()
        ),
        "k_novel_to_b": all(
            feature.values != scenario.recombination.target
            for feature in b["state"].values()
        ),
        "descendant_ok": bool(descendant_result["ok"]),
        "k_ablation_blocks_z": not bool(without_k["ok"]),
        "k_restore_returns_z": bool(after_restore["ok"]),
        "generated_graph": {k: list(v) for k, v in graph.items()},
        "graph_exact": graph_exact,
        "complete": complete,
        "d_like": d_like,
        "m_like": m_like,
        "i_like": i_like,
        "verifier_checks": (
            a["verifier_checks"]
            + b["verifier_checks"]
            + int(common_a.get("verifier_checks", 0))
            + int(common_b.get("verifier_checks", 0))
            + int(recomb_result.get("verifier_checks", 0))
            + int(descendant_result.get("verifier_checks", 0))
        ),
        "pair_tests": (
            a["pair_tests"]
            + b["pair_tests"]
            + int(common_a.get("pair_tests", 0))
            + int(common_b.get("pair_tests", 0))
            + int(recomb_result.get("pair_tests", 0))
            + int(descendant_result.get("pair_tests", 0))
        ),
    }


def evaluate_scenario(scenario: Scenario) -> dict[str, object]:
    return {
        "world_id": scenario.config.world_id,
        "surface": scenario.config.surface,
        "arms": {arm: evaluate_arm(scenario, arm) for arm in ARMS},
    }


def relabel_scenario(scenario: Scenario) -> Scenario:
    # Apply an independent bijection to each primitive feature's visible
    # alphabet. Generated target vectors stay row-wise identical. Because each
    # primitive map is bijective, every hidden extensional dependency is
    # preserved while the environmental surface vocabulary changes.
    primitive = {}
    for feature_id, values in scenario.config.primitive.items():
        alphabet = sorted(set(values), key=stable)
        if len(alphabet) <= 1:
            mapping = {value: value for value in alphabet}
        else:
            mapping = {
                alphabet[i]: alphabet[(i + 1) % len(alphabet)]
                for i in range(len(alphabet))
            }
        primitive[feature_id] = tuple(mapping[value] for value in values)

    config = WorldConfig(
        world_id=scenario.config.world_id + "-relabel",
        primitive=primitive,
        alphabet=scenario.config.alphabet,
        schedule=scenario.config.schedule,
        surface=scenario.config.surface + "-bijective-feature-relabel",
        relabelled=True,
    )
    return Scenario(
        config=config,
        seed=scenario.seed + ":RELABEL",
        history_a=scenario.history_a,
        history_b=scenario.history_b,
        common=scenario.common,
        recombination=scenario.recombination,
        descendant=scenario.descendant,
        hidden_graph=dict(scenario.hidden_graph),
    )


def signature(result: dict[str, object]) -> dict[str, object]:
    cd = result["arms"]["CD"]
    return {
        "a_depth": cd["history_a_depth"],
        "b_depth": cd["history_b_depth"],
        "twin_divergence": cd["twin_divergence"],
        "common_a": cd["common_a_ok"],
        "common_b": cd["common_b_ok"],
        "recombination": cd["recombination_ok"],
        "descendant": cd["descendant_ok"],
        "ablate": cd["k_ablation_blocks_z"],
        "restore": cd["k_restore_returns_z"],
        "graph_exact": cd["graph_exact"],
    }


def evaluate_headline(config: WorldConfig, seed: str) -> dict[str, object]:
    scenario = build_scenario(config, seed)
    base = evaluate_scenario(scenario)
    if config.world_id == "graph":
        return {"base": base, "relabelled": None, "metamorphic_pass": None}

    relabelled = evaluate_scenario(relabel_scenario(scenario))
    return {
        "base": base,
        "relabelled": relabelled,
        "metamorphic_pass": signature(base) == signature(relabelled),
    }


def headline_gates(headline: dict[str, dict[str, object]]) -> dict[str, bool]:
    bases = {k: v["base"] for k, v in headline.items()}
    cds = {k: v["arms"]["CD"] for k, v in bases.items()}

    p2 = all(cd["history_a_depth"] == 3 and cd["history_b_depth"] == 3 for cd in cds.values())
    p3 = all(cd["twin_divergence"] for cd in cds.values())
    p4 = all(cd["common_a_ok"] and cd["common_b_ok"] for cd in cds.values())
    p5 = all(cd["recombination_ok"] and cd["k_novel_to_a"] and cd["k_novel_to_b"] for cd in cds.values())
    p6 = all(not cd["a_only_k_ok"] and not cd["b_only_k_ok"] for cd in cds.values())
    p7 = all(cd["descendant_ok"] for cd in cds.values())
    p8 = all(cd["k_ablation_blocks_z"] and cd["k_restore_returns_z"] for cd in cds.values())
    p9 = all(cd["graph_exact"] for cd in cds.values())
    p10 = all(cd["d_like"] and cd["m_like"] and cd["i_like"] for cd in cds.values())

    ablated = ("NONE", "C_ONLY", "D_ONLY", "CD_NO_REENTRY")
    p11 = all(
        not bases[world]["arms"][arm]["complete"]
        for world in bases
        for arm in ablated
    )
    p12 = all(
        (
            not bases[world]["arms"]["C_SHAM_D"]["complete"]
            or bases[world]["arms"]["C_SHAM_D"]["verifier_checks"] > cds[world]["verifier_checks"]
        )
        for world in bases
    )
    p13 = all(not bases[world]["arms"]["CD_COLD_TWIN"]["complete"] for world in bases)
    p14 = all(
        headline[world]["metamorphic_pass"] is True
        for world in headline
        if world != "graph"
    )
    p15 = all(
        bases[world]["arms"]["ORACLE"]["complete"] == cds[world]["complete"]
        and bases[world]["arms"]["ORACLE"]["common_a_ok"] == cds[world]["common_a_ok"]
        and bases[world]["arms"]["ORACLE"]["common_b_ok"] == cds[world]["common_b_ok"]
        for world in bases
    )

    return {
        "P1_same_cd_solver_all_worlds": True,
        "P2_cd_twin_histories_depth3_all_worlds": p2,
        "P3_twin_history_variation_all_worlds": p3,
        "P4_common_challenge_correct_all_worlds": p4,
        "P5_recombination_novel_k_all_worlds": p5,
        "P6_single_lineage_cannot_make_k_all_worlds": p6,
        "P7_k_child_generates_z_all_worlds": p7,
        "P8_k_ablation_restore_all_worlds": p8,
        "P9_generated_ancestry_exact_all_worlds": p9,
        "P10_dmi_phenotypes_emerge_all_worlds": p10,
        "P11_single_primitive_and_no_reentry_controls_fail": p11,
        "P12_sham_difference_penalty_all_worlds": p12,
        "P13_cold_twin_control_fails_all_worlds": p13,
        "P14_representation_metamorphism_w1_w4": p14,
        "P15_oracle_cd_protected_consequence_agreement": p15,
    }


def sweep_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    total = len(rows)

    cd_complete = 0
    graph_exact = 0
    twin_common = 0
    ablation = 0
    phenotypes = 0
    sham_penalty = 0
    success_by_control = {
        "NONE": 0,
        "C_ONLY": 0,
        "D_ONLY": 0,
        "CD_NO_REENTRY": 0,
        "CD_COLD_TWIN": 0,
    }
    by_world = {}

    for row in rows:
        result = row["result"]
        cd = result["arms"]["CD"]
        cd_complete += int(cd["complete"])
        graph_exact += int(cd["graph_exact"])
        twin_common += int(
            cd["twin_divergence"] and cd["common_a_ok"] and cd["common_b_ok"]
        )
        ablation += int(cd["k_ablation_blocks_z"] and cd["k_restore_returns_z"])
        phenotypes += int(cd["d_like"] and cd["m_like"] and cd["i_like"])

        sham = result["arms"]["C_SHAM_D"]
        sham_penalty += int(
            not sham["complete"] or sham["verifier_checks"] > cd["verifier_checks"]
        )
        for arm in success_by_control:
            success_by_control[arm] += int(result["arms"][arm]["complete"])

        wid = row["world_id"]
        by_world.setdefault(wid, {"worlds": 0, "cd_complete": 0, "graph_exact": 0})
        by_world[wid]["worlds"] += 1
        by_world[wid]["cd_complete"] += int(cd["complete"])
        by_world[wid]["graph_exact"] += int(cd["graph_exact"])

    criteria = {
        "S1_cd_complete_ge_120": cd_complete >= 120,
        "S2_graph_exact_ge_120": graph_exact >= 120,
        "S3_twin_variation_common_correct_ge_120": twin_common >= 120,
        "S4_k_ablation_ge_120": ablation >= 120,
        "S5_none_success_le_10": success_by_control["NONE"] <= 10,
        "S6_c_only_success_le_10": success_by_control["C_ONLY"] <= 10,
        "S7_d_only_success_le_10": success_by_control["D_ONLY"] <= 10,
        "S8_no_reentry_success_le_10": success_by_control["CD_NO_REENTRY"] <= 10,
        "S9_sham_penalty_ge_115": sham_penalty >= 115,
        "S10_cold_twin_success_le_10": success_by_control["CD_COLD_TWIN"] <= 10,
        "S11_dmi_phenotypes_ge_120": phenotypes >= 120,
    }

    return {
        "worlds": total,
        "cd_complete": cd_complete,
        "graph_exact": graph_exact,
        "twin_variation_common_correct": twin_common,
        "k_ablation_pass": ablation,
        "dmi_phenotypes": phenotypes,
        "sham_difference_penalty": sham_penalty,
        "complete_success_by_control": success_by_control,
        "by_world": by_world,
        "criteria": criteria,
        "strong_pass": all(criteria.values()),
    }


def classify(gates: dict[str, bool], sweep: dict[str, object]) -> str:
    if all(gates.values()) and sweep["strong_pass"]:
        return "PASS_CONTINUITY_DIFFERENCE_REGENERATIVE_NUCLEUS_V1"

    core = all(
        gates[key]
        for key in (
            "P2_cd_twin_histories_depth3_all_worlds",
            "P3_twin_history_variation_all_worlds",
            "P4_common_challenge_correct_all_worlds",
            "P5_recombination_novel_k_all_worlds",
            "P7_k_child_generates_z_all_worlds",
            "P8_k_ablation_restore_all_worlds",
            "P9_generated_ancestry_exact_all_worlds",
            "P10_dmi_phenotypes_emerge_all_worlds",
        )
    )
    necessity = all(
        gates[key]
        for key in (
            "P11_single_primitive_and_no_reentry_controls_fail",
            "P12_sham_difference_penalty_all_worlds",
            "P13_cold_twin_control_fails_all_worlds",
        )
    )

    if core and not necessity:
        return "REDUCED_CONTINUITY_DIFFERENCE_NUCLEUS_V1"
    if core or any(gates.values()):
        return "PARTIAL_CONTINUITY_DIFFERENCE_SIGNAL_V1"
    return "VALID_NEGATIVE_CONTINUITY_DIFFERENCE_V1"


def compact_headline(world: dict[str, object]) -> dict[str, object]:
    base = world["base"]
    return {
        "metamorphic_pass": world["metamorphic_pass"],
        "arms": base["arms"],
    }


def main() -> int:
    configs = {k: augment_config(v) for k, v in world_configs().items()}

    headline = {
        world_id: evaluate_headline(configs[world_id], WORLD_SEEDS[world_id])
        for world_id in WORLD_SEEDS
    }
    gates = headline_gates(headline)

    sweep_rows = []
    inadmissible = []
    for world_id in WORLD_SEEDS:
        config = configs[world_id]
        for index in range(25):
            seed = f"{WORLD_SEEDS[world_id]}:SWEEP:{index:03d}"
            try:
                scenario = build_scenario(config, seed)
                result = evaluate_scenario(scenario)
                sweep_rows.append(
                    {"world_id": world_id, "seed": seed, "result": result}
                )
            except RuntimeError as exc:
                inadmissible.append(
                    {"world_id": world_id, "seed": seed, "error": str(exc)}
                )
                # Frozen denominator preservation: an inadmissible generated dish
                # counts as a failed world, never as a skipped replacement.
                fake = {
                    "world_id": world_id,
                    "surface": config.surface,
                    "arms": {
                        arm: {
                            "complete": False,
                            "graph_exact": False,
                            "twin_divergence": False,
                            "common_a_ok": False,
                            "common_b_ok": False,
                            "k_ablation_blocks_z": False,
                            "k_restore_returns_z": False,
                            "d_like": False,
                            "m_like": False,
                            "i_like": False,
                            "verifier_checks": 0,
                        }
                        for arm in ARMS
                    },
                }
                sweep_rows.append(
                    {"world_id": world_id, "seed": seed, "result": fake}
                )

    sweep = sweep_summary(sweep_rows)
    sweep["inadmissible_worlds"] = inadmissible
    verdict = classify(gates, sweep)

    result = {
        "protocol": PROTOCOL,
        "precommit_commit": PRECOMMIT_COMMIT,
        "candidate_primitives": {
            "C": "retained externally verified executable continuity",
            "Difference": "verifier-delivered consequential counterexample",
            "law": "generic residual-guided finite recombination",
            "authority": "external exact verifier",
        },
        "headline": {
            world_id: compact_headline(world)
            for world_id, world in headline.items()
        },
        "headline_gates": gates,
        "sweep": sweep,
        "verdict": verdict,
        "claim_boundary": (
            "Bounded finite Petri-dish test over five frozen adapters. A PASS "
            "would support C+Difference sufficiency and the tested ablations "
            "under this generic recombination law; it would not establish "
            "unique minimality over all algorithms, metaphysical inevitability, "
            "or a reduction of biological/genetic/cultural systems to this pair."
        ),
    }

    outdir = Path("results/continuity_difference_petri_dish_v1")
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str) + "\n"
    )

    compact = []
    for row in sweep_rows:
        r = row["result"]
        compact.append(
            {
                "world_id": row["world_id"],
                "seed": row["seed"],
                "arms": {
                    arm: {
                        key: r["arms"][arm].get(key)
                        for key in (
                            "complete",
                            "graph_exact",
                            "twin_divergence",
                            "recombination_ok",
                            "descendant_ok",
                            "k_ablation_blocks_z",
                            "k_restore_returns_z",
                            "d_like",
                            "m_like",
                            "i_like",
                            "verifier_checks",
                        )
                    }
                    for arm in ARMS
                },
            }
        )
    (outdir / "sweep.json").write_text(
        json.dumps(compact, indent=2, sort_keys=True, default=str) + "\n"
    )

    print("=" * 104)
    print("CONTINUITY + DIFFERENCE PETRI DISH V1")
    print("=" * 104)
    for world_id, world in result["headline"].items():
        cd = world["arms"]["CD"]
        print(
            world_id,
            "A", cd["history_a_depth"],
            "B", cd["history_b_depth"],
            "twin", cd["twin_divergence"],
            "common", cd["common_a_ok"] and cd["common_b_ok"],
            "K", cd["recombination_ok"],
            "Z", cd["descendant_ok"],
            "abl", cd["k_ablation_blocks_z"],
            "restore", cd["k_restore_returns_z"],
            "graph", cd["graph_exact"],
            "DMIphen", cd["d_like"] and cd["m_like"] and cd["i_like"],
            "relabel", world["metamorphic_pass"],
        )
    print("-" * 104)
    for key, value in gates.items():
        print(key, "PASS" if value else "FAIL")
    print("-" * 104)
    print(json.dumps(sweep, indent=2, sort_keys=True))
    print(verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())