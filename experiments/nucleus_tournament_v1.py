#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
import copy
import hashlib
import json

PROTOCOL = "NUCLEUS_TOURNAMENT_V1"
PRECOMMIT_COMMIT = "5a1cf1d01e05937e48b848225a1b35c24a67c980"
HEADLINE_SEED = "TRISKELION_NUCLEUS_TOURNAMENT_V1_HEADLINE"
SWEEP_PREFIX = "TRISKELION_NUCLEUS_TOURNAMENT_V1_SWEEP"
BLIND_BUDGET = 48
N_RAW = 5
N_ROWS = 1 << N_RAW

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


def digest(*parts: object) -> str:
    return hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest()


def raw_sem(index: int) -> int:
    out = 0
    for row in range(N_ROWS):
        if (row >> index) & 1:
            out |= 1 << row
    return out


RAWS = {f"q{i}": raw_sem(i) for i in range(N_RAW)}


def apply_table(table: int, left: int, right: int) -> int:
    out = 0
    for row in range(N_ROWS):
        a = (left >> row) & 1
        b = (right >> row) & 1
        if (table >> (a + 2 * b)) & 1:
            out |= 1 << row
    return out


def essential_table(table: int) -> bool:
    left_matters = any(
        ((table >> (0 + 2 * b)) & 1) != ((table >> (1 + 2 * b)) & 1)
        for b in (0, 1)
    )
    right_matters = any(
        ((table >> (a + 0)) & 1) != ((table >> (a + 2)) & 1)
        for a in (0, 1)
    )
    return left_matters and right_matters


ESSENTIAL_TABLES = tuple(t for t in range(16) if essential_table(t))


def observed_essential(target: int, left: int, right: int) -> bool:
    rows = [
        ((left >> r) & 1, (right >> r) & 1, (target >> r) & 1)
        for r in range(N_ROWS)
    ]
    left_matters = False
    right_matters = False

    for bval in (0, 1):
        buckets: dict[int, set[int]] = {}
        for a, b, y in rows:
            if b == bval:
                buckets.setdefault(a, set()).add(y)
        if 0 in buckets and 1 in buckets:
            if any(x != y for x in buckets[0] for y in buckets[1]):
                left_matters = True

    for aval in (0, 1):
        buckets = {}
        for a, b, y in rows:
            if a == aval:
                buckets.setdefault(b, set()).add(y)
        if 0 in buckets and 1 in buckets:
            if any(x != y for x in buckets[0] for y in buckets[1]):
                right_matters = True

    return left_matters and right_matters


def fit_relation(target: int, left: int, right: int) -> int | None:
    """Fit the exact finite relation induced on the sealed 32-row carrier.

    If a binary input combination is absent from the carrier induced by the two
    candidate features, the unobserved table cell is canonically completed with
    zero. Authority is only over the sealed carrier, so no claim is made about
    absent combinations.
    """
    table: dict[int, int] = {}
    for row in range(N_ROWS):
        key = ((left >> row) & 1) + 2 * ((right >> row) & 1)
        value = (target >> row) & 1
        if key in table and table[key] != value:
            return None
        table[key] = value

    if not observed_essential(target, left, right):
        return None

    return sum(table.get(key, 0) << key for key in range(4))


def sufficient_pairs(target: int, features: dict[str, int]) -> list[tuple[str, str, int]]:
    out = []
    for left_id, right_id in combinations(sorted(features), 2):
        relation = fit_relation(target, features[left_id], features[right_id])
        if relation is not None:
            out.append((left_id, right_id, relation))
    return out


def relation_order(seed: str, generation: int, replacement: bool = False) -> list[int]:
    phase = "REPLACE" if replacement else "NORMAL"
    return sorted(
        ESSENTIAL_TABLES,
        key=lambda table: digest(seed, phase, generation, table),
    )


@dataclass(frozen=True)
class WorldEpisode:
    generation: int
    episode_id: str
    hidden_table: int
    target: int
    parent_ids: tuple[str, str]
    minimum_pairs: tuple[tuple[str, str, int], ...]


