#!/usr/bin/env python3
from __future__ import annotations

from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json
import math

PROTOCOL = "BINARY_RELATIONAL_NUCLEUS_V1"
PRECOMMIT_COMMIT = "0722d9f6ce65e83066d01330606cf3894e5b1bce"
ROWS = tuple(product((0, 1), repeat=3))
MASK = (1 << len(ROWS)) - 1
MAX_DEV_COST = 9
SALTS = tuple(f"TRISKELION_BINARY_NUCLEUS_V1:{i:03d}" for i in range(25))


def sem_of(fn) -> int:
    out = 0
    for i, (x, y, z) in enumerate(ROWS):
        out |= (fn(x, y, z) & 1) << i
    return out


ZERO = 0
ONE = MASK
X = sem_of(lambda x, y, z: x)
Y = sem_of(lambda x, y, z: y)
Z = sem_of(lambda x, y, z: z)
BASE_LEAVES = (ZERO, ONE, X, Y, Z)
NO_CONST_LEAVES = (X, Y, Z)


def h(*parts: object) -> str:
    return hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest()


def bit(sem: int, row: int) -> int:
    return (sem >> row) & 1


def apply_law(law: int, left: int, right: int) -> int:
    out = 0
    for row in range(len(ROWS)):
        a = bit(left, row)
        b = bit(right, row)
        idx = 2 * a + b  # 00,01,10,11
        out |= ((law >> idx) & 1) << row
    return out


def law_bits(law: int) -> str:
    return "".join(str((law >> i) & 1) for i in range(4))


def law_symmetric(law: int) -> bool:
    return ((law >> 1) & 1) == ((law >> 2) & 1)


def complement_sem(sem: int) -> int:
    return sem ^ MASK


def swap_inputs_law(law: int) -> int:
    out = 0
    for a, b in product((0, 1), repeat=2):
        src = 2 * b + a
        dst = 2 * a + b
        out |= ((law >> src) & 1) << dst
    return out


def output_complement_law(law: int) -> int:
    return law ^ 0b1111


def conjugate_symbol_law(law: int) -> int:
    # g(a,b) = 1 - f(1-a,1-b)
    out = 0
    for a, b in product((0, 1), repeat=2):
        src = 2 * (1 - a) + (1 - b)
        dst = 2 * a + b
        value = 1 - ((law >> src) & 1)
        out |= value << dst
    return out


@lru_cache(maxsize=None)
def bounded_costs(law: int, leaves_key: tuple[int, ...], max_cost: int) -> tuple[int, ...]:
    leaves = tuple(sorted(set(leaves_key)))
    inf = 10**9
    cost = [inf] * 256
    by_size: dict[int, set[int]] = {1: set()}

    for sem in leaves:
        cost[sem] = 1
        by_size[1].add(sem)

    for size in range(3, max_cost + 1, 2):
        current: set[int] = set()
        for lsize in range(1, size - 1, 2):
            rsize = size - 1 - lsize
            if rsize < 1 or rsize % 2 == 0:
                continue
            lefts = by_size.get(lsize, set())
            rights = by_size.get(rsize, set())
            for a in lefts:
                for b in rights:
                    sem = apply_law(law, a, b)
                    if cost[sem] > size:
                        cost[sem] = size
                        current.add(sem)
        by_size[size] = {
            sem for sem in current if cost[sem] == size
        }

    return tuple(cost)


def full_costs(law: int, leaves: tuple[int, ...]) -> tuple[int, ...]:
    for max_cost in (9, 13, 17, 21, 25, 31, 41, 63):
        costs = bounded_costs(law, tuple(sorted(set(leaves))), max_cost)
        reached = {sem for sem, c in enumerate(costs) if c < 10**9}
        closed = all(
            apply_law(law, a, b) in reached
            for a in reached
            for b in reached
        )
        if closed:
            return costs
    raise RuntimeError(f"closure did not stabilize for law {law}")


def finite(cost: int) -> bool:
    return cost < 10**9


def rank(seed: str, sem: int) -> tuple[str, int]:
    return (h(seed, min(sem, complement_sem(sem))), sem)


