# V118 — fixed-parameter binder qualification result

**Status:** `QUALIFIED_FIXED_PARAMETER_OBSTRUCTION`

**External substrate:** `heathsanchez/specimen`

**Hosted workflow run:** `31879997219`

**Artifact:** `v118-fixed-parameter-qualification`

**Artifact digest:** `sha256:9f8565b354ff8c1ea30c922119ea735b4f20fd76083feb6454835ca24cd42bae`

## Frozen matched arms

V118 compared two minimal, ordinary-universe fixtures that differ in one structural fact:

1. `EXPLICIT/INDEX`: the parameter is a real constructor/index argument.
2. `IMPLICIT/UNIFORM`: the parameter is a uniform inductive parameter supplied by the family context.

## Hosted result

- explicit/index control: `rc = 0`
- implicit/uniform acquisition: `rc = 1`

The failing arm produced the exact binder-role residual:

`Function expected at V118ImplicitExpr.unit`

`but this term has type V118ImplicitExpr ?m`

`Expected a function because this term is being applied to the argument a_1`

The hosted workflow emitted:

`QUALIFIED_FIXED_PARAMETER_OBSTRUCTION`

## Interpretation

V117 had already falsified the narrower `Type 1 / higher-universe parameter` hypothesis because both its low- and high-universe parameterized families failed identically.

V118 prospectively isolates the stronger representation error:

`UNIFORM FIXED PARAMETER != EXPLICIT CONSTRUCTOR/INDEX ARGUMENT`.

The current constructor pipeline succeeds when the value is genuinely an explicit constructor/index argument and fails when an analogous value is only a uniform inductive parameter. Therefore the acquisition world is qualified for a binder-aware K1 intervention.

## Claim boundary

This result establishes only the obstruction qualification. It does not establish that a K1 mechanism repairs it, transfers to Strata, preserves protected behavior, or causally expands constructibility.

No held-out Strata execution is admitted until the generic K1 implementation is frozen on acquisition evidence alone.
