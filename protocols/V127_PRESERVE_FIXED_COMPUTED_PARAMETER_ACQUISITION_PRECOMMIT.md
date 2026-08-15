# V127 — Preserve fixed computed parameter acquisition precommit

Date frozen: 2026-08-16 NZST

## Prior evidence

- V120 K2 repaired the implicit-fixed-constructor-parameter obstruction while preserving the explicit/index control.
- V121 preserved the full current Specimen suite.
- V122 generalized K2 to field-carrying and recursive controlled families with ablation.
- V124 direct known-world Strata remained blocked after K2 by a fresh hidden parameter equality of the form `unk = T.mono` where the hidden parameter lives in `Type 1`.
- V125 falsified the hypothesis that `Type 1` alone is sufficient: matched direct `Type` and `Type 1` fixed-parameter arms both passed under K2.
- V126 prospectively isolated the sharper mechanism: ID arm passed, while a matched MAP arm whose family parameter was a deterministic transform `V126Lift p` failed with the same generated equality/sort shape as V124.

## Frozen K3 hypothesis

`PRESERVE_FIXED_COMPUTED_PARAMETER`.

When a proper function application occurs in a constructor conclusion and **all free variables on which that application depends are already fixed top-level inputs**, the application is a deterministic carried parameter. It should not be flattened into a fresh independently-produced unknown plus equality premise.

Instead, preserve that function application symbolically through conclusion unification. The existing range representation can carry an application head plus argument ranges; no inverse or new generator is required because the application is never an output to discover.

This rule is generic. It may inspect only free-variable dependence on the frozen input-name set. It may not mention Strata, `mono`, `V126`, `V126Lift`, `LExprParamsT`, or any concrete target name.

## Frozen patch scope

Patch only the conclusion linearization/flattening path in `Specimen/DeriveConstrainedProducer.lean`:

1. Make `linearizeAndFlatten` aware of top-level `inputNames`.
2. From the proper function applications collected from the conclusion, exclude an application from flattening iff every free variable occurring in that application corresponds to a name in `inputNames`.
3. Continue flattening all other proper function applications exactly as before.
4. Do not change scheduler scoring, `ArbitrarySizedSuchThat`, V120 K2, or test fixtures.

## Acquisition and controls

Run exact V120 K2 first, then K3.

Primary acquisition:
- V126 MAP: K2 FAIL must reproduce; K2+K3 must PASS.

Matched controls:
- V126 ID must PASS under K2+K3.
- V125 U1 (`Type 1` direct fixed parameter) must PASS under K2+K3.
- V119 explicit/index and implicit/uniform pair must both PASS.
- V122 field-carrying and recursive arms must both PASS.

Causal ablation:
- remove K3 while retaining K2; V126 MAP must return to FAIL.

## Gates

G1 K2 reproduces V126 MAP failure.
G2 K2+K3 makes V126 MAP compile.
G3 all frozen controls pass under K2+K3.
G4 K3 ablation restores V126 MAP failure.
G5 K3 patch contains no target-specific names.
G6 ordinary `lake build` succeeds under K2+K3.

Verdict `PASS_V127_FIXED_COMPUTED_PARAMETER_ACQUISITION` iff G1-G6 hold.

If G2 fails, reject K3 as insufficient. If a protected control fails, reject as harmful. No tuning against V124 is allowed during V127.

## Post-acquisition rule

Only if V127 passes may the exact frozen K3 be replayed on V124 direct Strata as a known-world transfer test. V124 remains known-world, not blind transfer.

## Claim boundary

A pass supports a second acquired mechanism: deterministic function-valued family parameters of already-fixed inputs can be carried symbolically rather than converted into impossible independent producer obligations. It does not establish arbitrary dependent-function support.
