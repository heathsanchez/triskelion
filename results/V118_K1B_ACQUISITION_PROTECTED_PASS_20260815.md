# V118 K1b — binder-aware constructor parameter handling

**Status:** `PASS_ACQUISITION_AND_PROTECTED_CONTROLS`

**Frozen K1 implementation commit:** `261e394efdbe0e210b16b19a0dd33ba53052bd40` in `heathsanchez/specimen`

**Hosted run:** `31880264485`

**Artifact:** `v118-k1-acquisition`

**Artifact digest:** `sha256:acd69bd7388ee10a4055e7692e260fc367f6a9f01b2d72c3424f0880c229be3c`

## K1b mechanism

K1a had shown that dropping every metadata-declared uniform constructor parameter repaired the acquisition case but broke an explicit-uniform protected control. K1b therefore uses the constructor telescope's binder information:

- implicit uniform inductive parameters are omitted from emitted explicit constructor arguments;
- explicit uniform binders are preserved;
- generic search limits and constructor search budget are unchanged.

The implementation is a generic patch to `convertToCtorExpr`; it contains no V118 fixture names and no Strata-specific names.

## Hosted result

The hosted run first reproduced K0:

- explicit/index control: PASS
- implicit/uniform acquisition: FAIL

Then it applied K1b and rebuilt Specimen from the patched source.

Under K1b:

- explicit/index protected control: **PASS**
- implicit/uniform acquisition: **PASS**
- existing Specimen protected test suite: **PASS**

## Interpretation

The acquisition evidence supports a real constructor-representation distinction rather than a generic search increase:

`IMPLICIT UNIFORM PARAMETER != EXPLICIT UNIFORM PARAMETER`.

K1b changes which constructor applications the deriver can lawfully emit while preserving the case where the corresponding value is genuinely explicit.

## Freeze point

K1b is now frozen at commit `261e394efdbe0e210b16b19a0dd33ba53052bd40` before direct execution on the natural Strata target.

No later held-out evidence may change the K1b implementation for purposes of the V118 transfer claim. If Strata fails for another reason, the outcome is `NULL_NO_TRANSFER` for this K1b rather than permission to retune it on the held-out target.

## Remaining gates

This is not yet `PASS_V118_FIXED_PARAMETER_CONSTRUCTOR_DEVELOPMENT`.

Still required:

- direct source-distinct Strata parameterized derivation without the copied `LExprU` workaround;
- generated-value checking against the unchanged typing relation;
- causal ablation restoring the natural-target failure;
- no target-specific change to K1b.
