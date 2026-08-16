# V137 — Semantic Quotient Recovery precommit

Status: FROZEN BEFORE V137 OUTCOMES.

## Purpose

V136 exposed a vocabulary-expansion ambiguity when the 60th syntactic relation candidate was restored. Before acquiring more evidence, V137 tests the stronger rival explanation that the apparent ambiguity is representational redundancy rather than uncertainty about behavior.

The key prospective hypothesis is that comparator relations related by operand swap and comparator duality are the same semantic capability:

`KEEP:(s|r) ~ SWAP:(dual(s)|dual(r))`.

For example `KEEP:<|<=` and `SWAP:>|>=` are predicted to be extensionally identical.

## Frozen corpus and verifier

- QuixBugs Python commit `4257f44b0ff1181dedaedee6a447e133219fcebf`.
- Inherit V135 qualification, source separation, verifier semantics, timeout handling and held-out boundary unchanged.
- V137 may not inspect held-out outcomes to define equivalence classes.

## Stage A — exact semantic quotient

Generate the complete V136 G4 60-candidate relation grammar.

Define `dual(<)=>`, `dual(>)=<`, `dual(<=)>=`, `dual(>=)<=`, with `==` and `!=` self-dual.

Canonical semantic class of candidate `(swap, strict, relaxed)` is:

- `(strict, relaxed)` if `swap=False`;
- `(dual(strict), dual(relaxed))` if `swap=True`.

A1 passes iff the 60 syntactic candidates collapse to exactly 30 semantic classes, each of size 2.

A2 passes iff exhaustive truth-table evaluation over all ordered value pairs in `{-2,-1,0,1,2}` proves both members of every class identical for strict and relaxed predicates.

## Stage B — acquisition re-evaluation at class level

Run the frozen V135 natural-code stratum using G4. For each whole-program fold, map every acquisition-perfect syntactic candidate to its frozen semantic class before any held-out evaluation.

B1 passes iff every evaluable fold has exactly one acquisition-perfect semantic class even where syntactic `perfect_n > 1`.

Then run the same V135 stratum with a deterministic 30-representative quotient grammar. Representative choice is fixed before outcomes: choose the lexicographically smallest candidate ID after preferring a candidate already present in the V135 G0 grammar. No held-out information participates.

B2 passes iff every evaluable fold has exactly one perfect representative under the quotient grammar.

B3 passes iff quotient held-out transport and targeted ablation remain at least 90%, and cross-family REVERSE reuse remains at least 90%.

## Stage C — distinguish redundancy from genuine missing information

Replay V136 orientation folds under the 30-class quotient grammar.

- If the previous `>-><` failure collapses to one semantic class, classify it `C_REDUNDANCY_RESOLVED`.
- If more than one semantic class remains acquisition-perfect, classify it `C_GENUINE_INFORMATION_AMBIGUITY`.

C1 reports this result; it is not forced to PASS.

## Verdicts

- `PASS_SEMANTIC_QUOTIENT_RECOVERY` iff A1, A2, B1, B2 and B3 pass.
- `PARTIAL_SEMANTIC_QUOTIENT_RECOVERY` iff exact quotienting is valid but one natural-code gate remains open.
- `REJECT_SEMANTIC_QUOTIENT_HYPOTHESIS` iff candidates merged by the proposed quotient are not extensionally equivalent or induce different verified behavior.
- `INVALID_V137` iff the inherited information boundary is violated.

## Claim boundary

V137 can establish that a syntactic ambiguity was an artifact of representation and that semantic quotienting restores identifiable capability classes. It cannot establish natural multigeneration, constructor growth, cross-domain generality or open-ended recursive development.