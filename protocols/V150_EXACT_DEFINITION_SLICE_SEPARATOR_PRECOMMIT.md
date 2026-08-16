# V150 — Exact-definition slice separator precommit

Frozen 2026-08-16 NZST under Rigorous Breakthrough Stack v1.1 before any V150 model outcome.

## Residual from V149

V149 passed its source-context eligibility gate: the exact buggy implementations for T2 (`strip_jsonp` in `youtube_dl/utils.py`) and T3 (`xs` in `pandas/core/generic.py`) were selected before model calls. Under the frozen two-call / three-seed budget, T2 produced 0/3 solves in cold, 0/3 in D+O1, and 0/3 in sham, so O2 was not admitted and T3 was not spent.

However, almost all T2 candidates failed at transport/application before the native verifier. The V149 adapter exposed large source excerpts plus unrelated fallback files. Two rival diagnoses therefore remain live:

1. bounded semantic/search failure: O1 gives no useful advantage on T2 under this model/budget;
2. representation/interface failure: large/noisy source context prevents the model from expressing an applicable candidate even when the correct implementation is present.

V150 is a separator between those diagnoses. It is not a new developmental claim.

## Frozen scientific inheritance

V150 inherits unchanged from V145/V149:
- stream: `httpie/5 -> youtube-dl/32 -> pandas/66`;
- model: `Qwen/Qwen3.5-9B`;
- seeds: `202608161, 202608162, 202608163`;
- maximum two model calls per seed;
- maximum 2048 generated tokens per call;
- exact historical BugsInPy verifier/runtime;
- O1 construction from the verified T1 intervention;
- cold / D+O1 / character-matched sham arms on T2;
- capability text, sham construction, stopping rules, and all semantic acceptance criteria.

No task, seed, budget, model, verifier, capability, or arm substitution is allowed.

## Only changed assumption: exact-definition source representation

V150 replaces the V149 whole-file/fallback context with one deterministic source slice derived entirely from already-visible failing-test evidence:

1. Parse visible `test_*` names exactly as V149.
2. Generate identifier candidates exactly as V149.
3. Search the buggy checkout only for exact Python function/method definitions.
4. Choose the same best exact hit ordering as V149: longest identifier first, then lexical path.
5. Expose only the selected definition's local source slice: from up to 12 lines before the definition through up to 80 lines after it, capped at 12,000 characters.
6. No unrelated fallback source files are included.
7. Tests, fixtures, environments, fixed source, `bug_patch.txt`, developer patches and Git history remain excluded.
8. The selected identifier/path and context SHA are frozen before model calls.

This representation may contain nearby source lines solely because they are contiguous with the exact matched definition. No semantic ranking of neighboring code is allowed.

## Eligibility gate

Before any V150 repair call, T2 and T3 must each resolve to exactly one selected best exact-definition hit under the deterministic ordering, with a non-empty slice and no forbidden path. Otherwise stop as `R10_CONTEXT_SLICE_INCONCLUSIVE` with no semantic conclusion.

## Frozen interpretation

Primary separator is T2.

- If any V150 arm reaches the native verifier with an applicable candidate where the corresponding V149 arm systematically failed at patch application, this is evidence that source representation was a material bottleneck. It does not by itself establish developmental advantage.
- If D+O1 solves T2 and cold/sham do not under the unchanged budget, O1 causal advantage is licensed and the unchanged V145 developmental controller may construct O2 and proceed to T3.
- If all three T2 arms remain unsolved with the exact-definition slice and no R10, record a bounded null/negative for O1 -> O2 on this stream/model/budget. Do not increase the budget inside V150.
- A solve shared by cold/sham and O1 is reachability without developmental advantage.
- Patch-format/model-output failures are retained as search/interface outcomes, not infrastructure failures, unless the deterministic adapter or verifier itself fails.

## Claim boundary

V150 can decide only whether V149's large-source representation was masking T2 and, if the original gates happen to pass, can resume the bounded three-episode causal test. It cannot establish open-ended or recursive development.