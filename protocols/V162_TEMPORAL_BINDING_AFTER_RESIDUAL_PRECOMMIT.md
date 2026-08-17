# V162 — Temporal Binding After Residual

Status: PRECOMMITTED BEFORE OUTCOMES
Date: 2026-08-17

## Residual

V160 showed that semantic capability + correct locus causally routes executable repairs to `thefuck/rules/ls_lah.py`, but did not solve `thefuck/32`.

V161 injected a local binding packet at the initial clean state. The binding arms generated edits addressed to a later post-first-repair state and therefore transport-failed. V161A replayed the frozen right-binding candidate after the frozen first repair. The candidate applied and moved the verifier residual from false-positive `lsof` to false-negative bare `ls`, confirming temporal state alignment but not a verified solution.

Therefore the next hypothesis is specifically temporal:

> a local binding should be introduced only after the first verifier residual has established the current refinement state, not at the initial clean task state.

## Frozen task / model / verifier

- Task: `thefuck/32`
- Model: `Qwen/Qwen3.5-9B`
- Seeds: `202608171, 202608172, 202608173`
- BugsInPy snapshot: `11c5f1eea954a42132cfd06bf257766a7963e0fd`
- Historical runtime: pinned Python 3.7.0 image used by V160/V161
- Structured-edit protocol: unchanged
- Native verifier: unchanged exact historical compile + test adapter
- Fresh independent checkout per arm/seed
- Persistent workspace within each arm/seed
- Maximum model calls: 3

## Temporal intervention

Call 1 is generated without any local-binding packet.

After a successfully applied but verifier-failing call 1:

1. retain the actual modified workspace;
2. expose the exact synchronized current-source window;
3. expose the native verifier residual;
4. inject the arm-specific binding packet for calls 2 and 3.

Thus the binding intervention begins only after the first falsified candidate has created a concrete refinement state.

## Arms

1. `SEM_TEMP_NONE`
   - semantic frozen capability + correct locus;
   - no binding packet after call 1.

2. `SEM_TEMP_RIGHT_BIND`
   - semantic frozen capability + correct locus;
   - after call 1 only, inject the V161 right binding: standalone command-token identity for command `ls`, with the same observed positive/negative examples.

3. `SEM_TEMP_WRONG_BIND`
   - semantic frozen capability + correct locus;
   - after call 1 only, inject the length-matched V161 wrong substring binding.

4. `OPAQUE_TEMP_RIGHT_BIND`
   - opaque same-shape capability control + correct locus;
   - after call 1 only, inject the same right binding.

5. `COLD_TEMP_RIGHT_BIND`
   - correct locus only;
   - after call 1 only, inject the same right binding.

All arms receive identical persistent-state, verifier-feedback, and source-synchronization machinery.

## Primary endpoint

Native verifier-confirmed solve of `thefuck/32` within 3 model calls.

## Secondary mechanism endpoints

- call-1 executable right-locus repair;
- call-2/3 executable right-locus refinement;
- transition of verifier failure class / failing example;
- transport failures;
- verifier calls;
- calls to solve.

Secondary endpoints cannot upgrade a failed primary endpoint.

## Frozen interpretation

`PASS_V162_TEMPORAL_BINDING_CAUSALLY_COMPLETES_TRANSFER` requires:

- `SEM_TEMP_RIGHT_BIND` solves at least 1/3 seeds; and
- its solved count is strictly greater than both `SEM_TEMP_NONE` and `SEM_TEMP_WRONG_BIND`; and
- its solved count is strictly greater than both `OPAQUE_TEMP_RIGHT_BIND` and `COLD_TEMP_RIGHT_BIND`.

If right binding solves but either opaque or cold right-binding controls match it, classify binding as sufficient but retained capability semantics as unnecessary.

If right binding changes the refinement trajectory but produces no verified solve, classify `OBSTRUCTED_V162_TEMPORAL_BINDING_MOVES_FRONTIER_NO_SOLUTION`.

If right binding does not outperform no-binding/wrong-binding on either verified solve or a preregistered verifier-residual transition, classify `NEGATIVE_V162_TEMPORAL_BINDING_NOT_CAUSAL`.

Any infrastructure error or insufficient comparable cells is R10 / obstructed and cannot count as a semantic negative.

## Claim boundary

A V162 pass would establish only that, on this frozen natural task and model, retained capability semantics + correct routing + temporally aligned local binding causally improve verified repair reachability over matched controls. It would not yet establish downstream developmental compounding. A pass would license admission/restart and a fresh downstream test; a failure would not.
