# V115 Disjoint BugsInPy Prospective Quotient Test — PRECOMMIT

Date: 2026-08-15 NZST

Status: frozen before any V115 target source checkout or target outcome is inspected.

## Why V115 exists

A pre-execution audit of the queued V111 implementation found a protocol-conformance defect: the frozen V111 protocol specified comparator replacement **with optional reversible operand swap**, but the committed V111 implementation enumerated comparator-token replacement only.

No V111 runner had started when this was discovered: the job remained queued with zero steps. V111 is therefore retained as a pending/invalid-for-headline implementation lineage rather than silently reinterpreted.

Because that queued historical head could still execute later, V115 uses a **disjoint deterministic target set** so even a later V111 execution cannot contaminate V115 target outcomes.

## Question

Does a quotient structure frozen entirely from the pre-BugsInPy QuixBugs chain prospectively predict causal comparator repairs in a disjoint set of historical BugsInPy bugs?

## Frozen prior object

Use only the two recurrent historical quotient repair classes already observed in blind V110, represented by V110's canonical key:

`qkey(source,target,swap) = min((source,target,swap), (dual(source),dual(target),swap))`

for order comparators, where

`dual(<)=>`, `dual(>)=<`, `dual(<=)=>=`, `dual(>=)=<=`.

The two frozen V110 recurrent keys are:

1. `ORDER,<,<=,0` — boundary relaxation without operand swap;
2. `ORDER,<,>=,1` — reversed-coordinate strictness/boundary repair with operand swap.

No V115 outcome may add, remove, merge, or redefine these classes.

This is intentionally narrower than allowing every plausible comparison relation from V108/V109.

## Target corpus and disjoint selection

Repository: `soarsmu/BugsInPy`.

For every project with at least two numeric bug IDs:

1. sort project names lexicographically;
2. sort numeric bug IDs ascending;
3. select the **second-smallest** bug ID.

V111 selected the smallest bug ID. Therefore the V115 target set is disjoint from V111 by construction.

Projects with fewer than two bug IDs are recorded as selection-ineligible, not silently replaced.

Evaluation order is frozen lexicographically by project.

## Information boundary

Primary V115 may use only:

- metadata necessary for buggy checkout/provisioning;
- buggy revision/source;
- bug-relevant test commands and outputs;
- verifier pass/fail under candidate edits.

It MUST NOT read:

- fixed source revision;
- known patch/diff;
- fix commit contents;
- human repair descriptions;
- issue/PR solution text.

Only BugsInPy version `0` (buggy) may be checked out.

## Candidate language

For up to 12 deterministic comparison sites per qualified case, enumerate all one-site variants over:

- comparator token in `<, <=, >, >=`;
- operand coordinate `KEEP` or `SWAP`.

Reject semantic no-ops:

- KEEP with unchanged comparator;
- SWAP with the dual comparator, because `x < y` and `y > x` (and relaxed analogues) are the same relation.

Every remaining candidate is verifier-tested without target-derived ranking.

For a SWAP candidate, replace the complete comparison expression with parenthesized reversed operands and the selected comparator; for KEEP, replace only the comparator token.

## Causal repair

A candidate is causal only if:

`buggy FAIL -> candidate PASS -> restore buggy source -> FAIL`.

Every passing candidate is retained in the artifact; no semantic cherry-picking among passes.

## Frozen gates

### G1 — disjointness
Every selected V115 `(project,bug_id)` differs from the V111 smallest-ID selection for the same project.

### G2 — executable qualification
At least one selected case checks out/provisions and has failing bug-relevant baseline tests.

### G3 — nontrivial blind search
At least 8 non-noop candidate edits are verifier-tested.

### G4 — prospective causal repair
At least one candidate satisfies FAIL -> PASS -> ablation FAIL.

### G5 — frozen prior-class prediction
At least one causal repair has V110 `qkey` equal to one of the two frozen recurrent historical keys above.

### G6 — competing alternatives
For any prior-class hit, at least one other candidate at the same case/site or elsewhere in qualified search must have been verifier-rejected; success cannot arise from a singleton supplied patch.

### G7 — leakage boundary
Artifact must attest no version-1/fixed checkout, diff, patch, repair description, or target-derived relation update.

### G8 — infrastructure accounting
Every selected case reached before the total budget expires receives a terminal status. Infrastructure failures are preserved and cannot be replaced by outcome-guided cases.

## Secondary diagnostics — not primary gates

Report:

- whether the target literal signature uses the opposite dual coordinate from the canonical `<` representative;
- which of the two frozen historical classes is hit;
- hit rate among causal repairs;
- number of causal repairs outside the frozen prior classes;
- candidate count and rejection rate.

These diagnostics cannot modify the frozen relation or primary verdict.

## Verdict

`PASS_V115_BUGSINPY_DISJOINT_PROSPECTIVE` iff G1–G8 all pass.

Failure modes remain informative:

- no qualified targets -> infrastructure/coverage limitation;
- qualified targets, no causal repair -> no support for this candidate language/sample;
- causal repairs, no frozen-class hit -> prospective quotient prediction fails on this disjoint sample;
- frozen-class hit with leakage -> invalid evidence.

## Claim boundary

A pass supports prospective cross-corpus recurrence of two quotient repair classes frozen from QuixBugs in a disjoint deterministic BugsInPy sample under a one-site comparison-edit grammar. It does not establish arbitrary patch discovery, universal repair ontology, or open-ended reasoning-language growth.
