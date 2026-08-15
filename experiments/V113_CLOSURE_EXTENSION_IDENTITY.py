from __future__ import annotations

import json
from itertools import product
from pathlib import Path

OUT = Path('artifacts/v113_closure_extension_identity')
OUT.mkdir(parents=True, exist_ok=True)


def make_field(q):
    if q == 5:
        add = lambda x, y: (x + y) % 5
        mul = lambda x, y: (x * y) % 5
        return add, mul
    if q == 4:
        # GF(4)=GF(2)[a]/(a^2+a+1), encoding 0,1,a,a+1 as 0..3.
        def add(x, y): return x ^ y
        def mul(x, y):
            x0, x1 = x & 1, (x >> 1) & 1
            y0, y1 = y & 1, (y >> 1) & 1
            c0 = (x0*y0) ^ (x1*y1)
            c1 = (x0*y1) ^ (x1*y0) ^ (x1*y1)
            return c0 | (c1 << 1)
        return add, mul
    raise ValueError(q)


def compose(f, g):
    return tuple(f[g[x]] for x in range(len(f)))


def closure(old, seed):
    S = set(old)
    if seed not in S:
        S.add(seed)
    frontier = {seed}
    while frontier:
        cur = list(S)
        new = set()
        for f in frontier:
            for g in cur:
                a = compose(f, g)
                b = compose(g, f)
                if a not in S: new.add(a)
                if b not in S: new.add(b)
        S |= new
        frontier = new
    return frozenset(S)


def analyze(q):
    add, mul = make_field(q)
    universe = {tuple(v) for v in product(range(q), repeat=q)}
    affine = {tuple(add(mul(a, x), b) for x in range(q)) for a in range(q) for b in range(q)}
    units = {tuple(add(mul(a, x), b) for x in range(q)) for a in range(1, q) for b in range(q)}
    non = universe - affine

    def orbit(f):
        return frozenset(compose(post, compose(f, pre)) for pre in units for post in units)

    orbits = []
    rem = set(non)
    while rem:
        s = min(rem)
        o = orbit(s) & non
        orbits.append(frozenset(o))
        rem -= o

    # Exact closure once per orbit representative. By the theorem, every member of
    # the orbit must generate the same closure. We independently verify the two-way
    # reachability needed by that theorem: every orbit member is in rep closure and
    # the rep is in the member's old-unit orbit.
    closures = []
    theorem_checks = []
    for i, o in enumerate(orbits):
        rep = min(o)
        cl = closure(affine, rep)
        closures.append(cl)
        every_member_reachable = o <= cl
        rep_recoverable_from_every_member = all(rep in orbit(f) for f in o)
        theorem_checks.append({
            'orbit': i,
            'orbit_size': len(o),
            'closure_size': len(cl),
            'every_member_reachable_from_rep': every_member_reachable,
            'rep_old-unit-recoverable_from_every_member': rep_recoverable_from_every_member,
            'pass': every_member_reachable and rep_recoverable_from_every_member,
        })

    # Exact developmental identities are full closure sets, not cardinalities.
    dev_groups = {}
    for i, cl in enumerate(closures):
        dev_groups.setdefault(cl, []).append(i)
    dev_classes = list(dev_groups.values())
    coarser = [g for g in dev_classes if len(g) >= 2]

    same_size_diff_closure = []
    for i in range(len(closures)):
        for j in range(i+1, len(closures)):
            if len(closures[i]) == len(closures[j]) and closures[i] != closures[j]:
                same_size_diff_closure.append((i, j, len(closures[i])))

    # Mutual reachability between orbit representatives; compare to closure equality.
    mutual_matrix = []
    mismatch = []
    reps = [min(o) for o in orbits]
    for i in range(len(orbits)):
        row = []
        for j in range(len(orbits)):
            mutual = reps[i] in closures[j] and reps[j] in closures[i]
            equal = closures[i] == closures[j]
            row.append(mutual)
            if mutual != equal:
                mismatch.append((i, j, mutual, equal))
        mutual_matrix.append(row)

    return {
        'q': q,
        'literal_nonaffine_count': len(non),
        'old_affine_count': len(affine),
        'old_unit_count': len(units),
        'orbit_count': len(orbits),
        'orbit_sizes': [len(o) for o in orbits],
        'developmental_closure_count': len(dev_classes),
        'developmental_groups_by_orbit': dev_classes,
        'coarser_than_orbit_groups': coarser,
        'closure_sizes_by_orbit': [len(c) for c in closures],
        'same_size_distinct_closure_pairs': same_size_diff_closure,
        'theorem_checks': theorem_checks,
        'mutual_reachability_mismatches': mismatch,
        'literal_to_orbit_compression': len(non) / len(orbits),
        'literal_to_developmental_compression': len(non) / len(dev_classes),
        'orbit_to_developmental_compression': len(orbits) / len(dev_classes),
    }


def main():
    worlds = [analyze(4), analyze(5)]
    G1 = all(all(x['pass'] for x in w['theorem_checks']) for w in worlds)
    coarser_any = any(w['coarser_than_orbit_groups'] for w in worlds)
    G3 = any(w['developmental_closure_count'] >= 2 for w in worlds)
    same_size_any = any(w['same_size_distinct_closure_pairs'] for w in worlds)
    G6 = all(not w['mutual_reachability_mismatches'] for w in worlds)
    result = {
        'canonical_id': 'V113_CLOSURE_EXTENSION_IDENTITY',
        'worlds': worlds,
        'gates': {
            'G1_orbit_implies_same_closure_theorem_check': G1,
            'G2_converse_discovery_coarser_than_orbit': coarser_any,
            'G3_multiple_developmental_identities': G3,
            'G4_same_size_can_hide_distinct_closures': same_size_any,
            'G5_compression_reported': True,
            'G6_mutual_reachability_equals_closure_identity': G6,
        },
        'primary_discovery': 'COARSER_THAN_ORBIT' if coarser_any else 'ORBIT_TIGHT_IN_TESTED_WORLDS',
        'verdict': 'PASS_IMPLEMENTATION_GATES' if G1 and G3 and G6 else 'FAIL_IMPLEMENTATION_GATES',
        'claim_boundary': 'Exact unary GF(4)/GF(5) function monoids only; developmental identity defined by exact generated closure.',
    }
    (OUT/'RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    if result['verdict'] != 'PASS_IMPLEMENTATION_GATES':
        raise SystemExit(1)

if __name__ == '__main__':
    main()
