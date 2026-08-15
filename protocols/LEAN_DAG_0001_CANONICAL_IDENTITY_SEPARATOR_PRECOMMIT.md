# LEAN-DAG-0001 — Canonical identity / DAG separator precommit

Date frozen: 2026-08-16 NZST

Protocol: RGRS v1

## 0. Why this experiment is allowed

The current Lean programme has already shown a conditional evaluation regime: a recent mechanism produced a large Cedar improvement while performing very poorly on CSLib, and a more aggressive variant crossed semantic/completeness boundaries on larger suites. Under RGRS this blocks further global eager-vs-lazy tuning and promotes R5 Applicability / R4 Observability as active explanations.

Separately, prior profiling showed that environment canonicalization changes effective cache identity on a large fraction of complex inference calls and can greatly increase reuse. That is evidence for an R3 Redundancy / R8 Access hypothesis, but not yet sufficient to admit a full canonical DAG.

The canonical-DAG proposal is therefore allowed only as a separator experiment. It is not predeclared as the next architecture.

## 1. Primary residual

`rho = (R3 Redundancy, proof/environment identity boundary, repeated normalization/reconstruction and cache-key fragmentation among semantically equivalent structures, Lean checker hot path, medium confidence)`

Secondary competing residuals:

- R4 Observability: excess work may come primarily from forcing irrelevant structure, not identity fragmentation.
- R5 Applicability: the right mechanism may depend on workload shape.
- R12 Displacement: interning may simply move work into construction, hashing, memory retention, or GC.

## 2. Hypothesis

### H_DAG

A material part of the remaining checker cost comes from repeated work on semantically equivalent proof/environment structures that lack stable shared identity.

The smallest representation change is not “make everything a DAG”. It is:

> For one already-identified normalization/reconstruction boundary, assign canonical identity to equivalent immutable nodes and reuse the verified result by identity rather than reconstructing/re-normalizing the equivalent structure.

No evaluator eagerness policy may change in this experiment.

## 3. Strongest old-representation explanation

### H_OLD

The observed duplicate-looking work is incidental. Runtime differences are primarily caused by which branches/arguments are evaluated and by workload-specific evaluation regimes. Canonical identity will therefore either have negligible benefit or shift equal/greater cost into hashing, interning, lookup, retention, and GC.

## 4. Smallest separator question

> Holding evaluation policy fixed, does canonical identity at one high-duplication boundary causally reduce repeated verified-equivalent computations on the duplication-heavy workload while preserving low-duplication/control behavior and improving total cost?

This question separates R3/R8 from R4/R5 without changing both at once.

## 5. Frozen arms

All arms use the same checker commit, evaluator policy, compiler flags, PGO mode, corpus files, runner class, and verification procedure.

### D0 — instrumentation-only baseline

Current representation. Add counters only:

- nodes/keys presented to target boundary;
- unique structural values;
- repeated structurally equivalent values;
- target normalization/reconstruction invocations;
- target cache hits/misses;
- bytes/nodes retained by target representation if measurable.

No semantic behavior or caching policy changes.

### D1 — canonical identity

At exactly one frozen boundary:

1. canonicalize/intern immutable structures by a semantics-preserving structural key;
2. return stable shared identity for equal keys;
3. key the existing verified computation/reuse path by canonical identity;
4. preserve current evaluator forcing/eagerness decisions exactly.

### D2 — causal ablation

Retain D1's instrumentation and all surrounding code, but disable identity reuse at the final lookup/use point so equivalent structures are recomputed as under D0.

The canonicalization construction cost remains present in D2. This is deliberate: D1 vs D2 isolates reuse benefit, while D0 vs D1 measures total-system benefit including construction cost.

## 6. Frozen opposing discriminators

Minimum corpus:

1. **Cedar** — candidate duplication-heavy/favorable workload.
2. **CSLib** — opposing workload where broad recent mechanisms performed poorly.
3. **init-prelude** — small stable control for overhead and semantic drift.

If frozen Arena procedure requires additional standard suites for semantic validation, they may be added as semantic gates but may not replace the three separator workloads after seeing timing results.

## 7. Pre-run qualification gate

Before interpreting performance, D0 must establish that the chosen boundary actually has measurable duplicate-equivalent traffic on at least one discriminator.

Let:

`dup_ratio = (presented - unique) / max(1, presented)`.

Qualification requires either:

