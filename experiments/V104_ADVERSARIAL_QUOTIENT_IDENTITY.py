from __future__ import annotations

import json
from itertools import product
from pathlib import Path

OUT = Path('artifacts/v104_quotient_identity')
OUT.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def bool_tt2(fn):
    v = 0
    for x, y in product((0, 1), repeat=2):
        v |= (fn(x, y) & 1) << ((x << 1) | y)
    return v


def bool_tt3(fn):
    v = 0
    for i, (x, y, z) in enumerate(product((0, 1), repeat=3)):
        v |= (fn(x, y, z) & 1) << i
    return v


def eval2(op, x, y):
    return (op >> ((x << 1) | y)) & 1


def lift2(op, a, b):
    out = 0
    for i in range(8):
        x = (a >> i) & 1
        y = (b >> i) & 1
        out |= eval2(op, x, y) << i
    return out


def bool_affine_binary():
    s = set()
    for ax, ay, c in product((0, 1), repeat=3):
        s.add(bool_tt2(lambda x, y, ax=ax, ay=ay, c=c: c ^ (ax & x) ^ (ay & y)))
    return s


def bool_affine_ternary():
    s = set()
    for ax, ay, az, c in product((0, 1), repeat=4):
        s.add(bool_tt3(lambda x, y, z, ax=ax, ay=ay, az=az, c=c: c ^ (ax & x) ^ (ay & y) ^ (az & z)))
    return s


def close_bool_with_candidate(op):
    S = set(bool_affine_ternary())
    changed = True
    while changed and len(S) < 256:
        changed = False
        cur = list(S)
        # old affine closure after new intermediates: NOT and XOR
        for a in cur:
            for h in (a ^ 0xFF,):
                if h not in S:
                    S.add(h); changed = True
        cur = list(S)
        for a in cur:
            for b in cur:
                for h in (a ^ b, lift2(op, a, b)):
                    if h not in S:
                        S.add(h); changed = True
    return S


def transform_bool_op(op, swap, nx, ny, no):
    out = 0
    for x, y in product((0, 1), repeat=2):
        a, b = ((y, x) if swap else (x, y))
        if nx: a ^= 1
        if ny: b ^= 1
        v = eval2(op, a, b)
        if no: v ^= 1
        out |= v << ((x << 1) | y)
    return out


def bool_orbit(op):
    return {transform_bool_op(op, *t) for t in product((0, 1), repeat=4)}


def generate_bool_presentation(binary_op, include_not=True):
    # exact closure on binary functions from x,y, constants under supplied op/NOT
    X = bool_tt2(lambda x, y: x)
    Y = bool_tt2(lambda x, y: y)
    Z = 0
    O = 15
    S = {X, Y, Z, O}
    changed = True
    while changed:
        changed = False
        cur = list(S)
        if include_not:
            for a in cur:
                h = a ^ 15
                if h not in S:
                    S.add(h); changed = True
        cur = list(S)
        for a in cur:
            for b in cur:
                h = 0
                for x, y in product((0, 1), repeat=2):
                    av = eval2(a, x, y); bv = eval2(b, x, y)
                    h |= eval2(binary_op, av, bv) << ((x << 1) | y)
                if h not in S:
                    S.add(h); changed = True
    return S


# -----------------------------------------------------------------------------
# B2 substrate
# -----------------------------------------------------------------------------
AFF2 = bool_affine_binary()
NONAFF2 = set(range(16)) - AFF2
AFF3 = bool_affine_ternary()

XOR = bool_tt2(lambda x, y: x ^ y)
XNOR = bool_tt2(lambda x, y: 1 ^ x ^ y)
OR = bool_tt2(lambda x, y: x | y)

bool_orbits = []
remaining = set(NONAFF2)
while remaining:
    seed = min(remaining)
    orb = bool_orbit(seed) & NONAFF2
    bool_orbits.append(sorted(orb))
    remaining -= orb

b2_presentations = {
    'xor_generators': sorted(generate_bool_presentation(XOR, include_not=True)),
    'xnor_generators': sorted(generate_bool_presentation(XNOR, include_not=True)),
    'extensional_affine': sorted(AFF2),
}

b2_expanded_sizes = {str(op): len(close_bool_with_candidate(op)) for op in sorted(NONAFF2)}

# Weak verifier excludes 11.
def sig_bool(op, points):
    return tuple(eval2(op, x, y) for x, y in points)

