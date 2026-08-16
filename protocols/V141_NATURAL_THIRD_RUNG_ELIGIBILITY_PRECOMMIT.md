# V141 — Natural third-rung eligibility gate

Frozen: 2026-08-16 NZST
Controller: Rigorous Breakthrough Stack v1.1
Parent corpus lock: CP3 BugsInPy frozen corpus, 501 bugs / 17 projects.

## Question

Before spending a causal O1→O2→O3 experiment, does the already-frozen CP3 acquisition partition contain a third independently qualified natural repair episode beyond the two previously frozen acquisition cases (`httpie/5`, `youtube-dl/32`)?

This experiment is an eligibility/corpus gate only. It does not inspect or use protected-project outcomes and cannot establish O3, causal development, or capability compounding.

## Frozen selection

Use only the unresolved acquisition project `pandas`. Do not search protected projects for a convenient third episode.

Within pandas, use the pre-existing `cp3/qualify_remaining.py` protocol unchanged:

- enumerate the frozen BugsInPy manifest;
- require exactly 501 bugs and the frozen 17-project set;
- order pandas candidates by SHA256(`project/id`) lexical hexadecimal ascending;
- test each candidate in that order;
- admit only fixed-pass AND buggy-fail;
- infrastructure/reproduction negatives are recorded and skipped only as R10-style nonsemantic negatives;
- stop at the first semantic qualification;
- no semantic cherry-picking.

No task source, fixed patch, protected evidence, or model repair outcome may be inspected to alter selection.

## Gates

E1 apparatus/corpus identity: observed corpus contains exactly the frozen 501 bugs / 17 projects.

E2 deterministic selection discipline: candidate order and admission rule are unchanged from `cp3/qualify_remaining.py`.

E3 third natural acquisition episode: pandas yields at least one `fixed_pass_buggy_fail` candidate before exhaustion.

## Verdicts

- `PASS_V141_THIRD_NATURAL_EPISODE_EXISTS` iff E1–E3 hold.
- `CORPUS_CEILING_V141_NO_THIRD_ACQUISITION_EPISODE` iff E1/E2 hold and pandas is semantically exhausted without a qualifying candidate.
- Any clone, Docker, timeout, historical-runtime, runner, or other apparatus failure is `R10_INCONCLUSIVE`; it implies no semantic conclusion.

## Next-step boundary

A V141 PASS only licenses a separate frozen structural/frontier-eligibility census across the three acquisition episodes. That later census must establish a defensible O1/O2/O3 dependency hypothesis before any causal matched-arm spend.

No V141 outcome alone licenses the terms O3, multi-generation development, recursive development, open-ended development, or self-improvement.