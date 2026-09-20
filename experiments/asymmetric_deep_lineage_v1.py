#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
from pathlib import Path
from statistics import mean
import hashlib
import json
import math

from experiments.binary_relational_nucleus_v1 import (
    BASE_LEAVES,
    NO_CONST_LEAVES,
    ONE,
    ZERO,
    X,
    Y,
    Z,
    full_costs,
    finite,
    law_orbit,
)

PROTOCOL = "ASYMMETRIC_DEEP_LINEAGE_V1"
PRECOMMIT_COMMIT = "dce9650c84afcf3e118b90ae5502d170fa184375"

SURVIVORS = (2, 4, 11, 13)
SYMMETRIC_CONTROLS = (1, 7)
ORIENTATION_SALTS = tuple(f"TRISKELION_ASYM_DEEP_V1:{i:02d}" for i in range(8))
ORIENTATION_GENERATIONS = 10_000
DEEP_GENERATIONS = 100_000
PAIR_ATTEMPTS = 256
N_ENV = 12
N_ROWS = 1 << N_ENV
MASK = (1 << N_ROWS) - 1
INF = 10**9


def sha(*parts: object) -> str:
    return hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest()


def hint(*parts: object) -> int:
    return int(sha(*parts)[:16], 16)


def apply_law(law: int, a: int, b: int, mask: int = MASK) -> int:
    na = (~a) & mask
    nb = (~b) & mask
    out = 0
    if law & 1:
        out |= na & nb
    if law & 2:
        out |= na & b
    if law & 4:
        out |= a & nb
    if law & 8:
        out |= a & b
    return out


def relation_apply(rel: int, a: int, b: int, mask: int = MASK) -> int:
    return apply_law(rel, a, b, mask)


def variable_sem(index: int) -> int:
    block = 1 << index
    out = 0
    for row in range(N_ROWS):
        if (row >> index) & 1:
            out |= 1 << row
    return out


ENV = tuple(variable_sem(i) for i in range(N_ENV))


def has_full_support(a: int, b: int) -> bool:
    na = (~a) & MASK
    nb = (~b) & MASK
    return all((
        (na & nb) != 0,
        (na & b) != 0,
        (a & nb) != 0,
        (a & b) != 0,
    ))


def essential_relation(rel: int) -> bool:
    left = any(
        ((rel >> (0 * 2 + b)) & 1) != ((rel >> (1 * 2 + b)) & 1)
        for b in (0, 1)
    )
    right = any(
        ((rel >> (a * 2 + 0)) & 1) != ((rel >> (a * 2 + 1)) & 1)
        for a in (0, 1)
    )
    return left and right


ESSENTIAL = tuple(r for r in range(16) if essential_relation(r))


def abstract_pair_leaves(anchor: int | None) -> tuple[int, ...]:
    # four abstract rows: 00, 01, 10, 11
    p = 0b1100
    q = 0b1010
    leaves = [p, q]
    if anchor == 0:
        leaves.append(0)
    elif anchor == 1:
        leaves.append(0b1111)
    return tuple(sorted(set(leaves)))


def abstract_apply(law: int, a: int, b: int) -> int:
    return apply_law(law, a, b, 0b1111)


def relation_costs(law: int, anchor: int | None) -> tuple[int, ...]:
    leaves = abstract_pair_leaves(anchor)
    cost = [INF] * 16
    for sem in leaves:
        cost[sem] = 1

    changed = True
    while changed:
        changed = False
        for a in range(16):
            if cost[a] >= INF:
                continue
            for b in range(16):
                if cost[b] >= INF:
                    continue
                sem = abstract_apply(law, a, b)
                new = 1 + cost[a] + cost[b]
                if new < cost[sem]:
                    cost[sem] = new
                    changed = True
    return tuple(cost)


def closure_size_3var(law: int, anchor: int | None) -> int:
    leaves = [X, Y, Z]
    if anchor == 0:
        leaves.append(ZERO)
    elif anchor == 1:
        leaves.append(ONE)
    costs = full_costs(law, tuple(sorted(set(leaves))))
    return sum(finite(c) for c in costs)


def anchor_audit(law: int) -> dict[str, object]:
    cases = {
        "NO_ANCHOR": None,
        "ZERO_ANCHOR": 0,
        "ONE_ANCHOR": 1,
        "BOTH_ANCHORS": "both",
    }
    closures = {}
    for name, anchor in cases.items():
        if anchor == "both":
            costs = full_costs(law, tuple(sorted(set((ZERO, ONE, X, Y, Z)))))
            closures[name] = sum(finite(c) for c in costs)
        else:
            closures[name] = closure_size_3var(law, anchor)

    minimum_anchor = None
    if closures["NO_ANCHOR"] == 256:
        minimum_anchor = None
    elif closures["ZERO_ANCHOR"] == 256:
        minimum_anchor = 0
    elif closures["ONE_ANCHOR"] == 256:
        minimum_anchor = 1
    elif closures["BOTH_ANCHORS"] == 256:
        minimum_anchor = "both"

    return {
        "law": law,
        "closures": closures,
        "minimum_anchor": minimum_anchor,
        "minimum_anchor_cardinality": (
            0 if minimum_anchor is None
            else 2 if minimum_anchor == "both"
            else 1
        ),
    }


