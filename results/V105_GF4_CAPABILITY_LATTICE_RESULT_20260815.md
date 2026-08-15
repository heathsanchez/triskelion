# V105 Fresh GF(4) Capability-Lattice Validation

Protocol was frozen first in `protocols/V105_GF4_CAPABILITY_LATTICE_PRECOMMIT.md` before any GF(4) orbit/closure counts were inspected.

## Primary verdict

**PASS_V105_GF4_CAPABILITY_LATTICE**

Local exact execution of the committed finite algorithm passed all seven frozen gates. GitHub Actions attestation is still pending/subject to the current runner-allocation issue affecting V104; do not call this Actions-attested unless a hosted run later completes.

## Exact substrate

Unary functions over GF(4)=GF(2)[a]/(a²+a+1):

- total unary functions: **256**;
- old affine capability `x -> ax+b`: **16** maps;
- invertible old affine coordinate maps: **12**;
- non-affine candidates: **240**.

## G1 — nontrivial quotient structure: PASS

The 240 non-affine functions split into **4** old-automorphism orbits, with sizes:

- 48
- 36
- 144
- 12

So the fresh substrate independently rejects the naive “all non-old operators are one class” picture and supports the richer quotient structure suggested exploratorily by GF(5).

## G2 — within-orbit representative invariance: PASS

For every orbit, the lexicographically first and last representatives generated closures with identical cardinality and identical reachable-orbit profile:

| orbit | first closure | last closure | reachable quotient profile |
|---:|---:|---:|---|
| 0 | 64 | 64 | {0} |
| 1 | 52 | 52 | {1} |
| 2 | 244 | 244 | {0,1,2} |
| 3 | 28 | 28 | {3} |

Literal representatives within the same old-coordinate orbit therefore had the same measured developmental consequence.

## G3 — between-orbit capability distinction: PASS

Different quotient classes caused sharply different exact closure growth:

- orbit 0 -> closure size **64**;
- orbit 1 -> **52**;
- orbit 2 -> **244**;
- orbit 3 -> **28**.

Thus the quotient partition is not decorative. The classes differ causally in what becomes reachable after admission.

## G4 — nontrivial directed reachability order: PASS

The exact quotient reachability graph contains directed edges:

- orbit **2 -> 0**;
- orbit **2 -> 1**.

But the reverse reachability does not hold.

So the developmental structure is ordered: admitting orbit 2 subsumes capabilities represented by orbits 0 and 1, while admitting 0 or 1 does not recover orbit 2.

This is the cleanest prospective evidence so far that capability growth is better represented as a directed reachability structure over quotient classes than as an unordered bag of invented primitives.

## G5 — same-class addition is redundant: PASS

For all four quotient classes, after admitting the first tested representative, the second tested representative from the same orbit was already reachable and added no further closure.

That is exactly the behavior expected if the orbit, rather than literal syntax, is the relevant identity unit.

## G6 — verifier-indexed refinement: PASS

The deterministic search found the first weak-verifier collision:

- old affine function: `(0,0,0,0)`;
- non-affine function: `(0,0,0,1)`;
- weak verifier on inputs `0,1,2`: both give `(0,0,0)`;
- withheld separator input `3`: old gives `0`, new gives `1`.

So a weak verifier merges an old and genuinely non-affine behavior, while the strong verifier splits them.

Again, novelty identity must be indexed by verifier authority as well as old reachability.

## G7 — negative controls: PASS

A non-invertible old affine pre-map can spuriously erase novelty:

- non-affine `(0,0,0,1)`;
- precompose with constant-3 map;
- result collapses to old affine constant-1.

This confirms why arbitrary old maps cannot define identity; the coordinate transformations used for quotienting must be invertible/structure-preserving.

The deliberately incomplete old presentation generated only **6/16** affine maps and was correctly rejected.

## Main result

V105 prospectively confirms the richer structure discovered after V104:

> **The relevant developmental object is not a literal operator and not merely a binary old/new class. It is a verifier-indexed quotient class with a measurable position in a directed reachability structure.**

In the fresh GF(4) world:

- literal variants inside a class have the same capability consequence;
- different classes have different capability consequence;
- some classes strictly subsume others;
- same-class re-addition is redundant;
- verifier refinement can split apparent old/new equivalence.

A compact representation is therefore closer to:

`A_t -> Q(A_t,V) -> admit class C -> Reach(A_t + C)`

with developmental comparison induced by reachability inclusion.

## Emerging theory — not yet promoted

Together with V104 and the exploratory GF(5) result, the natural candidate is a **verified capability preorder/lattice**:

- nodes/classes: verifier-distinguishable behavioral orbits modulo invertible transformations already realizable by the current state;
- order: `C1 <= C2` when admitting C2 makes C1 reachable;
- EXTEND: move to a state with new reachable quotient classes;
- REFINE: verifier growth splits an observational class;
- RETRACT/COLLAPSE: governance withdraws a class or later capability growth makes a prior novelty distinction redundant.

Whether this forms a true lattice in general is still open; V105 establishes only a nontrivial directed preorder structure in this fresh finite substrate.

## Claim boundary

Fresh exact GF(4) unary substrate only. This is strong evidence for quotient-level capability identity and directed reachability structure under a frozen protocol, but it does not establish a universal lattice theorem, natural-world operator invention, or open-ended reasoning-language growth.
