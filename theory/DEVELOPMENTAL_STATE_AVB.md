# Verifier-Resource Indexed Developmental State

Date: 2026-08-15 NZST

This note combines the two independently exposed axes in the current Triskelion evidence:

1. verifier authority can split observational equivalence classes;
2. lawful composition/resource horizon can collapse apparent novelty by exposing deeper constructions.

The resulting developmental judgment should therefore be indexed explicitly by capability state, verifier authority, and resource horizon.

## 1. State

Write

`D = (A, V, B)`

where:

- `A` is the currently admitted executable capability state / old language;
- `V` is the authoritative verifier/observation set;
- `B` is the lawful composition/search/resource horizon used when asking what `A` can already express.

For a candidate `O`, write

`Reach_B(A)`

for behaviours reachable from `A` within horizon `B`.

In exact finite settings, `B = ∞` denotes full composition closure:

`Reach_∞(A) = Cl(A)`.

The operational novelty judgment is

`Novel(O | A,V,B)`

when `O` is verifier-distinguishable in the relevant scope and is not already in the bounded lawful reachability of `A`.

The verifier clause is intentionally separate from reachability: a behaviour can be executable yet not distinguishable under current authority, or distinguishable yet already constructible from existing capability.

## 2. Law A — resource monotonicity

For horizons `B0 <= B1`,

`Reach_B0(A) subseteq Reach_B1(A)`.

Therefore, holding `A,V` fixed:

`Novel(O | A,V,B1) => Novel(O | A,V,B0)`.

Equivalently, increasing lawful search/composition budget can turn NEW into OLD/REACHABLE, but cannot turn something already reachable at a smaller budget into unreachable at a larger one.

This is the formal version of the V101P/V114 phenomenon.

### Consequence

A failed shallow search is not an obstruction certificate.

Any claim of forced construction must specify either:

- the exact/full closure in a tractable finite setting; or
- the operational horizon `B` under which closure is claimed, plus an explicit statement that novelty is horizon-relative.

## 3. Law V — verifier authority monotonicity

For verifier authorities `V0 subseteq V1`, observational equivalence satisfies:

`x ~_(V1) y => x ~_(V0) y`.

Thus stronger authority refines the observational partition.

Holding `A,B` fixed, adding verifier authority may expose a distinction that was previously invisible.

This is structurally opposite to increasing `B`:

- larger `V` tends toward **finer** observational distinctions;
- larger `B` tends toward **coarser** novelty judgments because more candidates become already reachable.

## 4. Law A-state — capability monotonicity

If `A0 subseteq A1` and the composition discipline is unchanged, then

`Reach_B(A0) subseteq Reach_B(A1)`

for the same budget convention.

Thus a construction that was genuinely novel relative to an earlier state can cease to be novel after capability acquisition.

Novelty is therefore developmental, not permanent:

`Novel(O | A_t,V,B)` need not imply `Novel(O | A_(t+1),V,B)`.

This is the principled form of novelty collapse after the language grows.

## 5. Exact developmental identity

For exact closure, define

`O1 ≡dev_A O2`

iff

`Cl(A ∪ {O1}) = Cl(A ∪ {O2})`.

This identifies candidates by the state transition they induce rather than by literal syntax.

The old-unit orbit theorem in `CAPABILITY_ORBIT_PREORDER.md` gives a sufficient condition:

`O1 ~_A O2 => O1 ≡dev_A O2`.

V113 establishes in GF(5) that the converse need not hold: distinct coordinate orbits can generate the same enlarged closure.

Thus the hierarchy is:

`literal identity  ->  old-unit orbit identity  ->  developmental closure identity`.

Each step removes distinctions that do not alter future executable reachability.

## 6. Developmental reachability order

On exact developmental classes, define

`C1 <= C2`

when admitting a representative of `C2` makes a representative of `C1` reachable from the old state.

This is a preorder before quotienting by mutual reachability and a partial order after the mutual-reachability quotient.

The GF(5) V113A result falsifies the stronger universal-lattice hypothesis: joins need not exist.

Therefore the general term should be **capability reachability preorder/poset**, not capability lattice.

## 7. Four primitive state transitions

