# TERNARY POINTED NUCLEUS CENSUS V1 — prospective precommit

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

## Governing question

Nucleus Transport V1 showed that the frozen generativity signature transported from the Boolean nucleus into three non-Boolean ordered worlds (H3, K3, T3) but not the cyclic Z3 world.

The next question is no longer whether a few hand-picked examples work.

It is:

[
oxed{	extbf{Across every pointed binary algebra on a 3-element carrier, which exact algebraic properties predict generativity?}}
]

The carrier is:

[
A={0,1,2}.
]

There are exactly

[
3^{3^2}=3^9=19{,}683
]

binary operations (d:A^2	o A).

Crossed with three possible references (gin A), this gives:

[
oxed{59{,}049	ext{ pointed nuclei }(A,g,d).}
]

Every one is included, either directly or via an exact symmetry orbit with its full orbit weight.

## Term language

For each pointed nucleus:

[
t ::= g mid x_i mid d(t,t).
]

No learned language, promotion, archive, provenance, revocation, or optimizer exists in this experiment.

## Exact semantic worlds

For each pointed nucleus compute exact closure at:

### Unary world

Seeds:

[
{x_0,g}.
]

All unary term functions (A	o A) are represented extensionally. There are exactly:

[
3^3=27
]

possible unary functions.

### Binary world

Seeds:

[
{x_0,x_1,g}.
]

All binary term functions (A^2	o A) are represented extensionally. There are exactly:

[
3^9=19{,}683
]

possible binary functions.

For reference ablation, repeat the binary closure from:

[
{x_0,x_1}
]

with no distinguished ground.

All closure calculations are exact finite subalgebra generation under pointwise application of (d).

## Exact symmetry reduction

To make the census computationally tractable without changing its mathematical content, quotient pointed nuclei by transformations that preserve exact closure cardinality and the frozen generativity measurements:

1. simultaneous permutation of the carrier labels by any (piin S_3), with:
   [
   gmapstopi(g),
   qquad
   d'( pi(a),pi(b))=pi(d(a,b));
   ]
2. swapping the two arguments of (d).

Each raw pointed nucleus is mapped to the lexicographically least canonical representative over this 12-element action.

For every representative record its exact orbit weight.

The total orbit weight must equal:

[
59{,}049.
]

A deterministic sample of raw pointed nuclei is recomputed directly and checked against its canonical representative to validate the quotient implementation.

## Fresh-difference measurement

For each representative:

1. compute exact unary closure with (g);
2. embed every unary function into the binary world by ignoring (x_1);
3. compute exact binary closure with (g);
4. count binary consequences not contained in the embedded unary closure.

Record:

[
Delta_E
=
|mathrm{Cl}(x_0,x_1,g)|
-
|mathrm{Embed}(mathrm{Cl}(x_0,g))|.
]

Fresh environmental difference reopens the reachable space iff:

[
Delta_E>0.
]

## Reference measurement

Compute:

[
Delta_g
=
|mathrm{Cl}(x_0,x_1,g)|
-
|mathrm{Cl}(x_0,x_1)|.
]

Also record whether every constant function is derivable without (g).

## Frozen generativity signature

A pointed nucleus satisfies the **transport-style generativity signature** iff all hold:

1. binary closure contains more than the distinct binary seeds;
2. fresh environmental difference adds at least one consequence:
   [
   Delta_E>0;
   ]
3. either:
   [
   Delta_g>0,
   ]
   or every constant function is internally derivable without (g).

This definition is fixed before seeing the census.

It does **not** require functional completeness.

## Strong generativity

After exact closure sizes are known, define the weighted 90th percentile (Q_{0.90}) of binary closure cardinality across all 59,049 raw pointed nuclei.

A pointed nucleus is **strongly generative** iff:

- it satisfies the frozen generativity signature; and
- its binary closure cardinality is at least (Q_{0.90}).

The percentile rule is fixed prospectively; its numerical threshold is an outcome.

## Structural features

For each canonical representative compute the following name-blind algebraic features.

### Symmetry / direction
- commutative;
- asymmetry score = number of unordered distinct pairs ({a,b}) with:
  [
  d(a,b)
eq d(b,a).
  ]

### Basic algebraic laws
- idempotent;
- associative;
- conservative:
  [
  d(a,b)in{a,b};
  ]
- two-sided cancellative;
- has any one-sided identity;
- has a two-sided identity;
- has any one-sided absorber;
- has a two-sided absorber.

