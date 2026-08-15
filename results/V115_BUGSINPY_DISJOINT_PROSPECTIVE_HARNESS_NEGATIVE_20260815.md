# V115 BugsInPy Disjoint Prospective — Harness Negative

Hosted run: `31872297730`

Hosted job: `94982722493`

Head: `dbf7595df0728e13b775d761688a3a08059affe8`

Artifact: `9243826406`, digest `sha256:9973bf23918853941443063f7170761c664bcd564b6ea63aca2ccf8be7d6cd5e`.

## Verdict

**INCOMPLETE / HARNESS — no scientific prospective result.**

The workflow completed successfully as infrastructure, but the scientific run reached zero qualified cases and tested zero repair candidates.

All selected cases failed at provisioning with:

`This is not a checkout project folder`

The cause is now identified from the pinned BugsInPy checkout implementation. `bugsinpy-checkout -w ROOT` clones the project into `ROOT/<project>`, whereas V115 passed the parent `ROOT` to `bugsinpy-compile` and `bugsinpy-test` as though it were the checkout itself.

Thus:

- qualified cases: **0**;
- candidate tests: **0**;
- causal repairs: **0**;
- G2–G6 were never scientifically reached.

Do not treat V115 as evidence against prospective quotient prediction.

## Additional information-boundary correction

Audit of the pinned BugsInPy framework also exposed a second issue that should not be hidden. The stock `bugsinpy-checkout -v 0` script internally resets to the fixed commit long enough to stage benchmark test files/change metadata before resetting to the buggy commit. V115's artifact stated `fixed_revision_checked_out=false`, which is too strong as a description of the *framework's internal provisioning path*.

The primary repair-search Python did not inspect fixed implementation source, a known patch, or repair text, and no candidate outcome was reached. Nevertheless, future protocols should distinguish:

1. **verifier provisioning** — the benchmark framework may stage test files from the fixed revision;
2. **repair-search information** — the algorithm must not inspect fixed production implementation, patch/diff, human repair text, or target-derived relation updates.

A stricter replacement experiment must use a disjoint target set and state this boundary honestly before execution.

## Consequence

V115 remains preserved as a useful harness negative. It must not be repaired in place and then reported as if the original run had exercised the frozen scientific gates. A disjoint successor should be used for the next prospective attempt.
