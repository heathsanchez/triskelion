# V122 — source-distinct fixed-parameter stress test precommit

**Status:** FROZEN BEFORE TARGET EXECUTION

## Purpose

V120/V121 established acquisition repair plus full protected-suite preservation for `CARRY_IMPLICIT_FIXED_PARAMETER`. Before searching for a natural blind capstone target, test whether the frozen mechanism generalizes beyond the nullary one-constructor acquisition shape.

This is deliberately a **controlled source-distinct mechanism stress test**, not the natural held-out capstone.

## Frozen K2

Use the exact V120 patch script unchanged:

`scripts/v120_apply_binder_aware_fixed_parameter.py`

No K2 modification is permitted in V122.

## Frozen target families

Create two new fixtures that were not used to design K2:

### Arm A — field-carrying uniform parameter

A value-level uniform parameter `P` is implicit in an inductive family, while the constructor has two genuine explicit fields of different types. The relation fixes `P` and constrains a produced family value.

Required shape:

- at least one `Nat` field;
- at least one `Bool` field;
- the uniform `P` is not an explicit constructor field;
- successful emitted constructor syntax must retain both real fields while not over-applying `P`.

### Arm B — recursive uniform parameter

A value-level uniform parameter `P` is implicit in a recursive inductive family with at least:

- one base constructor;
- one recursive constructor carrying a genuine explicit payload plus a recursive child;
- a relation whose constrained producer exercises the recursive family.

The fixture must not copy the V119 acquisition type/name/constructor structure except for the abstract property being tested: one fixed uniform value parameter.

## K0/K2 prediction

For each arm, freeze the prediction before execution:

- K0 should fail from the same family-parameter over-application mechanism;
- exact frozen K2 should pass.

If K0 already passes an arm, record `NULL_ARM_ALREADY_CONSTRUCTIBLE`; do not redesign that arm after observing the result.

## Causal ablation

For every arm that is K0-fail/K2-pass, restore the unmodified `DeriveConstrainedProducer.lean` and rerun the exact same fixture. Failure must return.

## Gates

- G0: pinned Specimen branch builds.
- G1: at least one source-distinct arm is K0-fail.
- G2: every K0-fail arm becomes K2-pass under exact frozen mechanism.
- G3: all K2-pass admissions revert to fail when K2 is ablated.
- G4: existing V119 explicit/index control remains K2-pass.
- G5: existing V119 implicit/uniform acquisition remains K2-pass.
- G6: no K2 source modification.

`PASS_V122_SOURCE_DISTINCT_STRESS` requires G0–G6.

## Claim boundary

A pass supports structural generalization of the frozen binder-aware mechanism across new constructor shapes and recursion. It does **not** count as natural blind transfer because the stress fixtures are protocol-authored after K2 was frozen.

The natural constructor-development capstone remains separately required.