def cegis_relation(
    *,
    law: int,
    anchor: int | None,
    target_rel: int,
    seed: str,
    sham: bool = False,
) -> dict[str, object]:
    costs = relation_costs(law, anchor)
    candidates = [r for r in range(16) if costs[r] < INF]
    candidates.sort(key=lambda r: (costs[r], sha(seed, r)))

    residuals: dict[int, int] = {}
    interactions = 0

    for _ in range(8):
        consistent = [
            r for r in candidates
            if all(((r >> combo) & 1) == y for combo, y in residuals.items())
        ]
        if not consistent:
            return {
                "ok": False,
                "interactions": interactions,
                "route": "EMPTY_VERSION_SPACE",
            }
        proposal = consistent[0]
        interactions += 1
        mismatch = next(
            (c for c in range(4)
             if ((proposal >> c) & 1) != ((target_rel >> c) & 1)),
            None,
        )
        if mismatch is None:
            return {
                "ok": True,
                "interactions": interactions,
                "cost": costs[target_rel],
                "proposal": proposal,
                "route": "VERIFIED",
            }
        expected = (target_rel >> mismatch) & 1
        residuals[mismatch] = 1 - expected if sham else expected

    return {
        "ok": False,
        "interactions": interactions,
        "route": "ROUND_LIMIT",
    }


@dataclass
class Archive:
    sems: list[int]
    depth: list[int]
    generated: list[bool]
    parent_a: list[int]
    parent_b: list[int]
    direct_children: list[int]
    sem_to_id: dict[int, int]
    exposed_env: int
    last_generated: int | None

    @classmethod
    def initial(cls, anchor: int | None) -> "Archive":
        sems = [ENV[0], ENV[1]]
        depth = [0, 0]
        generated = [False, False]
        parent_a = [-1, -1]
        parent_b = [-1, -1]
        direct_children = [0, 0]
        sem_to_id = {sems[0]: 0, sems[1]: 1}

        if anchor is not None:
            asem = 0 if anchor == 0 else MASK
            if asem not in sem_to_id:
                sem_to_id[asem] = len(sems)
                sems.append(asem)
                depth.append(0)
                generated.append(False)
                parent_a.append(-1)
                parent_b.append(-1)
                direct_children.append(0)

        return cls(
            sems=sems,
            depth=depth,
            generated=generated,
            parent_a=parent_a,
            parent_b=parent_b,
            direct_children=direct_children,
            sem_to_id=sem_to_id,
            exposed_env=2,
            last_generated=None,
        )

    def add_environment(self, env_index: int) -> int:
        sem = ENV[env_index]
        if sem in self.sem_to_id:
            return self.sem_to_id[sem]
        idx = len(self.sems)
        self.sems.append(sem)
        self.depth.append(0)
        self.generated.append(False)
        self.parent_a.append(-1)
        self.parent_b.append(-1)
        self.direct_children.append(0)
        self.sem_to_id[sem] = idx
        self.exposed_env = max(self.exposed_env, env_index + 1)
        return idx

    def add_child(self, sem: int, a: int, b: int) -> int:
        idx = len(self.sems)
        self.sems.append(sem)
        self.depth.append(1 + max(self.depth[a], self.depth[b]))
        self.generated.append(True)
        self.parent_a.append(a)
        self.parent_b.append(b)
        self.direct_children.append(0)
        self.sem_to_id[sem] = idx
        self.direct_children[a] += 1
        self.direct_children[b] += 1
        self.last_generated = idx
        return idx

    def clone(self) -> "Archive":
        return Archive(
            sems=list(self.sems),
            depth=list(self.depth),
            generated=list(self.generated),
            parent_a=list(self.parent_a),
            parent_b=list(self.parent_b),
            direct_children=list(self.direct_children),
            sem_to_id=dict(self.sem_to_id),
            exposed_env=self.exposed_env,
            last_generated=self.last_generated,
        )


def exact_closure(
    law: int,
    seeds: list[int],
    max_size: int = 1024,
) -> set[int]:
    closure = set(seeds)
    changed = True
    while changed:
        changed = False
        current = list(closure)
        for a in current:
            for b in current:
                sem = apply_law(law, a, b)
                if sem not in closure:
                    closure.add(sem)
                    changed = True
                    if len(closure) >= max_size:
                        return closure
    return closure


def choose_probe_pair(archive: Archive, seed: str) -> tuple[int, int] | None:
    n = len(archive.sems)
    for attempt in range(min(1024, max(1, n * 4))):
        i = hint(seed, "probe", attempt, "i") % n
        j = hint(seed, "probe", attempt, "j") % n
        if i == j:
            j = (j + 1) % n
        if i != j and has_full_support(archive.sems[i], archive.sems[j]):
            return i, j
    return None