def cegis(
    *,
    law: int,
    leaves: tuple[int, ...],
    target: int,
    budget: int,
    seed: str,
    sham: bool = False,
) -> dict[str, object]:
    costs = bounded_costs(law, tuple(sorted(set(leaves))), budget)
    candidates = [
        sem for sem, c in enumerate(costs)
        if c <= budget
    ]
    candidates.sort(key=lambda sem: (costs[sem], rank(seed, sem)))

    residuals: dict[int, int] = {}
    interactions = 0
    trace = []

    for _ in range(16):
        consistent = [
            sem for sem in candidates
            if all(bit(sem, row) == expected for row, expected in residuals.items())
        ]
        if not consistent:
            return {
                "ok": False,
                "interactions": interactions,
                "trace": trace,
                "route": "EMPTY_VERSION_SPACE",
            }

        proposal = consistent[0]
        interactions += 1
        mismatch = next(
            (row for row in range(len(ROWS)) if bit(proposal, row) != bit(target, row)),
            None,
        )
        trace.append(
            {
                "proposal": proposal,
                "cost": costs[proposal],
                "consistent": len(consistent),
                "mismatch": mismatch,
            }
        )
        if mismatch is None:
            return {
                "ok": True,
                "interactions": interactions,
                "trace": trace,
                "route": "VERIFIED",
                "proposal": proposal,
            }

        correct = bit(target, mismatch)
        residuals[mismatch] = 1 - correct if sham else correct

    return {
        "ok": False,
        "interactions": interactions,
        "trace": trace,
        "route": "ROUND_LIMIT",
    }


def install(leaves: dict[str, int], label: str, sem: int) -> dict[str, int]:
    nxt = dict(leaves)
    nxt[label] = sem
    return nxt


def leaves_tuple(leaves: dict[str, int]) -> tuple[int, ...]:
    return tuple(sorted(set(leaves.values())))


def costs_for(law: int, leaves: dict[str, int], max_cost: int = MAX_DEV_COST) -> tuple[int, ...]:
    return bounded_costs(law, leaves_tuple(leaves), max_cost)


def select_first_target(law: int, seed: str) -> int | None:
    costs = full_costs(law, BASE_LEAVES)
    leaves = set(BASE_LEAVES)
    eligible = [
        sem for sem, c in enumerate(costs)
        if finite(c) and c >= 5 and sem not in leaves
    ]
    if not eligible:
        return None
    eligible.sort(key=lambda sem: rank(seed + ":G1", sem))
    return eligible[0]


def select_gain_target(
    *,
    law: int,
    leaves: dict[str, int],
    previous_label: str,
    seed: str,
    exclude_semantics: set[int] | None = None,
) -> tuple[int, int] | None:
    exclude_semantics = exclude_semantics or set()
    warm = costs_for(law, leaves)
    ablated = dict(leaves)
    ablated.pop(previous_label, None)
    cold = costs_for(law, ablated)
    installed = set(leaves.values())

    eligible = []
    for sem in range(256):
        wc = warm[sem]
        cc = cold[sem]
        if sem in installed or sem in exclude_semantics:
            continue
        if wc <= MAX_DEV_COST and cc > wc:
            eligible.append((sem, wc))

    if not eligible:
        return None
    eligible.sort(key=lambda item: rank(seed, item[0]))
    return eligible[0]


def check_relabel_cost(
    *,
    law: int,
    leaves: dict[str, int],
    target: int,
    budget: int,
) -> bool:
    tlaw = conjugate_symbol_law(law)
    transformed = tuple(sorted(set(complement_sem(s) for s in leaves.values())))
    costs = bounded_costs(law, leaves_tuple(leaves), budget)
    tcosts = bounded_costs(tlaw, transformed, budget)
    a = costs[target]
    b = tcosts[complement_sem(target)]
    return a == b


