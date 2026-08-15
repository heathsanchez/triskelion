# V109 Cross-Family Reuse of a Verifier-Induced Quotient Relation — PRECOMMIT

Date: 2026-08-15 NZST

Status: frozen before execution.

## Question

V108 induced a comparison-coordinate quotient relation from one repair family (`<= -> <`) inside a generic 59-relation grammar. Does that relation behave like reusable structural knowledge, or is it only a fitted description of that one failure family?

V109 tests whether the fold-local relation learned **only from family A** can transport a different, unseen **family B** repair on held-out natural-code programs.

## External corpus

Same pinned QuixBugs commit and frozen 13-site task set as V108:

`4257f44b0ff1181dedaedee6a447e133219fcebf`

Programs remain source-distinct under leave-one-program-out evaluation.

## Family A — relation acquisition only

Exactly V108 acquisition evidence:

- canonical correct presentation: `left < right` passes;
- causal mutation: `left <= right` fails;
- generic 59-pair comparison-coordinate candidate grammar;
- exact failing-pytest-node signature matching;
- unique fold-local relation required.

No family-B result may enter relation selection.

## Family B — protected transfer family

A different mutation is constructed after relation selection:

Source coordinate:

- correct: `left < right`
- mutation B: `left > right`
- source literal repair: `> -> <`

For a selected invertible coordinate relation that maps the source strict presentation into a target strict presentation, transport mutation B by conjugation through that relation and derive the target repair from the transported correct/mutated labels.

For example, if acquisition independently selects the operand-swapped strict dual relation, then:

- source correct `a < b` maps to target correct `b > a`;
- source mutation `a > b` maps to target mutation `b < a`;
- source literal repair `> -> <` transports to target repair `< -> >`.

This example describes the algebra of conjugation only; the relation must still be selected by frozen family-A evidence in each fold.

## Family-B qualification

A held-out site is protected-family-B-qualified iff, under the fold-selected relation:

1. source correct passes unchanged upstream tests;
2. target correct passes;
3. source mutation B fails;
4. conjugated target mutation B fails;
5. source literal repair restores source correctness;
6. transported target repair restores target correctness.

Qualification is evaluated only after relation selection. It may reduce the held-out test count but cannot alter the selected relation.

## Baselines

- **Literal reuse:** retain family-B source repair `> -> <` literally and apply it to target mutation. If target mutation has a different literal comparator, the repair is inapplicable.
- **Quotient reuse:** transport the family-B repair through the previously selected relation.
- **Ablation:** remove the transported repair, leaving target mutation B.

## Frozen gates

### G1 — family-A relation acquisition repeats
Every LOPO fold uniquely selects the same relation under the V108 family-A protocol.

### G2 — protected cross-family coverage
At least 6 family-B-qualified held-out tasks total across at least 4 held-out programs.

### G3 — no family-B selection leakage
Family-B verifier outcomes are evaluated only after each fold relation is frozen.

### G4 — literal cross-family baseline
Literal family-B source repair solves 0 protected target tasks.

### G5 — quotient cross-family reuse
Transporting family-B repair through the family-A-selected relation solves 100% of protected target tasks.

### G6 — causal ablation
Removing the transported repair restores failure on 100% of protected target tasks.

### G7 — different repair family
Family B uses the strict reversal mutation `LT -> GT`; no `<=`/`>=` mutation outcome is used in protected evaluation.

### G8 — source-distinctness
Each protected held-out program is absent from relation-acquisition evidence in its fold.

## Primary verdict

`PASS_V109_CROSS_FAMILY_QUOTIENT_REUSE` only if G1–G8 pass.

## Allowed interpretation

A pass supports:

> A comparison-coordinate quotient relation induced from one verifier-grounded repair family can be reused, without reselection, to transport a different repair family onto source-distinct held-out natural-code programs where literal repair reuse fails.

This would support the quotient relation as reusable structural capability rather than merely a relabeling fitted to one mutation family. It still does not establish arbitrary relation invention or open-ended natural-code ontology growth.
