# BINARY RELATIONAL NUCLEUS V1 — prospective precommit

Status: **FROZEN BEFORE OUTCOME IMPLEMENTATION OR EXECUTION**

## Original goal

This experiment exists to protect the original research question:

[
oxed{	extbf{What is the smallest nucleus from which warranted development can regenerate every form it needs?}}
]

It is **not** a test of whether binary notation is aesthetically appealing, whether nature is literally made of bits, or whether +/− symbolism is metaphysically fundamental.

The immediate question is narrower:

> Can the previously tested C+Difference / D-M-I developmental behavior be pushed one level lower to a two-symbol relational substrate plus one recursively reusable binary interaction law?

If not, the reduction stops here.

## Candidate substrate

The only primitive alphabet is:

[
oxed{B={0,1}}
]

where 0 and 1 have no semantic interpretation beyond being distinct symbols.

A candidate interaction law is one binary operation

[
f:B	imes B	o B.
]

Every such law is completely specified by its outputs on:

[
00, 01, 10, 11.
]

Therefore the candidate space is exhaustive:

[
oxed{2^4=16	ext{ binary interaction laws}.}
]

No preferred law is selected in advance.

## Symmetry question

For every law record whether

[
f(0,1)=f(1,0).
]

Thus the experiment directly tests whether the surviving one-law nuclei, if any, require directional/asymmetric polarity or whether a symmetric interaction law can suffice.

## Exact finite universe

Primary universe:

- three opaque binary variables (x,y,z);
- constants 0 and 1;
- all (2^{2^3}=256) Boolean consequences over the complete eight-row carrier.

For every one of the 16 laws, compute the exact semantic closure under arbitrary recursive composition.

This is not sampling.

The first primary result is therefore:

[
|mathrm{Cl}_f({0,1,x,y,z})|.
]

A law is **extensionally complete on the universe** iff its exact closure contains all 256 functions.

## Controls

For every law also compute:

### NO-CONSTANTS
Closure from ({x,y,z}) only.

This tests whether fixed polarity anchors 0/1 are necessary for that law's completeness.

### NO-REENTRY
Verified generated children may solve their current target but may not become unit-cost primitives for later targets.

This tests whether recursive child→parent reuse is causally necessary for developmental compounding.

### ONE-SYMBOL
Collapse 0 and 1 into one symbol before any interaction.

This is the one-symbol lower-bound control. It can distinguish no two Boolean consequences and therefore cannot count as a successful nucleus merely by convention.

### COLD
Each developmental episode starts again from ({0,1,x,y,z}).

### SHAM-WARRANT
Counterexample labels are deterministically permuted before synthesis; exact external verification still decides admission.

This tests whether arbitrary binary variation can substitute for correct consequential difference.

## External authority

The exact eight-row truth table is external authority.

A proposal never self-certifies.

The learner receives only counterexample rows and expected 0/1 outcomes until exact verification succeeds.

## Expression cost

Leaves have cost 1.

A composed term has:

[
operatorname{cost}(f(a,b))=1+operatorname{cost}(a)+operatorname{cost}(b).
]

For every reachable semantic function, compute exact minimum expression cost under the candidate law.

Installed verified children become unit-cost leaves for subsequent developmental episodes.

## Developmental lineage test

The extensional-completeness test is necessary but not sufficient.

For every extensionally complete law, run a six-generation mechanically selected developmental lineage.

### G1

Choose the hash-first function outside the trivial leaf set with exact cold minimum cost at least 5.

Synthesize it only through verifier counterexamples under the candidate law.

After exact verification, install G1 as a unit-cost leaf.

### G2–G6

At generation (t>1):

1. compute exact minimum costs with the current verified children installed;
2. compute the same costs with the immediately previous child removed;
3. eligible targets are semantics for which:
   - warm minimum cost is finite;
   - removing the previous child strictly increases minimum cost;
   - the target is not already an installed child;
   - warm minimum cost is at most 9;
4. choose the hash-first eligible target under the frozen seed for that generation;
5. freeze budget (B_t) to the warm exact minimum cost;
6. synthesize with verifier counterexamples;
7. require success within (B_t);
8. remove the previous child and require the target to become unreachable within (B_t);
9. restore the exact child and require reachability within (B_t).

If no eligible target exists, the lineage terminates. No rescue target may be inserted.

This is a direct test of:

[
oxed{	ext{verified child becomes causally useful parent}.}
]

## Twin-history variation test

For every law that completes G1–G6, fork two identical inherited states after G2.

Twin A receives two further mechanically selected targets under seed A.

Twin B receives two different mechanically selected targets under seed B.

Then both receive the same common target.

Required signal:

- both twins remain externally correct;
- their installed semantic sets differ before the common target;
- both can verify the common target;
- at least one exact minimum expression for the common target differs in its installed-child dependency set between the twins, or the two twins reach it at different minimum cost.

This tests:

[
	ext{same law}+	ext{same origin}+	ext{different history}
Rightarrow
	ext{different competent developmental state}.
]

## Recombination test

After the twin histories, form a union state containing both verified lineages.

Mechanically choose a target satisfying all of:

- reachable in the union within cost 9;
- not reachable within the same budget from Twin A alone;
- not reachable within the same budget from Twin B alone;
- removing at least one A-only installed child increases cost beyond budget;
- removing at least one B-only installed child increases cost beyond budget.

The target must then be synthesized and externally verified.

This is the binary-law analogue of:

[
A_{	ext{history}}+B_{	ext{history}}	o K.
]

K is installed and must subsequently serve as a causal parent for one additional descendant Z under the same remove/restore criterion.

If no such recombination target exists, the law fails this gate; no target substitution is permitted.

## Post-hoc phenotype test

The solver does not receive D/M/I labels.

After the lineage, classify whether these behaviors emerged:

- **D-like** — verifier residuals eliminated candidate terms/parent choices;
- **M-like** — a novel composed binary relation was constructed;
- **I-like** — a verified child re-entered as a unit-cost parent and later changed exact reachability.

A law counts as regenerating the earlier nucleus phenotype only if all three occur causally.

## Cross-law inevitability test

The experiment must not call one law "the law" merely because it works.

Record the entire survivor set:

[
mathcal S=
{f:	ext{all frozen gates pass}}.
]

Interpretation:

- (|mathcal S|=0): one binary law is insufficient under V1.
- (|mathcal S|=1): a unique survivor exists in this finite family.
- (|mathcal S|>1): the evidence supports an equivalence class of binary nuclei, not a unique law.

Also quotient survivors by:
- input swap;
- output complement;
- simultaneous symbol relabelling (0leftrightarrow1).

This tests whether apparently different laws are merely representational variants of the same interaction structure.

## Replication worlds

Run the exact 16-law tournament under 25 deterministic target-selection salts:

`TRISKELION_BINARY_NUCLEUS_V1:000` through `:024`.

The extensional closure result is salt-independent; the developmental/twin/recombination lineage is salt-dependent.

A law is a **robust survivor** only if it passes the complete developmental suite in at least 23/25 salts.

## Headline gates per law

L1. Exact closure size = 256.
L2. CEGIS verifier synthesis succeeds for G1.
L3. Six-generation child-reentry lineage completes.
L4. Every G2–G6 previous-child remove/restore gate passes.
L5. NO-REENTRY fails at least one later-generation frozen budget gate.
L6. COLD loses at least one warm budget gate.
L7. SHAM-WARRANT fails or uses strictly more verifier interactions on at least one generation.
L8. Twin histories diverge while both remain correct.
L9. Both twins verify the common target.
L10. A true two-lineage recombination target exists and verifies.
L11. Neither twin alone reaches the recombination target within the frozen union budget.
L12. Recombined K causally enables descendant Z under remove/restore.
L13. D-like, M-like and I-like behaviors all appear post hoc.
L14. ONE-SYMBOL control fails.
L15. Representation relabelling (0leftrightarrow1) preserves the gate vector up to the frozen equivalence transformation.

## Experiment-level outputs

Report:

- all 16 truth tables;
- symmetry/asymmetry;
- exact closure sizes;
- exact minimum-cost distributions;
- NO-CONSTANTS closure sizes;
- per-salt developmental gate vectors;
- robust survivors;
- equivalence classes of survivors under binary relabelling/input swap/output complement;
- whether any symmetric survivor exists;
- whether any asymmetric survivor exists;
- whether any survivor remains complete without constants.

## Verdicts

- `PASS_BINARY_RELATIONAL_NUCLEUS_CLASS_V1`
  - at least one robust survivor;
  - every survivor passes the frozen causal developmental gates;
  - controls separate as preregistered.

- `PARTIAL_BINARY_RELATIONAL_NUCLEUS_V1`
  - binary laws achieve exact completeness but do not robustly regenerate the full developmental suite.

- `REDUCED_BELOW_BINARY_PAIR_V1`
  - a preregistered lower control unexpectedly matches the full developmental suite.

- `VALID_NEGATIVE_BINARY_RELATIONAL_NUCLEUS_V1`
  - no candidate law satisfies the frozen sufficiency gates.

## Claim boundary

A PASS would establish only:

> within the complete three-variable Boolean universe and the frozen developmental lineage/twin/recombination protocol, at least one single binary interaction law over a two-symbol alphabet is sufficient to regenerate the tested recursive developmental behaviors under external verification.

It would **not** establish:

- that physical reality is binary;
- that + and − are ontological substances;
- that one law is uniquely fundamental unless the exhaustive survivor quotient is actually unique;
- unrestricted natural-world intelligence;
- unique minimality over all possible non-binary or non-symbolic computational substrates.

The original goal remains unchanged: remove every reconstructible handhold until further removal destroys warranted regenerative development.