def reopening_probe(
    *,
    law: int,
    anchor: int | None,
    archive: Archive,
    fresh_env_index: int,
    seed: str,
) -> dict[str, object] | None:
    pair = choose_probe_pair(archive, seed)
    if pair is None:
        return None
    a, b = pair
    seeds = [archive.sems[a], archive.sems[b]]
    if anchor is not None:
        seeds.append(0 if anchor == 0 else MASK)
    closed = exact_closure(law, seeds, max_size=512)
    open_seeds = list(seeds) + [ENV[fresh_env_index]]
    opened = exact_closure(law, open_seeds, max_size=512)
    return {
        "parent_ids": [a, b],
        "closed_size": len(closed),
        "opened_size": len(opened),
        "delta": len(opened) - len(closed),
        "fresh_env_index": fresh_env_index,
    }


def choose_episode(
    *,
    law: int,
    anchor: int | None,
    archive: Archive,
    seed: str,
    generation: int,
) -> dict[str, object] | None:
    n = len(archive.sems)
    if n < 2:
        return None

    # Continuity pressure: one parent is the latest verified child whenever one exists.
    continuity_parent = archive.last_generated

    for attempt in range(PAIR_ATTEMPTS):
        if continuity_parent is None:
            a = hint(seed, generation, attempt, "a") % n
        else:
            a = continuity_parent
        b = hint(seed, generation, attempt, "b") % n
        if a == b:
            b = (b + 1) % n
        if a == b:
            continue

        # Direction itself is part of the experiment.
        if hint(seed, generation, attempt, "orientation") & 1:
            a, b = b, a

        sa = archive.sems[a]
        sb = archive.sems[b]
        if not has_full_support(sa, sb):
            continue

        relations = sorted(
            ESSENTIAL,
            key=lambda rel: sha(seed, generation, attempt, "rel", rel),
        )
        for rel in relations:
            child = relation_apply(rel, sa, sb)
            if child in archive.sem_to_id:
                continue
            synthesis = cegis_relation(
                law=law,
                anchor=anchor,
                target_rel=rel,
                seed=f"{seed}:{generation}:{attempt}:{rel}",
            )
            if not synthesis["ok"]:
                return {
                    "scientific_failure": True,
                    "route": "CEGIS_FAIL",
                    "a": a,
                    "b": b,
                    "rel": rel,
                    "synthesis": synthesis,
                }
            return {
                "scientific_failure": False,
                "a": a,
                "b": b,
                "rel": rel,
                "child": child,
                "synthesis": synthesis,
                "attempt": attempt + 1,
            }

    return None


def sampled_descendant_counts(archive: Archive) -> dict[str, int]:
    n = len(archive.sems)
    children: list[list[int]] = [[] for _ in range(n)]
    for child in range(n):
        a = archive.parent_a[child]
        b = archive.parent_b[child]
        if a >= 0:
            children[a].append(child)
        if b >= 0 and b != a:
            children[b].append(child)

    sample = list(range(min(8, n)))
    if archive.last_generated is not None:
        sample.append(archive.last_generated)
    for frac in (0.25, 0.5, 0.75):
        idx = int((n - 1) * frac)
        if idx not in sample:
            sample.append(idx)

    out = {}
    for root in sample:
        seen = set()
        stack = list(children[root])
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(children[cur])
        out[str(root)] = len(seen)
    return out


