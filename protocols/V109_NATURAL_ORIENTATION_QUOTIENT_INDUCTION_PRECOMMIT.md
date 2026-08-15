# V109 Natural-Orientation Quotient Induction — PRECOMMIT

Date: 2026-08-15 NZST

Status: frozen before qualification/result inspection.

## Motivation

V108 induced the same repair-transport relation uniquely from a generic 59-relation comparison grammar across all eight source-distinct folds, but it still started each task in a constructed canonical-LT coordinate frame.

V109 removes that engineered presentation bridge from held-out evaluation. Acquisition uses only **naturally occurring `<` sites** in the externally authored correct QuixBugs programs. Held-out evaluation uses only **naturally occurring `>` sites** in different source programs. No canonicalization or supplied LT↔GT presentation pair is used to create held-out tasks.

The only controlled intervention is causal strict-bound relaxation at the naturally occurring site.

This remains bounded relation induction in a supplied generic local AST grammar; it is not arbitrary transformation invention or historical bug repair.

## External corpus

Pinned QuixBugs commit:

`4257f44b0ff1181dedaedee6a447e133219fcebf`

Frozen program list and maximum-three-sites rule are inherited from V106B–V108.

Use correct Python programs and unchanged upstream pytest verifiers only.

## Natural acquisition tasks

For each originally authored strict binary comparison site whose operator is literally `<`:

1. verify the untouched correct program passes;
2. mutate only that site `< -> <=`;
3. require the unchanged upstream verifier to fail with at least one named failing pytest node;
4. restoring `<` must pass.

Only such sites are acquisition-eligible.

## Natural held-out tasks

For each originally authored strict binary comparison site whose operator is literally `>`:

1. verify the untouched correct program passes;
2. mutate only that site `> -> >=`;
3. require the unchanged upstream verifier to fail with at least one named failing pytest node;
4. restoring `>` must pass.

Only such sites are held-out-eligible.

No site is reoriented to create either set.

## Source separation

Each held-out GT program is evaluated in one fold. Its entire program is excluded from acquisition relation induction in that fold, including any LT sites it may also contain.

Acquisition evidence in a fold consists only of causal natural-LT sites from all *other* programs.

## Generic relation grammar

Same generic 59-relation space as V108:

- operand coordinate: KEEP or SWAP;
- strict target token from `<, >, <=, >=, ==, !=`;
- relaxed target token from the same six tokens;
- strict and relaxed target tokens must differ;
- same operand-coordinate choice for strict/relaxed;
- exclude literal identity `(KEEP, <, <=)`.

No candidate named DUAL_CMP or SWAP_AND_FLIP is supplied.

## Acquisition evidence signature

For each natural-LT acquisition task, a candidate relation is supported iff:

- its transformed strict target passes the unchanged upstream verifier;
- its transformed relaxed target fails;
- the relaxed target reproduces the exact failing pytest-node set of the original natural `< -> <=` mutation.

Candidate outcome variants may be cached per `(swap, token)` action, but scientific scoring is over the full 59 relation pairs.

## Fold-local induction

A candidate is PERFECT iff it satisfies the acquisition evidence signature on every acquisition task in that fold.

Require exactly one PERFECT candidate. Held-out GT results cannot break ties or influence selection.

## Held-out transport

The acquisition repair is literal `<= -> <`.

If the induced relation is `(swap, strict_target, relaxed_target)`, its transported repair is the token transition:

`relaxed_target -> strict_target`.

A held-out natural-GT task is counted solved only if the induced target pair is applicable to the natural `> -> >=` relaxed site and applying the transported repair makes the unchanged upstream tests pass.

Literal-retention baseline keeps only `<= -> <`; it receives no coordinate transport and therefore cannot edit a natural `>=` held-out site.

## Frozen gates

### G1 — natural orientation coverage
At least 6 causal natural-LT acquisition tasks from at least 3 programs, and at least 3 causal natural-GT held-out tasks from at least 2 programs.

### G2 — generic space
Exactly 59 nonidentity candidate relations are enumerated from the declared grammar.

### G3 — unique acquisition-only induction
Every natural-GT held-out-program fold has exactly one PERFECT relation induced from natural-LT sites in other programs.

### G4 — cross-fold stability
The independently induced relation is identical across all held-out-program folds.

### G5 — literal baseline
Literal `<= -> <` solves 0 natural-GT held-out tasks.

### G6 — natural-orientation transfer
The induced transported repair solves 100% of causal natural-GT held-out tasks.

### G7 — causal ablation
Removing the transported repair leaves 100% of natural-GT held-out tasks failing.

### G8 — no source leakage
No held-out GT program contributes any LT acquisition site in its fold.

### G9 — nontrivial rejection
At least 90% of generic candidates are rejected in every fold.

### G10 — no engineered held-out presentation
The report must show held-out tasks were selected from originally authored `>` AST nodes and were not produced by LT↔GT canonicalization.

## Verdict

`PASS_V109_NATURAL_ORIENTATION_QUOTIENT_INDUCTION` only if G1–G10 all pass.

## Allowed interpretation

A pass supports:

> A quotient repair relation induced from causal naturally occurring `<` sites in externally authored programs transfers to causal naturally occurring `>` sites in source-distinct held-out programs, without constructing the held-out orientation, while literal repair identity fails.

It does not establish arbitrary relation invention, historical bug repair, unrestricted natural-code ontology induction, or a universal representation-independent identity criterion.
