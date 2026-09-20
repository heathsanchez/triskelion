# NUCLEUS TRANSPORT V1 — prospective precommit

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

## Governing question

The Boolean candidate nucleus is:

[
oxed{	ext{reference}+	ext{directed distinction}}
]

with Boolean realization:

[
g=1,qquad D(a,b)=
eg aland b.
]

This experiment asks whether the same *structural pattern* remains developmentally generative in finite non-Boolean algebras, or whether the observed effect is specific to Boolean / powerset structure.

No claim of domain-independence is assumed.

## General setup

Each world is a finite pointed algebra:

[
(A,g,d)
]

with:

- carrier A;
- distinguished reference g;
- binary directed operation d:A×A→A;
- independent environmental projections x_i.

Terms are generated only by:

[
t ::= g mid x_i mid d(t,t).
]

For arity n, every n-ary term is evaluated exactly on all (|A|^n) inputs and represented extensionally.

For each world and n=1,2 record:

- exact closure cardinality;
- total number of possible n-ary functions;
- closure fraction;
- closure rounds;
- whether every constant function is derivable;
- whether removing g lowers closure;
- whether adding a second independent environmental projection strictly enlarges closure;
- deterministic closure hash.

The Boolean baseline is additionally checked at n=3.

## Frozen worlds

### B — Boolean directed difference
Carrier {0,1}; g=1.

[
d(a,b)=
eg aland b.
]

This is the established Boolean realization.

### H3 — three-element Heyting chain
Carrier {0,1,2}, ordered 0<1<2; g=2.

Meet is min. Heyting negation on this chain is:

[

eg 0=2,quad 
eg 1=0,quad 
eg 2=0.
]

Define:

[
d(a,b)=min(
eg a,b).
]

This is the literal (
eg aland b) construction in a non-Boolean Heyting algebra.

### K3 — three-valued involutive chain
Carrier {0,1,2}; g=2.

Negation:

[

eg a=2-a.
]

Meet is min.

Define:

[
d(a,b)=min(2-a,b).
]

This preserves an involutive negation but drops Boolean complement laws.

### T3 — truncated directed difference
Carrier {0,1,2}; g=2.

[
d(a,b)=max(0,b-a).
]

This is an order-residual interpretation of “what remains in b relative to a”.

### Z3 — cyclic directed difference
Carrier (mathbb Z_3); g=0.

[
d(a,b)=b-apmod 3.
]

This preserves orientation but lives in a group rather than an ordered/Boolean algebra.

## Frozen symmetric controls

Each non-Boolean world gets one paired symmetric control with the same carrier and reference.

### H3-control
[
s(a,b)=min(a,b).
]

### K3-control
[
s(a,b)=min(a,b).
]

### T3-control
[
s(a,b)=|b-a|.
]

### Z3-control
[
s(a,b)=a+bpmod 3.
]

These controls are descriptive comparisons only. They are not assumed inferior.

## Representation-invariance sanity check

For the Boolean world, compute the exact same closures twice:

1. truth tables as bit vectors;
2. truth tables as sets of satisfying input rows.

The two implementations must agree exactly on closure cardinality and hash.

This is only a representation check; it is not counted as cross-substrate evidence.

## Fresh-difference test

For each world:

1. compute the unary closure generated from x0 and g;
2. compute the binary closure generated from x0,x1 and g;
3. embed every unary term into the binary world by ignoring x1;
4. record whether binary closure contains consequences not in that embedded unary closure.

This is the exact finite version of:

[
	ext{closed local structure}+	ext{fresh environmental coordinate}	o	ext{new reachable consequences}.
]

## Reference-ablation test

Repeat each world with g removed.

Record:

[
Delta_g = |mathrm{Cl}(x_0,x_1,g)|-|mathrm{Cl}(x_0,x_1)|.
]

Reference is causal only when (Delta_g>0).

## Cross-world structural signature

For a non-Boolean directed world, call the candidate pattern **transported** under this protocol iff all hold:

1. closure strictly exceeds the seed set;
2. fresh environmental difference strictly enlarges closure;
3. exact deterministic replay holds;
4. the directed operation is not extensionally identical to its symmetric control;
5. either reference ablation lowers closure or all constants are internally derivable without the reference.

This is deliberately weaker than functional completeness.

The experiment does not require every transported world to be complete.

## Frozen gates

T1. All five directed worlds and four controls are evaluated exactly at n=1,2.

T2. Boolean directed world is evaluated exactly at n=3.

T3. Deterministic replay reproduces all closure hashes.

T4. Boolean bit-vector and set implementations agree exactly.

T5. Boolean directed world is complete at n=1,2,3 with reference.

T6. Every reported closure count is <= the exact total function count.

T7. Fresh-difference result is reported for every directed world.

T8. Reference-ablation delta is reported for every directed world.

T9. Directed-vs-symmetric closure comparison is reported for every non-Boolean substrate.

T10. At least one non-Boolean directed world satisfies the frozen transported signature.

T11. Report exactly which non-Boolean worlds satisfy the transported signature.

T12. Report whether all transported worlds share reference dependence.

T13. Report whether any transported world derives every constant without g.

T14. Report whether directed operations outperform, tie, or underperform their paired symmetric controls in closure cardinality; no post-hoc winner rule.

T15. No semantic names influence closure or ranking.

T16. Explicitly report whether the evidence supports only a Boolean/powerset nucleus or a broader reference+directed-difference hypothesis under this protocol.

## Verdicts

- PASS_NUCLEUS_TRANSPORT_V1
- PARTIAL_NUCLEUS_TRANSPORT_V1
- VALID_NEGATIVE_NUCLEUS_TRANSPORT_V1

PASS requires T1-T10. T11-T16 are required reported outcomes, not positive-result requirements.

## Claim boundary

A PASS would establish only that the abstract pointed-operation pattern shows the frozen generativity signature in at least one exact finite non-Boolean algebra.

It would not establish a universal developmental nucleus, physical law, biological law, general intelligence principle, or substrate-independent completeness.

The scientific target is:

[
oxed{	extbf{Does reference + directed distinction survive outside Boolean algebra at all?}}
]
