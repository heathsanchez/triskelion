# V132 — output-dependent input-determined parameter acquisition precommit

Date frozen: 2026-08-16 NZST

## Prior evidence

- V126 isolated a computed-parameter bridge: direct family parameter passed, deterministic transformed family parameter failed under V120 K2.
- V128 showed that preserving every input-determined proper application can causally repair that acquisition.
- V129 rejected that broad K4 because the full protected suite regressed in ordinary computed term/pattern cases.
- V130 rejected constructor fixed-parameter position as a separator.
- V131 prospectively found a structural separator: `V126Lift p` occurs in the inferred dependent type/family of an output-position term, while protected `x * x` does not.

## Frozen K5 hypothesis

`PRESERVE_INPUT_DETERMINED_OUTPUT_TYPE_APPLICATION`.

A proper application may bypass flattening only if BOTH conditions hold before conclusion unification:

1. all free-variable dependencies of the application occur in constructor conclusion relation-input positions (all positions not listed in `outputIndices`); and
2. the exact application occurs in the inferred type of at least one constructor conclusion output-position argument.

This is the conjunction of the necessary causal criterion from V128 and the scope separator from V131.

The rule may not inspect target names, Strata identifiers, `V126`, `V126Lift`, `mono`, `LExprParamsT`, concrete function names, universe level, or later unification results.

## Frozen patch scope

Modify only conclusion linearization/flattening in `Specimen/DeriveConstrainedProducer.lean`.

Do not modify:

- V120 K2;
- scheduler scoring;
- `ArbitrarySizedSuchThat`;
- generated pattern semantics;
- V125/V126/V119/V122 fixtures;
- protected tests;
- unification semantics.

## Acquisition sequence

1. Apply exact frozen V120 K2.
2. Reproduce V126 MAP failure.
3. Apply K5 unchanged.
4. Require V126 MAP pass.
5. Run frozen controls.
6. Remove K5 while retaining K2 and require V126 MAP failure to return.
7. Run the full ordinary protected Specimen build/test surface under K2+K5 without exclusions or rewrites.

## Frozen controls

All must pass under K2+K5:

- V126 ID;
- V125 U1 direct `Type 1` fixed parameter;
- V119 explicit/index;
- V119 implicit/uniform;
- V122 field-carrying;
- V122 recursive;
- isolated ordinary multiplication/function-call fixture equivalent to the V129 protected counterexample.

## Gates

G1: K2 reproduces V126 MAP failure.
G2: K2+K5 makes V126 MAP pass.
G3: all frozen controls pass.
G4: removing K5 while retaining K2 restores V126 MAP failure.
G5: ordinary `lake build` passes under K2+K5.
G6: full unfiltered `lake test` passes under K2+K5.
G7: K5 patch contains no target-specific names.
G8: K5 uses only input-position dependency plus output-dependent-type role available before conclusion unification.

Verdict `PASS_V132_OUTPUT_DEPENDENT_PARAMETER_ADMISSION` iff G1-G8 all hold.

If G2 fails: reject K5 as insufficient.
If G3/G5/G6 fail: reject K5 as harmful.
If G4 fails: reject causal attribution.

## Post-pass rule

Only after V132 passes may exact frozen K5 be replayed on the already-known V124 direct Strata target. That replay remains known-world validation, not blind transfer.

## Claim boundary

A pass supports a narrow retained constructor mechanism inside pinned Specimen: deterministic computed applications that are fully input-determined and carried in the dependent type of an output can remain symbolic instead of becoming independent generation obligations.

It does not establish arbitrary dependent computation or universal higher-universe generation.
