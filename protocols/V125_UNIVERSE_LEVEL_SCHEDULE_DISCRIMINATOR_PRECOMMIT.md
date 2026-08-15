# V125 — Universe-level schedule discriminator precommit

Date frozen: 2026-08-16 NZST

## Motivation

V124 run 31893364853 reproduced a real residual after the exact frozen V120 K2 patch: generated schedules contain unknowns of type `LExprParamsT : Type 1` where downstream generated machinery expects `Type`. This is a new residual, not evidence that V120 K2 failed on the binder-role distinction it was designed to repair.

V124 is a known-world Strata validation and must not be tuned directly until the residual is isolated outside Strata.

## Question

Under exact frozen V120 K2, does an otherwise matched constructor/typing-generation task change outcome solely when a fixed parameter lives in `Type 1` rather than `Type`?

## Frozen discriminator

Create two new controlled relations in Specimen after this protocol commit.

- Arm U0: fixed implicit parameter type itself lives in `Type`; derive a constrained generator over a parameterized data family.
- Arm U1: structurally matched fixed implicit parameter type itself lives in `Type 1`; derive the same-shaped constrained generator.

Both arms must have the same constructor count, same field shapes modulo parameter universe, same output request shape, and use the exact frozen V120 K2 patch unchanged.

## Sequence

1. Verify exact V120 K2 can be applied unchanged.
2. Run U0 under K2.
3. Run U1 under K2.
4. Record complete Lean diagnostics for each.

No K3 or other repair may be designed or applied until U0/U1 outcomes are recorded.

## Gates

- G1: U0 compiles under exact K2.
- G2: U1 fails under exact K2 with a universe/sort diagnostic involving `Type 1` versus `Type`, or equivalent generated-schedule universe mismatch.
- G3: the two fixtures are structurally matched except parameter universe.

Verdict `PASS_V125_UNIVERSE_DISCRIMINATOR` iff G1-G3 all hold.

If U0 and U1 both pass, verdict `NULL_UNIVERSE_NOT_SUFFICIENT`.
If both fail for same non-universe reason, verdict `INVALID_DISCRIMINATOR`.
If U1 fails for a different mechanism, record that mechanism and do not rescue the hypothesis.

## Claim boundary

A pass isolates a new universe-level acquisition obstruction after V120. It does not show a repair, does not count as natural transfer, and does not change the V120 claim.
