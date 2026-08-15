# V133 — Strata known-world replay result

**Status:** `NULL_V133_K5_DOES_NOT_RESOLVE_STRATA`

**External substrate:** `heathsanchez/specimen`

**Hosted run:** `31910830705`

**Job:** `95075494280`

**Head SHA:** `a071857e43e1b21af4d860509e5986ed67585f19`

**Artifact:** `v133-strata-known-world-replay`

**Artifact ID:** `9253610171`

**Artifact digest:** `sha256:16426e3c5e12de3e3752929573c12455ca02ac870a9ad142c9eb7c815229a727`

## Frozen result

The K2-only direct Strata obstruction reproduced as required. Exact frozen V132 K5 was then applied unchanged.

K2+K5 still failed, so the workflow correctly emitted `NULL_V133_K5_DOES_NOT_RESOLVE_STRATA` and skipped ablation.

## Residual refinement

The important result is that the failure signature changed.

Under K2 alone, the direct Strata target fails on hidden `LExprParamsT : Type 1` values/equality producers where generated machinery expects `Type`.

Under K2+K5, that universe/equality signature is no longer the primary diagnostic. The derivation gets farther and fails during typeclass synthesis for parameter-dependent values such as:

- `Arbitrary a_1.mono.base.Metadata`
- `Arbitrary (Identifier a_1.mono.base.IDMeta)`

and analogous obligations for another symbolic relation parameter.

Therefore V133 falsifies only the stronger sufficiency claim that K2+K5 closes the complete Strata obstruction. It does not invalidate the controlled V132 acquisition/admission result.

## RGRS classification

Primary residual after V133: `R6 Representation`.

Candidate missing distinction: a top-level relation input fixes a family parameter, but downstream instance synthesis still sees types indexed by a symbolic constructor-local parameter rather than by the specialized top-level value.

Do **not** rescue V133 by merely adding target-specific `Arbitrary` instances. That would hide whether the generic derivation is failing to propagate specialization before instance synthesis.

## Next admissible question

Prospectively isolate whether the failure is specifically:

`fixed relation parameter -> projected/derived type index -> required typeclass instance`

where the system requests an instance over a symbolic local family parameter rather than specializing that parameter from the already-fixed relation input.

The next experiment must use a small controlled family unrelated to Strata and must be frozen before any repair mechanism is designed.

## Claim boundary

V133 is a known-world negative/obstruction refinement, not blind transfer. Supported conclusion:

> K5 removes part of the earlier computed-output-type obstruction but is insufficient for direct Strata; the next exposed residual concerns parameter-dependent typeclass synthesis under symbolic family parameters.