The combined structure distinguishes four operations that earlier experiments could misleadingly group together.

### EXTEND

A candidate survives the old-closure test and is admitted, enlarging executable reachability:

`Reach(A_(t+1)) strictly contains Reach(A_t)`.

### REFINE

Verifier authority grows and splits a previously observationally equivalent class:

`Pi(V_(t+1))` refines `Pi(V_t)`.

No new executable primitive is necessarily required.

### COLLAPSE

A previous novelty distinction disappears because lawful composition horizon or admitted capability has grown enough to make the candidate reachable:

`O notin Reach_B0(A)` but `O in Reach_B1(A)` for `B1>B0`,

or

`O notin Reach(A_t)` but `O in Reach(A_(t+1))`.

### RETRACT

Contradictory verifier evidence invalidates an admitted scope/capability under the governance rule, causing disablement, narrowing, or withdrawal.

RETRACT is epistemic/governance action, not the inverse of EXTEND in pure algebra: provenance must be retained even when operational availability is removed.

## 8. Two-dimensional falsification grid

For a fixed candidate pair, vary `V` and `B` independently.

| | smaller B | larger B |
|---|---|---|
| weaker V | coarse evidence + shallow reach | coarse evidence + deeper reach |
| stronger V | refined evidence + shallow reach | refined evidence + deeper reach |

This grid exposes two common category errors:

1. **search failure mistaken for representation inadequacy** — fixed by increasing `B`;
2. **observational alias mistaken for true identity** — fixed by increasing `V`.

A robust construction claim should survive the relevant movement along both axes:

- it remains outside the lawful old reachability at the declared/exact `B`;
- it remains a meaningful distinction under sufficient verifier authority `V`.

## 9. Boundary-choice objection becomes a parameter, not a debate

The question “did the researcher draw the old-language boundary favourably?” decomposes into explicit variables:

- What is admitted in `A`?
- Which lawful compositions count and at what horizon `B`?
- Which distinctions are authoritative under `V`?
- Which invertible transformations already in `A` are presentation changes rather than new capability?

A result can then be stress-tested by varying each axis while holding the others fixed.

The strongest invariance target is not absolute representation independence. It is **stability under changes that preserve the same effective reachable capability state and verifier semantics**.

## 10. Admission rule

A conservative verifier-governed constructor should use the following decision order:

1. observe a verified residual;
2. enlarge lawful old-language search to the precommitted `B`;
3. if the target enters `Reach_B(A)`, classify as SEARCH/CLOSURE, not construction;
4. quotient candidate representations by old-capability automorphisms where valid;
5. if still outside reach, construct candidate capability;
6. externally verify causal help and protected non-harm;
7. infer/verify scope separately;
8. retain the induced developmental class/state change, not merely the literal implementation;
9. on new evidence, REFINE, COLLAPSE, RETRACT, or retain as warranted.

This is a Reliability-Ratchet-like controller over the growth of the executable reasoning language itself.

## 11. Current empirical anchors

- V101P: widening lawful natural-code composition from depth 1 to depth 2 killed an apparent missing-operator claim.
- V104: coordinate/presentation changes inside old capability did not alter tested novelty identity; non-invertible maps caused false collapses.
- V105: quotient classes had different directed reachability consequences.
- V108: a comparison-coordinate relation was selected from verifier evidence within a generic grammar.
- V109: the induced relation transported a different repair family.
- V110: recurrent quotient structure appeared in blind historical repairs, while V112B showed retrospective recurrence alone was not statistically decisive.
- V113: exact developmental closure identity was strictly coarser than coordinate-orbit identity in GF(5).
- V113A: the resulting developmental order was not a lattice.
- V114: fresh Z4 prospectively exposed horizon coarsening: two distinct horizon-1/orbit classes became mutually reachable at exactly two seed occurrences.
- V111: prospective cross-corpus BugsInPy prediction remains pending execution.

## 12. Claim boundary

The monotonicity statements follow from the stated definitions. The empirical studies show these transition types occur in bounded exact and executable software settings. They do not establish tractable exact closure, autonomous verifier design, or unrestricted conceptual growth in open-ended systems.
