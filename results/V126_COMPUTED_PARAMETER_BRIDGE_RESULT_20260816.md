# V126 — computed-parameter bridge discriminator result

**Status:** `PASS_V126_COMPUTED_PARAMETER_BRIDGE`

**External substrate:** `heathsanchez/specimen`

**Hosted workflow run:** `31893628193`

**Job:** `95033473902`

**Artifact:** `v126-computed-parameter-bridge`

**Artifact ID:** `9249202680`

**Artifact digest:** `sha256:dcc4d73242f38df157cef2c8e8939b3e9b74ce7b459087dca649726a7054ad69`

## Precommit

Protocol frozen before fixture outcomes: `protocols/V126_COMPUTED_PARAMETER_BRIDGE_DISCRIMINATOR_PRECOMMIT.md`, commit `414b5da8d0d08725eb39b1b7004f848b6470ae6d`.

## Frozen matched arms

Both arms use exact V120 K2 and the same basic constructor/relation shape.

- ID: relation fixed parameter `p : V126Base`; constructed data family directly parameterized by `p`.
- MAP: relation fixed parameter `p : V126Base`; constructed data family parameterized by deterministic `V126Lift p : V126Wrapped`, where `V126Wrapped : Type 1`.

V125 had already established that the universe level alone was not sufficient.

## Hosted result

- ID: PASS (`rc=0`).
- MAP: FAIL (`rc=1`).

The MAP diagnostic contains exactly the sharpened mechanism:

- fresh `unk_0` has type `V126Wrapped` of sort `Type 1` but generated producer machinery expects sort `Type`;
- the generated property is `fun unk_0 => unk_0 = V126Lift a_1`.

Workflow verdict: `PASS_V126_COMPUTED_PARAMETER_BRIDGE`.

## Interpretation

The failure is not explained by `Type 1` alone. It appears when conclusion linearization converts a deterministic family parameter computed from already-fixed inputs into a fresh independently-produced unknown plus equality obligation.

This closely matches V124's known-world `unk = a_1.mono` residual and prospectively isolates a second representation barrier after V120.

## Developmental significance

The sequence is now:

1. V119/V120: distinguish implicit fixed constructor parameters from explicit constructor material.
2. V121/V122: preserve existing behavior and generalize structurally.
3. V124: encounter a distinct residual in a known natural world.
4. V125: reject the coarse universe-only explanation.
5. V126: isolate computed fixed-parameter flattening as the sharper mechanism.

## Claim boundary

V126 isolates a controlled mechanism; it does not itself repair it and does not count as natural transfer.
