# V129 — K2+K4 protected-suite validation precommit

Date frozen: 2026-08-16 NZST

## Frozen mechanisms

- V120 K2: `CARRY_IMPLICIT_FIXED_PARAMETER`.
- V128 K4: `PRESERVE_INPUT_POSITION_COMPUTED_PARAMETER`.

Both are frozen before this validation. No mechanism changes are permitted based on protected-suite outcomes.

## Question

Does the composed K2+K4 capability preserve the complete current ordinary Specimen build/test surface while retaining V128 acquisition?

## Sequence

1. On unchanged branch source, run ordinary `lake build` and `lake test` as K0 reference.
2. Apply exact V120 K2 script unchanged.
3. Apply exact V128 K4 script unchanged.
4. Run ordinary `lake build` and `lake test` without filtering, skipping, test rewriting, or expected-failure edits.
5. Recheck V126 MAP under K2+K4 and require PASS.

## Gates

G1 K0 ordinary build/test pass.
G2 exact K2+K4 ordinary build pass.
G3 exact K2+K4 ordinary test pass.
G4 V126 MAP remains acquired under K2+K4.
G5 no protected tests are modified by the workflow.

Verdict `PASS_V129_K2_K4_PROTECTED_SUITE` iff G1-G5 hold.

If the ordinary suite fails only under K2+K4, reject the composition as harmful pending a separately precommitted refinement; do not exclude the failing test.

## Claim boundary

A pass establishes compatibility with the current protected Specimen suite, not semantic completeness outside that suite.