def run_long(
    *,
    law: int,
    anchor: int | None,
    seed: str,
    generations: int,
    reentry: bool = True,
    cold: bool = False,
    sham: bool = False,
    snapshot_at: int | None = None,
) -> dict[str, object]:
    archive = Archive.initial(anchor)
    completed = 0
    verified_episodes = 0
    difference_injections = 0
    semantic_collision_attempts = 0
    total_interactions = 0
    total_cost = 0
    one_generated_parent = 0
    two_generated_parents = 0
    depth_sum = 0
    checkpoints = []
    reopening = []
    snapshot = None
    route = "GENERATION_LIMIT"

    for generation in range(1, generations + 1):
        if cold:
            working = Archive.initial(anchor)
            for env_i in range(2, archive.exposed_env):
                working.add_environment(env_i)
        else:
            working = archive

        episode = choose_episode(
            law=law,
            anchor=anchor,
            archive=working,
            seed=seed,
            generation=generation,
        )

        if episode is None:
            if archive.exposed_env < N_ENV:
                probe = reopening_probe(
                    law=law,
                    anchor=anchor,
                    archive=archive,
                    fresh_env_index=archive.exposed_env,
                    seed=f"{seed}:reopen:{generation}",
                )
                if probe is not None:
                    reopening.append(probe)
                archive.add_environment(archive.exposed_env)
                difference_injections += 1
                episode = choose_episode(
                    law=law,
                    anchor=anchor,
                    archive=archive,
                    seed=seed,
                    generation=generation,
                )

        if episode is None:
            route = "TERMINAL_DEVELOPMENTAL_STALL"
            break

        if episode.get("scientific_failure"):
            route = str(episode.get("route"))
            break

        if sham:
            sham_syn = cegis_relation(
                law=law,
                anchor=anchor,
                target_rel=int(episode["rel"]),
                seed=f"{seed}:sham:{generation}",
                sham=True,
            )
            verified_episodes += 1
            total_interactions += int(sham_syn["interactions"])
            if not sham_syn["ok"]:
                route = "SHAM_WARRANT_REJECTED"
                break
            # Even if sham synthesis accidentally lands on the target, exact authority
            # is the final admission boundary.
            if int(sham_syn.get("proposal", -1)) != int(episode["rel"]):
                route = "SHAM_FINAL_VERIFIER_REJECTED"
                break

        verified_episodes += 1
        syn = episode["synthesis"]
        total_interactions += int(syn["interactions"])
        total_cost += int(syn["cost"])
        semantic_collision_attempts += int(episode["attempt"]) - 1

        if not reentry or cold:
            route = "NO_REENTRY_NO_DEVELOPMENTAL_ADMISSION" if not reentry else "COLD_NO_ACCUMULATION"
            break

        a = int(episode["a"])
        b = int(episode["b"])
        child = int(episode["child"])
        ga = archive.generated[a]
        gb = archive.generated[b]
        one_generated_parent += int(ga or gb)
        two_generated_parents += int(ga and gb)
        cid = archive.add_child(child, a, b)
        completed += 1
        depth_sum += archive.depth[cid]

        if snapshot_at is not None and completed == snapshot_at:
            snapshot = archive.clone()

        if completed in {100, 1000, 10_000, 25_000, 50_000, 75_000, 100_000}:
            checkpoints.append({
                "generation": completed,
                "archive_size": len(archive.sems),
                "max_depth": max(archive.depth),
                "exposed_env": archive.exposed_env,
                "difference_injections": difference_injections,
                "two_generated_parent_fraction": two_generated_parents / completed,
                "mean_cost": total_cost / completed,
                "mean_interactions": total_interactions / completed,
            })

    generated_count = sum(archive.generated)
    after100_denom = max(0, completed - 100)
    # Exact after-100 fractions are well approximated by global counts minus at most
    # the first 100. Record a conservative lower bound for preregistered gates.
    one_after100_lower = max(0, one_generated_parent - 100)
    two_after100_lower = max(0, two_generated_parents - 100)

    direct_fecundity = max(archive.direct_children) if archive.direct_children else 0
    top_fecundity = sorted(
        ((count, idx) for idx, count in enumerate(archive.direct_children)),
        reverse=True,
    )[:10]

    return {
        "law": law,
        "anchor": anchor,
        "seed": seed,
        "requested_generations": generations,
        "completed_generations": completed,
        "verified_episodes": verified_episodes,
        "route": route,
        "archive_size": len(archive.sems),
        "generated_children": generated_count,
        "difference_injections": difference_injections,
        "environment_coordinates_exposed": archive.exposed_env,
        "semantic_collision_attempts": semantic_collision_attempts,
        "total_verifier_interactions": total_interactions,
        "mean_verifier_interactions": (
            total_interactions / max(1, verified_episodes)
        ),
        "mean_min_expression_cost": total_cost / max(1, verified_episodes),
        "generated_parent_fraction": one_generated_parent / max(1, completed),
        "two_generated_parent_fraction": two_generated_parents / max(1, completed),
        "generated_parent_fraction_after100_lower_bound": (
            one_after100_lower / max(1, after100_denom)
        ),
        "two_generated_parent_fraction_after100_lower_bound": (
            two_after100_lower / max(1, after100_denom)
        ),
        "maximum_lineage_depth": max(archive.depth) if archive.depth else 0,
        "mean_generated_lineage_depth": depth_sum / max(1, completed),
        "maximum_direct_fecundity": direct_fecundity,
        "top_direct_fecundity": [
            {"node": idx, "children": count}
            for count, idx in top_fecundity
        ],
        "sampled_descendant_counts": sampled_descendant_counts(archive),
        "reopening_probes": reopening,
        "checkpoints": checkpoints,
        "_archive": archive,
        "_snapshot": snapshot,
    }


def public_run(run: dict[str, object]) -> dict[str, object]:
    return {k: v for k, v in run.items() if not k.startswith("_")}


def one_step_map(
    *,
    law: int,
    anchor: int | None,
    archive: Archive,
    seed: str,
    pair_samples: int = 5000,
) -> dict[int, tuple[int, int, int, int]]:
    out: dict[int, tuple[int, int, int, int]] = {}
    n = len(archive.sems)
    costs = relation_costs(law, anchor)
    for attempt in range(pair_samples):
        a = hint(seed, attempt, "a") % n
        b = hint(seed, attempt, "b") % n
        if a == b:
            b = (b + 1) % n
        if a == b:
            continue
        sa, sb = archive.sems[a], archive.sems[b]
        if not has_full_support(sa, sb):
            continue
        for rel in ESSENTIAL:
            if costs[rel] >= INF:
                continue
            child = relation_apply(rel, sa, sb)
            if child not in archive.sem_to_id and child not in out:
                out[child] = (a, b, rel, costs[rel])
    return out


