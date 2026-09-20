# RETROSPECTIVE NUCLEUS PURIFICATION V1 — prospective precommit

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

## Governing question

Can the protected end consequences of a developed exact system be used retrospectively to remove unnecessary structure from its beginning, without confusing end accuracy with developmental minimality?

The frozen rule is:

\[
\boxed{\text{grow forward} \rightarrow \text{test protected end consequences} \rightarrow \text{compress backward} \rightarrow \text{regrow}}
\]

The target is not an ultimate metaphysical primitive. The target is the **minimum sufficient generative nucleus under the frozen worlds and protected developmental signature**.

This experiment is downstream of NUCLEUS_TRANSPORT_V1, whose authoritative result hash is:

b68ff7c70c8685f98d671367b1f536dba64664a16d0b64aa555d97091a3c2d1f

and whose exact directed binary closure counts were:

- B: 16
- H3: 22
- K3: 84
- T3: 3888
- Z3: 9

The transported protected worlds are frozen as:

\[
\boxed{\mathrm{B},\mathrm{H3},\mathrm{K3},\mathrm{T3}}
\]

Z3 remains a contrast world because the previous transport experiment did not classify it as reference-dependent transport.

## Frozen constitution

For each world, the full developmental constitution is:

\[
(g,D;\mathrm{Cl},E)
\]

where:

- G is the distinguished reference;
- D is the frozen directed operation;
- Cl permits recursively generated outputs to re-enter composition;
- E supplies two independent environmental projections x0,x1.

External warrant is exact extensional equality over the entire finite input space. It is not a candidate primitive and is not ablated.

For arity 2 the full term system is:

\[
t ::= g \mid x_0 \mid x_1 \mid D(t,t)
\]

closed to a fixed point.

The protected end consequence is the **exact extensional closure set**, not merely its cardinality.

## Frozen worlds

Exactly the same worlds and operations as Nucleus Transport V1:

### B
Carrier {0,1}, g=1,

\[
D(a,b)=\neg a\land b.
\]

### H3
Carrier {0,1,2}, g=2, three-element Heyting chain,

\[
D(a,b)=\min(\neg a,b),\quad \neg0=2,\ \neg1=\neg2=0.
\]

### K3
Carrier {0,1,2}, g=2,

\[
D(a,b)=\min(2-a,b).
\]

### T3
Carrier {0,1,2}, g=2,

\[
D(a,b)=\max(0,b-a).
\]

### Z3
Carrier Z3, g=0,

\[
D(a,b)=b-a\pmod 3.
\]

## Retrospective ablations

Each ablation is compared against the exact full closure set.

### -G: remove reference

Use only x0,x1,D,Cl.

Record exact closure, loss cardinality, retained fraction, and a canonical missing consequence witness.

### -D: remove directed operation

Use only g,x0,x1.

No higher construction is permitted.

### -R: remove recursive re-entry

Keep g,x0,x1,D, but allow exactly one application layer:

\[
S_1=S_0\cup\{D(a,b):a,b\in S_0\}
\]

with no generated child allowed to become a parent.

### -E: remove fresh second environmental distinction

Generate the exact unary closure from g,x0,D,Cl, embed it into the binary world by ignoring x1, and compare with the full binary closure.

## Reference sweep

For every world, replace the distinguished reference by every carrier element and compute exact closure.

Record exactly which references reproduce the protected full closure.

Also record whether the original reference constant is derivable in the no-ground closure.

## Orientation sanity

Replace D(a,b) by D-rev(a,b)=D(b,a).

Because the term language allows arbitrary ordered arguments, exact closure should be unchanged. This tests that the claim is about **asymmetry/directed difference as a class**, not an arbitrary naming of left and right.

## End-accuracy underdetermination control

In the Boolean world only, exhaustively test all 16 binary Boolean relations with the same explicit reference g=1.

Record every relation whose exact binary closure equals the protected D+ground closure.

This is a required control: if multiple distinct operators reproduce the same end consequence set, then final computation accuracy alone cannot uniquely identify the nucleus.

No semantic name may influence this enumeration.

## Retrospective QCK minimizer

Treat the four frozen ingredients as:

- nucleus candidates: G, D
- developmental conditions: R, E

A component is retrospectively removable only if deleting it preserves the exact protected closure in **all four protected worlds** B/H3/K3/T3.

The minimizer reports:

1. retained nucleus components;
2. retained developmental conditions;
3. world-specific exceptions;
4. exact consequence witnesses proving necessity.

No component may be retained merely because it was present historically.

## Frozen gates

P1. Reproduce the parent Nucleus Transport V1 binary closure counts for all five worlds exactly.

P2. Exact closure sets and hashes replay deterministically.

P3. Every protected world grows beyond its raw seed set.

P4. Removing G loses at least one protected end consequence in every protected world.

P5. Removing D loses at least one protected end consequence in every protected world.

P6. Removing recursive re-entry R loses at least one protected end consequence in every protected world.

P7. Removing fresh environmental coordinate E loses at least one protected end consequence in every protected world.

P8. Reversing the argument orientation of D preserves the exact full closure in every world.

P9. At least one protected world rejects at least one alternative reference value.

P10. The original distinguished reference is not derivable from the no-ground closure in every protected world.

P11. Boolean end-accuracy is underdetermined: at least two distinct binary relations with ground 1 reproduce the exact protected Boolean end closure.

P12. The retrospective minimizer retains both G and D across the protected worlds.

P13. The retrospective minimizer separately reports R and E as developmental conditions rather than silently promoting them into the nucleus.

P14. Every retained component has at least one exact canonical missing-consequence witness under ablation.

P15. Z3 is reported separately and cannot override the frozen protected-world classification.

P16. The result explicitly distinguishes end-consequence sufficiency, developmental sufficiency, and universal/ontological minimality, which is not claimed.

## Verdicts

- PASS_RETROSPECTIVE_NUCLEUS_PURIFICATION_V1
- PARTIAL_RETROSPECTIVE_NUCLEUS_PURIFICATION_V1
- VALID_NEGATIVE_RETROSPECTIVE_NUCLEUS_PURIFICATION_V1

PASS requires P1–P16.

## Claim boundary

A PASS would establish only that, under these exact finite pointed algebras and this frozen protected developmental signature, backward QCK-style ablation retains the reference and directed operation while also requiring recursive closure and environmental novelty as contextual developmental conditions.

It would **not** establish that (g,D) is universally irreducible, that final accuracy uniquely determines a seed, or that the same nucleus governs arbitrary mathematical, physical, biological, or intelligent systems.

The scientific target is:

\[
\boxed{\textbf{Can the end interrogate the beginning without overfitting the beginning to the end?}}
\]
