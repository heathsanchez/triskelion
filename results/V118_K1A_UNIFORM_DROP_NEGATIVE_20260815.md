# V118 K1a — uniform-parameter drop candidate

**Hosted run:** `31880191980`

**Artifact:** `v118-k1-acquisition`

**Artifact digest:** `sha256:9035b01c66c6a257add8c8a194cb98f0b414d460db65e998cbadddd1447f587f`

## Candidate

K1a used constructor metadata `numParams` to remove all uniform inductive parameters before `ConstructorExpr` emission.

## Result

Frozen K0 reproduction:

- explicit/index control: PASS
- implicit/uniform acquisition: FAIL

After K1a:

- implicit/uniform acquisition: **PASS**
- explicit/index protected control: **FAIL**

The protected-control failure was:

`pure V118ExplicitExpr.unit`

where Lean expected `V118ExplicitExpr a_1`; the constructor still required its explicit `P` argument.

## Verdict

`REJECT_K1A — OVERCOLLAPSED_BINDER_ROLES`

K1a repaired the acquisition residual but was too coarse. `ConstructorVal.numParams` alone does not identify which parameters should be omitted from emitted syntax: a parameter can be uniform in the inductive metadata yet still be an explicit constructor binder that must be supplied.

## Representation update

The missing distinction is therefore sharper than:

`UNIFORM PARAMETER != CONSTRUCTOR ARGUMENT`.

It must preserve at least:

`IMPLICIT UNIFORM PARAMETER != EXPLICIT UNIFORM PARAMETER`.

The successor K1 candidate must use binder information, not only uniform-parameter count.

No held-out Strata target was executed. K1a is retained as a protected-control negative and is not admitted.
