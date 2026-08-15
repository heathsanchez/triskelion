# V115B — BugsInPy third-ID prospective test

**Canonical ID:** `V115B_BUGSINPY_THIRD_ID_PROSPECTIVE`

**Hosted run:** `31877237725`

**Head SHA:** `f8a1153798296e5183f7f9c06c9e1ff5393b2422`

**Artifact:** `v115b-bugsinpy-third-id-prospective`

**Artifact digest:** `sha256:faa1174dc630bf0e1938201ade1ee97793aa89a7c66a0f5fd81087cc2a052678`

## Verdict

`INVALID_FOR_CROSS_CORPUS_SCIENTIFIC_CLAIM — ENVIRONMENT-CONFOUNDED QUALIFICATION`

The GitHub Actions job itself completed successfully and executed the full committed search. The artifact reports 12 nominally qualified cases, 702 one-site comparison candidates tested, 702 candidate rejections, zero causal repairs, and zero hits in the two quotient classes frozen from V110.

Those counts are **not** admitted as a scientific negative against prospective quotient transfer.

## Why the nominal qualification is invalid

Direct inspection of the primary artifact shows that many baseline failures are caused by historical-environment incompatibility on the Python 3.12 hosted runner rather than reproduced benchmark defects. Examples include:

- PySnooper: the relevant command reaches `pytest: command not found`.
- ansible / thefuck: historical pytest imports `imp`, which is absent in Python 3.12.
- black: historical `regex` extension fails with an undefined Python ABI symbol.
- httpie / keras / pandas / tqdm: historical pytest/`py` combinations fail to import `TerminalWriter`.
- scrapy: dependency import failure (`six.moves`).
- fastapi / sanic / spacy: provisioning timed out in old dependency builds.
- tornado: selected case was `baseline_not_failing`.

Therefore `baseline failing` did not reliably mean `the target historical bug is reproduced under a healthy verifier environment`.

A comparator candidate cannot be expected to repair a broken test/runtime environment. Counting these cases as substantive repair opportunities would turn infrastructure failure into evidence against the hypothesis.

## Frozen result counts

From the hosted artifact:

- nominal `qualified_cases`: **12**
- `candidate_tests`: **702**
- `candidate_rejections`: **702**
- `causal_repairs`: **0**
- `prior_class_hits`: **0**

The artifact's internal gates G2/G3 are implementation-level predicates. Their names must not be interpreted as proof of scientifically valid bug reproduction once the baseline traces are inspected.

## Information-boundary status

The primary search still respected the intended repair-information boundary:

- no fixed production implementation read by the repair search;
- no human repair text read;
- no known patch/diff read;
- no target-derived update to the frozen quotient relation;
- stock BugsInPy provisioning may stage fixed-revision test files.

This boundary is preserved, but it does not rescue the invalid reproduction environment.

## What this result does and does not say

V115B says that the current GitHub-hosted BugsInPy harness is not a scientifically valid cross-corpus discriminator because historical runtime compatibility dominates the selected cases.

It does **not** support either of these claims:

- `the frozen QuixBugs quotient classes transfer prospectively to BugsInPy`;
- `the frozen QuixBugs quotient classes fail to transfer prospectively to BugsInPy`.

Both remain unresolved.

## Required successor condition

Do not create another target split merely to seek a positive result. A future BugsInPy cross-corpus experiment counts only if qualification first establishes a healthy historical execution environment and reproduces the bug-specific expected failure, separately from dependency/interpreter/provisioning failures.

Preferred qualification predicate:

`fixed revision passes relevant tests under the same environment` **and** `buggy revision fails those same tests for a bug-relevant assertion/exception`.

Only after that should blind candidate repair search begin.

This preserves the programme rule: infrastructure is not science, and a failed verifier environment is not a negative capability result.
