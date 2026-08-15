# V119 — CARRY_FIXED_PARAMETER acquisition result

**Status:** `NULL_K1_DOES_NOT_REPAIR_OR_REGRESSES`

**External substrate:** `heathsanchez/specimen`

**Hosted workflow run:** `31881002795`

**Hosted artifact:** `v119-carry-fixed-parameter-acquisition`

**Artifact digest:** `sha256:8f5bcb8607b54861017fbdd3807bde5a594e427d7aff35569d64770c8ea34915`

## Frozen acquisition discriminator

K0 reproduced the qualified V118 asymmetry:

- explicit/index control: PASS (`rc=0`)
- implicit/uniform fixed-parameter acquisition: FAIL (`rc=1`)

## Frozen K1

V119 implemented `CARRY_FIXED_PARAMETER` by reading Lean constructor metadata and dropping the first `ctorInfo.numParams` arguments from the fully elaborated constructor application before reconstruction.

## Hosted result

The intervention produced a selective inversion rather than the required joint pass:

- K1 explicit/index control: FAIL (`rc=1`)
- K1 implicit/uniform acquisition: PASS (`rc=0`)

The repaired implicit arm no longer over-applied its uniform parameter. However the explicit/index arm now emitted the bare constructor and failed because its explicit `P` argument was genuinely required:

`V119ExplicitExpr.unit : (P : V119Params) → V119ExplicitExpr P`

was emitted where `V119ExplicitExpr a_1` was required.

## Scientific interpretation

V119 falsifies the naive rule:

> drop every constructor argument counted by `numParams`.

The result is nevertheless mechanistically informative because the exact same edit repairs the target while breaking the matched control. This strongly localizes the missing distinction to **binder role / explicitness**, not merely constructor parameter count.

The next admissible acquisition refinement may inspect constructor binder metadata and distinguish an implicit carried parameter from an explicit constructor argument. This is acquisition-side refinement only; no held-out natural target may be inspected before the refined K1 is frozen.

## Claim boundary

V119 is not a capability-growth pass. It establishes neither protected preservation nor source-distinct transfer. It is a negative acquisition result with a selective causal inversion that narrows the mechanism hypothesis.
