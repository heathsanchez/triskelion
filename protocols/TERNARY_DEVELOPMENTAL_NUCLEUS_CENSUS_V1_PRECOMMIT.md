# TERNARY DEVELOPMENTAL NUCLEUS CENSUS V1 — prospective precommit

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

## Governing question

The exact ternary pointed census showed that raw functional generativity is common:

- 59,049 pointed binary algebras on A={0,1,2};
- 49,323 satisfied the frozen transport-style generativity signature;
- 24,534 were fully complete over all 19,683 binary functions.

Therefore closure size alone is not a useful discriminator of a developmental nucleus.

This experiment asks:

\[
\boxed{\textbf{Among equally expressive nuclei, which are minimal, fast-growing, recurrently persistent, and robust to local perturbation?}}
\]

The goal is not to invent another architecture. It is to measure developmental behaviour intrinsic to the pointed operation itself.

## Candidate space

Reuse the exact 5,130 symmetry-orbit representatives and orbit weights from the prior authoritative ternary pointed census result.

These exactly cover all 59,049 raw pointed nuclei.

No candidate is selected by semantic name.

## Frozen developmental metrics

For each canonical pointed nucleus \((A,g,d)\):

### D1. Bounded semantic growth profile

In the binary world begin with:

\[
S_0=\{x_0,x_1,g\}.
\]

Define synchronous bounded closure:

\[
S_{r+1}
=
S_r\cup\{d(f,h):f,h\in S_r\}.
\]

Compute exact distinct semantic function counts for:

\[
|S_0|,\ |S_1|,\ |S_2|,\ |S_3|.
\]

The depth-3 count is the frozen **early semantic growth** metric.

This is deliberately bounded at depth 3 to avoid conflating intrinsic early generativity with exhaustive fixed-point size.

### D2. Early recombinant consequence count

Within \(S_3\), count functions that depend essentially on both environmental coordinates.

A binary function \(f(x_0,x_1)\) is essential in \(x_0\) iff some fixed \(x_1\) value admits two \(x_0\) values with different outputs; analogously for \(x_1\).

Record:

\[
R_3=
|\{f\in S_3:f\text{ depends essentially on both }x_0,x_1\}|.
\]

This is the frozen early recombination metric.

### D3. Deterministic recurrence persistence

For each of the nine ordered seed pairs from:

\[
B=\{x_0,x_1,g\},
\]

iterate:

\[
(a_t,b_t)\mapsto
(b_t,d(a_t,b_t)).
\]

Because the semantic pair state is finite, every trajectory eventually repeats.

For all nine starts record exactly:

- preperiod;
- cycle length;
- total distinct pair states before repeat.

Aggregate:

- mean distinct pair states;
- maximum distinct pair states;
- mean cycle length;
- maximum cycle length.

No environmental injection, archive, promotion or learned policy is used.

### D4. Local mutation robustness

A binary operation has 9 table cells. Each cell can be changed to either of the other two carrier values, giving exactly:

\[
18
\]

single-cell mutations.

For each pointed nucleus, use the already completed exhaustive census to look up every one-cell mutant with the same reference.

Record the fractions of 18 mutants that preserve:

1. full binary completeness;
2. the frozen transport-style generativity signature;
3. reference independence (\(\Delta_g=0\)).

This requires no sampled mutation and no new semantic assumption.

### D5. Reference minimality

Reuse exact census outcomes:

- complete with reference?
- complete without reference?
- reference delta;
- whether all constants are internally derivable without the reference.

A complete pointed nucleus is **reference-minimal** iff it is complete with \(g\) and not complete without \(g\).

A complete operation is **reference-free complete** iff it remains complete after removing \(g\).

No preference is assumed in advance; both classes are reported separately.

## Frozen comparison population

The primary comparison population is the 24,534 raw pointed nuclei that are fully complete with reference.

This controls for final expressive power.

All percentile thresholds below are computed using raw-pointed-nucleus weighting from orbit sizes.

## Frozen developmental thresholds

Within the complete population compute weighted quartiles for:

- depth-3 semantic growth \(G_3=|S_3|\);
- early recombinant count \(R_3\);
- mean recurrent distinct-pair-state count \(P\);
- completeness-preserving mutation fraction \(M\).

A complete nucleus is in the **joint developmental class** iff it is at or above the weighted 75th percentile on all four metrics:

\[
G_3\ge Q_{.75}(G_3),
\quad
R_3\ge Q_{.75}(R_3),
\quad
P\ge Q_{.75}(P),
\quad
M\ge Q_{.75}(M).
\]