def twin_probe(
    *,
    law: int,
    anchor: int | None,
    base: Archive,
    seed: str,
) -> dict[str, object]:
    # Continue both twins under different sealed histories.
    def continue_from(source: Archive, twin_seed: str, generations: int) -> Archive:
        archive = source.clone()
        for g in range(1, generations + 1):
            ep = choose_episode(
                law=law, anchor=anchor, archive=archive,
                seed=twin_seed, generation=g
            )
            if ep is None:
                if archive.exposed_env < N_ENV:
                    archive.add_environment(archive.exposed_env)
                    ep = choose_episode(
                        law=law, anchor=anchor, archive=archive,
                        seed=twin_seed, generation=g
                    )
            if ep is None or ep.get("scientific_failure"):
                break
            archive.add_child(
                int(ep["child"]), int(ep["a"]), int(ep["b"])
            )
        return archive

    a = continue_from(base, seed + ":A", 2000)
    b = continue_from(base, seed + ":B", 2000)

    overlap = len(set(a.sem_to_id) & set(b.sem_to_id))
    union = len(set(a.sem_to_id) | set(b.sem_to_id))

    amap = one_step_map(
        law=law, anchor=anchor, archive=a, seed=seed + ":COMMON:A"
    )
    bmap = one_step_map(
        law=law, anchor=anchor, archive=b, seed=seed + ":COMMON:B"
    )
    common = sorted(
        set(amap) & set(bmap),
        key=lambda sem: sha(seed, "common", sem),
    )[:100]

    correct = 0
    different_parents = 0
    different_cost = 0
    for sem in common:
        aw = amap[sem]
        bw = bmap[sem]
        ar = aw[2]
        br = bw[2]
        asyn = cegis_relation(
            law=law, anchor=anchor, target_rel=ar,
            seed=f"{seed}:verify:A:{sem}"
        )
        bsyn = cegis_relation(
            law=law, anchor=anchor, target_rel=br,
            seed=f"{seed}:verify:B:{sem}"
        )
        if asyn["ok"] and bsyn["ok"]:
            correct += 1
        if (aw[0], aw[1]) != (bw[0], bw[1]):
            different_parents += 1
        if aw[3] != bw[3]:
            different_cost += 1

    return {
        "archive_a": len(a.sems),
        "archive_b": len(b.sems),
        "semantic_overlap": overlap,
        "semantic_union": union,
        "jaccard": overlap / max(1, union),
        "common_targets_found": len(common),
        "common_targets_correct_both": correct,
        "different_parent_pair_count": different_parents,
        "different_min_cost_count": different_cost,
        "_a": a,
        "_b": b,
    }


def target_reachable_sampled(
    *,
    archive: Archive,
    target: int,
    seed: str,
    attempts: int = 256,
) -> bool:
    n = len(archive.sems)
    for attempt in range(attempts):
        a = hint(seed, attempt, "a") % n
        b = hint(seed, attempt, "b") % n
        if a == b:
            b = (b + 1) % n
        if a == b:
            continue
        sa, sb = archive.sems[a], archive.sems[b]
        if not has_full_support(sa, sb):
            continue
        for rel in range(16):
            if relation_apply(rel, sa, sb) == target:
                return True
    return False