@dataclass(frozen=True)
class Feature:
    feature_id: str
    semantics: int
    dependencies: tuple[str, ...] = ()
    provenance: str = "primitive"


def choose_episode(
    *,
    seed: str,
    generation: int,
    previous_id: str,
    previous_semantics: int,
    raw_id: str,
    expected_features: dict[str, int],
    episode_id: str,
    replacement: bool = False,
    exclude_table: int | None = None,
) -> WorldEpisode:
    for table in relation_order(seed, generation, replacement):
        if exclude_table is not None and table == exclude_table:
            continue

        target = apply_table(table, previous_semantics, expected_features[raw_id])

        # Frozen admissibility conditions from the precommit.
        if target in RAWS.values():
            continue

        declared = fit_relation(
            target,
            previous_semantics,
            expected_features[raw_id],
        )
        if declared is None:
            continue

        pairs = sufficient_pairs(target, expected_features)

        if generation > 1:
            if any(a.startswith("q") and b.startswith("q") for a, b, _ in pairs):
                continue
            if not any(previous_id in (a, b) for a, b, _ in pairs):
                continue

        return WorldEpisode(
            generation=generation,
            episode_id=episode_id,
            hidden_table=table,
            target=target,
            parent_ids=(previous_id, raw_id),
            minimum_pairs=tuple(pairs),
        )

    raise RuntimeError(
        f"sealed world construction failed: seed={seed} generation={generation}"
    )


def build_world(seed: str) -> list[WorldEpisode]:
    expected = dict(RAWS)
    previous_id = "q0"
    previous_semantics = expected[previous_id]
    raw_schedule = ("q1", "q2", "q3", "q4", "q0", "q1")

    episodes = []
    for generation, raw_id in enumerate(raw_schedule, 1):
        episode = choose_episode(
            seed=seed,
            generation=generation,
            previous_id=previous_id,
            previous_semantics=previous_semantics,
            raw_id=raw_id,
            expected_features=expected,
            episode_id=f"G{generation}",
        )
        episodes.append(episode)
        expected[episode.episode_id] = episode.target
        previous_id = episode.episode_id
        previous_semantics = episode.target

    return episodes


def build_replacement_world(
    seed: str,
    original: list[WorldEpisode],
) -> list[WorldEpisode]:
    expected = dict(RAWS)
    for episode in original[:2]:
        expected[episode.episode_id] = episode.target

    replacement = choose_episode(
        seed=seed,
        generation=3,
        previous_id="G2",
        previous_semantics=expected["G2"],
        raw_id="q3",
        expected_features=expected,
        episode_id="G3R",
        replacement=True,
        exclude_table=original[2].hidden_table,
    )

    out = [replacement]
    expected["G3R"] = replacement.target
    previous_id = "G3R"
    previous_semantics = replacement.target

    for index, raw_id in zip(range(3, 6), ("q4", "q0", "q1")):
        hidden_table = original[index].hidden_table
        target = apply_table(
            hidden_table,
            previous_semantics,
            expected[raw_id],
        )
        pairs = sufficient_pairs(target, expected)
        episode = WorldEpisode(
            generation=index + 1,
            episode_id=f"G{index + 1}R",
            hidden_table=hidden_table,
            target=target,
            parent_ids=(previous_id, raw_id),
            minimum_pairs=tuple(pairs),
        )
        out.append(episode)
        expected[episode.episode_id] = target
        previous_id = episode.episode_id
        previous_semantics = target

    return out


def initial_state() -> dict[str, Feature]:
    return {
        feature_id: Feature(feature_id, semantics)
        for feature_id, semantics in RAWS.items()
    }


