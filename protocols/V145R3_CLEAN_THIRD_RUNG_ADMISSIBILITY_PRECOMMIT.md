# V145R3 — Clean Third-Rung Admissibility

## Purpose
Continue the exact V145R2 pandas SHA stream after `pandas/14` passed exposure-clean runtime qualification but failed the inherited causal intervention law because its developer patch edits a test file.

## Inheritance
V145R3 changes no BugsInPy corpus lock, pandas candidate order, exact-runtime adapter, fixed-pass/buggy-fail qualification, timeout discipline, or no-semantic-skipping rule.

## Exposure revision
`pandas/14` is added to the exposure denylist before V145R3 execution because its developer patch was opened after V145R2 selected it. The older exposed cases remain unchanged.

## New intervention-admissibility gate
For a non-denylisted candidate that first satisfies fixed-pass/buggy-fail qualification, inspect only the changed-file paths in its BugsInPy `bug_patch.txt`; do not inspect hunk bodies or repair semantics.

Changed paths are parsed exactly as the inherited V145 causal runner: collect unique paths from lines beginning `+++ b/`.

Reject the candidate as `REFERENCE_INTERVENTION_INELIGIBLE_TEST_PATH` if any changed path is under a path component exactly `test` or `tests`, or the filename starts `test_`, or ends `_test.py`, case-insensitive. This is the exact old V145 `rejects_tests` law.

A path-ineligible candidate is recorded and the deterministic pandas SHA stream continues. No replacement is chosen by repair semantics.

If the patch file is missing or cannot be parsed, classify the candidate as infrastructure/apparatus-ineligible rather than silently admitting it.

## Admission
A provisional E3 candidate must therefore satisfy all of:
1. not in the prefrozen exposure denylist;
2. fixed version passes exact native verifier;
3. buggy version fails exact native verifier;
4. developer intervention changed paths pass the inherited no-test-edit law.

Stop at the first candidate satisfying all four, or exhaust the pandas stream.

## Post-selection boundary
Any selected case remains provisional until the independently frozen post-selection exposure audit is applied. V145R3 does not inspect the selected repair semantics.

## Claim boundary
A V145R3 PASS establishes only existence of an exact-runtime, verifier-qualified, intervention-path-admissible provisional clean third real episode. It does not establish O1→O2→O3 developmental causality, especially because the previously tested BugsInPy `httpie/5 → youtube-dl/32` bridge is a fair bounded negative.