This rule is fixed prospectively. Numerical thresholds are outcomes.

Two subclasses are then reported:

- joint developmental + reference-minimal;
- joint developmental + reference-free complete.

## Frozen structural analyses

Using the exact structural features already frozen in the prior census, report their weighted enrichment in the joint developmental class versus all complete nuclei.

For each Boolean feature:

- prevalence among complete nuclei;
- prevalence among joint-developmental nuclei;
- enrichment ratio.

For integer features:

- asymmetry score;
- isotone-order count;
- residual-order count;
- reference-top-residual-order count;

report weighted means in:

- all complete nuclei;
- joint-developmental nuclei.

## Frozen ablations / separators

### A. Closure-only separator

Compare joint-developmental nuclei with complete nuclei outside the joint class.

Because both groups have identical final closure size \(19,683\), any measured difference cannot be attributed to final functional completeness.

### B. Reference separator

Compare developmental metrics between:

- reference-minimal complete nuclei;
- reference-free complete nuclei.

### C. Mutation separator

Compare early growth and recurrence persistence for complete nuclei above vs below the median mutation-completeness fraction.

### D. Commutativity separator

Report whether commutative complete nuclei can enter the joint developmental class.

No direction is preregistered as preferred.

## Extremal reports

Report:

- maximum depth-3 closure;
- maximum early recombinant count;
- maximum recurrent distinct-pair-state count;
- maximum completeness-preserving mutation fraction;
- all canonical orbits simultaneously maximizing each metric;
- all Pareto-undominated complete canonical orbits across:
  \[
  (G_3,R_3,P,M),
  \]
  maximizing all four.

## Frozen gates

DVC1. All 5,130 canonical pointed-orbit representatives are evaluated.

DVC2. Orbit weights still sum exactly to 59,049 raw pointed nuclei.

DVC3. Every representative has exact depth-0 through depth-3 semantic closure counts.

DVC4. Every representative has an exact early recombinant count.

DVC5. Every representative has exact recurrence metrics for all 9 frozen seed-pair starts.

DVC6. Every representative has all 18 one-cell mutations resolved through the prior exhaustive census.

DVC7. Mutation-lookup canonicalization reproduces prior orbit representatives deterministically.

DVC8. Complete-population raw weight is exactly 24,534, matching the prior census.

DVC9. All four weighted 75th-percentile thresholds are computed from the complete population.

DVC10. Joint developmental membership is reported for every complete orbit representative.

DVC11. Reference-minimal and reference-free joint subclasses are both reported exactly, even if one is empty.

DVC12. Frozen structural enrichment statistics are reported for every prior Boolean structural feature.

DVC13. Frozen integer structural summaries are reported for all four prior integer features.

DVC14. All four frozen separators A-D are reported.

DVC15. Exact Pareto-undominated complete orbits are reported.

DVC16. Deterministic aggregation hash reproduces exactly.

## Required reports, not positive-result gates

R1. What fraction of functionally complete nuclei are in the joint developmental class?

R2. Are reference-minimal or reference-free complete nuclei more prevalent in the joint developmental class?

R3. Does asymmetry materially enrich among the joint developmental class after conditioning on completeness?

R4. Do residual-order signatures materially enrich after conditioning on completeness?

R5. Can commutative nuclei be joint-developmental?

R6. What operation/reference structural features show the strongest enrichment after controlling for final closure?

R7. How many complete nuclei are robust to at least 9/18 one-cell mutations remaining complete?

R8. Does early semantic growth correlate with mutation robustness, recurrence persistence, both, or neither?

R9. Are the original hand-picked H3/K3/T3 transport operations developmentally unusual relative to the full complete population? If any are not complete and therefore outside the primary population, report that rather than forcing a comparison.

R10. Does the developmental census support a narrow nucleus family, or does developmental usefulness remain broadly distributed?

## Verdicts

- PASS_TERNARY_DEVELOPMENTAL_NUCLEUS_CENSUS_V1
- PARTIAL_TERNARY_DEVELOPMENTAL_NUCLEUS_CENSUS_V1
- VALID_NEGATIVE_TERNARY_DEVELOPMENTAL_NUCLEUS_CENSUS_V1

PASS requires DVC1-DVC16.

## Claim boundary

A PASS establishes only an exact finite developmental census on the three-element carrier under the frozen bounded-growth, recurrence and one-cell-mutation metrics.

It does not establish universal minimality, intelligence, open-ended evolution, causality from feature enrichment, or a domain-independent law.

The target is:

\[
\boxed{\textbf{After controlling for final expressive power, what actually distinguishes developmental behaviour?}}
\]