### Reference-specific laws
- reference is a one-sided identity;
- reference is a two-sided identity;
- reference is a one-sided absorber;
- reference is a two-sided absorber;
- diagonal value (d(g,g)=g);
- image size of (d);
- diagonal image size.

### Order-theoretic signatures

Enumerate all six total orders on (A).

For each order test:

- isotone in both arguments;
- antitone in first and isotone in second;
- isotone in first and antitone in second.

Record:

- number of isotone orders;
- maximum of the two oriented residual counts;
- number of oriented-residual orders for which (g) is the top element.

These are structural measurements only. No feature is privileged as the expected answer.

## Predictor analysis

For every Boolean structural feature, weighted by orbit size, report:

- prevalence among all 59,049 pointed nuclei;
- prevalence among generative nuclei;
- prevalence among strongly generative nuclei;
- weighted mean binary closure size when feature is true;
- weighted mean binary closure size when feature is false;
- enrichment ratio in the strongly-generative class.

For integer features such as asymmetry score and residual-order count, report weighted closure distributions by exact feature value.

No machine-learning classifier is used in V1. The goal is transparent exact census statistics.

## Extremal outcomes

Report:

- maximum binary closure size;
- all canonical orbit representatives achieving the maximum;
- number of raw pointed nuclei in maximum orbits;
- number of functionally complete pointed nuclei:
  [
  |mathrm{Cl}|=19{,}683;
  ]
- whether any complete pointed nucleus remains complete without the reference;
- minimum nonzero reference delta among generative nuclei;
- maximum reference delta;
- maximum fresh-difference delta.

## Frozen gates

C1. All 59,049 raw pointed nuclei are covered exactly by canonical orbit weights.

C2. Every canonical representative has exact unary, binary-with-reference, and binary-without-reference closures.

C3. Every reported closure count is within the exact carrier-function bound.

C4. Deterministic canonicalization produces the same representative for every replayed raw pointed nucleus.

C5. At least 256 SHA256-selected raw pointed nuclei are directly recomputed and agree with their canonical representative on unary closure count, binary closure count, no-reference closure count, fresh-difference delta, and reference delta.

C6. Generativity signature is reported for every orbit representative and therefore every raw pointed nucleus.

C7. Weighted 90th-percentile threshold is computed from all 59,049 pointed nuclei.

C8. Structural features are computed for every orbit representative.

C9. Weighted predictor statistics are reported for every frozen Boolean feature.

C10. Exact distributions are reported for asymmetry score, isotone-order count, residual-order count, and reference-top residual-order count.

C11. Maximum binary closure and all maximizing orbits are reported.

C12. Functional-completeness count is reported exactly.

C13. Reference-dependence statistics are reported exactly.

C14. Fresh-difference statistics are reported exactly.

C15. At least one structural feature has a strongly-generative enrichment ratio different from 1.0, unless the census shows exact independence for every frozen feature.

C16. Deterministic aggregation hash reproduces from the complete set of shard outputs.

## Required reports, not positive-result gates

R1. Is noncommutativity enriched or depleted among strongly generative nuclei?

R2. Which asymmetry score has the highest weighted mean closure?

R3. Are residual-order signatures enriched among strongly generative nuclei?

R4. Is reference dependence enriched among strongly generative nuclei?

R5. Are any commutative pointed nuclei strongly generative?

R6. Are any zero-reference-delta pointed nuclei strongly generative?

R7. Do any pointed nuclei generate all 19,683 binary functions?

R8. If complete nuclei exist, do any remain complete with the reference removed?

R9. What minimal structural conjunction, among the frozen measured features, describes the largest strongly-generative enrichment without using semantic operation names?

R10. Does the exact census support:
- generic asymmetry;
- ordered directed residual;
- reference + directed residual;
- or no simple frozen structural family?

The answer is determined from the exact statistics and must not be chosen by intuition.

## Verdicts

- PASS_TERNARY_POINTED_NUCLEUS_CENSUS_V1
- PARTIAL_TERNARY_POINTED_NUCLEUS_CENSUS_V1
- VALID_NEGATIVE_TERNARY_POINTED_NUCLEUS_CENSUS_V1

PASS requires C1-C16.

## Claim boundary

A PASS establishes only an exact finite census of pointed binary algebras on a three-element carrier and transparent associations between frozen algebraic features and exact closure behaviour.

It does not establish causality from correlation, universal minimality, a physical law, a biological law, general intelligence, or substrate-independent completeness.

The target is narrower:

[
oxed{	extbf{What exact algebraic structure predicts generativity on the smallest non-Boolean census large enough to be exhaustive?}}
]
