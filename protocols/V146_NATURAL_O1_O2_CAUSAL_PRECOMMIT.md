# V146 natural O1 → O2 causal separator — frozen precommit

Controller: Rigorous Breakthrough Stack v1.1.

## Natural stream
The task identities were fixed by the pre-existing CP3 acquisition corpus before this experiment:
- O1 source episode: `httpie/5` (already qualified acquisition case).
- O2 target episode: `youtube-dl/32` (already qualified acquisition case).
- Reserved third episode: `pandas/66`, independently selected/qualified by V141. **V146 must not inspect or run a model repair on pandas/66.**

Existing CP3 jointly compressed httpie/5 + youtube-dl/32 into one capability. That prior result is not evidence of O1→O2 development. V146 instead asks whether a capability learned from httpie/5 alone causally changes the youtube-dl/32 discovery frontier.

## O1 freeze
O1 is synthesized from the verified successful intervention trace for httpie/5 only. The model sees only httpie acquisition evidence. It must emit a concise reusable repair policy; project/case names are forbidden in the artifact. O1 is frozen before any V146 youtube arm is evaluated.

## Frozen O2 arms
Matched on model, visible buggy source/failing native test, candidate language (unified diff), max tokens, verifier, exact historical runtime, task identity, and seed schedule.
- D: cold; no retained capability.
- D+O1: identical prompt plus the frozen O1 policy.
- D+sham: identical prompt plus a deterministic word-order permutation of O1 with matched text length/content tokens but destroyed policy semantics.

Seeds: 20260815, 20260816, 20260817, 20260818. One model call per seed per arm. No verifier feedback retry. This makes model calls fixed at four per arm and prevents one arm receiving extra search.

## Costs
Record per arm/seed: model call count, returned token/usage metadata when available, response length, patch parse/apply status, native verifier duration, total wall clock, success, and diff hash. Retained text byte length is recorded for O1 and sham.

## Gates
Strong O1→O2 causal frontier PASS requires:
1. O1 source intervention replay passes native verifier and O1 synthesis/freeze completes before youtube evaluation.
2. Youtube baseline reproduction fails natively without infrastructure error.
3. D+O1 obtains at least one verified youtube repair.
4. D obtains zero verified repairs across the same four seeds.
5. D+sham obtains zero verified repairs across the same four seeds.
6. No arm edits tests.
7. All arm executions use the same exact historical verifier/runtime.

If D also succeeds, classify reachability as NULL and compare preregistered efficiency only: first successful seed index, verifier calls, model calls (fixed), response bytes/tokens where available, and wall clock. A material efficiency advantage is `FRONTIER_EFFICIENCY`, not new reachability.

If D+O1 fails as well, O1→O2 causal development is NEGATIVE under this frozen budget. If any arm is blocked by runtime/provider/build/network apparatus, classify those affected comparisons R10 and draw no semantic conclusion.

## O2 promotion boundary
Only if D+O1 produces a verifier-passing repair and the causal gate is not explained by D or sham may that verified O1-assisted youtube episode be used in a **new preregistration** to synthesize O2. V146 itself does not test pandas/66 and cannot establish multi-generation development.