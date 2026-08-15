# V120 — binder-aware fixed-parameter acquisition result

**Status:** `PASS_V120_ACQUISITION`

**External substrate:** `heathsanchez/specimen`

**Hosted workflow run:** `31881547168`

**Head SHA:** `12cebb1d004126685cd2509f9f25a5c612a1c176`

**Artifact:** `v120-binder-aware-fixed-parameter`

**Artifact digest:** `sha256:5c9e3f2e928ff3ce943a7ad79b6210eb9d59a45f3458a5203d9b3194572e9418`

## Frozen K0 discriminator

Hosted reproduction before intervention:

- explicit/index control: `rc=0`
- implicit/uniform fixed-parameter acquisition: `rc=1`

So the V118 obstruction reproduced without drift.

## V119 negative used for refinement

V119's parameter-count-only rule repaired the implicit arm but broke the explicit control. That falsified `drop all ctorInfo.numParams arguments` and justified a binder-aware acquisition refinement before any natural held-out execution.

## Frozen V120 mechanism

`CARRY_IMPLICIT_FIXED_PARAMETER` reads the constructor telescope and considers only the leading positions identified by `ctorInfo.numParams`.

It omits a parameter from reconstructed constructor syntax only when the constructor binder is implicit, strict-implicit, or instance-implicit. A default/explicit binder is retained. All non-parameter arguments remain eligible for the pre-existing argument filtering logic.

The mechanism contains no acquisition type name, constructor name, Strata name, or held-out name.

## Hosted result

After applying the frozen K2 patch:

- explicit/index control: `rc=0`
- implicit/uniform acquisition: `rc=0`

The workflow emitted:

`PASS_V120_ACQUISITION`

The patch compiled successfully as `Specimen.DeriveConstrainedProducer` before the acquisition arms were rerun.

## Causal sequence so far

`K0: explicit PASS / implicit FAIL`

→ naive V119 parameter-count intervention

`explicit FAIL / implicit PASS`

→ binder-role refinement

`K2: explicit PASS / implicit PASS`.

This is a selective representation correction rather than generic search expansion.

## Interpretation

The acquisition evidence supports the distinction:

`EXPLICIT CONSTRUCTOR ARGUMENT != IMPLICIT UNIFORM PARAMETER`.

For constructor reconstruction, an implicit uniform parameter belongs to carried family context rather than the emitted constructor-field list.

## Claim boundary

This is still only an acquisition pass. It does **not** yet establish constructor-language growth, source-distinct transfer, natural-world transfer, or full protected-suite preservation.

The exact K2 mechanism is frozen by the committed patch script and workflow head above. Natural held-out selection must occur only after this point and cannot be used to alter K2.
