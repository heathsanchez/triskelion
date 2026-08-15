# V118 Strata transfer — attempt 2

**Run:** `31880526053`

**Artifact digest:** `sha256:a3cc5cac696cd4d6e0dc307396b7d27380b4bb4be49f19394588226098e8876e`

## Verdict

`INVALID_TARGET_SHAPE — NO K1 TRANSFER ADJUDICATION`

After the first harness repair, both K0 and frozen K1b reached the held-out file. Both stopped at the same `derive_mutual` target-shape precondition before constructor derivation:

`V118T0 is expected to be a variable.`

The target had specialized the parameterized Strata family through a constant abbreviation `V118T0`. Specimen's constrained deriver requires such family parameters to appear as bound variables in the derivation specification.

Consequently the later typeclass-synthesis failure is downstream of the missing derivation, not evidence against K1b.

## Scientific handling

- K1b remains frozen and unchanged at `261e394efdbe0e210b16b19a0dd33ba53052bd40`.
- No constructor-level Strata evidence was exposed in this attempt.
- The only admissible correction is to express the same natural target with the parameter as an input variable, supplying the required metadata typeclass assumptions generically.
- If that corrected target reaches constructor derivation, its result will be the first valid held-out transfer adjudication.