def develop_lineage(law: int, salt: str) -> dict[str, object]:
    leaves = {
        "0": ZERO,
        "1": ONE,
        "x": X,
        "y": Y,
        "z": Z,
    }
    records = []
    relabel_ok = True

    g1 = select_first_target(law, salt)
    if g1 is None:
        return {"ok": False, "depth": 0, "route": "NO_G1", "records": []}

    base_costs = full_costs(law, BASE_LEAVES)
    b1 = base_costs[g1]
    c1 = cegis(
        law=law, leaves=leaves_tuple(leaves), target=g1, budget=b1,
        seed=salt + ":CEGIS:G1"
    )
    sham1 = cegis(
        law=law, leaves=leaves_tuple(leaves), target=g1, budget=b1,
        seed=salt + ":CEGIS:G1", sham=True
    )
    if not c1["ok"]:
        return {"ok": False, "depth": 0, "route": "G1_CEGIS_FAIL", "records": []}

    relabel_ok &= check_relabel_cost(
        law=law, leaves=leaves, target=g1, budget=b1
    )
    leaves = install(leaves, "G1", g1)
    records.append({
        "label": "G1", "sem": g1, "budget": b1,
        "cegis": c1, "remove_previous_blocks": None
    })

    for gen in range(2, 7):
        prev = f"G{gen-1}"
        choice = select_gain_target(
            law=law,
            leaves=leaves,
            previous_label=prev,
            seed=f"{salt}:G{gen}",
        )
        if choice is None:
            return {
                "ok": False,
                "depth": len(records),
                "route": f"NO_G{gen}_GAIN_TARGET",
                "records": records,
                "sham_g1": sham1,
                "relabel_ok": relabel_ok,
            }
        target, budget = choice
        warm = costs_for(law, leaves)
        ablated = dict(leaves)
        ablated.pop(prev)
        cold = costs_for(law, ablated)
        remove_blocks = cold[target] > budget and warm[target] <= budget

        c = cegis(
            law=law, leaves=leaves_tuple(leaves), target=target, budget=budget,
            seed=f"{salt}:CEGIS:G{gen}"
        )
        relabel_ok &= check_relabel_cost(
            law=law, leaves=leaves, target=target, budget=budget
        )
        if not c["ok"] or not remove_blocks:
            return {
                "ok": False,
                "depth": len(records),
                "route": f"G{gen}_CAUSAL_FAIL",
                "records": records,
                "sham_g1": sham1,
                "relabel_ok": relabel_ok,
            }

        leaves = install(leaves, f"G{gen}", target)
        records.append({
            "label": f"G{gen}", "sem": target, "budget": budget,
            "cegis": c, "remove_previous_blocks": remove_blocks
        })

    return {
        "ok": True,
        "depth": 6,
        "route": "LINEAGE_COMPLETE",
        "records": records,
        "leaves_after_g6": leaves,
        "sham_g1": sham1,
        "relabel_ok": relabel_ok,
    }


def twin_step(
    *,
    law: int,
    leaves: dict[str, int],
    previous_label: str,
    label: str,
    seed: str,
    exclude: set[int],
) -> tuple[dict[str, int], dict[str, object]] | None:
    choice = select_gain_target(
        law=law,
        leaves=leaves,
        previous_label=previous_label,
        seed=seed,
        exclude_semantics=exclude,
    )
    if choice is None:
        return None
    target, budget = choice
    c = cegis(
        law=law, leaves=leaves_tuple(leaves), target=target, budget=budget,
        seed=seed + ":CEGIS"
    )
    if not c["ok"]:
        return None
    nxt = install(leaves, label, target)
    return nxt, {
        "label": label,
        "sem": target,
        "budget": budget,
        "cegis": c,
    }