def state_digest(state: dict[str, Feature]) -> str:
    rows = [
        (
            f.feature_id,
            f.semantics,
            list(f.dependencies),
            f.provenance,
        )
        for f in sorted(state.values(), key=lambda x: x.feature_id)
    ]
    return hashlib.sha256(
        json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def directed_differentiation(
    target: int,
    state: dict[str, Feature],
) -> tuple[tuple[str, str, int] | None, int]:
    tested = 0
    for left_id, right_id in combinations(sorted(state), 2):
        tested += 1
        relation = fit_relation(
            target,
            state[left_id].semantics,
            state[right_id].semantics,
        )
        if relation is not None:
            return (left_id, right_id, relation), tested
    return None, tested


def blind_mediation(
    *,
    seed: str,
    episode_id: str,
    target: int,
    state: dict[str, Feature],
) -> tuple[tuple[str, str, int] | None, int]:
    candidates = []
    for left_id, right_id in combinations(sorted(state), 2):
        for table in range(16):
            candidates.append(
                (
                    digest(seed, episode_id, left_id, right_id, table),
                    left_id,
                    right_id,
                    table,
                )
            )
    candidates.sort()

    checked = 0
    for _, left_id, right_id, table in candidates[:BLIND_BUDGET]:
        checked += 1
        proposal = apply_table(
            table,
            state[left_id].semantics,
            state[right_id].semantics,
        )
        if proposal == target and observed_essential(
            target,
            state[left_id].semantics,
            state[right_id].semantics,
        ):
            return (left_id, right_id, table), checked

    return None, checked


def flags_for_arm(arm: str) -> tuple[bool, bool, bool]:
    if arm == "NONE":
        return False, False, False
    if arm in {"DMI_COLD", "ORACLE_STACK"}:
        return True, True, True
    return tuple(letter in arm for letter in "DMI")  # type: ignore[return-value]


def solve_episode(
    *,
    seed: str,
    episode: WorldEpisode,
    arm: str,
    state: dict[str, Feature],
) -> tuple[dict[str, object], dict[str, Feature]]:
    target = episode.target

    # Reuse exact active semantics before constructing anything new.
    for feature in state.values():
        if feature.semantics == target:
            return (
                {
                    "ok": True,
                    "route": "REUSE",
                    "selected": [feature.feature_id],
                    "distinction_tests": 0,
                    "verifier_candidate_checks": 0,
                    "installed": False,
                    "novel": False,
                    "dual_dependence": False,
                },
                state,
            )

    differentiate, mediate, integrate = flags_for_arm(arm)
    oracle = arm == "ORACLE_STACK"

    selected: tuple[str, str, int] | None = None
    distinction_tests = 0
    verifier_checks = 0

    if oracle:
        left_id, right_id = episode.parent_ids
        if left_id not in state or right_id not in state:
            return (
                {
                    "ok": False,
                    "route": "ORACLE_PARENT_MISSING",
                    "distinction_tests": 0,
                    "verifier_candidate_checks": 0,
                },
                state,
            )
        relation = fit_relation(
            target,
            state[left_id].semantics,
            state[right_id].semantics,
        )
        if relation is None:
            return (
                {
                    "ok": False,
                    "route": "ORACLE_PAIR_NOT_FUNCTIONAL",
                    "distinction_tests": 0,
                    "verifier_candidate_checks": 0,
                },
                state,
            )
        selected = (left_id, right_id, relation)
        verifier_checks = 1

    else:
        if not mediate:
            return (
                {
                    "ok": False,
                    "route": "NO_MEDIATOR",
                    "distinction_tests": 0,
                    "verifier_candidate_checks": 0,
                },
                state,
            )

        if differentiate:
            selected, distinction_tests = directed_differentiation(target, state)
            if selected is None:
                return (
                    {
                        "ok": False,
                        "route": "NO_SUFFICIENT_PAIR",
                        "distinction_tests": distinction_tests,
                        "verifier_candidate_checks": 0,
                    },
                    state,
                )
            # The compiled relation still crosses the external authority once.
            verifier_checks = 1
        else:
            selected, verifier_checks = blind_mediation(
                seed=seed,
                episode_id=episode.episode_id,
                target=target,
                state=state,
            )
            if selected is None:
                return (
                    {
                        "ok": False,
                        "route": "BLIND_BUDGET_EXHAUSTED",
                        "distinction_tests": 0,
                        "verifier_candidate_checks": verifier_checks,
                    },
                    state,
                )

    assert selected is not None
    left_id, right_id, relation = selected
    proposal = apply_table(
        relation,
        state[left_id].semantics,
        state[right_id].semantics,
    )

    if proposal != target:
        return (
            {
                "ok": False,
                "route": "VERIFIER_REFUTED",
                "distinction_tests": distinction_tests,
                "verifier_candidate_checks": verifier_checks,
            },
            state,
        )

    novel = all(f.semantics != proposal for f in state.values())
    dual = observed_essential(
        target,
        state[left_id].semantics,
        state[right_id].semantics,
    )

    installed = False
    next_state = state
    if integrate or oracle:
        next_state = copy.deepcopy(state)
        next_state[episode.episode_id] = Feature(
            feature_id=episode.episode_id,
            semantics=proposal,
            dependencies=(left_id, right_id),
            provenance=(
                f"{PRECOMMIT_COMMIT}:{seed}:{episode.episode_id}:"
                f"{left_id}:{right_id}:{relation}"
            ),
        )
        installed = True

    return (
        {
            "ok": True,
            "route": "VERIFIED_CHILD",
            "selected": [left_id, right_id, relation],
            "distinction_tests": distinction_tests,
            "verifier_candidate_checks": verifier_checks,
            "installed": installed,
            "novel": novel,
            "dual_dependence": dual,
        },
        next_state,
    )


def open_authority_control(state: dict[str, Feature]) -> dict[str, object]:
    before = state_digest(state)
    # An OPEN packet may contain positive observations but cannot close the
    # relation support. By constitutional rule it produces no promotion.
    after = state_digest(state)
    return {
        "route": "UNKNOWN",
        "state_before": before,
        "state_after": after,
        "mutations": 0 if before == after else 1,
    }


def run_arm(seed: str, world: list[WorldEpisode], arm: str) -> dict[str, object]:
    state = initial_state()
    open_control = open_authority_control(state)
    records = []
    snapshots: dict[int, dict[str, Feature]] = {}

    for episode in world:
        if arm == "DMI_COLD":
            state = initial_state()

        result, state = solve_episode(
            seed=seed,
            episode=episode,
            arm=arm,
            state=state,
        )
        result.update(
            {
                "generation": episode.generation,
                "episode_id": episode.episode_id,
                "expected_parents": list(episode.parent_ids),
                "uses_previous_child": (
                    episode.generation == 1
                    or (
                        bool(result.get("selected"))
                        and episode.parent_ids[0]
                        in result.get("selected", [])
                    )
                ),
            }
        )
        records.append(result)
        snapshots[episode.generation] = copy.deepcopy(state)

        if not result["ok"]:
            break

    return {
        "arm": arm,
        "open_control": open_control,
        "records": records,
        "depth": sum(1 for row in records if row["ok"]),
        "distinction_tests": sum(
            int(row.get("distinction_tests", 0)) for row in records
        ),
        "verifier_candidate_checks": sum(
            int(row.get("verifier_candidate_checks", 0))
            for row in records
        ),
        "installed_children": sum(
            int(bool(row.get("installed"))) for row in records
        ),
        "_state": state,
        "_snapshots": snapshots,
    }


def remove_dependency_cone(
    state: dict[str, Feature],
    root: str,
) -> tuple[dict[str, Feature], set[str]]:
    next_state = copy.deepcopy(state)
    removed: set[str] = set()
    frontier = {root}

    while frontier:
        current = frontier.pop()
        if current in removed:
            continue
        removed.add(current)
        for feature_id, feature in list(next_state.items()):
            if current in feature.dependencies:
                frontier.add(feature_id)

    for feature_id in removed:
        next_state.pop(feature_id, None)

    return next_state, removed


def causal_ablation(
    *,
    seed: str,
    world: list[WorldEpisode],
    full_run: dict[str, object],
) -> dict[str, object]:
    snapshots = full_run["_snapshots"]
    if 4 not in snapshots or 3 not in snapshots:
        return {"eligible": False, "pass": False}

    state_after_g4 = copy.deepcopy(snapshots[4])
    ablated, removed = remove_dependency_cone(state_after_g4, "G3")

    fail_result, _ = solve_episode(
        seed=seed,
        episode=world[3],
        arm="DMI",
        state=copy.deepcopy(ablated),
    )

    restored = copy.deepcopy(ablated)
    restored["G3"] = copy.deepcopy(snapshots[3]["G3"])
    restore_result, _ = solve_episode(
        seed=seed,
        episode=world[3],
        arm="DMI",
        state=restored,
    )

    passed = (
        removed == {"G3", "G4"}
        and not fail_result["ok"]
        and restore_result["ok"]
    )
    return {
        "eligible": True,
        "removed": sorted(removed),
        "without_g3": fail_result,
        "after_exact_g3_restore": restore_result,
        "pass": passed,
    }


def metamorphosis(
    *,
    seed: str,
    world: list[WorldEpisode],
    full_run: dict[str, object],
) -> dict[str, object]:
    snapshots = full_run["_snapshots"]
    if 6 not in snapshots:
        return {"eligible": False, "pass": False}

    replacement = build_replacement_world(seed, world)
    state, removed = remove_dependency_cone(
        copy.deepcopy(snapshots[6]),
        "G3",
    )

    preserved_ancestors = "G1" in state and "G2" in state
    descendants_removed = all(
        feature_id not in state
        for feature_id in ("G3", "G4", "G5", "G6")
    )

    records = []
    for episode in replacement:
        result, state = solve_episode(
            seed=f"{seed}:REPLACEMENT",
            episode=episode,
            arm="DMI",
            state=state,
        )
        records.append(result)
        if not result["ok"]:
            break

    passed = (
        removed == {"G3", "G4", "G5", "G6"}
        and preserved_ancestors
        and descendants_removed
        and len(records) == 4
        and all(row["ok"] for row in records)
    )
    return {
        "eligible": True,
        "old_g3_hidden_table": world[2].hidden_table,
        "new_g3_hidden_table": replacement[0].hidden_table,
        "removed": sorted(removed),
        "preserved_ancestors": preserved_ancestors,
        "descendants_removed": descendants_removed,
        "records": records,
        "pass": passed,
    }


def public_run(run: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in run.items()
        if not key.startswith("_")
    }


def evaluate_world(seed: str) -> dict[str, object]:
    world = build_world(seed)
    runs = {arm: run_arm(seed, world, arm) for arm in ARMS}
    full = runs["DMI"]

    ablation = causal_ablation(
        seed=seed,
        world=world,
        full_run=full,
    )
    change = metamorphosis(
        seed=seed,
        world=world,
        full_run=full,
    )

    world_record = [
        {
            "generation": episode.generation,
            "episode_id": episode.episode_id,
            "hidden_table": episode.hidden_table,
            "parent_ids": list(episode.parent_ids),
            "target_sha256": hashlib.sha256(
                episode.target.to_bytes(4, "little")
            ).hexdigest(),
            "minimum_sufficient_pairs": [
                [a, b, relation]
                for a, b, relation in episode.minimum_pairs
            ],
        }
        for episode in world
    ]

    return {
        "seed": seed,
        "world": world_record,
        "runs": {arm: public_run(run) for arm, run in runs.items()},
        "causal_ablation": ablation,
        "metamorphosis": change,
    }


def headline_gates(result: dict[str, object]) -> dict[str, bool]:
    runs = result["runs"]
    full = runs["DMI"]

    all_open_unknown = all(
        row["open_control"]["route"] == "UNKNOWN"
        and row["open_control"]["mutations"] == 0
        for row in runs.values()
    )

    full_records = full["records"]
    child_quality = (
        len(full_records) == 6
        and all(
            row["ok"]
            and row["route"] == "VERIFIED_CHILD"
            and row["novel"]
            and row["dual_dependence"]
            and row["installed"]
            for row in full_records
        )
    )
    recursive_parentage = (
        len(full_records) == 6
        and all(row["uses_previous_child"] for row in full_records[1:])
    )

    proper_subsets = ("NONE", "D", "M", "I", "DM", "DI", "MI")
    no_subset_matches = all(
        runs[arm]["depth"] < 6
        for arm in proper_subsets
    )

    h9 = (
        runs["MI"]["depth"] < full["depth"]
        or (
            runs["MI"]["depth"] == full["depth"]
            and runs["MI"]["verifier_candidate_checks"]
            > full["verifier_candidate_checks"]
        )
    )

    return {
        "H1_open_unknown_zero_mutation": all_open_unknown,
        "H2_dmi_g1_g6": full["depth"] == 6,
        "H3_children_novel_dual_verified_provenanced": child_quality,
        "H4_child_becomes_parent_g2_g6": recursive_parentage,
        "H5_g3_ablation_remove_restore": bool(
            result["causal_ablation"]["pass"]
        ),
        "H6_cold_cannot_full_lineage": runs["DMI_COLD"]["depth"] < 6,
        "H7_remove_i_reduces_reach": runs["DM"]["depth"] < full["depth"],
        "H8_remove_m_reduces_reach": runs["DI"]["depth"] < full["depth"],
        "H9_remove_d_cost_or_reach_penalty": h9,
        "H10_counterevidence_revokes_descendants_preserves_ancestors": (
            result["metamorphosis"]["eligible"]
            and result["metamorphosis"]["preserved_ancestors"]
            and result["metamorphosis"]["descendants_removed"]
        ),
        "H11_regenerate_g3r_g6r": bool(result["metamorphosis"]["pass"]),
        "H12_no_proper_subset_matches_full": no_subset_matches,
    }


def sweep_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    full_depth = sum(
        1 for row in rows if row["runs"]["DMI"]["depth"] == 6
    )
    cold_depth = sum(
        1 for row in rows if row["runs"]["DMI_COLD"]["depth"] == 6
    )
    metamorphosis = sum(
        1 for row in rows if row["metamorphosis"]["pass"]
    )
    ablation = sum(
        1 for row in rows if row["causal_ablation"]["pass"]
    )

    ablation_loss = {}
    for arm in ("DM", "DI", "MI"):
        ablation_loss[arm] = sum(
            1
            for row in rows
            if row["runs"][arm]["depth"] < row["runs"]["DMI"]["depth"]
        )

    arm_full_depth = {
        arm: sum(1 for row in rows if row["runs"][arm]["depth"] == 6)
        for arm in ARMS
    }

    strong = {
        "S1_dmi_full_depth_ge_95": full_depth >= 95,
        "S2_dmi_metamorphosis_ge_95": metamorphosis >= 95,
        "S3_cold_full_depth_le_5": cold_depth <= 5,
        "S4_dm_loss_ge_90": ablation_loss["DM"] >= 90,
        "S5_di_loss_ge_90": ablation_loss["DI"] >= 90,
        "S6_mi_loss_ge_90": ablation_loss["MI"] >= 90,
    }

    return {
        "worlds": len(rows),
        "dmi_full_depth": full_depth,
        "dmi_causal_ablation_pass": ablation,
        "dmi_metamorphosis_pass": metamorphosis,
        "dmi_cold_full_depth": cold_depth,
        "single_role_ablation_loss": ablation_loss,
        "full_depth_by_arm": arm_full_depth,
        "strong_criteria": strong,
        "strong_pass": all(strong.values()),
    }


def classify(
    headline: dict[str, object],
    gates: dict[str, bool],
    sweep: dict[str, object],
) -> str:
    if all(gates.values()) and sweep["strong_pass"]:
        return "PASS_TRIADIC_NUCLEUS_SIGNAL_V1"

    full = headline["runs"]["DMI"]
    developmental_headline = (
        gates["H1_open_unknown_zero_mutation"]
        and gates["H2_dmi_g1_g6"]
        and gates["H3_children_novel_dual_verified_provenanced"]
        and gates["H4_child_becomes_parent_g2_g6"]
        and gates["H5_g3_ablation_remove_restore"]
        and gates["H10_counterevidence_revokes_descendants_preserves_ancestors"]
        and gates["H11_regenerate_g3r_g6r"]
    )
    if developmental_headline:
        role_gates = (
            gates["H7_remove_i_reduces_reach"]
            and gates["H8_remove_m_reduces_reach"]
            and gates["H9_remove_d_cost_or_reach_penalty"]
            and gates["H12_no_proper_subset_matches_full"]
        )
        if not role_gates:
            return "REDUCED_NUCLEUS_SIGNAL_V1"
        return "PARTIAL_NUCLEUS_SIGNAL_V1"

    if full["depth"] > 0:
        return "PARTIAL_NUCLEUS_SIGNAL_V1"

    return "VALID_NEGATIVE_NUCLEUS_TOURNAMENT_V1"


def main() -> int:
    headline = evaluate_world(HEADLINE_SEED)
    gates = headline_gates(headline)

    sweep_rows = [
        evaluate_world(f"{SWEEP_PREFIX}:{index:03d}")
        for index in range(100)
    ]
    sweep = sweep_summary(sweep_rows)
    verdict = classify(headline, gates, sweep)

    result = {
        "protocol": PROTOCOL,
        "precommit_commit": PRECOMMIT_COMMIT,
        "headline_seed": HEADLINE_SEED,
        "roles": {
            "D": "differentiate minimum sufficient current distinctions",
            "M": "mediate by constructing the exact finite relation",
            "I": "integrate verified child into executable future state",
            "external_authority": (
                "shared exact verifier; OPEN evidence cannot promote"
            ),
        },
        "headline": headline,
        "headline_gates": gates,
        "sweep": sweep,
        "verdict": verdict,
        "claim_boundary": (
            "Bounded exact finite-world causal test on a supplied five-bit "
            "carrier and finite binary relation meta-language. A PASS is a "
            "triadic developmental-nucleus signal under this protocol, not "
            "evidence that three is metaphysically fundamental or that D/M/I "
            "is sufficient for unrestricted natural-world intelligence."
        ),
    }

    outdir = Path("results/nucleus_tournament_v1")
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )

    compact_sweep = [
        {
            "seed": row["seed"],
            "depths": {
                arm: row["runs"][arm]["depth"]
                for arm in ARMS
            },
            "dmi_ablation": row["causal_ablation"]["pass"],
            "dmi_metamorphosis": row["metamorphosis"]["pass"],
            "typed_costs": {
                "DMI": {
                    "distinction_tests": row["runs"]["DMI"][
                        "distinction_tests"
                    ],
                    "verifier_candidate_checks": row["runs"]["DMI"][
                        "verifier_candidate_checks"
                    ],
                },
                "MI": {
                    "distinction_tests": row["runs"]["MI"][
                        "distinction_tests"
                    ],
                    "verifier_candidate_checks": row["runs"]["MI"][
                        "verifier_candidate_checks"
                    ],
                },
            },
        }
        for row in sweep_rows
    ]
    (outdir / "sweep.json").write_text(
        json.dumps(compact_sweep, indent=2, sort_keys=True) + "\n"
    )

    print("=" * 88)
    print("NUCLEUS TOURNAMENT V1")
    print("=" * 88)
    for arm in ARMS:
        row = headline["runs"][arm]
        print(
            f"{arm:12s} depth={row['depth']} "
            f"D-tests={row['distinction_tests']} "
            f"V-checks={row['verifier_candidate_checks']}"
        )
    print("-" * 88)
    for gate, passed in gates.items():
        print(gate, "PASS" if passed else "FAIL")
    print("-" * 88)
    print(json.dumps(sweep, indent=2, sort_keys=True))
    print(verdict)

    return 0 if verdict == "PASS_TRIADIC_NUCLEUS_SIGNAL_V1" else 2


if __name__ == "__main__":
    raise SystemExit(main())
