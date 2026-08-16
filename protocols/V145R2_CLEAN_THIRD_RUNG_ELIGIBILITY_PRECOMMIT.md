# V145R2 — Clean Third-Rung Eligibility

## Purpose
Continue the frozen V145R1 pandas eligibility stream after the mechanically selected `pandas/111` candidate failed the required retrospective exposure audit.

## Apparatus inheritance
V145R2 changes no runtime, corpus, candidate ordering, semantic qualification rule, timeout, or stopping rule from V145R1. It reuses the exact V145R1 qualifier implementation and exact-runtime adapter.

## Exposure revision fixed before execution
The denylist is expanded only from evidence that existed before V145R2 execution. In particular, the prior Witbrock native V10 audit explicitly opened and semantically classified developer repairs for `pandas/146` and `pandas/111`; both are therefore exposure-ineligible for the strongest blind-natural E3 claim. `pandas/66` was already denylisted.

The complete V145R2 denylist is frozen in `protocols/V145R2_EXPOSURE_DENYLIST.json` before any V145R2 runtime qualification outcome is observed.

## Candidate order
All pandas bug IDs in the frozen 501-case BugsInPy manifest are ordered by lexical hexadecimal `SHA256(project/id)` exactly as in V145R1. Denylisted cases are recorded as exposure-ineligible. Non-denylisted cases are evaluated in order. No semantic skipping or substitution is permitted.

## Admission
A non-denylisted case qualifies iff its exact-runtime fixed version passes its native verifier and its buggy version fails it. Infrastructure failures remain infrastructure-ineligible and do not count as semantic negatives.

## Stop
Stop at the first qualifying non-denylisted case, or exhaust the pandas stream.

## Claim boundary
Any selected case is only a **provisional clean E3 candidate** until the same fixed-procedure retrospective exposure audit is performed. A newly discovered prior semantic exposure invalidates clean use of that candidate and requires a new explicitly versioned denylist revision; it is never silently replaced.