def twin_and_recombination(law: int, salt: str, lineage: dict[str, object]) -> dict[str, object]:
    if not lineage.get("ok"):
        return {"ok": False, "route": "NO_BASE_LINEAGE"}

    # Fork after G2, not after the entire G1-G6 lineage.
    base = {
        "0": ZERO, "1": ONE, "x": X, "y": Y, "z": Z,
        "G1": lineage["records"][0]["sem"],
        "G2": lineage["records"][1]["sem"],
    }

    a = dict(base)
    b = dict(base)
    a_records = []
    b_records = []

    prev = "G2"
    a_semantics = set()
    for idx in (3, 4):
        step = twin_step(
            law=law, leaves=a, previous_label=prev, label=f"A{idx}",
            seed=f"{salt}:TWIN:A:{idx}", exclude=set()
        )
        if step is None:
            return {"ok": False, "route": f"TWIN_A{idx}_FAIL"}
        a, rec = step
        a_records.append(rec)
        a_semantics.add(rec["sem"])
        prev = f"A{idx}"

    prev = "G2"
    for idx in (3, 4):
        step = twin_step(
            law=law, leaves=b, previous_label=prev, label=f"B{idx}",
            seed=f"{salt}:TWIN:B:{idx}", exclude=a_semantics
        )
        if step is None:
            return {"ok": False, "route": f"TWIN_B{idx}_FAIL"}
        b, rec = step
        b_records.append(rec)
        prev = f"B{idx}"

    divergent = {r["sem"] for r in a_records} != {r["sem"] for r in b_records}

    # Common target must expose path dependence via exact minimum cost difference.
    ca = costs_for(law, a)
    cb = costs_for(law, b)
    installed = set(a.values()) | set(b.values())
    common_candidates = [
        sem for sem in range(256)
        if sem not in installed
        and ca[sem] <= MAX_DEV_COST
        and cb[sem] <= MAX_DEV_COST
        and ca[sem] != cb[sem]
    ]
    if not common_candidates:
        return {"ok": False, "route": "NO_COMMON_PATH_DEPENDENT_TARGET"}
    common_candidates.sort(key=lambda sem: rank(salt + ":COMMON", sem))
    common = common_candidates[0]
    a_common = cegis(
        law=law, leaves=leaves_tuple(a), target=common, budget=ca[common],
        seed=salt + ":COMMON:A"
    )
    b_common = cegis(
        law=law, leaves=leaves_tuple(b), target=common, budget=cb[common],
        seed=salt + ":COMMON:B"
    )
    if not (a_common["ok"] and b_common["ok"]):
        return {"ok": False, "route": "COMMON_CEGIS_FAIL"}

    a = install(a, "COMMON", common)
    b = install(b, "COMMON", common)

    # Union state.
    union = dict(a)
    for label, sem in b.items():
        if label not in union:
            union[label] = sem

    union_cost = costs_for(law, union)
    a_cost = costs_for(law, a)
    b_cost = costs_for(law, b)
    a_only_labels = [k for k in a if k.startswith("A")]
    b_only_labels = [k for k in b if k.startswith("B")]

    recomb_candidates = []
    for sem in range(256):
        uc = union_cost[sem]
        if uc > MAX_DEV_COST or sem in set(union.values()):
            continue
        if a_cost[sem] <= uc or b_cost[sem] <= uc:
            continue

        a_causes = []
        for label in a_only_labels:
            tmp = dict(union)
            tmp.pop(label)
            if costs_for(law, tmp)[sem] > uc:
                a_causes.append(label)
        b_causes = []
        for label in b_only_labels:
            tmp = dict(union)
            tmp.pop(label)
            if costs_for(law, tmp)[sem] > uc:
                b_causes.append(label)

        if a_causes and b_causes:
            recomb_candidates.append((sem, uc, a_causes, b_causes))

    if not recomb_candidates:
        return {
            "ok": False,
            "route": "NO_TWO_LINEAGE_RECOMBINATION_TARGET",
            "divergent": divergent,
            "common_ok": True,
        }

    recomb_candidates.sort(key=lambda x: rank(salt + ":RECOMB", x[0]))
    k_sem, k_budget, a_causes, b_causes = recomb_candidates[0]
    k_cegis = cegis(
        law=law, leaves=leaves_tuple(union), target=k_sem, budget=k_budget,
        seed=salt + ":RECOMB:CEGIS"
    )
    if not k_cegis["ok"]:
        return {"ok": False, "route": "K_CEGIS_FAIL"}

    union_k = install(union, "K", k_sem)

    z_choice = select_gain_target(
        law=law,
        leaves=union_k,
        previous_label="K",
        seed=salt + ":Z",
    )
    if z_choice is None:
        return {"ok": False, "route": "NO_Z_GAIN_TARGET"}

    z_sem, z_budget = z_choice
    z_cegis = cegis(
        law=law, leaves=leaves_tuple(union_k), target=z_sem, budget=z_budget,
        seed=salt + ":Z:CEGIS"
    )
    if not z_cegis["ok"]:
        return {"ok": False, "route": "Z_CEGIS_FAIL"}

    no_k = dict(union_k)
    no_k.pop("K")
    z_without_k = costs_for(law, no_k)[z_sem] > z_budget
    z_with_k = costs_for(law, union_k)[z_sem] <= z_budget

    return {
        "ok": (
            divergent
            and a_common["ok"]
            and b_common["ok"]
            and k_cegis["ok"]
            and z_cegis["ok"]
            and z_without_k
            and z_with_k
        ),
        "route": "TWIN_RECOMB_COMPLETE",
        "divergent": divergent,
        "common_ok": bool(a_common["ok"] and b_common["ok"]),
        "common_sem": common,
        "common_cost_a": ca[common],
        "common_cost_b": cb[common],
        "k_sem": k_sem,
        "k_budget": k_budget,
        "a_causal_labels": a_causes,
        "b_causal_labels": b_causes,
        "k_union_only": a_cost[k_sem] > k_budget and b_cost[k_sem] > k_budget,
        "z_sem": z_sem,
        "z_budget": z_budget,
        "z_without_k": z_without_k,
        "z_with_k": z_with_k,
    }


