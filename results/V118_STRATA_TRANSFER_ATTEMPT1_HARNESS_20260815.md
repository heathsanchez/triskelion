# V118 Strata transfer — attempt 1

**Run:** `31880420520`

**Artifact digest:** `sha256:5852e0cac011b1a08a89edc00ebad983981212ff1d2aa49fa85df0d30224087a`

## Verdict

`INFRA / HARNESS — NO SCIENTIFIC TARGET OBSERVATION`

Both the nominal K0 and K1b target executions failed before elaborating the held-out derivation because the workflow had built only the default `Specimen` library. `V118StrataDirectTransfer.lean` imports `SpecimenTest.StrataLexprGen`, and the `SpecimenTest` lean library had not been built into the search path.

Observed error in both arms:

`unknown module prefix 'SpecimenTest'`

Therefore:

- K0 ablation was not actually tested;
- K1b transfer was not actually tested;
- no Strata target evidence was exposed;
- the frozen K1b implementation remains unchanged.

The corrective action is harness-only: build the existing `SpecimenTest` lean library before invoking the standalone held-out target. The scientific protocol and K1b source remain frozen.
