# V119 — CARRY_FIXED_PARAMETER K1 precommit

**Status:** FROZEN BEFORE K1 IMPLEMENTATION

## Starting evidence

V118 prospectively qualified a matched obstruction in `heathsanchez/specimen`:

- explicit constructor/index parameter form: PASS;
- uniform fixed inductive parameter form: FAIL;
- repository build: PASS.

The failure is an emission-role error: a constructor already specialized by a uniform inductive parameter is emitted as though the same parameter still had to be applied as an explicit constructor argument.

## Research question

Can the acquisition residual justify a minimal generic constructor-language extension that distinguishes fixed environmental parameters from values still to be constructed/applied, and does that extension expand verified constructibility beyond the acquisition fixture?

## Frozen K1 mechanism family

Name: `CARRY_FIXED_PARAMETER`.

Semantic rule:

> An inductive family parameter that is already fixed by the derivation target and is not an explicit constructor field/output is carried as environment/context. It must not be reclassified as a generated output or re-applied to a constructor that Lean has already specialized by that uniform parameter.

Allowed implementation locations:

- constructor-expression classification;
- constructor metadata / binder-role representation;
- schedule environment;
- generated expression emission.

Disallowed changes:

- increasing generic search limits;
- special-casing acquisition declaration names;
- special-casing Strata or any held-out file/type name;
- adding a hand-written generator for the acquisition target;
- changing verifier/test semantics;
- reading held-out target source before the K1 implementation commit is frozen.

## Acquisition evidence allowed during K1 construction

Only:

- V118 explicit/index control;
- V118 implicit/fixed-parameter acquisition fixture;
- current Specimen generic implementation;
- compiler/elaborator/scheduler diagnostics produced by those acquisition fixtures;
- existing protected regression suite excluding held-out target selection.

## Important contamination correction

`SpecimenTest/StrataLexprGen.lean` has already been inspected during earlier diagnosis, so Strata is **not** admissible as a blind V119 held-out target.

It may be used later only as a secondary known natural-world validation after the primary held-out test is frozen and executed.

## Primary held-out selection

After the K1 implementation commit is frozen, select the primary natural held-out mechanically from the pinned pre-K1 Specimen tree.

Selection algorithm:

1. enumerate existing `.lean` files under `SpecimenTest/` in lexical path order;
2. exclude all V117/V118/V119 files, `StrataLexprGen.lean`, `StrataDefs/`, and any file whose contents were manually inspected during V119 K1 construction;
3. using an automated static scanner only, identify files containing both:
   - a parameterized inductive family with at least one uniform parameter not repeated as an explicit constructor field; and
   - a constrained derivation command (`derive_generator`, `derive_enumerator`, `derive_checker`, or `derive_mutual`) whose target depends on that family;
4. choose the first qualifying file for which pre-K1 Specimen fails with the same fixed-parameter role signature or an equivalent generated-constructor overapplication signature;
5. do not inspect the selected file manually until after K1 is frozen.

If no natural held-out qualifies, return `NULL_NO_NATURAL_HELDOUT`; do not synthesize a favourable held-out and call it transfer.

## Protected controls

Use the first three lexical existing Specimen test modules that compile under pre-K1 and do not trigger the fixed-parameter qualification signature.

## Gates

- G0 pinned repository builds.
- G1 V118 acquisition obstruction reproduces pre-K1.
- G2 minimal K1 causes V118 acquisition to compile.
- G3 explicit/index V118 control remains passing.
- G4 full existing protected controls remain passing.
- G5 K1 patch contains no target-name special cases and no generic search-budget increase.
- G6 primary natural held-out, mechanically selected after K1 freeze, changes FAIL -> PASS without K1 modification.
- G7 K1 ablation restores the held-out failure.
- G8 if sampled/generated values are executable, unchanged relation/checker validates them; compile-only success is not inflated into semantic soundness beyond what the target test checks.

## Strong pass

`PASS_V119_CARRY_FIXED_PARAMETER_TRANSFER` requires G0-G8.

## Null / failure outcomes

- `NULL_ACQUISITION_ALREADY_SOLVABLE`: K0 no longer reproduces obstruction.
- `NULL_K1_DOES_NOT_REPAIR`: mechanism fails on acquisition.
- `NULL_NO_NATURAL_HELDOUT`: no eligible untouched natural held-out exists.
- `NULL_NO_TRANSFER`: held-out remains failing after frozen K1.
- `NULL_NO_CAUSALITY`: ablation does not restore failure.
- `HARMFUL_REGRESSION`: protected behavior breaks.
- `INVALID_SPECIAL_CASE`: implementation encodes acquisition/held-out identity.
- `INVALID_SEARCH_EXPANSION`: result comes only from more generic search/compute.

## Claim boundary

A strong pass would support only:

> In a pinned natural Lean derivation system, a verifier-qualified binder-role obstruction justified a generic constructor mechanism that causally expanded constructibility to an independently selected existing test family while preserving protected behavior.

It would not establish open-ended arbitrary self-modification or representation-independent invention.
