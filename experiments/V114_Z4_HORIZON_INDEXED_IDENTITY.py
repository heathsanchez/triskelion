from __future__ import annotations

import heapq
import json
from itertools import product
from pathlib import Path

OUT = Path('artifacts/v114_z4_horizon_identity')
OUT.mkdir(parents=True, exist_ok=True)

Q = 4
UNIVERSE = {tuple(v) for v in product(range(Q), repeat=Q)}
AFFINE = {tuple((a*x+b) % Q for x in range(Q)) for a in range(Q) for b in range(Q)}
UNITS = {tuple((a*x+b) % Q for x in range(Q)) for a in (1,3) for b in range(Q)}
NON = UNIVERSE - AFFINE


def comp(f, g):
    return tuple(f[g[x]] for x in range(Q))


def orbit(f):
    return frozenset(comp(post, comp(f, pre)) for pre in UNITS for post in UNITS)


def exact_closure(seed):
    S = set(AFFINE) | {seed}
    frontier = {seed}
    while frontier:
        cur = list(S)
        new = set()
        for f in frontier:
            for g in cur:
                for h in (comp(f,g), comp(g,f)):
                    if h not in S:
                        new.add(h)
        S |= new
        frontier = new
    return frozenset(S)


def min_seed_cost(seed):
    INF = 10**9
    cost = {}
    pq = []
    for f in AFFINE:
        cost[f] = 0
        heapq.heappush(pq, (0, f))
    cost[seed] = min(cost.get(seed, INF), 1)
    heapq.heappush(pq, (cost[seed], seed))
    final = []
    final_set = set()
    while pq:
        cf, f = heapq.heappop(pq)
        if cf != cost.get(f) or f in final_set:
            continue
        for g in final:
            cg = cost[g]
            for h in (comp(f,g), comp(g,f)):
                nh = cf + cg
                if nh < cost.get(h, INF):
                    cost[h] = nh
                    heapq.heappush(pq, (nh, h))
        final.append(f)
        final_set.add(f)
    return cost


def main():
    orbits = []
    rem = set(NON)
    while rem:
        s = min(rem)
        o = orbit(s) & NON
        orbits.append(frozenset(o))
        rem -= o

    reps = [min(o) for o in orbits]
    closures = [exact_closure(r) for r in reps]
    costs = [min_seed_cost(r) for r in reps]

    G1 = all(set(costs[i]) == set(closures[i]) for i in range(len(reps)))

    # Distinct old-unit orbits that are mutually reachable by each tested horizon.
    mutual_by_k = {}
    for k in (1,2,3):
        pairs = []
        for i in range(len(reps)):
            for j in range(i+1, len(reps)):
                if costs[i].get(reps[j], 10**9) <= k and costs[j].get(reps[i], 10**9) <= k:
                    pairs.append((i,j))
        mutual_by_k[k] = pairs

    G2 = set(mutual_by_k[1]) <= set(mutual_by_k[2]) <= set(mutual_by_k[3])

    dev = {}
    for i,c in enumerate(closures):
        dev.setdefault(c, []).append(i)
    dev_groups = list(dev.values())
    eventual_pairs = set()
    for g in dev_groups:
        for a in range(len(g)):
            for b in range(a+1, len(g)):
                eventual_pairs.add((min(g[a],g[b]), max(g[a],g[b])))
    mutual_eventual = set()
    for i in range(len(reps)):
        for j in range(i+1,len(reps)):
            if reps[j] in closures[i] and reps[i] in closures[j]:
                mutual_eventual.add((i,j))
    G3 = eventual_pairs == mutual_eventual

    new_merges = sorted(set(mutual_by_k[2]) - set(mutual_by_k[1]))
    if not new_merges:
        new_merges = sorted(set(mutual_by_k[3]) - set(mutual_by_k[2]))
    witness = None
    if new_merges:
        i,j = new_merges[0]
        witness = {
            'orbit_i': i,
            'orbit_j': j,
            'rep_i': reps[i],
            'rep_j': reps[j],
            'i_to_j_min_seed_occurrences': costs[i][reps[j]],
            'j_to_i_min_seed_occurrences': costs[j][reps[i]],
            'same_exact_closure': closures[i] == closures[j],
            'closure_size': len(closures[i]),
        }

    # At horizon 1, there should be no mutual merges across distinct old-unit orbits.
    G6_equal = len(mutual_by_k[1]) == 0

    result = {
        'canonical_id': 'V114_Z4_HORIZON_INDEXED_IDENTITY',
        'counts': {
            'all_functions': len(UNIVERSE),
            'old_affine': len(AFFINE),
            'old_units': len(UNITS),
            'nonaffine_literals': len(NON),
            'old_unit_orbits': len(orbits),
            'orbit_sizes': [len(o) for o in orbits],
            'exact_developmental_classes': len(dev_groups),
            'developmental_groups_by_orbit': dev_groups,
            'closure_sizes_by_orbit': [len(c) for c in closures],
            'max_seed_occurrences_by_orbit': [max(c.values()) for c in costs],
        },
        'mutual_distinct_orbit_pairs_by_horizon': {str(k): v for k,v in mutual_by_k.items()},
        'false_invention_witness': witness,
        'compression_profile': {
            'literal': len(NON),
            'old_unit_orbit': len(orbits),
            'horizon1': len(orbits) - len(mutual_by_k[1]),
            'horizon2': len(dev_groups) if set(mutual_by_k[2]) == eventual_pairs else None,
            'horizon3': len(dev_groups) if set(mutual_by_k[3]) == eventual_pairs else None,
            'eventual_developmental': len(dev_groups),
        },
        'gates': {
            'G1_cost_reachable_set_equals_exact_closure': G1,
            'G2_horizon_mutual_reachability_monotone': G2,
            'G3_eventual_mutual_equals_closure_identity': G3,
            'G4_boundary_sensitivity_discovery': witness is not None,
            'G5_false_invention_witness_if_coarsening': witness is not None,
            'G6_horizon1_matches_old_unit_orbit_on_distinct_orbits': G6_equal,
            'G7_compression_profile_reported': True,
        },
        'primary_discovery': 'HORIZON_COARSENING_OBSERVED' if witness else 'NO_HORIZON_COARSENING_IN_Z4',
        'claim_boundary': 'Exact unary Z/4Z transformation monoid only; resource cost counts occurrences of the candidate seed while old affine maps have cost zero.',
    }
    (OUT/'RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    if not (G1 and G2 and G3 and G6_equal):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
