# V114 Z4 Horizon-Indexed Capability Identity — PRECOMMIT

Date: 2026-08-15 NZST

Status: frozen before inspecting any Z4 result.

## Motivation

Post-V113 exploratory analysis of GF(5) exposed a stronger mechanism: old-unit orbit classes that were distinct at the one-new-operator-use level merged into the same exact developmental closure, and every cross-orbit representative within those merged classes required exactly two uses of the other representative.

That suggests that researcher-chosen composition depth should not be hidden. Capability identity may itself be indexed by a resource/composition horizon.

V114 tests that idea prospectively in a fresh exact substrate.

## Fresh substrate

Unary functions on the ring Z/4Z.

- universe: all `4^4 = 256` unary functions;
- old capability `A`: all affine maps `x -> ax+b mod 4`, `a,b in Z4`;
- old invertible coordinate group: affine bijections with `a in {1,3}`;
- candidates: all functions outside the old affine closure.

This is distinct from V105's GF(4) field substrate: multiplication/addition are now ring arithmetic modulo 4, not GF(2)[a]/(a^2+a+1).

## Resource-indexed reachability

Old affine maps have new-operator cost 0.

For a candidate seed `O`, define `cost_O(f)` as the minimum number of occurrences of `O` in any finite composition expression over `A ∪ {O}` that yields `f`.

Define horizon reachability:

`f <=_k O` iff `cost_O(f) <= k`.

For candidate representatives `O1,O2`, define horizon mutual identity:

`O1 ≡_k O2` iff `cost_O1(O2) <= k` and `cost_O2(O1) <= k`.

Exact developmental identity is equality of generated closures / finite mutual reachability without a fixed k.

## Frozen computations

1. Enumerate exact old-unit orbits of all non-affine candidates.
2. Compute exact generated closure for one representative of every orbit.
3. Compute minimum new-seed occurrence cost to every reachable function for every orbit representative.
4. Construct mutual-identity partitions for horizons `k=1,2,3` and for eventual exact closure identity.

## Frozen gates

### G1 — cost correctness / closure consistency
For every representative, the finite-cost reachable set must equal its exact generated closure.

### G2 — monotone horizon coarsening
If two candidates are mutually reachable by horizon `k`, they must remain mutually reachable at every larger tested horizon.

Thus identity partitions may merge with larger composition budget but may not split.

### G3 — eventual identity equals closure-extension identity
The eventual mutual-reachability partition must equal the partition by exact generated closure sets.

### G4 — boundary-sensitivity discovery
Report whether any pair of candidates/orbits is distinct at horizon 1 but merges at horizon 2 or 3.

Two legitimate outcomes:
- `HORIZON_COARSENING_OBSERVED`;
- `NO_HORIZON_COARSENING_IN_Z4`.

### G5 — false-invention witness if coarsening occurs
If G4 finds a merge, provide the lexicographically first pair and exact minimum occurrence costs in both directions. This is a concrete case where a shallower old-language horizon would call the second candidate new but a deeper lawful composition search proves it already reachable.

### G6 — old-unit orbit comparison
Report whether the horizon-1 mutual partition equals old-unit orbit identity. If not, characterize whether non-invertible old affine maps already create additional one-use mutual equivalences.

### G7 — compression profile
Report number of candidate classes under:
- literal identity;
- old-unit orbit identity;
- mutual horizon k=1;
- k=2;
- k=3;
- exact developmental closure identity.

## Primary interpretation

The strongest hoped-for result is not that a fixed depth is universal. It is the opposite:

> capability identity is resource-indexed, and increasing lawful composition budget can collapse apparent novelty without changing the underlying task/verifier.

That would make the boundary-choice objection explicit and testable rather than something to argue away.

## Claim boundary

Fresh exact unary Z4 transformation monoid only. No natural-code or universal reasoning claim follows directly.