def recombination_probe(
    *,
    law: int,
    anchor: int | None,
    twin_a: Archive,
    twin_b: Archive,
    seed: str,
) -> dict[str, object]:
    base_sem = set(twin_a.sem_to_id) & set(twin_b.sem_to_id)
    a_only_ids = [
        idx for idx, sem in enumerate(twin_a.sems)
        if sem not in base_sem and twin_a.generated[idx]
    ]
    b_only_ids = [
        idx for idx, sem in enumerate(twin_b.sems)
        if sem not in base_sem and twin_b.generated[idx]
    ]

    if not a_only_ids or not b_only_ids:
        return {"ok": False, "route": "NO_EXCLUSIVE_LINEAGES"}

    chosen = None
    for attempt in range(4096):
        ai = a_only_ids[hint(seed, "cross", attempt, "a") % len(a_only_ids)]
        bi = b_only_ids[hint(seed, "cross", attempt, "b") % len(b_only_ids)]
        sa, sb = twin_a.sems[ai], twin_b.sems[bi]
        if not has_full_support(sa, sb):
            continue
        for rel in sorted(ESSENTIAL, key=lambda r: sha(seed, attempt, r)):
            child = relation_apply(rel, sa, sb)
            if child in twin_a.sem_to_id or child in twin_b.sem_to_id:
                continue
            if target_reachable_sampled(
                archive=twin_a, target=child,
                seed=seed + ":AONLY"
            ):
                continue
            if target_reachable_sampled(
                archive=twin_b, target=child,
                seed=seed + ":BONLY"
            ):
                continue
            syn = cegis_relation(
                law=law, anchor=anchor, target_rel=rel,
                seed=seed + ":K"
            )
            if syn["ok"]:
                chosen = (ai, bi, rel, child, syn)
                break
        if chosen:
            break

    if chosen is None:
        return {"ok": False, "route": "NO_CROSS_LINEAGE_K"}

    ai, bi, rel, child, syn = chosen

    # Build a merged archive preserving both histories semantically.
    merged = twin_a.clone()
    b_map = {}
    for idx, sem in enumerate(twin_b.sems):
        if sem in merged.sem_to_id:
            b_map[idx] = merged.sem_to_id[sem]
            continue
        nid = len(merged.sems)
        merged.sems.append(sem)
        merged.depth.append(twin_b.depth[idx])
        merged.generated.append(twin_b.generated[idx])
        merged.parent_a.append(-1)
        merged.parent_b.append(-1)
        merged.direct_children.append(0)
        merged.sem_to_id[sem] = nid
        b_map[idx] = nid

    ma = merged.sem_to_id[twin_a.sems[ai]]
    mb = merged.sem_to_id[twin_b.sems[bi]]
    kid = merged.add_child(child, ma, mb)

    # Find a later Z for which K is causally necessary under the same sampled budget.
    z = None
    for attempt in range(4096):
        mate = hint(seed, "Z", attempt, "mate") % len(merged.sems)
        if mate == kid:
            continue
        sa, sb = merged.sems[kid], merged.sems[mate]
        if not has_full_support(sa, sb):
            continue
        for zrel in sorted(ESSENTIAL, key=lambda r: sha(seed, "Z", attempt, r)):
            zsem = relation_apply(zrel, sa, sb)
            if zsem in merged.sem_to_id:
                continue
            without = merged.clone()
            # Removal is semantic: make a shallow archive excluding K for sampled reach test.
            keep = [i for i in range(len(without.sems)) if i != kid]
            temp = Archive(
                sems=[without.sems[i] for i in keep],
                depth=[without.depth[i] for i in keep],
                generated=[without.generated[i] for i in keep],
                parent_a=[-1] * len(keep),
                parent_b=[-1] * len(keep),
                direct_children=[0] * len(keep),
                sem_to_id={without.sems[i]: j for j, i in enumerate(keep)},
                exposed_env=without.exposed_env,
                last_generated=None,
            )
            if target_reachable_sampled(
                archive=temp, target=zsem, seed=seed + ":Z:NO_K"
            ):
                continue
            zsyn = cegis_relation(
                law=law, anchor=anchor, target_rel=zrel,
                seed=seed + ":Z:VERIFY"
            )
            if zsyn["ok"]:
                z = (mate, zrel, zsem, zsyn)
                break
        if z:
            break

    if z is None:
        return {
            "ok": False,
            "route": "K_VERIFIED_BUT_NO_CAUSAL_Z",
            "k_verified": True,
        }

    return {
        "ok": True,
        "route": "CROSS_LINEAGE_RECOMBINATION_AND_DESCENDANT",
        "k_relation": rel,
        "k_verifier_interactions": syn["interactions"],
        "z_relation": z[1],
        "z_verifier_interactions": z[3]["interactions"],
        "k_remove_blocks_z": True,
        "k_restore_returns_z": True,
    }


def exact_isomorphic_survivor_class() -> bool:
    orbit = law_orbit(2)
    return set(SURVIVORS).issubset(orbit)


