# V150 — Frozen-output transport replay diagnostic

## Status

**POST-V149 DIAGNOSTIC, PRECOMMITTED BEFORE V150 REPLAY**

V150 is not a fresh developmental experiment and cannot by itself establish O1 -> O2 causality. It is a residual-separating replay over the exact frozen V149 T2 model outputs.

## Trigger

V149 repaired the visible-source context adapter and passed its eligibility gate. T2 then returned 0/3 solves in COLD, O1 and SHAM. However, all six COLD candidate outputs and all six O1 candidate outputs reached zero native verifier calls because `git apply --check` rejected the generated unified diffs as malformed/corrupt. Three SHAM second attempts were applyable and reached the verifier but failed semantically.

A text-only parser probe performed after V149 showed that `git apply --numstat --recount` parses all six frozen O1 diffs that strict parsing rejected, and parses four of six frozen COLD diffs that strict parsing rejected. This licenses a transport-only replay test.

## Frozen evidence input

V150 must consume the immutable artifact from:

- repository: `heathsanchez/triskelion`
- workflow run: `31941708089`
- artifact: `v149-context-repaired-natural-third-rung`
- artifact digest reported by GitHub: `sha256:5225cd42a5519b89d475691104d594bdfb394abde17e15203910fc530c8ffe5f`
- V149 `V145_RESULT.json` SHA-256: `cf93c37fe1a3a5aaeba7add755fbb3e5b5b33c123273a915683d564777cb33b9`
- V149 context preflight SHA-256: `22b9ff3e49fdc1099cc4ea8036e5d6d0656e461069708fbf409c15af6b2f4c0c`

The expected T2 task is `youtube-dl/32`, model `Qwen/Qwen3.5-9B`, seeds `[202608161, 202608162, 202608163]`, and arms `D_COLD`, `D_PLUS_O1`, `D_PLUS_SHAM`.

No model call is permitted in V150.

## Intervention

For each exact frozen V149 T2 response, on a fresh unchanged buggy checkout:

1. extract the same candidate diff using the existing `base.extract_diff` routine;
2. reject any candidate that edits tests under the unchanged V145 rule;
3. attempt the original strict transport: `git apply --check` then `git apply`;
4. only if strict transport fails, attempt the same **unchanged diff bytes** with `git apply --check --recount` then `git apply --recount`;
5. if either route applies, run the exact historical native verifier;
6. record strict error, recount error, chosen transport, verifier result, hashes and timings.

`--recount` is permitted only as a transport normalization: it recomputes hunk line counts. V150 may not edit paths, context lines, additions, deletions, whitespace, source content, or model text.

If strict transport succeeds, do not use `--recount` for that candidate. This preserves the original successful strict route, including the V149 SHAM candidates.

## Apparatus

- use the same official BugsInPy source and exact historical Python runtime adapter as V149;
- use the V145A precompiled-checkout optimization only for runtime cost; semantic acceptance remains the native test;
- freeze one buggy baseline before candidate replay;
- every candidate starts from a fresh checkout/template copy;
- no developer patch or fixed source is inspected or applied.

## Diagnostic verdicts

`PASS_V150_TRANSPORT_RESIDUAL_CONFIRMED` requires at least one exact frozen candidate that failed strict transport in V149 to apply unchanged under strict-then-recount in V150.

`PASS_V150_O1_POSTHOC_SEMANTIC_CANDIDATE_EXISTS` additionally records that at least one exact frozen O1 candidate passes the native verifier after transport normalization. This is **post-hoc diagnostic evidence only** and does not establish causal developmental advantage.

`PASS_V150_NO_O1_SEMANTIC_RESCUE` means the transport residual is confirmed but no O1 candidate passes the verifier after all transportable frozen O1 candidates are tested.

`NULL_V150_RECOUNT_DOES_NOT_APPLY` means the text-only parser effect does not survive real-checkout application.

Any corpus/runtime/artifact/hash mismatch is `R10_INCONCLUSIVE`.

## Projection

If V150 confirms transport rescue, the next causal experiment may preregister strict-first/recount-fallback as an arm-symmetric output adapter and rerun the matched T2 causal separator from scratch.

If an O1 candidate passes natively in V150, that strongly justifies the rerun but the V150 result itself remains diagnostic because the transport intervention was selected after observing V149 outputs.

If transport succeeds but all O1 candidates fail semantically, the residual moves from output transport to repair-policy content/search under the frozen budget.

## Claim boundary

V150 cannot establish natural O1 -> O2 causality, O2 admission, pandas/O3 development, or three-rung compounding. Its sole scientific purpose is to determine whether V149's apparent O1 null was confounded by the unified-diff transport adapter.