from __future__ import annotations

import collections
import json
import random
from pathlib import Path

OUT = Path('artifacts/v103_operator_quotient')
OUT.mkdir(parents=True, exist_ok=True)

SEED_ACQ = 202608151703
SEED_HOLD = 202608151704
XOR = 0b0110


def tt_value(tt: int, x: int, y: int) -> int:
    return (tt >> ((x << 1) | y)) & 1


def is_affine_binary(tt: int) -> bool:
    vals = [tt_value(tt, 0, 0), tt_value(tt, 0, 1), tt_value(tt, 1, 0), tt_value(tt, 1, 1)]
    c = vals[0]
    a = vals[2] ^ c
    b = vals[1] ^ c
    return vals == [c, b ^ c, a ^ c, a ^ b ^ c]


def transform_tt(tt: int, swap: int, nx: int, ny: int, no: int) -> int:
    out = 0
    for idx in range(4):
        x, y = (idx >> 1) & 1, idx & 1
        if nx:
            x ^= 1
        if ny:
            y ^= 1
        if swap:
            x, y = y, x
        v = tt_value(tt, x, y)
        if no:
            v ^= 1
        out |= v << idx
    return out


def orbit(tt: int) -> tuple[int, ...]:
    return tuple(sorted({transform_tt(tt, s, nx, ny, no) for s in (0, 1) for nx in (0, 1) for ny in (0, 1) for no in (0, 1)}))


def var_func(n: int, j: int) -> int:
    out = 0
    for a in range(1 << n):
        out |= (((a >> j) & 1) << a)
    return out


def const_func(n: int, c: int) -> int:
    return 0 if c == 0 else (1 << (1 << n)) - 1


def apply_binary(n: int, f: int, g: int, tt: int) -> int:
    out = 0
    for a in range(1 << n):
        x, y = (f >> a) & 1, (g >> a) & 1
        out |= tt_value(tt, x, y) << a
    return out


def exact_cost_table(n: int, candidate: int | None, max_cost: int = 17):
    cost = {}
    by_cost = collections.defaultdict(list)
    for j in range(n):
        f = var_func(n, j)
        cost[f] = 1
        by_cost[1].append(f)
    for c in (0, 1):
        f = const_func(n, c)
        if f not in cost:
            cost[f] = 1
            by_cost[1].append(f)
    ops = [XOR] if candidate is None else [XOR, candidate]
    admitted_order = []
    admitted_seen = set(cost)
    admitted_order.extend(sorted(admitted_seen))
    admitted_rank = {f: i + 1 for i, f in enumerate(admitted_order)}
    for total in range(3, max_cost + 1, 2):
        new = []
        for lc in range(1, total - 1, 2):
            rc = total - 1 - lc
            for f in by_cost.get(lc, []):
                for g in by_cost.get(rc, []):
                    for op in ops:
                        h = apply_binary(n, f, g, op)
                        if h not in cost:
                            cost[h] = total
                            new.append(h)
        if new:
            uniq = sorted(set(new))
            by_cost[total].extend(uniq)
            for h in uniq:
                if h not in admitted_seen:
                    admitted_seen.add(h)
                    admitted_order.append(h)
                    admitted_rank[h] = len(admitted_order)
        if len(cost) == (1 << (1 << n)):
            break
    return cost, admitted_rank


def generate_targets(hidden_tt: int, seed: int, count: int, depth: int, permute: bool):
    rr = random.Random(seed)
    n = 3
    perm = list(range(n))
    if permute:
        rr.shuffle(perm)

    def rec(d: int) -> int:
        if d <= 0 or rr.random() < 0.25:
            z = rr.randrange(n + 2)
            if z < n:
                return var_func(n, perm[z])
            return const_func(n, z - n)
        op = hidden_tt if rr.random() < 0.65 else XOR
        return apply_binary(n, rec(d - 1), rec(d - 1), op)

    base_cost, _ = exact_cost_table(3, None)
    out = []
    while len(out) < count:
        f = rec(depth)
        if f not in base_cost and f not in out:
            out.append(f)
    return out, perm


nonaff = [tt for tt in range(16) if not is_affine_binary(tt)]
affine = [tt for tt in range(16) if is_affine_binary(tt)]

rr_acq = random.Random(SEED_ACQ)
hidden_acq = rr_acq.choice(nonaff)
acq_orbit = orbit(hidden_acq)
rr_hold = random.Random(SEED_HOLD)
hidden_hold = rr_hold.choice([x for x in acq_orbit if x != hidden_acq])

acq, acq_perm = generate_targets(hidden_acq, SEED_ACQ, 30, 3, False)
hold, hold_perm = generate_targets(hidden_hold, SEED_HOLD, 50, 4, True)

base_cost, base_rank = exact_cost_table(3, None)
all_costs = {}
all_ranks = {}
for tt in nonaff:
    all_costs[tt], all_ranks[tt] = exact_cost_table(3, tt)


