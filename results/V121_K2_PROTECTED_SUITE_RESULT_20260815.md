# V121 — K2 protected-suite validation result

**Status:** `PASS_V121_PROTECTED_SUITE`

**External substrate:** `heathsanchez/specimen`

**Hosted workflow run:** `31881674814`

**Head SHA:** `9e4195d4d0b675a7c920747b0f8fc0b8e61b307a`

**Artifact:** `v121-k2-protected-suite`

**Artifact digest:** `sha256:7921b040b67e38e04db4577346fd5e5687df456ea8f3e97ea6a4f7b70d673bf6`

## Frozen validation

The exact V120 `CARRY_IMPLICIT_FIXED_PARAMETER` patch was tested without modifying, skipping, filtering, or rewriting existing Specimen tests.

Sequence:

1. K0 default `lake build` — PASS.
2. K0 ordinary `lake test` — PASS.
3. Apply exact frozen V120 K2 patch — PASS.
4. Rebuild `Specimen.DeriveConstrainedProducer` — PASS.
5. K2 default `lake build` — PASS.
6. K2 ordinary `lake test` — PASS.
7. Recheck the matched acquisition pair under K2 — explicit/index PASS, implicit/uniform PASS.

## Suite evidence

The ordinary test runner reached `137/137 Built SpecimenTest` before K2 and again after K2. The protected suite includes existing constrained generators, enumerators, checkers, dependent-output and instance-parameter tests, mutual recursion, delegated production, STLC, Cedar, schedule-quality regression, and the existing Strata workaround example.

Warnings already present in the suite (for example no schedule for `LE.le[]` in BST tests) remained non-fatal and are not counted as K2 regressions.

## Acquisition preservation

After the full K2 protected-suite run:

- explicit/index matched control: `rc=0`
- implicit/uniform acquisition: `rc=0`

The workflow emitted `PASS_V121_PROTECTED_SUITE`.

## Interpretation

V121 rules out the simplest overfitting account that V120 merely repaired its two acquisition fixtures at the cost of current Specimen behavior. The same frozen binder-aware representation change preserves the full ordinary test library while retaining the newly constructible acquisition case.

## Claim boundary

The strongest supported claim at this checkpoint is:

> In a pinned natural Lean metaprogramming system, a prospectively isolated constructor-reconstruction obstruction was repaired by a generic binder-aware mechanism that changes acquisition constructibility while preserving the matched explicit control and the entire current Specimen test suite.

This is **not yet** the full constructor-development capstone. Source-distinct `K0 FAIL -> frozen K2 PASS -> ablation FAIL` transfer on a natural held-out target remains required.
