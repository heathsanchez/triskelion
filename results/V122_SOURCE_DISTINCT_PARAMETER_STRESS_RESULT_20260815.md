# V122 — source-distinct fixed-parameter stress result

**Status:** `PASS_V122_SOURCE_DISTINCT_STRESS`

**External substrate:** `heathsanchez/specimen`

**Hosted workflow run:** `31881893498`

**Head SHA:** `39650c5cde7cb611e9d57f8c466cefe589dfab57`

**Artifact:** `v122-source-distinct-parameter-stress`

**Artifact digest:** `sha256:7c0ece15e1d115ec9dd7441bb913ba68ac852b5af54c8b662901a823a8a654a3`

## Frozen stress arms

Arm A used a new uniform value-parameter family whose constructor carries two genuine fields (`Nat` and `Bool`).

Arm B used a new recursive uniform value-parameter family with a base constructor and a recursive constructor carrying both a `Nat` payload and a recursive child.

Neither arm was used to design or modify V120 K2.

## Hosted result

K0:

- Arm A: FAIL (`rc=1`)
- Arm B: FAIL (`rc=1`)

Exact frozen V120 K2:

- Arm A: PASS (`rc=0`)
- Arm B: PASS (`rc=0`)
- existing explicit/index matched control: PASS
- existing implicit/uniform acquisition: PASS

Ablation back to K0:

- Arm A: FAIL (`rc=1`)
- Arm B: FAIL (`rc=1`)

Workflow verdict: `PASS_V122_SOURCE_DISTINCT_STRESS`.

## Interpretation

The V120 mechanism is not limited to the acquisition's nullary single-constructor shape. It transfers unchanged to a field-carrying constructor and to a recursive family while preserving genuine constructor fields and recursive structure. Removing K2 restores both failures.

This is strong controlled structural generalization and causal ablation.

## Claim boundary

V122 remains protocol-authored after K2 was frozen, so it is **not** counted as natural blind transfer. It supports mechanism generality, not the final source-distinct natural constructor-development capstone.
