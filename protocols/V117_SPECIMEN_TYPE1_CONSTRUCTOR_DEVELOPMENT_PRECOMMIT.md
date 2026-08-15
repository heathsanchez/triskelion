# V117 — Fresh Specimen Type-1 constructor-development precommit

**Status:** FROZEN BEFORE SOLUTION INSPECTION OR IMPLEMENTATION

## Motivation

Specimen's existing Strata `LExpr` example explicitly documents a remaining orthogonal limitation: the real expression type carries a structure parameter `T : LExprParamsT` in `Type 1`, and the constrained deriver currently tries to generate that parameter. The shipped example therefore inlines a monomorphic specialization into a new `LExprU` type.

V117 tests whether that documented limitation can be turned into a genuine constructor-development event rather than another retrospective replay of an already-known mechanism.

## External substrate

Pinned target repository: `heathsanchez/specimen`.

Primary external verifier: Lean elaboration / `lake build` / unchanged Specimen tests.

Held-out natural target: the vendored Strata `Lambda.LExpr` / `LExpr.HasTypeA` relation already present in Specimen, using the real `LExprParamsT` structure parameter rather than the inlined `LExprU` surrogate.

## Frozen K0

`K0` is the current constrained-derivation mechanism set at the pinned Specimen target commit, including delegated production, multi-output, auto dependency derivation and mutual derivation, but **without any new rule for treating fixed higher-universe structure parameters as externally supplied immutable parameters**.

Search limits and existing scheduler machinery remain unchanged.

## Acquisition world

Before the Strata held-out target is opened for implementation, construct a small generic Lean fixture with:

- a structure parameter `P : Type 1`;
- an inductive family `F (P)` whose constructors carry/use that parameter;
- an inductive relation `Good (P) : F P -> Prop` with at least two constructors and one recursive case;
- a request to derive a constrained producer for `fun x => Good fixedP x`.

The acquisition fixture must be generic and not copy the Strata constructor set or typing rules.

Qualification succeeds only if:

1. full K0 fails specifically because the fixed `Type 1` structure parameter is treated as something to generate / cannot be represented in the current constrained constructor path;
2. lowering/removing the higher-universe parameter makes the analogous fixture derivable;
3. raising generic search limits alone does not remove the failure.

If these do not hold, return `NULL_WRONG_OBSTRUCTION`.

## K1 admissible mechanism family

The only new mechanism family allowed in V117 is:

`FIXED_HIGHER_UNIVERSE_PARAMETER`

Semantic intent:

> distinguish immutable parameters supplied by the derivation target from values that the generated witness must construct.

K1 may change classification, schedule environment, constructor expression representation, or emission as needed to carry such fixed parameters through derivation. It may not introduce a Strata-specific special case, hard-code `LExprParamsT`, or bypass the relation verifier.

## Frozen development sequence

1. Reproduce acquisition obstruction under K0.
2. Record the smallest failing internal state / diagnostic.
3. Construct K1 using only acquisition fixture, Specimen source and Lean feedback.
4. Freeze the K1 patch hash.
5. Only then run the real Strata held-out target using `Lambda.LExpr` with a fixed concrete `LExprParamsT` value.
6. Run causal ablation by disabling K1 only.
7. Run protected existing Specimen tests.

## Held-out target

The held-out target must derive directly over the real parameterized `Lambda.LExpr`, not a copied/inlined replacement type.

It may reuse the already-existing delegated lookup producer because that capability belongs to K0. No changes to the lookup mechanism are permitted after K1 freeze.

Success requires generated samples to be checked against the unchanged Strata typing relation / verifier, not merely compile a generator declaration.

## Gates

- **G0 TARGET_PINNED:** exact Specimen commit recorded before acquisition execution.
- **G1 ACQUISITION_OBSTRUCTION:** K0 fails for the higher-universe fixed-parameter reason.
- **G2 SEARCH_CONTROL:** increased ordinary K0 search does not solve acquisition.
- **G3 LOWER_UNIVERSE_CONTROL:** analogous lower-universe/fixed-parameter fixture succeeds, localizing the obstruction.
- **G4 K1_ACQUISITION:** frozen generic K1 solves acquisition.
- **G5 HELDOUT_STRATA:** unchanged K1 derives over real parameterized Strata `LExpr` and verifier-checked generated samples pass.
- **G6 ABLATION:** remove/disable only K1 and held-out derivation fails again.
- **G7 PROTECTED:** existing Specimen test suite remains passing with K1.
- **G8 SPECIFICITY:** K1 does not turn arbitrary higher-universe values into generated witnesses; it only carries parameters already fixed by the target.
- **G9 COMPLEXITY:** implementation diff / mechanism surface is recorded and ordinary search budget is held fixed.

## Strong pass

`PASS_V117_TYPE1_CONSTRUCTOR_DEVELOPMENT` requires G0–G9.

## Negative outcomes

- `NULL_WRONG_OBSTRUCTION`: the documented Strata issue is not reproduced by the acquisition fixture.
- `NULL_K0_COMPOSITION`: existing K0 mechanism already handles the target after lawful composition/configuration.
- `NULL_NO_HELDOUT_TRANSFER`: K1 solves acquisition but not real Strata.
- `NULL_NO_CAUSALITY`: ablation does not restore failure.
- `HARMFUL`: existing protected derivations regress.
- `INVALID_LEAKAGE`: a solution to this exact Type-1 parameter mechanism is inspected before K1 is frozen.
- `INVALID_SPECIAL_CASE`: K1 encodes Strata/LExpr-specific knowledge.
- `INFRA`: Lean/Specimen environment cannot be reproduced.

## Allowed claim if passed

> In a pinned natural Lean metaprogramming system, a verifier-reproduced constructor obstruction caused by a fixed higher-universe structure parameter was resolved by a generic new parameter-carrying mechanism learned on a separate acquisition fixture; the same frozen mechanism transferred causally to an independently authored Strata typing relation and preserved existing behavior.

This remains a bounded constructor-development result, not arbitrary autonomous meta-language invention.