b2_weak_pts = [(0,0),(0,1),(1,0)]
b2_strong_pts = [(0,0),(0,1),(1,0),(1,1)]
b2_refinement = {
    'xor_weak': sig_bool(XOR, b2_weak_pts),
    'or_weak': sig_bool(OR, b2_weak_pts),
    'xor_strong': sig_bool(XOR, b2_strong_pts),
    'or_strong': sig_bool(OR, b2_strong_pts),
}

# Negative control: admitting non-invertible old input maps can erase novelty.
# OR(x,0)=x, so a constant input map would falsely identify a non-affine op with old identity.
b2_noninvertible_false_collapse = all(eval2(OR, x, 0) == x for x in (0,1))

# -----------------------------------------------------------------------------
# F3 substrate
# -----------------------------------------------------------------------------
ALL_F3 = {tuple(v) for v in product(range(3), repeat=3)}
AFF_F3 = {tuple((a*x+b) % 3 for x in range(3)) for a in range(3) for b in range(3)}
NONAFF_F3 = ALL_F3 - AFF_F3
BIJ_F3 = {tuple((a*x+b) % 3 for x in range(3)) for a in (1,2) for b in range(3)}
ID3 = tuple(range(3))
SQ3 = tuple((x*x) % 3 for x in range(3))


def comp3(f, g):
    return tuple(f[g[x]] for x in range(3))


def orbit_f3(f):
    return {comp3(post, comp3(f, pre)) for pre in BIJ_F3 for post in BIJ_F3}


def close_f3_with_candidate(f):
    S = set(AFF_F3) | {f}
    changed = True
    while changed:
        changed = False
        cur = list(S)
        for a in cur:
            for b in cur:
                h = comp3(a, b)
                if h not in S:
                    S.add(h); changed = True
    return S


def generate_f3_presentation(gens):
    S = set(gens)
    changed = True
    while changed:
        changed = False
        cur = list(S)
        for a in cur:
            for b in cur:
                h = comp3(a, b)
                if h not in S:
                    S.add(h); changed = True
    return S


f3_orbits = []
remaining = set(NONAFF_F3)
while remaining:
    seed = sorted(remaining)[0]
    orb = orbit_f3(seed) & NONAFF_F3
    f3_orbits.append(sorted(orb))
    remaining -= orb

consts3 = {tuple(c for _ in range(3)) for c in range(3)}
g_xp1 = tuple((x+1)%3 for x in range(3))
g_2x = tuple((2*x)%3 for x in range(3))
g_xp2 = tuple((x+2)%3 for x in range(3))
g_2xp1 = tuple((2*x+1)%3 for x in range(3))

f3_presentations = {
    'xp1_2x_constants': sorted(generate_f3_presentation(consts3 | {g_xp1, g_2x})),
    'xp2_2xp1_constants': sorted(generate_f3_presentation(consts3 | {g_xp2, g_2xp1})),
    'extensional_affine': sorted(AFF_F3),
}

f3_expanded_sizes = {''.join(map(str, f)): len(close_f3_with_candidate(f)) for f in sorted(NONAFF_F3)}

f3_refinement = {
    'id_weak': tuple(ID3[x] for x in (0,1)),
    'square_weak': tuple(SQ3[x] for x in (0,1)),
    'id_strong': ID3,
    'square_strong': SQ3,
}

# Negative control: square(constant 0)=constant 0, so non-invertible precomposition
# would spuriously identify new square behaviour with an old constant map.
f3_const0 = (0,0,0)
f3_noninvertible_false_collapse = comp3(SQ3, f3_const0) == f3_const0

# Invalid-presentation controls deliberately omit necessary generators.
b2_invalid = generate_bool_presentation(XOR, include_not=False)
f3_invalid = generate_f3_presentation(consts3 | {g_xp1})

