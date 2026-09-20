# STRUCTURAL AUDIT + PHENOTYPE SPLIT V1 — prospective precommit

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

## Purpose

Audit the previous minimal-structural-sufficiency result before interpreting or naming it.

This experiment has three independent targets:

1. independently recompute the developmental measurements that can be recomputed directly from the pointed operation;
2. independently test whether V4 reconstructs the original pointed operation orbit rather than merely correlating with it;
3. separate measurement families to determine which families force injectivity.

No ontological interpretation is preregistered.

## Population

Use the authoritative 5,130 canonical pointed-operation representatives from the ternary pointed census, with raw orbit weights summing to 59,049.

Use the previously recorded developmental census only as the comparison target for audit, not as the source of recomputed values.

## A. Independent developmental measurement audit

Recompute in fresh Python code directly from each operation table:

### A1. Depth-bounded semantic growth

From seeds:

\[
S_0=\{x_0,x_1,g\}
\]

compute synchronously:

\[
S_{r+1}=S_r\cup\{d(f,h):f,h\in S_r\}
\]

for \(r=0,1,2\), recording:

\[
(d_0,d_1,d_2,d_3).
\]

### A2. Depth-3 two-coordinate dependence

For every function in \(S_3\), test essential dependence on both coordinates and count:

\[
R_3.
\]

### A3. Recurrence metrics

For each of the nine ordered semantic seed pairs from \(\{x_0,x_1,g\}\), iterate pointwise:

\[
(a_t,b_t)\mapsto(b_t,d(a_t,b_t)).
\]

Record exactly:
- distinct-state sum;
- distinct-state max;
- cycle-length sum;
- cycle-length max.

### A4. Mutation-neighborhood audit

Independently enumerate the 18 one-cell mutants for each representative and independently canonicalize every mutant.

The mutant's completeness/generativity/reference-independence labels may be looked up in the authoritative *pointed census* because recomputing the full 19,683-function closure for every mutation is outside this audit's intended cost.

Therefore this audit independently checks:
- all 18 mutations are enumerated;
- every mutant canonicalizes to the expected pointed-census orbit;
- the three mutation counts are reproduced from that independent enumeration + authoritative pointed labels.

It does **not** independently re-prove the pointed census's completeness/generativity classifications.

### A5. Cross-check

Compare every recomputed field against the authoritative developmental-census row.

Report mismatch counts and first mismatch for every field.

A clean audit requires zero mismatches on:
- d0,d1,d2,d3;
- recombinant3;
- recurrence fields;
- mutation_complete;
- mutation_generative;
- mutation_ref_independent.

## B. V4 reconstruction audit

For each pointed operation \((A,g,d)\), define:

\[
L_c(x)=d(c,x),\qquad R_c(x)=d(x,c).
\]

V4 retains, for each generator \(c\), the unordered pair:

\[
\{L_c,R_c\},
\]

plus the pointed carrier structure, quotienting carrier relabeling and global transpose.

Independently reconstruct candidate operations from V4 as follows:

1. For each \(c\), choose one of the two maps in \(\{L_c,R_c\}\) as the provisional left map.
2. The other becomes the provisional right map.
3. Keep only orientation assignments satisfying the consistency equations:
   \[
   L_a(b)=R_b(a)\quad\forall a,b\in A.
   \]
4. Build every consistent operation table.
5. Canonicalize every reconstructed pointed table under carrier relabeling + global transpose.
6. Compare the resulting canonical-orbit set with the source canonical orbit.

Report for every source orbit:
- number of consistent orientation assignments;
- number of reconstructed canonical operation orbits;
- whether the source orbit is the unique reconstructed orbit.

The decisive reconstruction audit is:

\[
\boxed{\text{every V4 object reconstructs exactly one canonical pointed-operation orbit}.}
\]

If true, V4 is a lossless coordinate representation in this census, not a nontrivial quotient.

## C. Phenotype-family split

Do not bundle all measurements into one phenotype.

For every frozen view V0–V5 from MINIMAL_STRUCTURAL_SUFFICIENCY_ONE_SHOT_V1, evaluate exact collision-class homogeneity separately for the following frozen measurement families.

### F1 — final semantic reach

\[
(\texttt{binary},\texttt{no_ground})
\]

These are final closure cardinalities only. This family does not claim equality of exact closure sets.

### F2 — bounded derivational geometry

\[
(d_0,d_1,d_2,d_3,R_3)
\]

### F3 — recurrence dynamics

\[
(
\texttt{recur_distinct_sum},
\texttt{recur_distinct_max},
\texttt{recur_cycle_sum},
\texttt{recur_cycle_max}
)
\]

### F4 — mutation neighborhood

\[
(
\texttt{mutation_complete},
\texttt{mutation_generative},
\texttt{mutation_ref_independent}
)
\]

### F5 — operational-without-presentation-neighborhood

\[
F1\cup F3
\]

This intentionally excludes bounded derivational depth and one-cell mutation geometry.

### F6 — intrinsic-current-run bundle

\[
F1\cup F2\cup F3
\]

This excludes mutation-neighborhood measurements.

### F7 — full primary measurements

\[
F1\cup F2\cup F3\cup F4
\]

Derived percentile/ranking labels (joint-developmental and Pareto membership) are excluded from all family definitions because they are downstream functions of the primary measurements.

## C2. Exact criterion

For each view/family pair:

\[
V_i(x)=V_i(y)
\Longrightarrow
F_j(x)=F_j(y).
\]

Report:
- heterogeneous collision classes;
- first counterexample;
- whether sufficient.

For each family report the minimal sufficient view(s) under the same frozen lattice:

- V0 < V1 < V3 < V5
- V0 < V2 < V3 < V5
- V0 < V1 < V4 < V5
- V0 < V2 < V5
- V4 < V5

## Frozen gates

SA1. 5,130 canonical representatives audited.
SA2. Raw orbit weights sum to 59,049.
SA3. Independent d0–d3 recomputation completed for all representatives.
SA4. Independent R3 recomputation completed for all representatives.
SA5. Independent recurrence recomputation completed for all representatives.
SA6. Independent 18-mutation enumeration/canonicalization completed for all representatives.
SA7. Zero mismatches in all audited developmental fields.
SA8. V4 reconstruction attempted for all representatives.
SA9. Every V4 reconstruction contains the source canonical orbit.
SA10. V4 reconstruction uniqueness reported for all representatives.
SA11. F1–F7 evaluated for V0–V5.
SA12. Exact minimal sufficient view set reported for each family.
SA13. Derived joint/Pareto labels excluded from family tests.
SA14. At least one counterexample reported for every insufficient view/family pair where a collision exists.
SA15. 256 deterministic symmetry audits reproduce V0–V5 signatures.
SA16. Two independently constructed result payloads have identical aggregate hashes.

## Verdicts

- PASS_STRUCTURAL_AUDIT_PHENOTYPE_SPLIT_V1
- PARTIAL_STRUCTURAL_AUDIT_PHENOTYPE_SPLIT_V1

PASS requires SA1–SA16.

## Claim boundary

A PASS audits the recorded finite measurements and identifies which frozen measurement families require which frozen structural views.

It does not identify a universal primitive, ontology, foundation, or theory name.

It also does not independently re-prove the prior pointed census's exhaustive final-closure classifications used by the mutation-neighborhood lookup.
