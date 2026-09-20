# TERNARY POINTED NUCLEUS CENSUS V1 — analysis and execution addendum

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

This addendum fixes the exact aggregation and performance rules omitted from the main precommit. It changes no scientific candidate space.

## Sharding

Canonical pointed-operation orbits may be partitioned across CI shards by canonical integer key modulo the fixed shard count.

Each shard computes exact closure independently for its representatives and emits raw rows.

The aggregate result is valid only if:

- canonical orbit weights sum to 59,049;
- every canonical representative appears exactly once;
- all 256 frozen SHA256 audit raw keys are accounted for;
- every audit agrees with its canonical representative.

## Frozen audit keys

The 256 raw pointed nuclei are selected by repeatedly computing:

[
operatorname{SHA256}(	ext{"TPCV1-AUDIT|"}i)
]

taking the first 16 hex digits modulo 59,049, and retaining first occurrences until 256 distinct keys are obtained.

The resulting key list is compiled into the harness before outcome execution.

## Exact closure engine

Binary functions on the ternary carrier are encoded as 9-trit integers in ([0,19682]).

Closure uses exact pointwise table lookup under the candidate operation. It may stop early only when all 19,683 binary functions have been reached.

No sampling is permitted in closure computation.

## Boolean predictor enrichment

For Boolean feature (F), define:

[
E_F=
rac{P(Fmid	ext{strong})}{P(F)}
]

using raw-pointed-nucleus counts reconstructed from orbit weights.

If no strongly-generative nuclei exist, enrichment is reported undefined and C15 is evaluated by the exact-independence alternative in the main protocol.

## Integer-feature reports

For each exact value of:

- asymmetry score;
- isotone-order count;
- residual-order count;
- reference-top residual-order count;

report weighted:

- raw count;
- generative count;
- strongly-generative count;
- mean binary closure.

## R9 conjunction rule

Consider conjunctions of one, two, or three **positive** frozen Boolean structural features.

Require raw weighted support of at least 100 pointed nuclei.

For each conjunction compute strongly-generative enrichment:

[
E_C=
rac{P(Cmid	ext{strong})}{P(C)}.
]

Choose the conjunction with greatest (E_C), tie-breaking by:

1. fewer features;
2. greater strongly-generative support;
3. lexicographic feature-name sequence.

This is reported descriptively and is not a causal claim.

## R10 classification rule

Define:

- (E_{
eg comm}): enrichment of noncommutativity among strongly-generative nuclei;
- (E_{res}): enrichment of residual-order-count > 0;
- (E_{g-res}): enrichment of reference-top-residual-order-count > 0;
- (E_{ref}): enrichment of reference-delta > 0.

Report:

- **reference + directed residual** if (E_{g-res}ge1.5) and (E_{ref}ge1.2);
- else **ordered directed residual** if (E_{res}ge1.5);
- else **generic asymmetry** if (E_{
eg comm}ge1.5);
- else **no simple frozen structural family**.

These thresholds are frozen before outcome execution.
