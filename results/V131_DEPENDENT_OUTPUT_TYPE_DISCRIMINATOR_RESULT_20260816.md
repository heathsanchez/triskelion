# V131 — dependent output-type discriminator result

**Status:** `PASS_V131_DEPENDENT_OUTPUT_TYPE_DISCRIMINATOR`

**External substrate:** `heathsanchez/specimen`

**Hosted workflow run:** `31895340880`

**Job:** `95037695820`

**Head SHA:** `20138926682e583b83c777c98dda1b475cbe476b`

**Artifact:** `v131-dependent-output-type-discriminator`

**Artifact ID:** `9249655928`

**Artifact digest:** `sha256:6d99dd422ce32ca49a1827d156a9b556c074ee7b68ce4700283c92120773b17d`

## Precommit

V131 was frozen only after V130 rejected constructor fixed-parameter position as the separator. No repair was attempted in V131.

## Hosted result

Under exact frozen V120 K2, diagnostic-only classification produced:

- V126 MAP candidate `V126Lift p`: `output_dependent_type=true`, `output_value=true`.
- protected ordinary term candidate `x * x`: `output_dependent_type=false`, `output_value=false`.
- V126 direct-ID control contained no `V126Lift` candidate.

The MAP arm still failed with the known hidden-unknown equality / `Type 1` producer mismatch, while ID and multiplication controls compiled.

All precommitted gates passed:

- G1 MAP computed application occurs in inferred type of an output-position term: PASS.
- G2 ordinary `x * x` computed term does not: PASS.
- G3 direct-ID control does not contain the computed bridge: PASS.

## Interpretation

V131 provides the first structural separator that survives the V129 protected counterexample and the V130 rejection:

> The V126 computed bridge is not merely input-determined and is not a constructor fixed parameter. It is a computed application carried in the dependent type/family of an output-position term.

This explains why flattening it into a fresh independently-generated value is qualitatively different from flattening ordinary term computations such as `x * x`, which protected tests rely on for lawful pattern/scheduler behavior.

## RGRS transition

`R5 applicability after V129 -> reject V130 separator -> V131 separator passes`.

The next admissible repair must combine the previously necessary input-determined criterion with this new output-dependent-type role. It may not broadly preserve every input-determined application.

## Claim boundary

V131 is a diagnostic separator only. It does not establish a repair, protected-suite compatibility, Strata transfer, or general dependent-type support.