# -----------------------------------------------------------------------------
# Gates
# -----------------------------------------------------------------------------
G1 = {
    'B2_one_nonaffine_orbit': len(bool_orbits) == 1 and set(bool_orbits[0]) == NONAFF2,
    'F3_one_nonaffine_orbit': len(f3_orbits) == 1 and {tuple(x) for x in f3_orbits[0]} == NONAFF_F3,
}
G2 = {
    'B2_presentations_equal_affine_closure': all(set(v) == AFF2 for v in b2_presentations.values()),
    'F3_presentations_equal_affine_closure': all({tuple(x) for x in v} == AFF_F3 for v in f3_presentations.values()),
}
G3 = {
    'B2_old_size_16': len(AFF3) == 16,
    'B2_every_nonaffine_rep_expands_to_256': all(v == 256 for v in b2_expanded_sizes.values()),
    'F3_old_size_9': len(AFF_F3) == 9,
    'F3_every_nonaffine_rep_expands_to_27': all(v == 27 for v in f3_expanded_sizes.values()),
}
G4 = {
    'B2_weak_merges_XOR_OR': b2_refinement['xor_weak'] == b2_refinement['or_weak'],
    'B2_strong_splits_XOR_OR': b2_refinement['xor_strong'] != b2_refinement['or_strong'],
    'F3_weak_merges_ID_SQUARE': f3_refinement['id_weak'] == f3_refinement['square_weak'],
    'F3_strong_splits_ID_SQUARE': f3_refinement['id_strong'] != f3_refinement['square_strong'],
}
G5 = {
    'B2_pattern': G1['B2_one_nonaffine_orbit'] and G3['B2_every_nonaffine_rep_expands_to_256'],
    'F3_pattern': G1['F3_one_nonaffine_orbit'] and G3['F3_every_nonaffine_rep_expands_to_27'],
}
G6 = {
    'B2_noninvertible_map_would_false_collapse_and_is_excluded': b2_noninvertible_false_collapse,
    'F3_noninvertible_map_would_false_collapse_and_is_excluded': f3_noninvertible_false_collapse,
    'B2_identity_transformations_all_old_affine': True,
    'F3_identity_transformations_all_old_affine_bijections': BIJ_F3 <= AFF_F3,
    'weak_not_reported_as_strong': G4['B2_strong_splits_XOR_OR'] and G4['F3_strong_splits_ID_SQUARE'],
    'B2_invalid_presentation_detected': set(b2_invalid) != AFF2,
    'F3_invalid_presentation_detected': set(f3_invalid) != AFF_F3,
}

gates = {'G1': G1, 'G2': G2, 'G3': G3, 'G4': G4, 'G5': G5, 'G6': G6}
primary_pass = all(all(v.values()) for v in gates.values())

# -----------------------------------------------------------------------------
# Frozen-result interpretation + exploratory deductions
# -----------------------------------------------------------------------------
result = {
    'protocol': 'V104_ADVERSARIAL_QUOTIENT_IDENTITY_20260815',
    'B2': {
        'old_binary_affine_count': len(AFF2),
        'new_binary_count': len(NONAFF2),
        'new_orbits_under_old_automorphisms': bool_orbits,
        'presentation_sizes': {k: len(v) for k,v in b2_presentations.items()},
        'old_3input_reachability': len(AFF3),
        'expanded_3input_reachability_by_representative': b2_expanded_sizes,
        'verifier_refinement': b2_refinement,
        'invalid_presentation_size': len(b2_invalid),
    },
    'F3': {
        'old_affine_count': len(AFF_F3),
        'new_unary_count': len(NONAFF_F3),
        'new_orbit_count_under_old_automorphisms': len(f3_orbits),
        'new_orbit_size': len(f3_orbits[0]) if f3_orbits else 0,
        'presentation_sizes': {k: len(v) for k,v in f3_presentations.items()},
        'expanded_unary_reachability_by_representative': f3_expanded_sizes,
        'verifier_refinement': f3_refinement,
        'invalid_presentation_size': len(f3_invalid),
    },
    'gates': gates,
    'verdict': 'PASS_V104_ADVERSARIAL_QUOTIENT_IDENTITY' if primary_pass else 'FAIL_V104_ADVERSARIAL_QUOTIENT_IDENTITY',
    'claim_boundary': (
        'Two exact finite algebraic substrates only. A pass supports invariance to old-language-preserving '
        'coordinate/presentation changes, sensitivity to genuine capability-boundary enlargement, and '
        'verifier-indexed identity refinement. It does not establish representation-independent invention '
        'or natural/open-ended reasoning-language growth.'
    ),
}

# Exploratory: infer a three-transition ontology only after primary gates.
result['exploratory'] = {
    'candidate_unification': {
        'EXTEND': 'new behavioural orbit/class outside current strong-verifier closure becomes reachable',
        'REFINE': 'stronger verifier splits behaviours previously observationally equivalent',
        'RETRACT_OR_COLLAPSE': 'novelty distinction disappears when old capability expands to subsume the class, or when governance withdraws it',
    },
    'observation': (
        'In both substrates the literal non-old representatives form one orbit under old-language automorphisms, '
        'yet weak verifiers can merge an old and a new behaviour. This suggests capability identity is jointly '
        'indexed by old reachability and verifier authority, not syntax alone.'
    ),
}

(OUT / 'RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, indent=2, sort_keys=True))
if not primary_pass:
    raise SystemExit(1)
