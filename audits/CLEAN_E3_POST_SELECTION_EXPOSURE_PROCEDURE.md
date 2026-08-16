# Clean E3 Post-Selection Exposure Audit — Frozen Procedure

## Purpose
Determine whether a mechanically qualified BugsInPy candidate can support the strongest **blind-natural E3** claim. Qualification and exposure are separate gates: native fixed-pass/buggy-fail proves runtime eligibility; it does not prove the case was unseen.

## Timing
Apply this procedure only after a candidate has been selected mechanically by a frozen qualifier. The procedure itself is frozen independently of the candidate identity. Only evidence that predates the candidate's selection may make it exposure-ineligible.

## Search surfaces
Search all available pre-existing research records on the following surfaces:

1. the user's persistent research/library files;
2. the Triskelion repository and its research/protocol/result files;
3. current-conversation history already present before candidate selection.

Do not inspect the candidate's developer patch, fixed source semantics, or solution narrative anew merely to perform this audit.

## Candidate-keyed searches
For selected case `<project>/<id>`, search the exact case identifier together with each of:

- `developer repair`
- `developer patch`
- `reference_move`
- `Prediction:`
- `fixed source`
- `solution`
- `semantic`

Also search the exact case identifier alone to catch structured JSON/results where the surrounding field names differ.

## Exposure-ineligible evidence
A candidate is exposure-ineligible iff a pre-selection record establishes that any of the following had already been semantically inspected:

- the developer/reference repair;
- the relevant fixed production implementation;
- a solution narrative that reveals the repair mechanism;
- a semantic classification derived from the repair/fixed implementation.

Merely seeing the case ID, bug metadata, native tests, buggy source, runtime qualification result, or fixed-pass/buggy-fail status is **not** sufficient for contamination unless the fixed implementation semantics were inspected.

## Decision
- `CLEAN_FOR_CAUSAL_SUCCESSOR`: no qualifying pre-selection semantic exposure is found after the complete fixed search procedure.
- `EXPOSURE_INELIGIBLE`: at least one qualifying pre-selection record is found; cite/record the evidence and add the case to a newly versioned denylist before rerunning the frozen stream.
- `R10_INCONCLUSIVE`: required search surfaces are unavailable or the evidence date/order cannot be established.

## Non-substitution rule
Never silently skip an exposed selected candidate and take the next runtime-qualified case. Exposure rejection must terminate that run's clean claim and produce a new explicitly versioned denylist revision.