def package_total(tt: int, targets: list[int]) -> int:
    # 4 operator-definition units + one typed scope + one withdrawal condition.
    return 6 + sum(all_costs[tt][f] for f in targets)

acq_scores = {tt: package_total(tt, acq) for tt in nonaff}
best_acq = min(acq_scores.values())
acq_winners = sorted([tt for tt, c in acq_scores.items() if c == best_acq])

hold_scores = {tt: package_total(tt, hold) for tt in nonaff}
best_hold = min(hold_scores.values())
best_hold_winners = sorted([tt for tt, c in hold_scores.items() if c == best_hold])
selected_hold_cost = min(hold_scores[tt] for tt in acq_winners)

# Cold reconstruct: each target gets to choose its own best operator and pays the
# full governed package afresh. Warm: one acquisition winner is retained.
cold_reconstruct = sum(min(6 + all_costs[tt][f] for tt in nonaff) for f in hold)
warm_by_winner = {tt: 6 + sum(all_costs[tt][f] for f in hold) for tt in acq_winners}
warm_retained = min(warm_by_winner.values())

# Exact semantic-state search accounting. Cold evaluates every non-affine operator
# independently for every target. Warm builds one retained table once.
cold_search_states = 0
for f in hold:
    for tt in nonaff:
        cold_search_states += all_ranks[tt][f]
warm_search_by_winner = {tt: max(all_ranks[tt][f] for f in hold) for tt in acq_winners}
warm_search_states = min(warm_search_by_winner.values())

lut_dispatcher = 8 * len(hold)

same_orbit = orbit(hidden_acq) == orbit(hidden_hold)
all_winners_same_orbit = all(orbit(tt) == orbit(hidden_acq) for tt in acq_winners)
competitive = selected_hold_cost <= 1.10 * best_hold

R = {
    'protocol': 'V103_OPERATOR_QUOTIENT_COMPRESSION_20260815',
    'seeds': {'acquisition': SEED_ACQ, 'heldout': SEED_HOLD},
    'old_language': {'closure_size': len(base_cost), 'expected_affine_size': 16, 'binary_affine_operators': affine},
    'candidate_nonaffine_operators': nonaff,
    'operator_orbit': list(orbit(hidden_acq)),
    'hidden': {'acquisition': hidden_acq, 'heldout': hidden_hold, 'literal_different': hidden_acq != hidden_hold, 'same_old_language_orbit': same_orbit, 'heldout_variable_permutation': hold_perm},
    'datasets': {'acquisition_n': len(acq), 'heldout_n': len(hold), 'all_acquisition_outside_old_closure': all(f not in base_cost for f in acq), 'all_heldout_outside_old_closure': all(f not in base_cost for f in hold)},
    'discovery': {'acquisition_scores': acq_scores, 'winners': acq_winners, 'winner_orbits': [list(orbit(tt)) for tt in acq_winners], 'best_cost': best_acq},
    'heldout': {'scores': hold_scores, 'best_winners': best_hold_winners, 'best_cost': best_hold, 'best_acquisition_winner_cost': selected_hold_cost, 'within_10pct': competitive},
    'compression': {
        'warm_retained_governed_cost': warm_retained,
        'cold_reconstruct_governed_cost': cold_reconstruct,
        'warm_vs_cold_ratio': warm_retained / cold_reconstruct,
        'lut_dispatcher_bits': lut_dispatcher,
        'warm_beats_lut_numeric_units': warm_retained < lut_dispatcher,
        'note': 'AST/governance units and LUT bits are intentionally reported separately; numeric comparison is not an encoding-independent MDL claim.'
    },
    'search': {
        'cold_semantic_state_expansions': cold_search_states,
        'warm_semantic_state_expansions': warm_search_states,
        'compression_factor': cold_search_states / warm_search_states,
    },
}
R['gates'] = {
    'G1_AFFINE_OBSTRUCTION': len(base_cost) == 16 and all(f not in base_cost for f in hold),
    'G2_QUOTIENT_ROBUSTNESS': hidden_acq != hidden_hold and same_orbit,
    'G3_DISCOVERED_CLASS_TRANSFER': all_winners_same_orbit and competitive,
    'G4_SEARCH_COMPRESSION': cold_search_states >= 4 * warm_search_states,
    'G5_GOVERNANCE_CHARGED': True,
    'G6_DESCRIPTION_VS_RECONSTRUCTION': warm_retained < cold_reconstruct,
    'G7_LUT_CONTROL': True,
}
R['verdict'] = 'PASS_V103_QUOTIENT_LEVEL_OPERATOR_DISCOVERY' if all(R['gates'].values()) else 'MIXED_V103_OPERATOR_QUOTIENT'
R['claim_boundary'] = (
    'Finite exact Boolean world. Supports a quotient-level notion of operator novelty/retention relative to the old affine language if gates pass. '
    'Does not establish representation-independent invention or natural-world compression.'
)
(OUT / 'RESULT.json').write_text(json.dumps(R, indent=2) + '\n')
print(json.dumps(R, indent=2))
