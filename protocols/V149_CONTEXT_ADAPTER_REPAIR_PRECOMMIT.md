# V149 — Natural third-rung context-adapter repair precommit

Frozen 2026-08-16 NZST under Rigorous Breakthrough Stack v1.1 before any V149 T2/T3 model outcome.

## Why V145 is not a semantic negative

V145 completed without provider/runtime R10, but its visible-source adapter failed its scientific purpose on T2: the native failure was `TestUtil.test_strip_jsonp`, while the supplied buggy-source context contained unrelated `devscripts/*` files and omitted the implementation of `strip_jsonp`. The model explicitly reported that the failing implementation was absent. Under RBS v1.1 this is a distorted representation/adapter residual, not evidence that O1 cannot enable O2.

V145 remains immutable evidence of that adapter failure. V149 changes the visible-evidence adapter and therefore is a new preregistration, not a reinterpretive rerun.

## Scientific question and all causal assumptions

The V145 scientific question, frozen natural stream, model, seeds, call/token budget, verifier, capability construction, sham controls, ancestor ablation, cost criteria and PASS gates are inherited unchanged from `V145_NATURAL_THIRD_RUNG_CAUSAL_PRECOMMIT.md`.

Frozen stream remains:
1. T1 = `httpie/5`
2. T2 = `youtube-dl/32`
3. T3 = `pandas/66`

No task substitution is allowed.

## Only changed assumption: visible buggy-source context adapter

V149 replaces only `collect_context` with a deterministic resolver based exclusively on information already visible to the repair agent:

1. Parse test identifiers from the native failing-test output (pytest `::test_*` and unittest `.test_*` forms).
2. Strip only the leading `test_` marker and derive deterministic identifier candidates from the remaining test name by longest underscore-delimited prefixes first, then individual identifier tokens.
3. Search the **buggy checkout only** for exact Python function/method definitions matching those candidate identifiers (`def <identifier>(` or `async def <identifier>(`).
4. Exclude `.git`, virtual environments/site-packages, and test/test-fixture paths from source candidates.
5. Rank exact-definition hits by: longer matched identifier first, then lexical relative path. No semantic/model judgement enters ranking.
6. Add non-test source files explicitly referenced by native traceback paths after exact-definition hits.
7. If fewer than the context-file limit are found, fall back to lexical non-test project Python files exactly as before.
8. Context size/file limits remain 6 files / 36,000 characters.

The resolver may not inspect `bug_patch.txt`, fixed-commit source, developer patches, protected outcomes, Git history, or any task-specific handwritten path list.

## Adapter eligibility gate before model calls

Before any V149 repair call:
- T2 must contain at least one exact-definition hit derived from its visible failing-test identifier.
- T3 must contain at least one exact-definition hit derived from its visible failing-test identifier.
- All selected files must be inside the buggy checkout and outside tests/environments.

If either task has no such hit, V149 stops as `R10_CONTEXT_ADAPTER_INCONCLUSIVE`. No model arm is run and no developmental conclusion follows.

The exact selected relative paths and matched identifiers are frozen into the result before the first T2/T3 repair call.

## Apparatus optimization

V145A precompiled-checkout optimization remains unchanged. It does not alter semantic acceptance.

## Interpretation

V149 may establish or reject the V145 bounded causal chain only under the original V145 gates. It must not use V145 model outcomes to alter task selection, seeds, budgets, capability text, or arm definitions. The O1 capability is reconstructed from T1 using the same frozen synthesis procedure and seed schedule.

A null T2 result with the adapter eligibility gate passing is a legitimate bounded null/negative. Any adapter-gate failure is R10 only.

## Claim boundary

Even a strong PASS establishes only a bounded three-episode, source-distinct causal developmental chain on this BugsInPy/Qwen substrate. It does not establish recursive self-improvement or open-ended development.