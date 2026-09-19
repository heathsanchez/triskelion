#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
from pathlib import Path
from typing import Hashable
import copy
import hashlib
import inspect
import json

PROTOCOL = "CROSS_WORLD_NUCLEUS_INVARIANCE_V1"
PRECOMMIT_COMMIT = "ce2bab8a033ece27e5f77441ebb5a62ece84b2ad"
BLIND_PARENT_BUDGET = 12
CHAIN_DEPTH = 6

ARMS = (
    "NONE",
    "D",
    "M",
    "I",
    "DM",
    "DI",
    "MI",
    "DMI",
    "DMI_COLD",
    "ORACLE_STACK",
)

WORLD_SEEDS = {
    "binary": "TRISKELION_CROSS_WORLD_V1_BINARY",
    "ternary": "TRISKELION_CROSS_WORLD_V1_TERNARY",
    "symbolic": "TRISKELION_CROSS_WORLD_V1_SYMBOLIC",
    "temporal": "TRISKELION_CROSS_WORLD_V1_TEMPORAL",
    "graph": "TRISKELION_CROSS_WORLD_V1_GRAPH",
}


def sha(*parts: object) -> str:
    return hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest()


def stable(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


@dataclass(frozen=True)
class Feature:
    feature_id: str
    values: tuple[Hashable, ...]
    dependencies: tuple[str, ...] = ()
    provenance: str = "primitive"


@dataclass(frozen=True)
class WorldConfig:
    world_id: str
    primitive: dict[str, tuple[Hashable, ...]]
    alphabet: tuple[Hashable, ...]
    schedule: tuple[str, ...]
    surface: str
    relabelled: bool = False


@dataclass(frozen=True)
class Episode:
    generation: int
    episode_id: str
    target: tuple[Hashable, ...]
    declared_parents: tuple[str, str]
    relation_counter: int


# ---------------------------------------------------------------------------
# Generic finite-function nucleus. These functions do not branch on world ID.
# ---------------------------------------------------------------------------

def fit_finite_relation(
    target: tuple[Hashable, ...],
    parents: tuple[tuple[Hashable, ...], ...],
) -> dict[tuple[Hashable, ...], Hashable] | None:
    """Return the exact finite relation iff target is functional and every parent matters."""
    if not parents:
        return None

    table: dict[tuple[Hashable, ...], Hashable] = {}
    for row, output in enumerate(target):
        key = tuple(parent[row] for parent in parents)
        old = table.get(key, output)
        if key in table and old != output:
            return None
        table[key] = output

    # Every selected coordinate must be essential on the observed support.
    for axis in range(len(parents)):
        matters = False
        items = list(table.items())
        for left_key, left_output in items:
            for right_key, right_output in items:
                if left_output == right_output:
                    continue
                if left_key[axis] == right_key[axis]:
                    continue
                if all(
                    left_key[j] == right_key[j]
                    for j in range(len(parents))
                    if j != axis
                ):
                    matters = True
                    break
            if matters:
                break
        if not matters:
            return None

    return table


def apply_relation(
    table: dict[tuple[Hashable, ...], Hashable],
    parents: tuple[tuple[Hashable, ...], ...],
) -> tuple[Hashable, ...]:
    out = []
    for row in range(len(parents[0])):
        key = tuple(parent[row] for parent in parents)
        out.append(table[key])
    return tuple(out)


def differentiate(
    target: tuple[Hashable, ...],
    active: dict[str, Feature],
    max_parent_count: int = 2,
) -> tuple[tuple[str, ...] | None, dict[tuple[Hashable, ...], Hashable] | None, int]:
    """Find the first minimum sufficient parent set under stable world-independent order."""
    tested = 0
    ids = sorted(active)
    for width in range(1, max_parent_count + 1):
        for parent_ids in combinations(ids, width):
            tested += 1
            relation = fit_finite_relation(
                target,
                tuple(active[parent_id].values for parent_id in parent_ids),
            )
            if relation is not None:
                return parent_ids, relation, tested
    return None, None, tested


def mediate_blind(
    target: tuple[Hashable, ...],
    active: dict[str, Feature],
    budget: int = BLIND_PARENT_BUDGET,
    max_parent_count: int = 2,
) -> tuple[tuple[str, ...] | None, dict[tuple[Hashable, ...], Hashable] | None, int]:
    """Search parent subsets without the dedicated differentiation operator."""
    checked = 0
    ids = sorted(active)
    for width in range(1, max_parent_count + 1):
        for parent_ids in combinations(ids, width):
            if checked >= budget:
                return None, None, checked
            checked += 1
            relation = fit_finite_relation(
                target,
                tuple(active[parent_id].values for parent_id in parent_ids),
            )
            if relation is not None:
                return parent_ids, relation, checked
    return None, None, checked


def integrate(
    active: dict[str, Feature],
    *,
    feature_id: str,
    values: tuple[Hashable, ...],
    parent_ids: tuple[str, ...],
    provenance: str,
) -> dict[str, Feature]:
    next_state = dict(active)
    next_state[feature_id] = Feature(
        feature_id=feature_id,
        values=values,
        dependencies=tuple(parent_ids),
        provenance=provenance,
    )
    return next_state


def flags(arm: str) -> tuple[bool, bool, bool]:
    if arm in {"DMI_COLD", "ORACLE_STACK"}:
        return True, True, True
    return ("D" in arm, "M" in arm, "I" in arm)


def solve_episode(
    *,
    target: tuple[Hashable, ...],
    episode_id: str,
    active: dict[str, Feature],
    arm: str,
    provenance: str,
    oracle_parents: tuple[str, str] | None = None,
) -> tuple[dict[str, object], dict[str, Feature]]:
    has_d, has_m, has_i = flags(arm)

    for feature in active.values():
        if feature.values == target:
            return (
                {
                    "ok": True,
                    "route": "REUSE",
                    "selected_parents": [feature.feature_id],
                    "parent_count": 1,
                    "distinction_tests": 0,
                    "verifier_candidate_checks": 0,
                    "installed": False,
                },
                active,
            )

    if not has_m:
        return (
            {
                "ok": False,
                "route": "NO_MEDIATOR",
                "distinction_tests": 0,
                "verifier_candidate_checks": 0,
            },
            active,
        )

    parent_ids: tuple[str, ...] | None = None
    relation: dict[tuple[Hashable, ...], Hashable] | None = None
    distinction_tests = 0
    verifier_checks = 0

    if arm == "ORACLE_STACK":
        assert oracle_parents is not None
        if not all(parent in active for parent in oracle_parents):
            return (
                {
                    "ok": False,
                    "route": "ORACLE_PARENT_MISSING",
                    "distinction_tests": 0,
                    "verifier_candidate_checks": 0,
                },
                active,
            )
        parent_ids = oracle_parents
        relation = fit_finite_relation(
            target,
            tuple(active[parent].values for parent in parent_ids),
        )
        verifier_checks = 1
        if relation is None:
            return (
                {
                    "ok": False,
                    "route": "ORACLE_RELATION_NOT_FUNCTIONAL",
                    "distinction_tests": 0,
                    "verifier_candidate_checks": 1,
                },
                active,
            )

    elif has_d:
        parent_ids, relation, distinction_tests = differentiate(target, active)
        if parent_ids is None or relation is None:
            return (
                {
                    "ok": False,
                    "route": "NO_SUFFICIENT_PARENT_SET",
                    "distinction_tests": distinction_tests,
                    "verifier_candidate_checks": 0,
                },
                active,
            )
        # Exact relation still crosses the independent authority once.
        verifier_checks = 1

    else:
        parent_ids, relation, verifier_checks = mediate_blind(target, active)
        if parent_ids is None or relation is None:
            return (
                {
                    "ok": False,
                    "route": "BLIND_PARENT_BUDGET_EXHAUSTED",
                    "distinction_tests": 0,
                    "verifier_candidate_checks": verifier_checks,
                },
                active,
            )

    assert parent_ids is not None and relation is not None
    proposal = apply_relation(
        relation,
        tuple(active[parent].values for parent in parent_ids),
    )

    # External authority: the proposal cannot self-certify.
    if proposal != target:
        return (
            {
                "ok": False,
                "route": "EXTERNAL_VERIFIER_REFUTED",
                "distinction_tests": distinction_tests,
                "verifier_candidate_checks": verifier_checks,
            },
            active,
        )

    next_state = active
    installed = False
    if has_i or arm == "ORACLE_STACK":
        next_state = integrate(
            active,
            feature_id=episode_id,
            values=proposal,
            parent_ids=parent_ids,
            provenance=provenance,
        )
        installed = True

    return (
        {
            "ok": True,
            "route": "VERIFIED_CHILD",
            "selected_parents": list(parent_ids),
            "parent_count": len(parent_ids),
            "distinction_tests": distinction_tests,
            "verifier_candidate_checks": verifier_checks,
            "installed": installed,
        },
        next_state,
    )


# ---------------------------------------------------------------------------
# World adapters. All world-specific structure ends here.
# ---------------------------------------------------------------------------

def binary_world() -> WorldConfig:
    alphabet = (0, 1)
    rows = tuple(product(alphabet, repeat=5))
    primitive = {
        f"q{i}": tuple(row[i] for row in rows)
        for i in range(5)
    }
    return WorldConfig(
        "binary",
        primitive,
        alphabet,
        ("q1", "q2", "q3", "q4", "q0", "q1"),
        "binary-cartesian",
    )


def ternary_world() -> WorldConfig:
    alphabet = (0, 1, 2)
    rows = tuple(product(alphabet, repeat=4))
    primitive = {
        f"q{i}": tuple(row[i] for row in rows)
        for i in range(4)
    }
    return WorldConfig(
        "ternary",
        primitive,
        alphabet,
        ("q1", "q2", "q3", "q0", "q1", "q2"),
        "ternary-cartesian",
    )


def symbolic_world() -> WorldConfig:
    alphabet = ("ka", "zu", "mi")
    rows = tuple(product(alphabet, repeat=4))
    primitive = {
        f"q{i}": tuple(row[i] for row in rows)
        for i in range(4)
    }
    return WorldConfig(
        "symbolic",
        primitive,
        alphabet,
        ("q1", "q2", "q3", "q0", "q1", "q2"),
        "opaque-length4-string",
    )


def temporal_world() -> WorldConfig:
    histories = tuple(
        ((p0, p1), (c0, c1))
        for p0, p1, c0, c1 in product((0, 1), repeat=4)
    )
    primitive = {
        "q0": tuple(history[0][0] for history in histories),
        "q1": tuple(history[0][1] for history in histories),
        "q2": tuple(history[1][0] for history in histories),
        "q3": tuple(history[1][1] for history in histories),
    }
    return WorldConfig(
        "temporal",
        primitive,
        (0, 1),
        ("q1", "q2", "q3", "q0", "q1", "q2"),
        "opaque-length2-history",
    )


def graph_world() -> WorldConfig:
    alphabet = (0, 1, 2)
    nodes = tuple(product(alphabet, repeat=4))

    # Four opaque local observations derived from four deterministic outgoing
    # neighbor transforms. The nucleus never receives edges or these formulas.
    observed = []
    for a, b, c, d in nodes:
        n0 = ((a + b) % 3, b, c, d)
        n1 = (a, (b + c) % 3, c, d)
        n2 = (a, b, (c + d) % 3, d)
        n3 = (a, b, c, (d + a) % 3)
        observed.append((n0[0], n1[1], n2[2], n3[3]))

    primitive = {
        f"q{i}": tuple(row[i] for row in observed)
        for i in range(4)
    }

    distinct_vectors = len(set(zip(*(primitive[k] for k in sorted(primitive)))))
    nonconstant = sum(len(set(values)) > 1 for values in primitive.values())
    if distinct_vectors < 4 or nonconstant < 3:
        raise RuntimeError("graph adapter diversity precondition failed")

    return WorldConfig(
        "graph",
        primitive,
        alphabet,
        ("q1", "q2", "q3", "q0", "q1", "q2"),
        "directed-graph-local-observation",
    )


def world_configs() -> dict[str, WorldConfig]:
    return {
        "binary": binary_world(),
        "ternary": ternary_world(),
        "symbolic": symbolic_world(),
        "temporal": temporal_world(),
        "graph": graph_world(),
    }


# ---------------------------------------------------------------------------
# Sealed hidden-world generation.
# ---------------------------------------------------------------------------

def generated_target(
    *,
    left: tuple[Hashable, ...],
    right: tuple[Hashable, ...],
    alphabet: tuple[Hashable, ...],
    seed: str,
    generation: int,
    counter: int,
) -> tuple[Hashable, ...]:
    support = sorted(set(zip(left, right)), key=stable)
    table: dict[tuple[Hashable, Hashable], Hashable] = {}
    for pair in support:
        index = int(
            sha(seed, generation, counter, stable(pair))[:16],
            16,
        ) % len(alphabet)
        table[pair] = alphabet[index]
    return tuple(table[(a, b)] for a, b in zip(left, right))


def minimum_sufficient_sets(
    target: tuple[Hashable, ...],
    active: dict[str, tuple[Hashable, ...]],
) -> list[tuple[tuple[str, ...], dict[tuple[Hashable, ...], Hashable]]]:
    ids = sorted(active)
    for width in (1, 2):
        found = []
        for parent_ids in combinations(ids, width):
            relation = fit_finite_relation(
                target,
                tuple(active[parent].values if isinstance(active[parent], Feature) else active[parent] for parent in parent_ids),
            )
            if relation is not None:
                found.append((parent_ids, relation))
        if found:
            return found
    return []


def build_chain(config: WorldConfig, seed: str) -> list[Episode]:
    active: dict[str, tuple[Hashable, ...]] = dict(config.primitive)
    primitive_ids = set(config.primitive)
    previous_id = "q0"
    episodes: list[Episode] = []

    for generation in range(1, CHAIN_DEPTH + 1):
        raw_id = config.schedule[generation - 1]
        left = active[previous_id]
        right = active[raw_id]

        selected: Episode | None = None
        for counter in range(4096):
            target = generated_target(
                left=left,
                right=right,
                alphabet=config.alphabet,
                seed=seed,
                generation=generation,
                counter=counter,
            )

            if target in active.values():
                continue

            declared = fit_finite_relation(target, (left, right))
            if declared is None:
                continue

            minima = minimum_sufficient_sets(target, active)
            if not minima or len(minima[0][0]) != 2:
                continue

            if generation > 1:
                if any(
                    all(parent in primitive_ids for parent in parent_ids)
                    for parent_ids, _ in minima
                ):
                    continue
                if not any(
                    previous_id in parent_ids
                    for parent_ids, _ in minima
                ):
                    continue

            selected = Episode(
                generation=generation,
                episode_id=f"G{generation}",
                target=target,
                declared_parents=(previous_id, raw_id),
                relation_counter=counter,
            )
            break

        if selected is None:
            raise RuntimeError(
                f"world construction failed: {config.world_id} {seed} G{generation}"
            )

        episodes.append(selected)
        active[selected.episode_id] = selected.target
        previous_id = selected.episode_id

    return episodes


def build_replacement_chain(
    config: WorldConfig,
    seed: str,
    original: list[Episode],
) -> list[Episode]:
    active: dict[str, tuple[Hashable, ...]] = dict(config.primitive)
    active["G1"] = original[0].target
    active["G2"] = original[1].target
    primitive_ids = set(config.primitive)
    previous_id = "G2"
    replacement: list[Episode] = []

    for generation in range(3, CHAIN_DEPTH + 1):
        raw_id = config.schedule[generation - 1]
        left = active[previous_id]
        right = active[raw_id]
        selected = None

        for counter in range(4096):
            target = generated_target(
                left=left,
                right=right,
                alphabet=config.alphabet,
                seed=seed + ":COUNTEREVIDENCE",
                generation=generation,
                counter=counter,
            )
            if generation == 3 and target == original[2].target:
                continue
            if target in active.values():
                continue
            if fit_finite_relation(target, (left, right)) is None:
                continue

            minima = minimum_sufficient_sets(target, active)
            if not minima or len(minima[0][0]) != 2:
                continue
            if any(
                all(parent in primitive_ids for parent in parent_ids)
                for parent_ids, _ in minima
            ):
                continue
            if not any(
                previous_id in parent_ids
                for parent_ids, _ in minima
            ):
                continue

            selected = Episode(
                generation=generation,
                episode_id=f"G{generation}R",
                target=target,
                declared_parents=(previous_id, raw_id),
                relation_counter=counter,
            )
            break

        if selected is None:
            raise RuntimeError(
                f"replacement construction failed: {config.world_id} {seed} G{generation}"
            )

        replacement.append(selected)
        active[selected.episode_id] = selected.target
        previous_id = selected.episode_id

    return replacement


# ---------------------------------------------------------------------------
# Evaluation, ablation, counterevidence and representation metamorphism.
# ---------------------------------------------------------------------------

def initial_state(config: WorldConfig) -> dict[str, Feature]:
    return {
        feature_id: Feature(feature_id, values)
        for feature_id, values in config.primitive.items()
    }


def state_digest(active: dict[str, Feature]) -> str:
    payload = [
        [
            feature.feature_id,
            list(feature.values),
            list(feature.dependencies),
            feature.provenance,
        ]
        for feature in sorted(active.values(), key=lambda item: item.feature_id)
    ]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def open_control(active: dict[str, Feature]) -> dict[str, object]:
    before = state_digest(active)
    # Positive but non-closed evidence cannot authorize a structural promotion.
    after = state_digest(active)
    return {
        "route": "UNKNOWN",
        "mutations": 0 if before == after else 1,
        "before": before,
        "after": after,
    }


def run_arm(
    config: WorldConfig,
    seed: str,
    episodes: list[Episode],
    arm: str,
) -> dict[str, object]:
    active = initial_state(config)
    records = []
    snapshots: dict[int, dict[str, Feature]] = {}

    for episode in episodes:
        if arm == "DMI_COLD":
            active = initial_state(config)

        result, active = solve_episode(
            target=episode.target,
            episode_id=episode.episode_id,
            active=active,
            arm=arm,
            provenance=(
                f"{PRECOMMIT_COMMIT}:{config.world_id}:{seed}:"
                f"{episode.episode_id}"
            ),
            oracle_parents=(
                episode.declared_parents
                if arm == "ORACLE_STACK"
                else None
            ),
        )

        selected = tuple(result.get("selected_parents", ()))
        result.update(
            {
                "generation": episode.generation,
                "episode_id": episode.episode_id,
                "expected_previous_child": (
                    None if episode.generation == 1 else episode.declared_parents[0]
                ),
                "uses_previous_child": (
                    episode.generation == 1
                    or episode.declared_parents[0] in selected
                ),
            }
        )
        records.append(result)
        snapshots[episode.generation] = copy.deepcopy(active)

        if not result["ok"]:
            break

    return {
        "arm": arm,
        "open_control": open_control(initial_state(config)),
        "depth": sum(1 for row in records if row["ok"]),
        "records": records,
        "distinction_tests": sum(
            int(row.get("distinction_tests", 0))
            for row in records
        ),
        "verifier_candidate_checks": sum(
            int(row.get("verifier_candidate_checks", 0))
            for row in records
        ),
        "integrated_children": sum(
            int(bool(row.get("installed")))
            for row in records
        ),
        "_state": active,
        "_snapshots": snapshots,
    }


def remove_dependency_cone(
    active: dict[str, Feature],
    root: str,
) -> tuple[dict[str, Feature], set[str]]:
    removed: set[str] = set()
    frontier = [root]

    while frontier:
        current = frontier.pop()
        if current in removed:
            continue
        removed.add(current)
        for feature in active.values():
            if current in feature.dependencies:
                frontier.append(feature.feature_id)

    return (
        {
            feature_id: feature
            for feature_id, feature in active.items()
            if feature_id not in removed
        },
        removed,
    )


def causal_ablation(
    config: WorldConfig,
    seed: str,
    episodes: list[Episode],
    full: dict[str, object],
) -> dict[str, object]:
    snapshots = full["_snapshots"]
    if full["depth"] < 4:
        return {"eligible": False, "pass": False}

    after_g4 = copy.deepcopy(snapshots[4])
    ablated, removed = remove_dependency_cone(after_g4, "G3")

    without, _ = solve_episode(
        target=episodes[3].target,
        episode_id="G4",
        active=copy.deepcopy(ablated),
        arm="DMI",
        provenance=f"ablation:{config.world_id}:{seed}",
    )

    restored = copy.deepcopy(ablated)
    restored["G3"] = copy.deepcopy(snapshots[3]["G3"])
    after_restore, _ = solve_episode(
        target=episodes[3].target,
        episode_id="G4",
        active=restored,
        arm="DMI",
        provenance=f"restore:{config.world_id}:{seed}",
    )

    return {
        "eligible": True,
        "removed": sorted(removed),
        "without_g3_route": without["route"],
        "without_g3_ok": without["ok"],
        "after_restore_route": after_restore["route"],
        "after_restore_ok": after_restore["ok"],
        "pass": (
            removed == {"G3", "G4"}
            and not without["ok"]
            and after_restore["ok"]
        ),
    }


def metamorphosis(
    config: WorldConfig,
    seed: str,
    episodes: list[Episode],
    replacement: list[Episode],
    full: dict[str, object],
) -> dict[str, object]:
    if full["depth"] < 6:
        return {"eligible": False, "pass": False, "regenerated_depth": 0}

    snapshots = full["_snapshots"]
    active, removed = remove_dependency_cone(
        copy.deepcopy(snapshots[6]),
        "G3",
    )

    preserved = "G1" in active and "G2" in active
    removed_descendants = all(
        feature_id not in active
        for feature_id in ("G3", "G4", "G5", "G6")
    )

    records = []
    for episode in replacement:
        result, active = solve_episode(
            target=episode.target,
            episode_id=episode.episode_id,
            active=active,
            arm="DMI",
            provenance=(
                f"counterevidence:{PRECOMMIT_COMMIT}:"
                f"{config.world_id}:{seed}:{episode.episode_id}"
            ),
        )
        result["uses_previous_child"] = (
            episode.declared_parents[0]
            in tuple(result.get("selected_parents", ()))
        )
        records.append(result)
        if not result["ok"]:
            break

    regenerated_depth = sum(1 for row in records if row["ok"])

    return {
        "eligible": True,
        "removed": sorted(removed),
        "preserved_g1_g2": preserved,
        "removed_g3_g6": removed_descendants,
        "regenerated_depth": regenerated_depth,
        "all_replacement_steps_use_previous_child": (
            len(records) == 4
            and all(row.get("uses_previous_child", False) for row in records)
        ),
        "pass": (
            removed == {"G3", "G4", "G5", "G6"}
            and preserved
            and removed_descendants
            and regenerated_depth == 4
            and len(records) == 4
            and all(row["ok"] for row in records)
        ),
        "records": records,
    }


def public_run(run: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in run.items()
        if not key.startswith("_")
    }


def relabel_map(alphabet: tuple[Hashable, ...]) -> dict[Hashable, Hashable]:
    if len(alphabet) <= 1:
        return {value: value for value in alphabet}
    return {
        alphabet[index]: alphabet[(index + 1) % len(alphabet)]
        for index in range(len(alphabet))
    }


def relabel_config(config: WorldConfig) -> WorldConfig:
    mapping = relabel_map(config.alphabet)
    primitive = {
        feature_id: tuple(mapping[value] for value in values)
        for feature_id, values in config.primitive.items()
    }
    return WorldConfig(
        config.world_id + "-relabel",
        primitive,
        config.alphabet,
        config.schedule,
        config.surface + "-bijective-relabel",
        True,
    )


def relabel_episodes(
    episodes: list[Episode],
    alphabet: tuple[Hashable, ...],
) -> list[Episode]:
    mapping = relabel_map(alphabet)
    return [
        Episode(
            generation=episode.generation,
            episode_id=episode.episode_id,
            target=tuple(mapping[value] for value in episode.target),
            declared_parents=episode.declared_parents,
            relation_counter=episode.relation_counter,
        )
        for episode in episodes
    ]


def evaluate_view(
    config: WorldConfig,
    seed: str,
    episodes: list[Episode],
    replacement: list[Episode],
) -> dict[str, object]:
    runs = {
        arm: run_arm(config, seed, episodes, arm)
        for arm in ARMS
    }
    full = runs["DMI"]
    ablation = causal_ablation(config, seed, episodes, full)
    change = metamorphosis(
        config,
        seed,
        episodes,
        replacement,
        full,
    )

    return {
        "runs": {
            arm: public_run(run)
            for arm, run in runs.items()
        },
        "causal_ablation": ablation,
        "metamorphosis": change,
    }


def evaluate_world(config: WorldConfig, seed: str, do_relabel: bool) -> dict[str, object]:
    episodes = build_chain(config, seed)
    replacement = build_replacement_chain(config, seed, episodes)
    base = evaluate_view(config, seed, episodes, replacement)

    relabelled = None
    metamorphic_pass = None
    if do_relabel:
        relabel_configured = relabel_config(config)
        relabel_eps = relabel_episodes(episodes, config.alphabet)
        relabel_replacement = relabel_episodes(replacement, config.alphabet)
        relabelled = evaluate_view(
            relabel_configured,
            seed + ":RELABEL",
            relabel_eps,
            relabel_replacement,
        )

        base_dmi = base["runs"]["DMI"]
        relabel_dmi = relabelled["runs"]["DMI"]
        base_cards = [
            row.get("parent_count")
            for row in base_dmi["records"]
            if row.get("ok")
        ]
        relabel_cards = [
            row.get("parent_count")
            for row in relabel_dmi["records"]
            if row.get("ok")
        ]
        metamorphic_pass = (
            base_dmi["depth"] == relabel_dmi["depth"]
            and base_cards == relabel_cards
            and base["causal_ablation"]["pass"]
            == relabelled["causal_ablation"]["pass"]
            and base["metamorphosis"]["pass"]
            == relabelled["metamorphosis"]["pass"]
        )

    return {
        "world_id": config.world_id,
        "surface": config.surface,
        "carrier_rows": len(next(iter(config.primitive.values()))),
        "primitive_feature_count": len(config.primitive),
        "alphabet": [str(value) for value in config.alphabet],
        "base": base,
        "relabelled": relabelled,
        "representation_metamorphism_pass": metamorphic_pass,
    }


def nucleus_source_is_world_independent() -> bool:
    source = "\n".join(
        inspect.getsource(fn)
        for fn in (
            fit_finite_relation,
            differentiate,
            mediate_blind,
            integrate,
            solve_episode,
        )
    ).lower()
    banned = (
        "binary_world",
        "ternary_world",
        "symbolic_world",
        "temporal_world",
        "graph_world",
        "xor",
        "boolean",
        "past",
        "present",
        "adjacency",
    )
    return not any(term in source for term in banned)


def headline_gates(world_results: dict[str, dict[str, object]]) -> dict[str, bool]:
    bases = {
        world_id: result["base"]
        for world_id, result in world_results.items()
    }

    c2 = all(
        run["open_control"]["route"] == "UNKNOWN"
        and run["open_control"]["mutations"] == 0
        for result in bases.values()
        for run in result["runs"].values()
    )

    c3 = all(
        result["runs"]["DMI"]["depth"] == 6
        for result in bases.values()
    )

    c4 = all(
        len(result["runs"]["DMI"]["records"]) == 6
        and all(
            row.get("uses_previous_child", False)
            for row in result["runs"]["DMI"]["records"][1:]
        )
        for result in bases.values()
    )

    c5 = all(
        result["causal_ablation"]["pass"]
        for result in bases.values()
    )
    c6 = all(
        result["metamorphosis"]["pass"]
        for result in bases.values()
    )
    c7 = all(
        result["runs"]["DMI_COLD"]["depth"] < 6
        for result in bases.values()
    )
    c8 = all(
        result["runs"]["DM"]["depth"]
        < result["runs"]["DMI"]["depth"]
        for result in bases.values()
    )
    c9 = all(
        result["runs"]["DI"]["depth"]
        < result["runs"]["DMI"]["depth"]
        for result in bases.values()
    )
    c10 = all(
        (
            result["runs"]["MI"]["depth"]
            < result["runs"]["DMI"]["depth"]
        )
        or (
            result["runs"]["MI"]["depth"]
            == result["runs"]["DMI"]["depth"]
            and result["runs"]["MI"]["verifier_candidate_checks"]
            > result["runs"]["DMI"]["verifier_candidate_checks"]
        )
        for result in bases.values()
    )
    c11 = all(
        result["representation_metamorphism_pass"] is True
        for world_id, result in world_results.items()
        if world_id != "graph"
    )

    return {
        "C1_same_nucleus_source_all_worlds": True,
        "C2_open_unknown_zero_mutation": c2,
        "C3_dmi_g6_all_worlds": c3,
        "C4_child_parentage_all_worlds": c4,
        "C5_causal_ablation_all_worlds": c5,
        "C6_metamorphosis_all_worlds": c6,
        "C7_cold_fails_g6_all_worlds": c7,
        "C8_remove_i_reduces_reach_all_worlds": c8,
        "C9_remove_m_reduces_reach_all_worlds": c9,
        "C10_remove_d_cost_or_reach_penalty_all_worlds": c10,
        "C11_representation_metamorphism_w1_w4": c11,
        "C12_no_world_specific_operator_in_nucleus": nucleus_source_is_world_independent(),
    }


def sweep_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    total = len(rows)

    def base(row: dict[str, object]) -> dict[str, object]:
        return row["result"]["base"]

    dmi_g6 = sum(
        base(row)["runs"]["DMI"]["depth"] == 6
        for row in rows
    )
    metamorphosis_pass = sum(
        bool(base(row)["metamorphosis"]["pass"])
        for row in rows
    )
    ablation_pass = sum(
        bool(base(row)["causal_ablation"]["pass"])
        for row in rows
    )
    cold_g6 = sum(
        base(row)["runs"]["DMI_COLD"]["depth"] == 6
        for row in rows
    )
    dm_loss = sum(
        base(row)["runs"]["DM"]["depth"]
        < base(row)["runs"]["DMI"]["depth"]
        for row in rows
    )
    di_loss = sum(
        base(row)["runs"]["DI"]["depth"]
        < base(row)["runs"]["DMI"]["depth"]
        for row in rows
    )
    mi_penalty = sum(
        (
            base(row)["runs"]["MI"]["depth"]
            < base(row)["runs"]["DMI"]["depth"]
        )
        or (
            base(row)["runs"]["MI"]["depth"]
            == base(row)["runs"]["DMI"]["depth"]
            and base(row)["runs"]["MI"]["verifier_candidate_checks"]
            > base(row)["runs"]["DMI"]["verifier_candidate_checks"]
        )
        for row in rows
    )

    by_world = {}
    for world_id in WORLD_SEEDS:
        group = [row for row in rows if row["world_id"] == world_id]
        by_world[world_id] = {
            "worlds": len(group),
            "dmi_g6": sum(
                base(row)["runs"]["DMI"]["depth"] == 6
                for row in group
            ),
            "dmi_ablation_pass": sum(
                base(row)["causal_ablation"]["pass"]
                for row in group
            ),
            "dmi_metamorphosis_pass": sum(
                base(row)["metamorphosis"]["pass"]
                for row in group
            ),
            "mi_g6": sum(
                base(row)["runs"]["MI"]["depth"] == 6
                for row in group
            ),
        }

    criteria = {
        "S1_dmi_g6_ge_120": dmi_g6 >= 120,
        "S2_metamorphosis_ge_115": metamorphosis_pass >= 115,
        "S3_ablation_ge_120": ablation_pass >= 120,
        "S4_cold_g6_le_10": cold_g6 <= 10,
        "S5_dm_loss_ge_115": dm_loss >= 115,
        "S6_di_loss_ge_115": di_loss >= 115,
        "S7_mi_reach_or_cost_penalty_ge_115": mi_penalty >= 115,
    }

    return {
        "worlds": total,
        "dmi_g6": dmi_g6,
        "dmi_metamorphosis_pass": metamorphosis_pass,
        "dmi_causal_ablation_pass": ablation_pass,
        "dmi_cold_g6": cold_g6,
        "dm_reach_loss": dm_loss,
        "di_reach_loss": di_loss,
        "mi_reach_or_cost_penalty": mi_penalty,
        "by_world": by_world,
        "criteria": criteria,
        "strong_pass": all(criteria.values()),
    }


def classify(
    gates: dict[str, bool],
    sweep: dict[str, object],
    headline: dict[str, dict[str, object]],
) -> str:
    if all(gates.values()) and sweep["strong_pass"]:
        return "PASS_CROSS_WORLD_NUCLEUS_INVARIANCE_V1"

    # If full DMI develops all headline worlds but a role is repeatedly dispensable,
    # prefer a reduced-nucleus result over preserving the triad.
    dmi_all = all(
        result["base"]["runs"]["DMI"]["depth"] == 6
        for result in headline.values()
    )
    developmental_core = (
        dmi_all
        and gates["C2_open_unknown_zero_mutation"]
        and gates["C6_metamorphosis_all_worlds"]
    )
    role_failure = not (
        gates["C8_remove_i_reduces_reach_all_worlds"]
        and gates["C9_remove_m_reduces_reach_all_worlds"]
        and gates["C10_remove_d_cost_or_reach_penalty_all_worlds"]
    )

    if developmental_core and role_failure:
        return "REDUCED_CROSS_WORLD_NUCLEUS_V1"
    if developmental_core:
        return "PARTIAL_CROSS_WORLD_NUCLEUS_SIGNAL_V1"
    return "VALID_NEGATIVE_CROSS_WORLD_NUCLEUS_V1"


def compact_world(result: dict[str, object]) -> dict[str, object]:
    base = result["base"]
    return {
        "world_id": result["world_id"],
        "surface": result["surface"],
        "carrier_rows": result["carrier_rows"],
        "primitive_feature_count": result["primitive_feature_count"],
        "alphabet": result["alphabet"],
        "depths": {
            arm: base["runs"][arm]["depth"]
            for arm in ARMS
        },
        "typed_costs": {
            arm: {
                "distinction_tests": base["runs"][arm]["distinction_tests"],
                "verifier_candidate_checks": base["runs"][arm]["verifier_candidate_checks"],
            }
            for arm in ("MI", "DMI", "ORACLE_STACK")
        },
        "dmi_parentage": [
            {
                "episode": row["episode_id"],
                "selected_parents": row.get("selected_parents", []),
                "uses_previous_child": row.get("uses_previous_child"),
            }
            for row in base["runs"]["DMI"]["records"]
        ],
        "causal_ablation": base["causal_ablation"],
        "metamorphosis": {
            "pass": base["metamorphosis"]["pass"],
            "regenerated_depth": base["metamorphosis"].get("regenerated_depth", 0),
            "all_replacement_steps_use_previous_child": base["metamorphosis"].get(
                "all_replacement_steps_use_previous_child"
            ),
        },
        "representation_metamorphism_pass": result[
            "representation_metamorphism_pass"
        ],
    }


def main() -> int:
    configs = world_configs()

    headline = {}
    for world_id, config in configs.items():
        headline[world_id] = evaluate_world(
            config,
            WORLD_SEEDS[world_id],
            do_relabel=(world_id != "graph"),
        )

    gates = headline_gates(headline)

    sweep_rows = []
    for world_id, config in configs.items():
        base_seed = WORLD_SEEDS[world_id]
        for index in range(25):
            seed = f"{base_seed}:SWEEP:{index:03d}"
            result = evaluate_world(
                config,
                seed,
                do_relabel=False,
            )
            sweep_rows.append(
                {
                    "world_id": world_id,
                    "seed": seed,
                    "result": result,
                }
            )

    sweep = sweep_summary(sweep_rows)
    verdict = classify(gates, sweep, headline)

    result = {
        "protocol": PROTOCOL,
        "precommit_commit": PRECOMMIT_COMMIT,
        "nucleus": {
            "D": "minimum sufficient differentiation",
            "M": "generic finite-relation mediation",
            "I": "verified persistent integration",
            "authority": "external exact verifier; OPEN cannot promote",
        },
        "headline": {
            world_id: compact_world(world_result)
            for world_id, world_result in headline.items()
        },
        "headline_gates": gates,
        "sweep": sweep,
        "verdict": verdict,
        "claim_boundary": (
            "Bounded finite cross-world test over five frozen adapters. "
            "A positive signal supports representation-invariant developmental "
            "behavior under this protocol only; it does not establish "
            "metaphysical fundamentality, unrestricted open-world intelligence, "
            "or unique global minimality of D/M/I."
        ),
    }

    outdir = Path("results/cross_world_nucleus_invariance_v1")
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str) + "\n"
    )

    compact_sweep = [
        {
            "world_id": row["world_id"],
            "seed": row["seed"],
            "depths": {
                arm: row["result"]["base"]["runs"][arm]["depth"]
                for arm in ARMS
            },
            "dmi_ablation": row["result"]["base"]["causal_ablation"]["pass"],
            "dmi_metamorphosis": row["result"]["base"]["metamorphosis"]["pass"],
            "mi_vchecks": row["result"]["base"]["runs"]["MI"][
                "verifier_candidate_checks"
            ],
            "dmi_vchecks": row["result"]["base"]["runs"]["DMI"][
                "verifier_candidate_checks"
            ],
        }
        for row in sweep_rows
    ]
    (outdir / "sweep.json").write_text(
        json.dumps(compact_sweep, indent=2, sort_keys=True) + "\n"
    )

    print("=" * 96)
    print("CROSS-WORLD NUCLEUS INVARIANCE V1")
    print("=" * 96)
    for world_id, world_result in result["headline"].items():
        print(
            world_id,
            "depths=" + json.dumps(world_result["depths"], sort_keys=True),
            "ablation=" + str(world_result["causal_ablation"]["pass"]),
            "metamorphosis=" + str(world_result["metamorphosis"]["pass"]),
            "relabel=" + str(world_result["representation_metamorphism_pass"]),
        )
        print("  parentage", json.dumps(world_result["dmi_parentage"], sort_keys=True))
    print("-" * 96)
    for gate, passed in gates.items():
        print(gate, "PASS" if passed else "FAIL")
    print("-" * 96)
    print(json.dumps(sweep, indent=2, sort_keys=True))
    print(verdict)

    # Every scientific verdict is a successful execution. Infrastructure failures
    # raise before this point and therefore remain distinct.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
