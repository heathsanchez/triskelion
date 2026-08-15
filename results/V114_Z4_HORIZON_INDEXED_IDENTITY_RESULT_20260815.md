# V114 Z4 Horizon-Indexed Capability Identity — Result

Protocol was frozen first in `protocols/V114_Z4_HORIZON_INDEXED_IDENTITY_PRECOMMIT.md`.

Experiment: `experiments/V114_Z4_HORIZON_INDEXED_IDENTITY.py`.

Primary execution was an exact local execution of the committed algorithm after protocol freeze. GitHub-hosted attestation remains pending runner availability.

## Primary discovery

**HORIZON_COARSENING_OBSERVED**

The fresh Z/4Z unary transformation world prospectively confirms that apparent capability identity changes with lawful composition horizon.

## Exact substrate

Unary functions on the ring Z/4Z:

- all unary functions: **256**
- old affine maps `x -> ax+b mod 4`: **16**
- old invertible affine coordinate maps: **8**
- non-affine literal candidates: **240**
- old-unit coordinate orbits: **10**

Orbit sizes:

`32, 16, 16, 64, 32, 8, 8, 32, 16, 16`

Exact generated-closure sizes by orbit:

`72, 32, 48, 192, 192, 24, 24, 120, 40, 64`

## Exact developmental identity

The 10 coordinate orbits reduce to **9** exact developmental closure identities.

All classes remain singleton except one:

`{orbit 3, orbit 4}`

The two representatives are:

- orbit 3 representative: `(0,0,1,2)`
- orbit 4 representative: `(0,0,1,3)`

They are not in the same old-unit coordinate orbit, but each generates the same exact **192-function** capability closure.

## Composition-horizon result

The minimum number of occurrences of one representative needed to construct the other is exactly:

- orbit 3 seed -> orbit 4 representative: **2**
- orbit 4 seed -> orbit 3 representative: **2**

At horizon 1 they remain distinct.

At horizon 2 they become mutually reachable and collapse to the same developmental identity.

No further class collapse occurs at horizon 3.

So the class-count profile is:

`240 literal operators -> 10 old-unit orbits / horizon-1 classes -> 9 horizon-2 classes -> 9 horizon-3 classes -> 9 exact developmental classes`.

## False-invention witness

This gives an exact prospective example of the boundary-choice problem.

If the effective old-language closure is truncated to one use of a retained operator, then the second representative appears unavailable/new.

If lawful composition is widened to two uses, it is already constructible from the first.

Thus:

`novel at B=1` does not imply `novel at B=2`.

The underlying task/verifier did not change; only the lawful composition horizon changed.

This is the finite structural analogue of the V101P natural-code diagnostic where depth-1 closure made a repair look unavailable but depth-2 composition recovered it.

## Gates

- G1 cost-reachable set equals exact closure — **PASS**
- G2 horizon mutual reachability is monotone — **PASS**
- G3 eventual mutual reachability equals exact closure identity — **PASS**
- G4 boundary-sensitivity discovery — **PASS**
- G5 explicit false-invention witness — **PASS**
- G6 horizon-1 distinct-orbit relation matches old-unit orbit identity — **PASS**
- G7 compression profile reported — **PASS**

## Stronger formulation

The result suggests that capability novelty should carry an explicit resource/composition index.

A useful operational judgment is therefore something like:

`Novel(O | A, V, B)`

where:

- `A` is the current capability state;
- `V` is verifier authority;
- `B` is the lawful composition/search/resource horizon.

Increasing verifier authority can **REFINE** observational classes.

Increasing lawful composition horizon can **COLLAPSE** apparent novelty by exposing constructions that were previously outside the bounded closure.

Those are distinct axes and move in opposite structural directions.

## Important terminology caution

Bounded mutual reachability at a fixed horizon is not assumed to be an equivalence relation in arbitrary systems. It is safest to treat it as a horizon-indexed reachability relation / bounded novelty judgment.

Stable developmental identity remains exact closure equality, equivalently eventual mutual reachability in these finite exact monoids.

## Claim boundary

Fresh exact unary Z/4Z transformation monoid only. Resource cost counts occurrences of the candidate seed while old affine maps cost zero. This does not establish a universal natural-code resource law, but it prospectively demonstrates that researcher-chosen composition depth can change an apparent novelty judgment in exactly the way the boundary-choice objection predicts.
