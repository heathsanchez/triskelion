# V118 — fixed-parameter binder distinction precommit

**Status:** FROZEN BEFORE V118 TARGET EXECUTION

## Discovery source

V117 qualification falsified the hypothesis that the documented Specimen limitation was specifically caused by a `Type 1` structure parameter. Matched lower- and higher-universe fixtures both failed with the same residual: an inductive constructor whose uniform parameter is implicit was emitted as though the parameter were an ordinary explicit constructor argument.

V118 changes the representation of the obstruction before any K1 implementation.

## Question

Does Specimen's constrained constructor language currently collapse two roles that need to remain distinct:

1. **fixed/uniform inductive parameter supplied by the target context**, and
2. **explicit constructor/index argument that generated code must apply**?

If so, can a minimal binder-aware constructor representation restore constructibility and transfer to the natural Strata parameterized-expression case?

## Frozen matched acquisition test

Use the same ordinary-universe parameter structure `P : V118Params` in both arms.

### Arm A — explicit/index control

Define an inductive family where `P` is an explicit constructor/index argument, e.g. the constructor itself takes `P` explicitly.

Expected under K0: derivation succeeds.

### Arm B — implicit/uniform parameter acquisition

Define the semantically analogous family using `inductive Expr (P : V118Params)` where the constructor carries `P` only as the uniform inductive parameter.

Expected under K0: derivation fails by applying the implicit parameter as an ordinary explicit argument.

The two arms must remain otherwise minimal and structurally matched.

## Qualification outcomes

- `QUALIFIED_FIXED_PARAMETER_OBSTRUCTION`: explicit arm passes and implicit/uniform arm fails with parameter-application residual.
- `NULL_TOO_BROAD`: both arms fail.
- `NULL_ALREADY_SUPPORTED`: both arms pass.
- `NULL_DIFFERENT_FAILURE`: acquisition fails for an unrelated reason.
- `INFRA`: Specimen cannot be reproduced.

No K1 work begins unless `QUALIFIED_FIXED_PARAMETER_OBSTRUCTION` is obtained.

## Frozen K1 mechanism family

If qualified, the only admissible constructor-language extension is:

`BINDER_AWARE_FIXED_PARAMETER`

The mechanism may change how constructor applications represent or emit fixed parameters, including preserving binder info or omitting parameters already supplied implicitly by expected result type/context.

It may **not**:

- special-case V118 fixture names or Strata identifiers;
- increase generic search limits;
- add a hand-written generator for the target expression relation;
- monomorphize/copy the target datatype;
- rewrite the natural held-out target into a different relation;
- read a known upstream solution implementing this exact mechanism, if one is later discovered.

## Development rule

K1 is developed from only:

- V118 acquisition residual;
- generic Specimen source involved in constructor representation/emission;
- Lean elaboration diagnostics;
- the frozen mechanism family above.

The broad Strata limitation is already known, so the later target is source-distinct but **not sealed/unseen**. No stronger claim is permitted.

## Held-out natural target

After K1 is frozen, apply it to the actual parameterized Strata `Lambda.LExpr`/typing relation rather than the `LExprU` copied workaround.

Success requires generated samples to be checked by the unchanged typing relation, not merely elaboration of a derivation command.

## Gates

- **G0:** pinned Specimen base builds.
- **G1:** matched acquisition qualifies: explicit/index control passes, implicit/uniform parameter arm fails.
- **G2:** failure trace identifies binder/parameter application rather than unrelated missing instance/search exhaustion.
- **G3:** minimal generic K1 makes acquisition pass.
- **G4:** K1 does not alter the explicit/index control outcome.
- **G5:** current Specimen protected suite remains passing.
- **G6:** frozen K1 transfers to direct natural Strata parameterized derivation without copied monomorphic datatype.
- **G7:** generated Strata samples satisfy the unchanged typing relation.
- **G8:** ablating only K1 restores the natural-target failure.
- **G9:** complexity accounting identifies the new representational distinction; generic search/compute is held fixed.

## Strong verdict

`PASS_V118_FIXED_PARAMETER_CONSTRUCTOR_DEVELOPMENT` requires G0–G9.

## Claim boundary

A pass would support:

> In a pinned natural Lean metaprogramming system, a verifier-grounded residual exposed a missing binder-role distinction in the constructor representation; a minimal generic extension developed on an independent fixture causally expanded constructibility and transferred to a source-distinct real typing relation.

It would not support blind discovery of the Strata limitation, arbitrary meta-language invention, or open-ended recursive self-improvement.