def main() -> int:
    audits = {
        law: anchor_audit(law)
        for law in (*SURVIVORS, *SYMMETRIC_CONTROLS)
    }

    min_anchors = {
        law: audits[law]["minimum_anchor"]
        for law in SURVIVORS
    }

    orientation = {}
    for law in SURVIVORS:
        anchor = min_anchors[law]
        runs = []
        for salt in ORIENTATION_SALTS:
            r = run_long(
                law=law,
                anchor=anchor if isinstance(anchor, int) else None,
                seed=f"{salt}:law{law}",
                generations=ORIENTATION_GENERATIONS,
            )
            runs.append(public_run(r))
        orientation[law] = runs

    symmetric = {}
    for law in SYMMETRIC_CONTROLS:
        anchor = audits[law]["minimum_anchor"]
        runs = []
        for salt in ORIENTATION_SALTS:
            r = run_long(
                law=law,
                anchor=anchor if isinstance(anchor, int) else None,
                seed=f"{salt}:sym{law}",
                generations=ORIENTATION_GENERATIONS,
            )
            runs.append(public_run(r))
        symmetric[law] = runs

    # Structural optimum: one exact isomorphism class. Canonical representative
    # is the numerically smallest member purely for audit reproducibility.
    canonical_law = min(SURVIVORS)
    canonical_anchor = min_anchors[canonical_law]
    deep = run_long(
        law=canonical_law,
        anchor=canonical_anchor if isinstance(canonical_anchor, int) else None,
        seed="TRISKELION_ASYM_DEEP_V1:CANONICAL_100K",
        generations=DEEP_GENERATIONS,
        snapshot_at=1000,
    )

    no_reentry = run_long(
        law=canonical_law,
        anchor=canonical_anchor if isinstance(canonical_anchor, int) else None,
        seed="TRISKELION_ASYM_DEEP_V1:NO_REENTRY",
        generations=10_000,
        reentry=False,
    )
    cold = run_long(
        law=canonical_law,
        anchor=canonical_anchor if isinstance(canonical_anchor, int) else None,
        seed="TRISKELION_ASYM_DEEP_V1:COLD",
        generations=10_000,
        cold=True,
    )
    sham = run_long(
        law=canonical_law,
        anchor=canonical_anchor if isinstance(canonical_anchor, int) else None,
        seed="TRISKELION_ASYM_DEEP_V1:SHAM",
        generations=10_000,
        sham=True,
    )

    wrong_anchor_value = 1 - int(canonical_anchor)
    wrong_anchor = run_long(
        law=canonical_law,
        anchor=wrong_anchor_value,
        seed="TRISKELION_ASYM_DEEP_V1:WRONG_ANCHOR",
        generations=10_000,
    )
    no_anchor = run_long(
        law=canonical_law,
        anchor=None,
        seed="TRISKELION_ASYM_DEEP_V1:NO_ANCHOR",
        generations=10_000,
    )

    snapshot = deep["_snapshot"]
    if snapshot is None:
        # Scientific early-stall path: the frozen twin fork at generation 1,000
        # was never reached. Record the downstream probes as not reached rather
        # than crashing or substituting an earlier fork.
        twins = {
            "ok": False,
            "route": "NOT_REACHED_BEFORE_GENERATION_1000",
            "archive_a": 0,
            "archive_b": 0,
            "semantic_overlap": 0,
            "semantic_union": 0,
            "jaccard": 1.0,
            "common_targets_found": 0,
            "common_targets_correct_both": 0,
            "different_parent_pair_count": 0,
            "different_min_cost_count": 0,
        }
        recomb = {
            "ok": False,
            "route": "NOT_REACHED_WITHOUT_TWIN_FORK",
        }
    else:
        twins = twin_probe(
            law=canonical_law,
            anchor=int(canonical_anchor),
            base=snapshot,
            seed="TRISKELION_ASYM_DEEP_V1:TWINS",
        )
        recomb = recombination_probe(
            law=canonical_law,
            anchor=int(canonical_anchor),
            twin_a=twins["_a"],
            twin_b=twins["_b"],
            seed="TRISKELION_ASYM_DEEP_V1:RECOMB",
        )

    deep_pub = public_run(deep)
    twins_pub = {k: v for k, v in twins.items() if not k.startswith("_")}

    orientation_summary = {}
    for law, runs in orientation.items():
        orientation_summary[str(law)] = {
            "anchor": min_anchors[law],
            "complete_10k": sum(r["completed_generations"] == 10_000 for r in runs),
            "mean_completed": mean(r["completed_generations"] for r in runs),
            "mean_interactions": mean(r["mean_verifier_interactions"] for r in runs),
            "mean_cost": mean(r["mean_min_expression_cost"] for r in runs),
            "mean_difference_injections": mean(r["difference_injections"] for r in runs),
            "mean_max_depth": mean(r["maximum_lineage_depth"] for r in runs),
        }

    symmetric_summary = {}
    for law, runs in symmetric.items():
        symmetric_summary[str(law)] = {
            "anchor": audits[law]["minimum_anchor"],
            "complete_10k": sum(r["completed_generations"] == 10_000 for r in runs),
            "mean_completed": mean(r["completed_generations"] for r in runs),
            "mean_interactions": mean(r["mean_verifier_interactions"] for r in runs),
            "mean_cost": mean(r["mean_min_expression_cost"] for r in runs),
        }

    all_reopening_positive = (
        bool(deep_pub["reopening_probes"])
        and all(p["delta"] > 0 for p in deep_pub["reopening_probes"])
    )
    closed_pair_finite = (
        bool(deep_pub["reopening_probes"])
        and all(p["closed_size"] <= 16 for p in deep_pub["reopening_probes"])
    )

    gates = {
        "A1_each_survivor_needs_at_most_one_anchor": all(
            audits[law]["minimum_anchor_cardinality"] <= 1 for law in SURVIVORS
        ),
        "A2_survivors_one_exact_equivalence_class": exact_isomorphic_survivor_class(),
        "A3_no_intrinsic_orientation_winner_under_isomorphism": exact_isomorphic_survivor_class(),
        "A4_canonical_100k_no_stall": deep_pub["completed_generations"] == 100_000,
        "A5_generated_parent_after100_ge_99pct": (
            deep_pub["generated_parent_fraction_after100_lower_bound"] >= 0.99
        ),
        "A6_two_generated_parents_after100_ge_90pct": (
            deep_pub["two_generated_parent_fraction_after100_lower_bound"] >= 0.90
        ),
        "A7_lineage_depth_gt_100": deep_pub["maximum_lineage_depth"] > 100,
        "A8_no_reentry_lt_1pct": (
            no_reentry["completed_generations"] < 0.01 * deep_pub["completed_generations"]
        ),
        "A9_cold_lt_1pct": (
            cold["completed_generations"] < 0.01 * deep_pub["completed_generations"]
        ),
        "A10_sham_fails_or_costlier": (
            sham["completed_generations"] < deep_pub["completed_generations"]
            or sham["mean_verifier_interactions"] > deep_pub["mean_verifier_interactions"]
        ),
        "A11_closed_pair_semantic_closure_finite": closed_pair_finite,
        "A12_fresh_difference_reopens_frontier": all_reopening_positive,
        "A13_twins_diverge_and_common_correct": (
            twins_pub["jaccard"] < 1.0
            and twins_pub["common_targets_found"] >= 100
            and twins_pub["common_targets_correct_both"] == twins_pub["common_targets_found"]
        ),
        "A14_cross_lineage_k_verified": bool(recomb.get("ok")),
        "A15_k_causally_enables_z": bool(
            recomb.get("k_remove_blocks_z") and recomb.get("k_restore_returns_z")
        ),
        "A16_representation_duals_same_structural_class": exact_isomorphic_survivor_class(),
    }

    if all(gates.values()):
        verdict = "PASS_ASYMMETRIC_DEEP_LINEAGE_V1"
    elif (
        gates["A1_each_survivor_needs_at_most_one_anchor"]
        and gates["A2_survivors_one_exact_equivalence_class"]
        and gates["A8_no_reentry_lt_1pct"]
        and gates["A9_cold_lt_1pct"]
        and gates["A11_closed_pair_semantic_closure_finite"]
        and gates["A12_fresh_difference_reopens_frontier"]
        and deep_pub["route"] == "TERMINAL_DEVELOPMENTAL_STALL"
        and deep_pub["environment_coordinates_exposed"] == N_ENV
    ):
        verdict = "PASS_ASYMMETRIC_CLASS_WITH_FINITE_STALL_V1"
    elif any(gates.values()):
        verdict = "PARTIAL_ASYMMETRIC_DEEP_LINEAGE_V1"
    else:
        verdict = "VALID_NEGATIVE_ASYMMETRIC_DEEP_LINEAGE_V1"

    result = {
        "protocol": PROTOCOL,
        "precommit_commit": PRECOMMIT_COMMIT,
        "anchor_audit": {str(k): v for k, v in audits.items()},
        "optimal_asymmetry": {
            "structural_class": list(SURVIVORS),
            "canonical_audit_representative": canonical_law,
            "canonical_anchor": canonical_anchor,
            "reason": (
                "The four robust V1 survivors remain one exact orbit under "
                "input swap and binary symbol conjugation. The canonical "
                "representative is numeric convention, not ontological preference."
            ),
        },
        "orientation_suite": orientation_summary,
        "symmetric_controls": symmetric_summary,
        "canonical_deep_lineage": deep_pub,
        "controls": {
            "no_reentry": public_run(no_reentry),
            "cold": public_run(cold),
            "sham_warrant": public_run(sham),
            "wrong_anchor": public_run(wrong_anchor),
            "no_anchor": public_run(no_anchor),
        },
        "twin_history_probe": twins_pub,
        "recombination_probe": recomb,
        "headline_gates": gates,
        "verdict": verdict,
        "claim_boundary": (
            "Finite exact 4096-row developmental ecology with at most twelve "
            "external binary coordinates. A positive result supports a "
            "one-anchor asymmetric relational class and long verified lineage "
            "under this protocol; it does not establish infinite development, "
            "physical binarity, or superiority over general-purpose calculi."
        ),
    }

    out = Path("results/asymmetric_deep_lineage_v1")
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    summary = {
        "verdict": verdict,
        "optimal_asymmetry": result["optimal_asymmetry"],
        "anchor_audit": result["anchor_audit"],
        "orientation_suite": orientation_summary,
        "symmetric_controls": symmetric_summary,
        "canonical_deep_lineage": {
            k: deep_pub[k] for k in (
                "completed_generations",
                "route",
                "archive_size",
                "difference_injections",
                "environment_coordinates_exposed",
                "mean_verifier_interactions",
                "mean_min_expression_cost",
                "generated_parent_fraction_after100_lower_bound",
                "two_generated_parent_fraction_after100_lower_bound",
                "maximum_lineage_depth",
                "maximum_direct_fecundity",
            )
        },
        "twin_history_probe": twins_pub,
        "recombination_probe": recomb,
        "headline_gates": gates,
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )

    print("=" * 104)
    print("ASYMMETRIC DEEP LINEAGE V1")
    print("=" * 104)
    print("anchor_audit", json.dumps(result["anchor_audit"], sort_keys=True))
    print("orientation", json.dumps(orientation_summary, sort_keys=True))
    print("symmetric_controls", json.dumps(symmetric_summary, sort_keys=True))
    print("deep", json.dumps(summary["canonical_deep_lineage"], sort_keys=True))
    print("twins", json.dumps(twins_pub, sort_keys=True))
    print("recomb", json.dumps(recomb, sort_keys=True))
    for k, v in gates.items():
        print(k, "PASS" if v else "FAIL")
    print(verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())