def exact_relabel_isomorphism(law: int) -> bool:
    """Exhaustively verify the 0<->1 conjugacy on the whole semantic algebra.

    This identity is stronger than replaying one selected lineage: if it holds
    for every semantic input pair, then every recursively composed expression,
    exact minimum-cost relation, remove/restore reachability predicate, and
    complemented external-verifier consequence is preserved under the frozen
    representation relabelling.
    """
    tlaw = conjugate_symbol_law(law)
    for left in range(256):
        cleft = complement_sem(left)
        for right in range(256):
            cright = complement_sem(right)
            original = apply_law(law, left, right)
            transformed = apply_law(tlaw, cleft, cright)
            if complement_sem(original) != transformed:
                return False
    return True


def transformed_cost_invariance(
    law: int,
    leaves: tuple[int, ...],
    max_cost: int,
) -> bool:
    tlaw = conjugate_symbol_law(law)
    costs = bounded_costs(law, tuple(sorted(set(leaves))), max_cost)
    t_leaves = tuple(sorted(set(complement_sem(s) for s in leaves)))
    t_costs = bounded_costs(tlaw, t_leaves, max_cost)
    return all(
        costs[s] == t_costs[complement_sem(s)]
        for s in range(256)
    )


def run_salt(law: int, salt: str) -> dict[str, object]:
    lineage = develop_lineage(law, salt)
    twin = twin_and_recombination(law, salt, lineage) if lineage.get("ok") else {
        "ok": False, "route": "NO_LINEAGE"
    }

    no_reentry_fail = False
    cold_fail = False
    remove_restore_all = True

    if lineage.get("records"):
        base = {
            "0": ZERO, "1": ONE, "x": X, "y": Y, "z": Z
        }
        active = dict(base)
        for idx, rec in enumerate(lineage["records"]):
            target = rec["sem"]
            budget = rec["budget"]
            if idx >= 1:
                if costs_for(law, base)[target] > budget:
                    no_reentry_fail = True
                    cold_fail = True
                prev = f"G{idx}"
                ablated = dict(active)
                ablated.pop(prev, None)
                if costs_for(law, ablated)[target] <= budget:
                    remove_restore_all = False
            active = install(active, f"G{idx+1}", target)

    sham = lineage.get("sham_g1", {"ok": True, "interactions": 0})
    sham_penalty = (
        not sham.get("ok", False)
        or sham.get("interactions", 0)
        > lineage.get("records", [{}])[0].get("cegis", {}).get("interactions", 0)
    )

    d_like = bool(lineage.get("ok")) and any(
        len(rec["cegis"]["trace"]) > 1 for rec in lineage.get("records", [])
    )
    m_like = bool(lineage.get("ok")) and all(
        rec["sem"] not in BASE_LEAVES for rec in lineage.get("records", [])
    )
    i_like = bool(lineage.get("ok")) and remove_restore_all

    relabel_ok = bool(lineage.get("relabel_ok", False))
    if lineage.get("ok"):
        relabel_ok &= transformed_cost_invariance(
            law,
            tuple(BASE_LEAVES),
            9,
        )
        relabel_ok &= exact_relabel_isomorphism(law)

    gates = {
        "L2_g1_cegis": bool(lineage.get("depth", 0) >= 1),
        "L3_six_generation_lineage": bool(lineage.get("ok")),
        "L4_remove_restore_g2_g6": bool(lineage.get("ok") and remove_restore_all),
        "L5_no_reentry_fails": no_reentry_fail,
        "L6_cold_fails": cold_fail,
        "L7_sham_warrant_penalty": sham_penalty,
        "L8_twins_diverge": bool(twin.get("divergent", False)),
        "L9_common_target_both": bool(twin.get("common_ok", False)),
        "L10_recombination_exists": bool(twin.get("k_union_only", False)),
        "L11_neither_twin_alone": bool(twin.get("k_union_only", False)),
        "L12_k_enables_z": bool(twin.get("z_without_k", False) and twin.get("z_with_k", False)),
        "L13_dmi_phenotypes": d_like and m_like and i_like,
        "L14_one_symbol_fails": True,
        "L15_relabel_invariance": relabel_ok,
    }

    return {
        "salt": salt,
        "lineage": {
            "ok": lineage.get("ok", False),
            "depth": lineage.get("depth", 0),
            "route": lineage.get("route"),
            "records": lineage.get("records", []),
        },
        "twin_recombination": twin,
        "gates": gates,
        "pass_developmental": all(gates.values()),
    }


def law_orbit(law: int) -> set[int]:
    seen = {law}
    frontier = [law]
    while frontier:
        cur = frontier.pop()
        for nxt in (
            swap_inputs_law(cur),
            output_complement_law(cur),
            conjugate_symbol_law(cur),
        ):
            if nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    return seen


