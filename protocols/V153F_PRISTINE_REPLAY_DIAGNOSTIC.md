# V153F — Pristine-cache zero-call replay correction

Frozen: 2026-08-16 NZST
Controller: Rigorous Breakthrough Stack v1.1

## Status

APPARATUS-CORRECTION DIAGNOSTIC ONLY. No model calls. V153 remains unchanged. V153D/E cross-seed replay counts are invalid for interpretation because those diagnostics did not seed the precompiled cache from a pristine buggy baseline before replaying candidate-modified worktrees.

## Frozen source

Use exact V153 result SHA-256:
`ae572174c253b47cef2db706254b45675a8c414feeb8d6bf7c86d516bd206057`.

## Apparatus correction

Before any candidate replay:

1. create a pristine buggy `youtube-dl/32` checkout;
2. hash `youtube_dl/utils.py`;
3. run the exact native verifier once, expecting semantic failure and no infrastructure error;
4. hash `youtube_dl/utils.py` again and require equality;
5. require the V145 precompiled template marker to exist after this pristine baseline call.

Only after this gate may frozen candidate bytes be replayed.

## Replay

For every RAW V153 seed, recover call 1 and the first distinct call-2 rival using the frozen V153D payload projection. Evaluate two separately labelled transport modes on independent pristine-template copies:

- `BASELINE_RELATIVE`: apply the selected rival directly to pristine buggy source, then native verifier if application succeeds.
- `CALL1_STATE_RELATIVE`: apply call 1, then apply the selected rival without reset, then native verifier if both applications succeed.

No fallback is allowed inside either mode and no verifier outcome influences selection.

## Diagnostic outputs

Record for every seed and mode: source hashes, transport status, selected rival SHA, verifier reachability, and verifier outcome.

This diagnostic exists only to determine the correct representation/executor residual and license a separately prospective successor. It cannot earn a developmental causal claim.

Execution trigger note: workflow already existed before this append-only note; no scientific or apparatus rule changed.