- `dup_ratio >= 0.10` on Cedar, or
- another pre-existing profiler counter demonstrates >=10% repeated equivalent target computations under the same frozen boundary.

If qualification fails, verdict is `NULL_NO_REDUNDANCY_AT_FROZEN_BOUNDARY`; do not build a broader DAG to rescue the hypothesis.

## 8. Frozen metrics

### Primary mechanism metric

Number of repeated target normalization/reconstruction computations.

D1 must reduce this relative to both D0 and D2.

### Primary resource metric

CPU time on the frozen workload procedure.

### Secondary resource metrics

- wall time;
- peak RSS;
- canonicalization/interning construction count/time;
- retained canonical node count/bytes if available;
- cache/identity lookup count.

No posthoc metric switching.

## 9. Semantic gate

All arms must produce identical verifier outcomes on the frozen semantic corpus.

Any false accept, false reject, missing dependency, environment mismatch, or changed decline state is R9 Soundness and immediate rejection regardless of speed.

## 10. Causal gate

Required mechanism pattern:

`D0 repeated_work = high`

`D1 repeated_work materially lower`

`D2 repeated_work returns toward D0`

A timing improvement without this counterfactual mechanism pattern does not validate H_DAG.

## 11. Total-cost / displacement gate

D1 is not a win merely because downstream target invocations fall.

For each workload compare total observed cost:

`C_total = C_construction + C_lookup + C_target_runtime + C_memory/GC proxy`.

Admission requires no material regression on CSLib or init-prelude under the frozen tolerance and a favorable aggregate resource result.

Initial frozen tolerance:

- no semantic regression anywhere;
- Cedar CPU improvement >= 5% versus D0;
- CSLib CPU regression <= 2%;
- init-prelude CPU regression <= 2%;
- peak RSS regression <= 5% on each discriminator unless CPU gain exceeds 10% and the follow-up total-cost protocol explicitly precommits a different tradeoff.

These thresholds are decision thresholds for this experiment, not universal architecture policy.

## 12. Decision table

### PASS_DAG_SEPARATOR

Requirements:

1. D0 qualifies redundancy at frozen boundary;
2. D1 materially reduces repeated target computations;
3. D2 restores those computations toward D0;
4. semantic gate passes;
5. resource/total-cost thresholds pass.

Next action: escalate the same representation to broader protected/Arena validation. Do not widen DAG scope yet.

### CONDITIONAL_DAG

D1 is causally effective but Cedar/CSLib remain incompatible under resource thresholds.

Primary residual becomes R5 Applicability. Next experiment searches for the smallest activation separator. Do not globally enable the DAG.

### DISPLACED_DAG

Repeated target work falls causally but total CPU/RSS is not improved because interning/hashing/retention absorbs the gain.

Primary residual R12 Displacement. Reject this representation at this boundary.

### NULL_DAG

Qualified duplicate traffic exists but D1 does not causally reduce target work or timing.

Reject H_DAG for this boundary and retain the negative law.

### NULL_NO_REDUNDANCY_AT_FROZEN_BOUNDARY

D0 does not show enough repeated equivalent traffic. Reject this boundary before intervention.

### REJECT_SOUNDNESS

Any semantic mismatch. Immediate R9 rejection.

## 13. Boundary robustness

If PASS_DAG_SEPARATOR occurs, one alternate reasonable identity boundary must be tested before making a broader “canonical DAG” claim.

At minimum compare:

- environment-level identity;
- one inner proof/expression node identity boundary.

The claim survives only if the gain is not an artifact of a single arbitrary key granularity, or if the narrower boundary is explicitly declared as the only supported scope.

## 14. What this experiment may prove

A pass supports:

> At the frozen checker boundary, stable canonical identity causally collapses repeated verified-equivalent computation and improves total checker cost under opposing workloads without changing semantics.

It does not prove:

- all proof terms should be globally hash-consed;
- canonical DAGs dominate laziness/observability mechanisms;
- the representation is universally optimal;
- identity reuse is free;
- the result generalizes outside the frozen checker/corpora.

## 15. RGRS next-state mapping

- PASS -> protected/Arena escalation.
- CONDITIONAL -> R5 activation-separator experiment.
- DISPLACED -> R12 cost-decomposition experiment or reject.
- NULL -> return to R4/R5 strongest alternative; do not widen DAG.
- SOUNDNESS -> reject immediately.

No outcome authorizes unconstrained “try more DAG variants” search.
