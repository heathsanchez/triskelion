# V153 — V138 O3 holdout-support diagnostic

Frozen: 2026-08-16 NZST
Controller: Rigorous Breakthrough Stack v1.1

## Residual

V138 passed CP5 natural developmental acceleration and CP6 recompression. Its repeated stream made two verified developmental transitions (`EMPTY→O1`, then `O1→O1+O2`) with replay preserved and a better final endpoint, but O3 had zero evaluable leave-one-program-out folds.

Audit of the frozen V138 runner shows why a program is evaluable for O3: the held-out program itself must contain at least one `RELAX_SAFE` and one `RELAX_SENSITIVE` site so balanced accuracy is defined. V138 observed both labels globally (8 safe, 16 sensitive) but reported zero evaluable programs.

V153 is **diagnostic only**. It does not retroactively change V138 or admit O3.

## Question

Was V138's O3 ceiling caused specifically by the granularity of single-program holdout support, or does the frozen O3 rule language still fail when held-out support is obtained without changing labels, features, rules, or verifier semantics?

## Frozen apparatus

V153 reuses exactly the V138 commit and machinery:

- QuixBugs commit `4257f44b0ff1181dedaedee6a447e133219fcebf`;
- the same natural strict-comparison site discovery;
- the same verifier outcomes and `RELAX_SAFE` / `RELAX_SENSITIVE` label definition;
- the same O3 feature set;
- the same one-literal / two-literal conjunction rule language;
- the same training selection rule (highest balanced accuracy, then fewer literals, then lexical rule id);
- no model calls.

V153 adds only evidence emission and one deterministic grouped-holdout diagnostic.

## Deterministic paired-program holdout

Programs are ordered by `SHA256(program_name)` ascending, with program name as a final deterministic tie-break. Consecutive programs are grouped in pairs. If the number of programs is odd, the final group contains the final unpaired program.

This grouping uses no labels, verifier outcomes, AST features, source text, program semantics, or O3 rule performance.

For each group:

- acquisition = all sites from programs outside the group;
- heldout = all sites from programs inside the group;
- the fold is evaluable only if heldout contains both O3 labels;
- train the unchanged V138 O3 selector on acquisition;
- score unchanged balanced accuracy on heldout.

No alternative grouping, re-pairing, fold count, random seed, or best-of-partitions search is permitted after outcomes.

## Diagnostic classifications

`PASS_V153_SINGLE_PROGRAM_SUPPORT_OBSTRUCTION`
iff:

1. V138-style single-program evaluable count is exactly 0;
2. deterministic paired-program holdout has at least 8 evaluable folds;
3. median heldout balanced accuracy across those folds is >= 0.75.

This means the V138 O3 ceiling was specifically a holdout-support/granularity obstruction and that the already-frozen O3 language remains viable under a deterministic source-grouped diagnostic. It is **not** an O3 admission or Q8 pass.

`NEGATIVE_V153_O3_RULE_LANGUAGE_UNDER_PAIRED_SUPPORT`
if at least 8 paired folds are evaluable but median heldout balanced accuracy is < 0.75.

`CORPUS_CEILING_V153_PAIRED_SUPPORT`
if fewer than 8 paired folds are evaluable.

Any commit mismatch or verifier/apparatus failure is R10/inconclusive.

## Claim boundary

A positive V153 only licenses the next experiment: expand/freeze an external natural corpus capable of supporting the original source-distinct O3 admission test. It cannot substitute paired-program evaluation for V138's preregistered single-program LOPO gate.