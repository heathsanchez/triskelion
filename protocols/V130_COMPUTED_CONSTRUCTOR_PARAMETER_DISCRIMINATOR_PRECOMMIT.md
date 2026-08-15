# V130 — computed constructor-parameter discriminator precommit

Date frozen: 2026-08-16 NZST

## Prior falsifier

V128 K4 prospectively repaired the V126 MAP acquisition by preserving every proper application whose free variables came only from relation input positions. V129 then rejected K4 as harmful on the full protected suite. Existing function-call tests showed why: ordinary computed *term* expressions such as `x * x`, despite being input-determined, must still be flattened so generated patterns remain lawful.

Therefore `input-determined` is not sufficient. The next distinction is structural role of the computed application.

## Question

Does the V126 acquisition application occupy a constructor-family **parameter position**, while the protected counterexamples occupy ordinary term/pattern positions?

## Frozen discriminator

Instrument conclusion traversal without changing generation semantics. For every proper application that the original linearizer would flatten, classify whether that exact application occurs as an argument to a constructor application in one of that constructor's fixed parameter positions (`arg index < ctorInfo.numParams`), and record the binder info of that constructor parameter.

Run this classifier on:

1. V126 MAP acquisition fixture;
2. `square_of'` / function-call protected fixture containing `x * x`;
3. the V119 explicit/index and implicit/uniform fixtures.

No repair is permitted in V130.

## Gates

G1: V126 `V126Lift p` is classified as occurring in a constructor fixed-parameter position.
G2: protected ordinary computation `x * x` is not classified as a constructor fixed-parameter occurrence.
G3: classification uses only constructor metadata and expression structure, not target names.

Verdict `PASS_V130_CONSTRUCTOR_PARAMETER_DISCRIMINATOR` iff G1-G3 hold.

If G1 fails, reject this refinement. If G2 fails, constructor-parameter role is still too broad and no K5 may be built from it.

## Claim boundary

A pass only isolates a structural separator for the harmful K4 overgeneralization. It does not itself repair V126 or justify a Strata replay.
