# V128 — input-position computed-parameter acquisition result

**Status:** `PASS_V128_INPUT_POSITION_COMPUTED_PARAMETER_ACQUISITION`

**External substrate:** `heathsanchez/specimen`

**Valid hosted workflow run:** `31894188189`

**Job:** `95034821711`

**Head SHA:** `94cd0c0174ccc9a757a019f7cd4427e863f88eaf`

**Artifact:** `v128-input-position-computed-parameter`

**Artifact ID:** `9249352289`

**Artifact digest:** `sha256:66e03b82e31d4a2eb2dafbbbdadb65f420c31d0fc3adb8c2f15f2dd73609f6c6`

## Precommit

`protocols/V128_INPUT_POSITION_COMPUTED_PARAMETER_ACQUISITION_PRECOMMIT.md`, commit `a44114a39a49cc44aa9ccf6a885df869db8c2e04`.

The frozen K4 rule uses only constructor-conclusion input/output position structure available before unification. Proper function applications whose free-variable dependencies are entirely contained in relation input positions are preserved symbolically instead of flattened into a fresh independently-produced unknown plus equality premise.

## Harness-only repairs

Run 1 (`31894011102`) was invalid before scientific execution because a mutable local was shadowed in the Lean patch implementation.

Run 2 (`31894086359`) was invalid before scientific execution because `List.all` requires a Boolean predicate while the patch used proposition-valued membership.

Both fixes preserved the frozen subset criterion exactly; no fixture, gate, target, or scientific decision rule changed.

## Valid hosted result

Under exact V120 K2 alone, the V126 MAP obstruction reproduced:

- V126 MAP: FAIL (`rc=1`).

Under K2 + frozen V128 K4:

- V126 MAP acquisition: PASS (`rc=0`).
- V126 ID control: PASS (`rc=0`).
- V125 direct `Type 1` control: PASS (`rc=0`).
- V119 explicit/index control: PASS (`rc=0`).
- V119 implicit/uniform acquisition: PASS (`rc=0`).
- V122 field-carrying arm: PASS (`rc=0`).
- V122 recursive arm: PASS (`rc=0`).
- ordinary package build: PASS.

Ablation removed K4 while retaining exact V120 K2:

- V126 MAP returned to FAIL (`rc=1`).

Workflow verdict: `PASS_V128_INPUT_POSITION_COMPUTED_PARAMETER_ACQUISITION`.

## Causal transition

The controlled capability transition is therefore:

`K2 FAIL -> K2+K4 PASS -> remove K4 while retaining K2 -> FAIL`.

The acquisition is selective: direct fixed parameters, higher-universe direct parameters, explicit/index parameters, field-carrying families, and recursive families remain valid.

## Interpretation

V127 showed that constructor-local names cannot be compared directly to eventual top-level input names before conclusion unification. V128 changed coordinates rather than broadening the exception: it used relation input positions, which are invariant at the point where linearization decides whether a computed subterm must become an independent producer obligation.

This repairs the exact mechanism prospectively isolated by V126: a deterministic family parameter computed entirely from already-fixed relation inputs no longer has to be rediscovered as a fresh value.

## Developmental sequence

1. V124 known-world residual exposed `unk = T.mono` after V120.
2. V125 rejected the coarse `Type 1` explanation.
3. V126 prospectively isolated computed-parameter flattening.
4. V127 rejected a name-coordinate repair.
5. V128 used the sharper input-position coordinate and produced causal acquisition with protected controls and ablation.

## Claim boundary

V128 supports a generic structural mechanism inside pinned Specimen: deterministic computed family parameters whose free-variable dependencies are entirely relation inputs can be carried symbolically rather than converted into independent generation obligations.

It does **not** establish arbitrary dependent computation, arbitrary higher-universe generation, or natural blind transfer. Full protected-suite validation and exact frozen replay on the already-known Strata case remain separate gates.
