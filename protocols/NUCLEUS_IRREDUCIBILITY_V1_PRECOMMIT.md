# NUCLEUS IRREDUCIBILITY V1 — prospective precommit

Status: **FROZEN BEFORE IMPLEMENTATION OR OUTCOME EXECUTION**

## Governing question

Strip away the developmental architecture and return to the original question:

[
oxed{	extbf{What is the smallest generative nucleus?}}
]

This experiment does not test archives, promotion, genealogy, revocation, learned grammar, or compiler policy.

It tests only candidate primitive nuclei under identical exact worlds.

## Candidate binary relations

Exhaustively test all 16 binary Boolean relations (R(a,b)).

For each relation test four anchor regimes:

1. no distinguished constant;
2. constant 0 only;
3. constant 1 only;
4. both 0 and 1.

Inputs themselves are always available.

No relation is privileged by name.

## Exact worlds

For arities (n=1,2,3,4), begin from the (n) independent Boolean projections and the anchors allowed by the regime.

Repeatedly close under the single candidate relation:

[
x,ymapsto R(x,y).
]

Because each n-variable Boolean function is represented by its exact (2^n)-row truth table, closure is finite and exhaustive.

For each candidate/regime/n record:

- exact number of reachable Boolean functions;
- total possible functions (2^{2^n});
- whether closure is complete;
- minimum expression cost for every reachable consequence;
- closure rounds;
- whether any anchor is itself derivable from inputs and R;
- deterministic canonical expression for each reachable consequence.

## Irreducibility / removal tests

For every complete nucleus:

### Remove relation
With projections and anchors but no R, record closure. A genuine relational nucleus must lose completeness.

### Remove anchor
If the complete nucleus uses one anchor, rerun with no anchor.

### Swap anchor
Replace 0 by 1 or 1 by 0.

### Add dual anchor
Check whether adding the second constant increases expressive closure or only changes minimum costs.

## Symmetry quotient

Classify the 16 relations under the transformations:

- swap inputs;
- complement first input;
- complement second input;
- complement output.

Record exact equivalence classes.

This is descriptive only; no class is preferred by hand.

## Developmental robustness without architecture

Functional completeness alone is not the whole target.

For each complete candidate nucleus, perform 1,024 deterministic lineage trials at n=4.

A lineage starts from two available consequences and repeatedly applies only R. Every 8 generations, one environmental projection not already in the active pair may be injected if available.

Record:

- generations before pair-local semantic repetition;
- whether fresh environmental difference reopens novelty;
- number of distinct consequences visited;
- maximum lineage length;
- fraction of trials surviving 32, 64, 128 generations.

No promotion/archive/reuse mechanism exists.

## Cross-world test

Repeat exact closure for the surviving minimal nuclei in two non-Boolean encodings that preserve only the abstract finite relation structure:

1. truth tables represented as sets of satisfying rows;
2. truth tables represented as bit vectors.

The two implementations must produce identical closure cardinalities and canonical hashes.

This is an implementation-independence check, not a non-Boolean semantic generalization.

## Minimality ordering

A candidate nucleus is **complete at n** iff it reaches every n-variable Boolean function.

A candidate is **minimal complete through n=4** iff:

- it is complete for n=1..4;
- removing R destroys completeness;
- removing every anchor in its regime destroys completeness;
- no strictly smaller anchor regime with the same R is complete through n=4.

A candidate is **robust-minimal** iff it is minimal complete and lies in the maximal developmental-robustness class under the frozen lineage metrics.

No winner is named before execution.

## Frozen gates

N1. All 16 relations × 4 anchor regimes are exhaustively evaluated for n=1..4.

N2. Closure results are exact and deterministic.

N3. Every claimed complete candidate reaches all (2^{2^n}) functions at n=1..4.

N4. Every claimed minimal candidate fails completeness when R is removed.

N5. Every claimed minimal candidate fails completeness when each required anchor is removed.

N6. No minimal candidate has a strictly smaller complete anchor regime.

N7. Symmetry classes cover all 16 relations exactly once.

N8. Canonical closure hashes reproduce on deterministic replay.

N9. Set and bit-vector implementations agree for every surviving minimal nucleus.

N10. At least one minimal complete nucleus exists through n=4.

N11. If a one-anchor nucleus exists, adding the dual anchor does not increase n=4 closure cardinality beyond complete closure.

N12. For every robust-minimal candidate, fresh environmental injection reopens novelty in at least one lineage that had pair-locally saturated.

N13. Robustness ranking is computed solely from frozen metrics, never semantic names.

N14. Report whether all robust-minimal candidates are symmetry-equivalent.

N15. Explicitly report whether Ground+Directed-Difference survives as a robust-minimal equivalence class; this is an outcome, not a gate requirement.

N16. Explicitly report whether any zero-anchor relation is complete through n=4.

## Verdicts

- PASS_NUCLEUS_IRREDUCIBILITY_V1
- PARTIAL_NUCLEUS_IRREDUCIBILITY_V1
- VALID_NEGATIVE_NUCLEUS_IRREDUCIBILITY_V1

PASS requires N1-N14. N15-N16 are required reported outcomes, not positive-result requirements.

## Claim boundary

Even a PASS establishes only a finite Boolean result through four independent variables plus the frozen lineage test.

It does not establish a metaphysical primitive, universal minimality across all logics, continuous systems, physics, biology, intelligence, or computation.

The scientific target is deliberately narrow:

[
oxed{	extbf{Is there an irreducible minimal generative Boolean nucleus, and what exact equivalence class does it occupy?}}
]