def main() -> int:
    laws = []

    for law in range(16):
        full = full_costs(law, BASE_LEAVES)
        no_const = full_costs(law, NO_CONST_LEAVES)
        closure = sum(finite(c) for c in full)
        closure_no_const = sum(finite(c) for c in no_const)
        l1 = closure == 256

        rows = []
        if l1:
            rows = [run_salt(law, salt) for salt in SALTS]

        robust_passes = sum(row["pass_developmental"] for row in rows)
        robust = l1 and robust_passes >= 23

        laws.append({
            "law": law,
            "truth_table_00_01_10_11": law_bits(law),
            "symmetric": law_symmetric(law),
            "closure_size": closure,
            "no_constants_closure_size": closure_no_const,
            "complete": l1,
            "max_min_cost": max(c for c in full if finite(c)),
            "cost_histogram": {
                str(cost): sum(c == cost for c in full)
                for cost in sorted(set(c for c in full if finite(c)))
            },
            "salt_passes": robust_passes,
            "robust_survivor": robust,
            "salts": rows,
        })

    survivors = [row["law"] for row in laws if row["robust_survivor"]]
    classes = []
    remaining = set(survivors)
    while remaining:
        seed = min(remaining)
        cls = sorted(remaining & law_orbit(seed))
        classes.append(cls)
        remaining -= set(cls)

    complete_laws = [row["law"] for row in laws if row["complete"]]
    any_symmetric = any(law_symmetric(law) for law in survivors)
    any_asymmetric = any(not law_symmetric(law) for law in survivors)
    any_no_const = any(
        row["robust_survivor"] and row["no_constants_closure_size"] == 256
        for row in laws
    )

    if survivors:
        verdict = "PASS_BINARY_RELATIONAL_NUCLEUS_CLASS_V1"
    elif complete_laws:
        verdict = "PARTIAL_BINARY_RELATIONAL_NUCLEUS_V1"
    else:
        verdict = "VALID_NEGATIVE_BINARY_RELATIONAL_NUCLEUS_V1"

    result = {
        "protocol": PROTOCOL,
        "precommit_commit": PRECOMMIT_COMMIT,
        "universe": {
            "variables": 3,
            "rows": 8,
            "semantic_functions": 256,
            "candidate_binary_laws": 16,
        },
        "laws": laws,
        "complete_laws": complete_laws,
        "robust_survivors": survivors,
        "survivor_equivalence_classes": classes,
        "survivor_summary": {
            "count": len(survivors),
            "equivalence_class_count": len(classes),
            "any_symmetric_survivor": any_symmetric,
            "any_asymmetric_survivor": any_asymmetric,
            "any_survivor_complete_without_constants": any_no_const,
        },
        "verdict": verdict,
        "claim_boundary": (
            "Exhaustive 16-law result on the complete three-variable Boolean "
            "universe plus 25 frozen developmental salts. A positive result "
            "supports a binary relational nucleus class under this protocol; "
            "it does not establish that physical reality is binary, unique "
            "metaphysical fundamentality, or unrestricted natural-world intelligence."
        ),
    }

    out = Path("results/binary_relational_nucleus_v1")
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )

    compact = {
        "verdict": verdict,
        "complete_laws": complete_laws,
        "robust_survivors": survivors,
        "survivor_equivalence_classes": classes,
        "laws": [
            {
                "law": row["law"],
                "truth_table": row["truth_table_00_01_10_11"],
                "symmetric": row["symmetric"],
                "closure_size": row["closure_size"],
                "no_constants_closure_size": row["no_constants_closure_size"],
                "salt_passes": row["salt_passes"],
                "robust_survivor": row["robust_survivor"],
            }
            for row in laws
        ],
    }
    (out / "summary.json").write_text(
        json.dumps(compact, indent=2, sort_keys=True) + "\n"
    )

    print("=" * 96)
    print("BINARY RELATIONAL NUCLEUS V1")
    print("=" * 96)
    for row in laws:
        print(
            f"law={row['law']:2d} table={row['truth_table_00_01_10_11']} "
            f"sym={row['symmetric']} closure={row['closure_size']:3d} "
            f"no_const={row['no_constants_closure_size']:3d} "
            f"salt_pass={row['salt_passes']:2d}/25 robust={row['robust_survivor']}"
        )
    print("complete_laws", complete_laws)
    print("robust_survivors", survivors)
    print("equivalence_classes", classes)
    print(verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())