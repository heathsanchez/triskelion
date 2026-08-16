# V154A — Label-blind external expansion manifest

Frozen: 2026-08-16 NZST
Controller: Rigorous Breakthrough Stack v1.1

## Motivation

V153A exactly replayed the V138 QuixBugs corpus and showed a genuine support obstruction: all 17 programs were label-pure, original single-program O3 evaluability was 0, and a deterministic paired-program diagnostic produced only 4 evaluable folds, below the frozen minimum of 8. V153A therefore remained `CORPUS_CEILING_V153_PAIRED_SUPPORT`; it did not admit O3 or establish rule-language failure.

The next licensed move is to increase natural source support without changing V138 O1/O2/O3 semantics.

## Purpose

V154A constructs an **outcome-blind source manifest only**. It performs no relaxed-comparison mutations and no O3 training/scoring.

External corpus: the already-frozen 501-case BugsInPy corpus across 17 projects, with the existing corpus lock and project list.

## Case selection — frozen before source/outcome inspection

For each of the 17 frozen BugsInPy projects independently:

1. enumerate all bug IDs from the frozen corpus;
2. order by the existing unsalted `SHA256(f"{project}/{bug_id}")` hexadecimal key;
3. select exactly the first **two** IDs;
4. never substitute another ID after checkout, runtime, baseline, syntax, or later mutation outcomes.

Thus at most 34 cases are inspected. Selection does not use developer patches, failure semantics, source features, test outcomes, comparison labels, or O3 performance.

## Fixed-version eligibility

For each selected case, checkout BugsInPy version 1 (fixed). A case is eligible for the later V154B mutation experiment only if all of the following hold:

- checkout succeeds;
- its historical Python version is one of the exact frozen images already supported by `cp3/bugsinpy_exact_runtime.py`;
- the fixed checkout passes the existing exact native verifier;
- production Python source contains at least **three** natural strict single-comparison sites using `<` or `>`.

No failed case is replaced.

## Production-source rule

Recursively scan `*.py` under the fixed checkout, excluding paths containing any of:

`test`, `tests`, `testing`, `.git`, `.cp3_tools`, `env`, `venv`, `.venv`, `site-packages`, `build`, `dist`, `doc`, `docs`, `example`, `examples`, `benchmark`, `benchmarks`.

Also exclude files whose names start `test_` or end `_test.py`.

A natural strict site is an `ast.Compare` with exactly one operator and one comparator and operator `ast.Lt` or `ast.Gt`.

Sites are identified by `(relative_path, lineno, col_offset, operator)` and ranked by `SHA256("relative_path:lineno:col_offset:operator")` only for stable later mutation ordering. V154A does not inspect the effect of any site.

## Manifest viability classification

`PASS_V154A_LABEL_BLIND_EXPANSION_MANIFEST`
iff at least **12 distinct projects** contain at least one eligible selected case.

`CORPUS_CEILING_V154A_EXPANSION_MANIFEST`
if fewer than 12 projects contain an eligible selected case.

Any corpus-lock mismatch, unclassified apparatus failure, or failure to emit the complete 34-case audit is R10/inconclusive.

The 12-project threshold is an eligibility threshold only. It does not imply that V154B will have 8 mixed-label project holdouts; that remains an untouched future verifier question.

## Claim boundary

A V154A pass freezes a label-blind external manifest that is large enough to justify spending verifier budget on V154B. It does not provide RELAX_SAFE/SENSITIVE labels, test O3, or upgrade V138 Q8/Q10.

If V154A passes, V154B must use exactly the eligible cases/sites emitted here; it may not replace cases after seeing mutation outcomes.