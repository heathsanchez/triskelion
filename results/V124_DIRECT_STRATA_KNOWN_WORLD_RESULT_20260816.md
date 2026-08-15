# V124 — direct Strata known-world validation result

**Status:** `NULL_K2_DOES_NOT_RESOLVE_DIRECT_STRATA`

**External substrate:** `heathsanchez/specimen`

**Valid hosted workflow run:** `31893364853`

**Job:** `95032838930`

**Artifact:** `v124-direct-strata-known-world`

**Artifact ID:** `9249137710`

**Artifact digest:** `sha256:95805103feee825844da9c69be2800d55c76428417e265d7b5fcab4105a14767`

## Harness note

The earlier run `31882011553` was invalid because the vendored support module had not been built before invoking the direct Lean file, yielding `unknown module prefix 'SpecimenTest'`. The workflow-only repair added `lake build SpecimenTest.StrataDefs.LambdaCore`; it did not modify the target, K2, or the scientific protocol.

## Valid rerun

The direct target uses the real parameterized `Lambda.LExpr` and `LExpr.HasTypeA` definitions from the existing vendored Strata slice rather than the monomorphic `LExprU` / `HasTypeAU` workaround.

K0 failed as expected. Exact frozen V120 K2 also failed.

The residual is not the V119/V120 constructor-binder-role failure. The generated schedule introduces a hidden value of type `LExprParamsT : Type 1` and attempts to satisfy an equality of the shape:

`unk = a_1.mono`

The emitted constrained-producer application then requires a value/predicate at sort `Type`, producing the observed `Type 1` versus `Type` mismatch.

## Interpretation

V124 is a useful negative. V120 K2 does **not** directly remove the known Strata workaround. Instead it reveals a second representation barrier: a computed family parameter (`T.mono`) is flattened into a fresh independently-produced unknown plus equality obligation.

This result triggered V125/V126 mechanism isolation. It must not be reported as transfer success.

## Claim boundary

V124 is a known-world validation, not a blind held-out test. Its supported conclusion is only that the exact V120 mechanism is insufficient for direct Strata and that the remaining residual has a distinct computed-parameter/equality shape.
