# V120 — binder-aware fixed-parameter refinement precommit

**Status:** FROZEN BEFORE V120 EXECUTION

## Starting evidence

V118 prospectively qualified the matched acquisition obstruction:

- explicit/index constructor argument: K0 PASS;
- implicit/uniform fixed inductive parameter: K0 FAIL.

V119 then applied the frozen rule `drop ctorInfo.numParams arguments` and produced an exact selective inversion:

- implicit/uniform arm repaired;
- explicit/index arm regressed.

Therefore V119 falsified parameter-count-only handling and localized the next admissible distinction to binder role / explicitness.

## Question

Can a generic constructor-reconstruction rule that omits only **implicit uniform constructor parameters** preserve genuinely explicit constructor arguments while repairing the fixed-parameter acquisition obstruction?

## Frozen K2 mechanism

Name: `CARRY_IMPLICIT_FIXED_PARAMETER`.

For a Lean constructor application encountered in `convertToCtorExpr`:

1. inspect the constructor constant's telescope;
2. consider only the leading positions reported by `ctorInfo.numParams`;
3. omit a leading parameter argument only when its constructor binder information is one of:
   - `implicit`,
   - `strictImplicit`,
   - `instImplicit`;
4. preserve a leading parameter argument whose binder information is `default` / explicit;
5. preserve all non-parameter arguments;
6. retain the pre-existing filtering of type arguments and typeclass arguments.

No acquisition type names, constructor names, Strata names, or held-out names may appear in the implementation.

## Frozen acquisition arms

Reuse unchanged:

- `SpecimenTest/V119ExplicitIndexControl.lean`
- `SpecimenTest/V119ImplicitParameterAcquisition.lean`

The pre-intervention K0 state must again reproduce explicit PASS / implicit FAIL.

## Gates

- **G0:** Specimen builds under the pinned toolchain.
- **G1:** K0 explicit/index control passes.
- **G2:** K0 implicit/uniform acquisition fails.
- **G3:** K2 explicit/index control passes.
- **G4:** K2 implicit/uniform acquisition passes.
- **G5:** implementation is generic and contains no target-name special case.
- **G6:** generic search/resource limits are unchanged.

`PASS_V120_ACQUISITION` requires G0–G6.

If K2 repairs implicit but breaks explicit, return `NULL_BINDER_RULE_STILL_TOO_BROAD`.

If explicit passes but implicit remains failing, return `NULL_BINDER_RULE_INSUFFICIENT`.

If both K0 arms no longer reproduce, return `INVALID_ACQUISITION_DRIFT`.

## Holdout discipline

No natural held-out Specimen target is inspected or executed during V120 acquisition development.

Only after a `PASS_V120_ACQUISITION` may the exact K2 source patch be frozen and a held-out target be selected mechanically from existing Specimen tests without reading candidate source bodies before selection.

Strata remains a secondary known-world validation only and cannot be used as the primary blind held-out because its workaround has already been inspected.

## Claim boundary

A V120 acquisition pass would establish only that the acquisition obstruction is repaired while its matched explicit control is preserved. It would not establish constructor-language growth until the frozen mechanism transfers source-distinctly and passes causal ablation/protected-suite tests.
