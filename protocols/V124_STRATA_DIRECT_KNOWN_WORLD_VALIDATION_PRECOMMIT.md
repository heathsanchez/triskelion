# V124 — direct Strata known-world validation precommit

**Status:** FROZEN BEFORE DIRECT-STRATA EXECUTION

## Role

This is a **secondary known-world validation**, not a blind held-out experiment. The existing `StrataLexprGen` workaround and its documented parameter limitation were inspected before K2 was constructed.

The purpose is practical/mechanistic: test whether the exact frozen V120 binder-aware mechanism removes the need to copy real parameterized `Lambda.LExpr` into the monomorphic `LExprU` workaround.

## Frozen K2

Use byte-identical V120 `CARRY_IMPLICIT_FIXED_PARAMETER` with no modification.

## Frozen target

Use the pre-existing real declarations from:

`SpecimenTest/StrataDefs/LambdaCore.lean`

Specifically, attempt constrained derivation directly over the real parameterized `Lambda.LExpr` and its real `LExpr.HasTypeA` relation at the same trivial monomorphic `LExprParamsT` instantiation represented by the existing `LExprU` workaround.

The new validation file may provide the same necessary ordinary support instances already present in `StrataLexprGen` (e.g. arbitrary base values and the de-Bruijn lookup delegated producer), but may not transcribe/copy `LExpr` or `HasTypeA` into a new inductive family.

## Frozen comparison

- K0 direct real-Strata derivation is predicted to FAIL from the already documented fixed-parameter limitation.
- Exact frozen K2 direct real-Strata derivation is predicted to PASS.
- Ablating K2 must restore the direct derivation failure.

## Soundness

If K2 derives the generator, sample at least the same scale as the existing workaround validation (60 samples across multiple context/type requests) and check them with the real or semantically unchanged Strata typing/type-check relation. Generator declaration elaboration alone is insufficient.

## Gates

- G0: pinned Specimen/Strata definitions build.
- G1: K0 direct real-Strata target fails.
- G2: exact frozen K2 derives the direct real-Strata constrained producer.
- G3: sampled outputs satisfy the unchanged real typing criterion.
- G4: K2 ablation restores direct-target failure.
- G5: no copied `LExprU`/`HasTypeAU` workaround is used in the admitted target.
- G6: K2 source is unchanged from V120.

`PASS_V124_STRATA_DIRECT_KNOWN_WORLD` requires G0–G6.

## Claim boundary

A pass would show that the independently motivated V120 mechanism resolves the concrete Strata limitation that originally required a monomorphic copied workaround. Because that limitation was already known before K2, this is corroborating mechanism evidence, not prospective blind transfer.
