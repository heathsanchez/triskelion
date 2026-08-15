# V115B BugsInPy Third-ID Prospective Quotient Test — PRECOMMIT

Date: 2026-08-15 NZST

Status: frozen before any V115B target checkout, provisioning, source inspection, verifier outcome, or candidate result.

## Why V115B exists

V115 failed before scientific qualification because its harness passed the checkout parent directory to `bugsinpy-compile`/`bugsinpy-test` rather than the actual `ROOT/<project>` checkout. V115 tested zero candidates. Audit also showed that the stock BugsInPy checkout script may internally stage benchmark tests from the fixed revision even when producing version 0. V115B therefore corrects both the path semantics and the information-boundary wording before touching a fresh target set.

## Frozen prior object

Use only the two recurrent V110 historical quotient repair classes, represented by:

`qkey(source,target,swap) = min((source,target,swap), (dual(source),dual(target),swap))`

where `dual(<)=>`, `dual(>)=<`, `dual(<=)=>=`, `dual(>=)=<=`.

Frozen recurrent keys:

1. `ORDER,<,<=,0`
2. `ORDER,<,>=,1`

No V115B target evidence may modify these keys.

## Fresh disjoint target set

For every BugsInPy project with at least three numeric bug IDs:

1. sort project names lexicographically;
2. sort bug IDs ascending;
3. select the **third-smallest** bug ID.

This target set is disjoint from:
- V111 smallest-ID selection;
- V115 second-smallest-ID selection.

Projects with fewer than three bugs are selection-ineligible and recorded.

## Provisioning boundary

The benchmark's stock `bugsinpy-checkout -v 0` may internally visit the fixed revision to stage benchmark verifier/test files before leaving the working tree at the buggy revision. This is explicitly allowed as **verifier provisioning**.

The repair-search algorithm itself MUST NOT inspect or use:
- fixed production implementation source;
- known patch/diff;
- fix-commit changed production lines;
- human repair descriptions;
- issue/PR solution text;
- any target-derived change to the frozen quotient keys.

After checkout, candidate search is restricted to the final buggy working tree plus the benchmark's bug-relevant verifier/tests and their outputs.

The artifact must report this distinction honestly; it must not claim that the provisioning framework never touched a fixed revision.

## Correct checkout path semantics

If checkout is called with `-w ROOT`, the project checkout is `ROOT/<project>`. Compile/test/source search must use exactly that project directory.

## Candidate language

For up to 12 deterministic single-comparison AST sites per qualified case, enumerate all one-site variants over:

- comparator token `<, <=, >, >=`;
- operand coordinate KEEP or SWAP.

Reject semantic no-ops:
- KEEP + unchanged comparator;
- SWAP + dual(old), e.g. `x<y` -> `y>x`.

Every remaining candidate is verifier-tested with deterministic enumeration and no target-derived ranking.

## Causal criterion

A repair counts only when:

`buggy FAIL -> candidate PASS -> restored buggy source FAIL`.

Every passing candidate is retained.

## Frozen gates

### G1 — disjointness
Every selected target differs from both the smallest and second-smallest ID for its project.

### G2 — executable qualification
At least one selected case reaches an actual project checkout, provisions, and has a failing baseline relevant-test verifier.

### G3 — nontrivial blind search
At least 8 non-noop candidate edits are verifier-tested.

### G4 — prospective causal repair
At least one candidate satisfies FAIL -> PASS -> ablation FAIL.

### G5 — frozen prior-class prediction
At least one causal target repair maps to one of the two V110 keys frozen above.

### G6 — competing alternatives
At least one verifier-rejected candidate exists in the exercised search; the successful repair cannot be a singleton supplied patch.

### G7 — repair-search leakage boundary
The V115B Python algorithm does not read fixed production implementation, patch/diff, human repair text, or update the frozen target relation. Benchmark fixed-test staging during stock provisioning is disclosed separately and does not count as production-fix access by the search algorithm.

### G8 — infrastructure accounting
Every reached target gets a terminal status. No failed/provisioning case can be silently swapped for an outcome-favorable case.

## Verdict

`PASS_V115B_BUGSINPY_THIRD_ID_PROSPECTIVE` iff G1–G8 all pass.

Failure interpretation:
- zero qualified targets = infrastructure/coverage limitation;
- qualified targets but no repair = no support in this target sample;
- causal repairs but no frozen-class hit = prospective class prediction fails on this fresh sample;
- prior-class hit with repair-search leakage = invalid.

## Claim boundary

A pass supports prospective recurrence of two quotient repair classes frozen from QuixBugs in a deterministic, disjoint BugsInPy sample under one-site comparator KEEP/SWAP search. It does not establish arbitrary patch discovery, universal repair ontology, autonomous invention of the edit grammar, or open-ended reasoning-language growth.
