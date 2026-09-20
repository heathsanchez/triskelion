# TERNARY DEVELOPMENTAL NUCLEUS CENSUS V1 — analysis addendum

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

This addendum fixes aggregation details left implicit by the main precommit. It changes no candidate space or developmental metric.

## Quartiles

All quartiles are weighted by raw-pointed-nucleus orbit weight.

For metric \(X\), \(Q_{.75}(X)\) is the smallest observed value whose cumulative raw weight reaches at least 75% of the complete-population raw weight.

Ties at the threshold are included.

For mutation completeness fraction, use the exact numerator in \(\{0,\dots,18\}\); division by 18 is only presentation.

## Recurrence aggregation

For each of the nine ordered seed-function pairs, recurrence is exact.

Because the operation acts pointwise, the global pair-state trajectory is computed from the nine carrier-pair trajectories. If local coordinate \(i\) has preperiod \(\mu_i\) and period \(\lambda_i\), then:

\[
\mu=\max_i\mu_i,
\qquad
\lambda=\operatorname{lcm}_i\lambda_i,
\qquad
\text{distinct states}=\mu+\lambda.
\]

This is exact, not a truncation.

The primary recurrence metric \(P\) is the arithmetic mean of the nine exact distinct-state counts.

## Mutation robustness

For each canonical representative, all 18 one-cell mutants are formed on that representative table with the same representative ground.

Each mutant is canonicalized under the prior census symmetry action and looked up in the authoritative prior census.

The multiset of 18 outcomes is invariant under carrier relabeling and argument swap, so the representative metric is assigned to the full raw orbit weight.

## Weighted correlations for R8

Within the complete population, compute raw-weighted Pearson correlations:

\[
\rho(G_3,M)
\]

and

\[
\rho(G_3,P).
\]

Report:
- **both** if both absolute correlations are at least 0.20;
- **mutation robustness** if only \(|\rho(G_3,M)|\ge0.20\);
- **recurrence persistence** if only \(|\rho(G_3,P)|\ge0.20\);
- **neither** otherwise.

The sign and exact coefficient are always reported.

## Structural enrichment

For each frozen Boolean structural feature \(F\):

\[
E_F=
\frac{P(F\mid\text{joint developmental})}{P(F\mid\text{complete})}.
\]

Features absent from the complete population have undefined enrichment.

R3 reports the enrichment of noncommutativity.

R4 reports the ratio of mean residual-order-count in the joint class to that in the complete population, with both means also reported.

R6 names the Boolean feature with largest defined enrichment, tie-breaking lexicographically.

## R10 narrow-versus-broad rule

Report **narrow measured family** iff both hold:

1. joint-developmental raw prevalence among complete nuclei is at most 10%;
2. at least one frozen Boolean structural feature has enrichment at least 1.5.

Otherwise report **developmental usefulness broadly distributed under frozen metrics**.

This is a descriptive census label only, not a universal claim.

## Pareto rule

Among complete canonical representatives, orbit \(a\) dominates orbit \(b\) iff it is at least as high on all four:

\[
(G_3,R_3,P,M)
\]

and strictly higher on at least one.

Report every undominated canonical representative and its raw orbit weight.
