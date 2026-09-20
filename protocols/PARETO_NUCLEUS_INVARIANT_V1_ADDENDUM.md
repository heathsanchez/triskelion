# PARETO NUCLEUS INVARIANT V1 — exact-analysis addendum

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

This addendum resolves implementation details without changing the scientific question.

## Term enumeration

Atoms are ordered:

\[
g < x < y.
\]

Terms are ordered first by exact number of \(d\)-nodes and then lexicographically by fully parenthesized prefix serialization:

\[
d(s,t).
\]

Every ordered pair of smaller terms whose node counts sum to \(k-1\) generates a size-\(k\) term. No commutativity or semantic pruning is applied.

All terms with 0,1,2,3 d-nodes are included.

## Translation monoid

Unary transformations are represented extensionally as triples.

Composition convention:

\[
(f\circ h)(x)=f(h(x)).
\]

The translation monoid is the exact closure under composition of:

- identity;
- all three \(L_a\);
- all three \(R_a\).

The action is called transitive iff for every \(u,v\in A\), some monoid element maps \(u\) to \(v\).

## Row/column feature invariance

Because global argument swap exchanges rows and columns, the pair:

\[
(\text{sorted row image sizes},\text{sorted column image sizes})
\]

is itself sorted lexicographically before storage.

Row/column Hamming-distance extrema are taken over the union of all distinct-row pairs and all distinct-column pairs.

## Subalgebras and congruences

A nonempty proper subset \(S\subsetneq A\) is a subalgebra iff:

\[
a,b\in S\Rightarrow d(a,b)\in S.
\]

A congruence is one of the five equivalence relations induced by the five set partitions of a three-element carrier, and is counted iff compatible with \(d\).

“Simple” means exactly two congruences: equality and universal.

Automorphisms are carrier permutations preserving both \(d\) and the distinguished ground \(g\).

## Recurrence-map basins

For:

\[
T(a,b)=(b,d(a,b)),
\]

a basin is one weak functional-graph component containing one directed cycle.

Maximum basin size is the largest component cardinality.

The reported recurrence signature stores the lexicographically sorted pair of the full feature tuple for \(d\) and \(d^{op}\).

## Identity prevalence

Raw-weighted prevalence is calculated by the prior orbit weights.

“Exclusive to Pareto” means the identity property holds on all 16 Pareto canonical orbits and on no other complete canonical orbit.

## Audit selection

Select 256 distinct raw pointed keys by iterating:

\[
h_i=\operatorname{SHA256}(\text{"PINV1-AUDIT|"}i),
\]

taking the first 16 hexadecimal digits modulo 59,049, and retaining first occurrences until 256 keys are obtained.

For each audit key compare the raw pointed algebra against its canonical representative.

## Separator scalar set

P1/P2 scalar comparisons include:

- distinct translation count;
- bijective translation count;
- constant translation count;
- minimum/maximum/mean translation image size;
- translation monoid size;
- ground orbit size;
- permutation row+column count;
- constant row+column count;
- minimum/maximum row/column Hamming distance;
- distinct pointed-minor count;
- proper subalgebra count;
- pointed proper subalgebra count;
- congruence count;
- pointed automorphism-group size;
- recurrence cycle count pair mean;
- recurrence maximum-cycle pair mean;
- recurrence cyclic-state pair mean;
- recurrence maximum-basin pair mean.

Boolean prevalence comparisons include translation transitivity, simple algebra, absence of pointed proper subalgebra, pointed-minor permutation/constant, and recurrence bijectivity.
