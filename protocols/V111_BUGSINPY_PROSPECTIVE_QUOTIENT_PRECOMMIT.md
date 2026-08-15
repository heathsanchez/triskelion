# V111 BugsInPy Prospective Quotient Prediction — PRECOMMIT

Date: 2026-08-15 NZST

Status: frozen before any V111 BugsInPy source checkout or target-corpus repair outcome is inspected.

## Question

Does the quotient relation induced and validated on QuixBugs before this experiment predict causal comparator repairs in a different historical bug corpus, BugsInPy, without learning or tuning the relation on BugsInPy?

## Prior frozen object

V108/V109 established a comparison-coordinate relation induced only from QuixBugs verifier evidence. V111 freezes that relation before target-corpus execution:

- operand swap is paired with order-direction reversal;
- boundary strictness is preserved as a separate coordinate;
- canonical order families are `{<, > with swap}` and `{<=, >= with swap}`.

No BugsInPy outcome may modify this relation.

## Target corpus

Repository: `soarsmu/BugsInPy`, cloned at the commit resolved by the V111 hosted run and recorded in the artifact.

Project selection is deterministic and outcome-blind:

1. enumerate all project directories in `projects/`;
2. sort project names lexicographically;
3. for each project, select its smallest numeric bug id present in metadata;
4. evaluate in that fixed order until all are attempted or the workflow time budget is exhausted.

No project/bug is selected by reading its source, fix, patch, issue text, or expected repair.

## Information boundary

Primary V111 may use only:

- BugsInPy project/bug metadata required to checkout the buggy revision;
- buggy source;
- the bug-relevant test command and its stdout/stderr;
- verifier pass/fail outcomes from candidate edits.

Primary V111 MUST NOT read:

- fixed source revision;
- known patch/diff;
- bug-fix commit contents;
- human repair description;
- issue/PR solution text.

The fixed revision is not checked out during primary search.

## Candidate search

The search language is frozen before target execution.

For each qualified buggy checkout:

1. baseline bug-relevant test must fail;
2. use failing verifier output to prioritize project `.py` files named in tracebacks; if none are named, use deterministic lexicographic source-file order;
3. enumerate at most 12 single-comparison AST sites across prioritized files;
4. for each site, enumerate the frozen comparator candidate family over `<, <=, >, >=` with optional reversible operand swap;
5. reject no-op variants;
6. run the same bug-relevant verifier after each one-site edit;
7. retain every candidate that changes fail -> pass;
8. restore the buggy source and re-run to confirm ablation fail.

No ranking is learned from BugsInPy beyond deterministic enumeration and verifier pass/fail.

## Quotient prediction

Every verifier-confirmed target repair is canonicalized using the QuixBugs-frozen relation only.

Primary success is not simply finding repairs. The key test is whether independently arising BugsInPy literal repairs map into quotient classes already represented by the QuixBugs historical/controlled evidence.

## Frozen gates

### G1 — executable target qualification
At least one deterministic BugsInPy case must successfully checkout/provision and show baseline bug-relevant test failure. Infrastructure failures are recorded as negatives and are not silently dropped.

### G2 — nontrivial blind search
At least 8 distinct non-noop one-site candidates must be verifier-tested across qualified cases.

### G3 — prospective causal repair
At least one candidate must produce baseline FAIL -> candidate PASS -> ablation FAIL without reading fixed source.

### G4 — prior-class prediction
At least one causal BugsInPy repair must canonicalize, under the relation frozen before V111, to a quotient class already observed in the prior QuixBugs chain. No target-derived relation change is allowed.

### G5 — literal-coordinate novelty
For at least one prior-class prediction, the target literal repair presentation must differ from at least one previously observed literal representative in that same prior quotient class. This prevents success from reducing to exact patch-token repetition only.

### G6 — source/corpus independence
The passing target example must be from BugsInPy and must not be a QuixBugs source/program.

### G7 — leakage audit
Artifact must attest that fixed source/diff/repair text was not read during primary search.

### G8 — infrastructure accounting
Every selected project/bug attempted before the budget expires must have a terminal status: qualified/no-repair/repair/checkout-fail/provision-fail/test-infra/timeout/no-comparator-site. No semantic cherry-picking.

## Verdict

`PASS_V111_BUGSINPY_PROSPECTIVE_QUOTIENT` only if G1–G8 all pass.

A failure is informative. In particular:

- no qualified cases => infrastructure/coverage failure, not theory falsification;
- qualified cases but no causal comparator repair => no support in this target sample;
- causal repairs but no prior-class hit => prospective quotient prediction fails for this sample;
- prior-class hit only by identical literal patch => weak recurrence, G5 fails.

## Claim boundary

A pass supports only prospective cross-corpus recurrence of a previously frozen comparator quotient relation on blind historical BugsInPy repair search. It does not establish arbitrary operator discovery, universal code-repair ontology, or unrestricted cross-domain transfer.
