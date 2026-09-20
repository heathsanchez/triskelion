# DISTINCTION THEORY ONE-SHOT V1 — prospective precommit

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

## Governing question

We now have exact developmental data for all 5,130 canonical pointed binary algebras on a 3-element carrier, plus exact distinction-transport dynamics.

The naming question can be made mathematical:

\[
\boxed{\textbf{Can the developmental phenotype be represented entirely in distinction-space, without needing the original object-first operation table?}}
\]

If yes, "Distinction Theory" is a serious candidate for the more fundamental layer.

If no, distinction dynamics is useful but not sufficient as the foundation.

## Population

Use the authoritative exact population:

- 5,130 canonical pointed-operation orbits;
- raw orbit weights sum to 59,049;
- all exact developmental metrics from TERNARY_DEVELOPMENTAL_NUCLEUS_CENSUS_V1;
- all exact distinction matrices from DISTINCTION_TRANSPORT_NUCLEUS_V1.

## Protected developmental phenotype

For each canonical orbit define the exact protected phenotype:

\[
\Phi_{\rm dev}
=
(
B,\ B_{\neg g},\ G_3,\ R_3,\ P_{\Sigma},\ M_C,\ M_G,\ M_R,\ J,\ \Pi
)
\]

where:

- \(B\): final binary closure cardinality;
- \(B_{\neg g}\): final binary closure without ground;
- \(G_3\): depth-3 semantic growth;
- \(R_3\): depth-3 recombinant count;
- \(P_{\Sigma}\): exact nine-start recurrence distinct-state sum;
- \(M_C\): count of 18 one-cell mutants remaining complete;
- \(M_G\): count remaining generative;
- \(M_R\): count remaining reference-independent;
- \(J\): joint-developmental membership;
- \(\Pi\): Pareto-frontier membership.

This phenotype is frozen before inspecting collisions.

## Three candidate representations

Let \(\Delta=\{(a,b):a\neq b\}\).

### D0 — Pure distinction dynamics

Use only the exact aggregate distinction-transfer matrix:

\[
C_{\delta,\delta'}
=
\#\{\tau:\tau(\delta)=\delta'\}
\]

canonicalized under all carrier relabelings.

No ground coloring is retained.

This is the strongest form of **pure Distinction Theory**.

### D1 — Pointed distinction dynamics

Use:

- the exact aggregate matrix \(C\);
- a color on each distinction indicating whether it touches the distinguished ground \(g\).

Canonicalize the colored matrix under all carrier relabelings.

This tests whether the irreducible object is **pointed distinction-space** rather than pure distinction-space.

### D2 — Full anonymous distinction action

For each of the six elementary translations:

\[
L_a(x)=d(a,x),\qquad R_a(x)=d(x,a),
\]

record its partial action on all oriented distinctions, with collapse represented by \(\bot\).

Discard the translation names and retain only the multiset of six distinction-action maps, plus the ground-touch coloring.

Canonicalize under all carrier relabelings.

Global left/right swap therefore changes nothing.

This is the richest representation still phrased entirely in distinction-space rather than by the original 3x3 operation table.

## Exact sufficiency criterion

A representation \(D_i\) is **developmentally sufficient under V1** iff every collision class under \(D_i\) is homogeneous in the full protected phenotype:

\[
D_i(x)=D_i(y)
\Longrightarrow
\Phi_{\rm dev}(x)=\Phi_{\rm dev}(y).
\]

No regression, threshold, classifier or approximation is allowed.

## Compression criterion

For each \(D_i\), report:

- number of unique signatures;
- number of collision classes;
- largest collision class;
- raw-weighted collision mass;
- whether the representation is injective on the 5,130 canonical operation orbits.

A sufficient representation is more interesting if it is non-injective, because then it has genuinely quotiented away object-level detail while preserving the protected developmental consequences.

## Reconstruction test

For D2, report whether the full canonical pointed operation orbit can be reconstructed injectively.

If D2 is injective, then it is an equivalent coordinate system for the original finite algebra, not yet evidence of compression.

If D2 is non-injective but phenotype-sufficient, that is stronger evidence for distinction-space as the right quotient.

## Frozen classification

Return exactly one:

1. **PURE_DISTINCTION_THEORY_SUPPORTED**
   if D0 is developmentally sufficient.

2. **POINTED_DISTINCTION_THEORY_SUPPORTED**
   if D0 fails but D1 is developmentally sufficient.

3. **ACTIONAL_DISTINCTION_THEORY_SUPPORTED**
   if D0 and D1 fail but D2 is developmentally sufficient.

4. **DISTINCTION_THEORY_NOT_SUFFICIENT_UNDER_V1**
   if D2 also fails.

This hierarchy is frozen prospectively.

## Strong one-shot criterion

Also report:

\[
\boxed{\texttt{STRONG\_DISTINCTION\_QUOTIENT}}
\]

iff the selected sufficient representation is non-injective on canonical operation orbits.

That means the distinction representation discards object-level differences while exactly preserving every protected developmental consequence.

Otherwise report:

\[
\boxed{\texttt{COORDINATE\_EQUIVALENCE\_ONLY}}
\]

if sufficiency requires an injective representation.

## Frozen gates

DT1. All 5,130 canonical operation orbits are evaluated.

DT2. Orbit weights sum exactly to 59,049.

DT3. D0 signatures are canonicalized under all six carrier relabelings.

DT4. D1 signatures are canonicalized under all six carrier relabelings with ground-touch coloring transported correctly.

DT5. D2 anonymous translation-action signatures are canonicalized under all six carrier relabelings.

DT6. Protected phenotype is reported for every orbit.

DT7. Exact collision classes are computed for D0.

DT8. Exact collision classes are computed for D1.

DT9. Exact collision classes are computed for D2.

DT10. Phenotype homogeneity is checked exhaustively within every D0 class.

DT11. Phenotype homogeneity is checked exhaustively within every D1 class.

DT12. Phenotype homogeneity is checked exhaustively within every D2 class.

DT13. Compression/injectivity statistics are reported for all three representations.

DT14. At least one explicit counterexample pair is reported for every insufficient representation.

DT15. 256 deterministic raw-vs-canonical symmetry audits reproduce D0, D1 and D2 exactly.

DT16. Deterministic aggregate hash reproduces exactly.

## Claim boundary

A positive result establishes only exact sufficiency for the frozen finite 3-element developmental phenotype.

It does not establish that all mathematics is fundamentally distinction theory.

But this one-shot asks the strongest useful finite question:

\[
\boxed{\textbf{Can we throw away the object-first representation and lose nothing developmental that we currently care about?}}
\]
