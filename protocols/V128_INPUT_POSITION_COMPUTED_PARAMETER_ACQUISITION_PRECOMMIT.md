# V128 — Input-position computed-parameter acquisition precommit

Date frozen: 2026-08-16 NZST

## Prior evidence and falsifier

V126 prospectively isolated a computed-parameter bridge: direct family parameter ID passed under V120 K2, while a matched MAP family parameter `lift p` failed with a fresh hidden unknown/equality producer obligation.

V127 K3 was rejected. It tried to recognize fixed dependencies by comparing constructor-local free-variable user names directly against the top-level producer `inputNames`. The V126 MAP residual remained unchanged. This showed that name identity is the wrong coordinate before conclusion unification: constructor-local forall variables are only later unified with top-level input variables.

## Frozen K4 hypothesis

`PRESERVE_INPUT_POSITION_COMPUTED_PARAMETER`.

Before conclusion unification, the stable structural information is not top-level variable naming but **relation argument position**.

For each proper function application collected from a constructor conclusion:

1. collect the free variables occurring in that application;
2. collect free variables occurring in the constructor conclusion's relation-input argument positions, i.e. all conclusion argument positions not listed in `outputIndices`;
3. if every free variable of the application occurs in those input-position variables, treat the application as input-determined and preserve it symbolically rather than flattening it into a fresh unknown plus equality premise;
4. otherwise retain existing flattening behavior.

A closed proper application with no free variables is also input-determined.

This rule may not inspect target names, eventual unification outcomes, Strata identifiers, or concrete functions.

## Frozen patch scope

Modify only `linearizeAndFlatten` in `Specimen/DeriveConstrainedProducer.lean` plus its helper logic. Do not modify:

- V120 K2;
- scheduler scoring;
- `ArbitrarySizedSuchThat` or `Gen`;
- V125/V126 fixtures;
- unification semantics.

## Acquisition sequence

1. Apply exact frozen V120 K2.
2. Reproduce V126 MAP failure.
3. Apply K4 unchanged.
4. Test acquisition and controls.
5. Ablate K4 while retaining K2 and require V126 MAP failure to return.

## Frozen controls

Under K2+K4 all must pass:

- V126 ID;
- V125 U1;
- V119 explicit/index;
- V119 implicit/uniform;
- V122 field-carrying;
- V122 recursive;
- ordinary `lake build`.

## Gates

G1: K2 reproduces V126 MAP failure.
G2: K2+K4 makes V126 MAP pass.
G3: all frozen controls pass.
G4: removing K4 while retaining K2 restores V126 MAP failure.
G5: K4 contains no target-specific names (`V126`, `V126Lift`, Strata, `mono`, `LExprParamsT`).
G6: K4 uses only conclusion input/output structure available before unification.

Verdict `PASS_V128_INPUT_POSITION_COMPUTED_PARAMETER_ACQUISITION` iff G1-G6 hold.

If G2 fails, reject K4. If any protected control fails, reject K4 as harmful. No adjustment using V124 is permitted during V128.

## Post-pass rule

Only after a V128 pass may the exact frozen K4 be replayed against V124 direct Strata. That replay remains a known-world transfer test, not a blind test.

## Claim boundary

A pass would support a generic structural distinction: a computed family parameter determined entirely by constructor relation-input positions need not be converted into an independently generated value. It would not establish arbitrary dependent computation or higher-universe generation.
