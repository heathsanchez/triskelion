# V155A — MBPP O3 support manifest

## Purpose
V153A established that V138 O3 is blocked by source/label support in the 17-program QuixBugs corpus, not by a demonstrated failure of the frozen O3 representation. V154A then showed the exact label-blind BugsInPy expansion is too sparse: only 5 projects had eligible frozen cases versus the preregistered 12-project threshold.

V155A asks only whether a larger independently collected Python benchmark supplies enough **baseline-valid strict-comparison source support** to justify a later mutation experiment. It generates no RELAX_SAFE/RELAX_SENSITIVE labels and performs no O3 scoring.

## Frozen external source
Repository: `google-research/google-research`
Pinned commit: `1eb8bb0cbe5fd9072311ae3fd760e3644fee690b`
Dataset path: `mbpp/sanitized-mbpp.json`

Only the sanitized MBPP subset is used.

## Schema-first rule
Before any source decision, load the JSON and record the top-level type, item count, and sorted keys of the first item. Require every record to contain `task_id`, `code`, `test_imports`, and `test_list`. A schema mismatch is R10/inconclusive.

## Baseline validity
Every dataset record is audited; there is no adaptive task selection. For each task:
1. parse `code` as Python;
2. execute `test_imports`, then `code`, then all `test_list` assertions in a fresh subprocess under the workflow Python;
3. enforce a 5-second timeout per task;
4. retain failures/timeouts in the manifest rather than substituting another task.

A task is baseline-valid only if parsing and all supplied tests succeed.

## Natural strict-comparison support
For each parseable canonical solution, enumerate `ast.Compare` nodes having exactly one operator and one comparator whose operator is `ast.Lt` or `ast.Gt`.

Record per task:
- task id;
- baseline status;
- strict-site count;
- deterministic site coordinates `(lineno, col_offset, operator)`.

No comparison is relaxed in V155A.

## Viability gate frozen before census outcomes
`PASS_V155A_MBPP_O3_SUPPORT_MANIFEST` iff:
- at least **20 baseline-valid tasks** contain at least **2** natural strict-comparison sites each; and
- baseline-valid tasks contain at least **50 strict sites total**.

Otherwise return `CORPUS_CEILING_V155A_MBPP_O3_SUPPORT` after the complete audit.

Any incomplete audit, dataset fetch/hash/schema failure, or unclassified apparatus failure is R10/inconclusive.

## Claim boundary
A PASS means only that sanitized MBPP contains enough outcome-blind, verifier-backed strict-comparison support to justify a separately frozen V155B mutation/held-out experiment. It does not admit O3, upgrade V138 Q8/Q10, or demonstrate developmental causality.
