# V126 — Computed-parameter bridge discriminator precommit

Date frozen: 2026-08-16 NZST

## Prior evidence

V124 run 31893364853, after harness repair, failed under exact frozen V120 K2 with generated-schedule constraints involving an unknown `LExprParamsT` and equality to `a_1.mono`.

V125 then falsified the simpler hypothesis that `Type 1` alone is sufficient: under exact K2, matched U0 (`Type`) and U1 (`Type 1`) arms both compiled. Therefore no K3 may be justified as a generic universe-level fix.

## Question

Is the remaining V124 residual caused by a *computed parameter bridge*: the relation is parameterized by one object `p`, while the recursively constructed datatype is parameterized by a deterministic transform `lift p`, forcing generated scheduling machinery to represent/equate a hidden family parameter rather than merely carry the relation parameter itself?

## Frozen matched discriminator

Create two controlled arms after this commit.

- ID arm: a relation with an implicit fixed parameter `p` and a data family directly parameterized by `p`.
- MAP arm: same relation/constructor shape, but the relation has implicit fixed parameter `p : Base` while the data family is parameterized by `lift p : Wrapped`.

`Wrapped` must live in `Type 1` to match the relevant V124 shape, but V125 has already shown that universe level alone is insufficient.

Use the exact frozen V120 K2 unchanged.

## Gates

- G1: ID arm compiles under exact K2.
- G2: MAP arm fails under exact K2.
- G3: MAP diagnostics contain an equality or schedule-generation mismatch involving the transformed hidden parameter (for example an unknown `Wrapped` constrained to equal `lift p`), analogous in mechanism to V124's `unk = a_1.mono` residual.
- G4: no repair is attempted in this experiment.

Verdict `PASS_V126_COMPUTED_PARAMETER_BRIDGE` iff G1-G4 hold.

If both arms pass: `NULL_COMPUTED_BRIDGE_NOT_SUFFICIENT`.
If both arms fail for the same reason: `INVALID_DISCRIMINATOR`.
If MAP fails for a different mechanism, record it and reject the bridge hypothesis.

## Claim boundary

A pass isolates the next representation barrier after V120. It does not repair Strata and does not count as natural transfer.
