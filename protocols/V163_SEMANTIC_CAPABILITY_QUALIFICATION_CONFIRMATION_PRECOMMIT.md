# V163 — Semantic Capability Qualification Confirmation

## Purpose

V162 produced a prospectively unplanned but native-verified 3/3 solve in `SEM_TEMP_NONE` under the combination of: frozen semantic capability, already-earned correct locus, persistent workspace, source synchronization, verifier feedback, and three calls. The binding interventions themselves did not cause the solve. V163 exists only to determine whether the semantic retained capability is causally necessary for that success once routing and temporal state are held fixed.

V163 must not be interpreted as evidence of downstream developmental compounding. It is an ancestor-qualification confirmation only.

## Frozen task and apparatus

- Task: `thefuck/32` from frozen BugsInPy commit `11c5f1eea954a42132cfd06bf257766a7963e0fd`.
- Model: `Qwen/Qwen3.5-9B` through the frozen River provider.
- Seeds: `202608171`, `202608172`, `202608173`.
- Maximum calls: 3 per seed/arm.
- Exact historical native verifier.
- Fresh independent checkout per seed/arm.
- Persistent workspace within each seed/arm across calls.
- Post-failure current-source synchronization before later calls.
- Structured-edit trust boundary unchanged.
- Correct locus signal `thefuck/rules/ls_lah.py` is supplied identically to every arm. V160 already established routing as a separate causal variable; V163 does not retest routing.
- No binding packet is supplied to any arm on any call.

## Frozen arms

1. `SEM_CONFIRM`: verified semantic capability manifest + correct locus.
2. `OPAQUE_CONFIRM`: same-length opaque capability manifest + correct locus.
3. `COLD_CONFIRM`: correct locus only.
4. `RAW_CONFIRM`: frozen raw acquisition memory + correct locus.
5. `RAG_CONFIRM`: deterministic retrieval from the frozen raw acquisition memory + correct locus.

No arm, seed, task, budget, memory construction, or pass threshold may be changed after outcomes are observed.

## Primary endpoint

Native verified solve of `thefuck/32` within three calls.

## Secondary mechanism endpoints

- call-1 executable edit at the correct locus;
- at least one executable post-first verifier-guided refinement;
- transport failures;
- verifier calls;
- calls to solve.

These mechanism endpoints cannot substitute for the primary endpoint.

## Frozen interpretation gate

Let `S_sem` be `SEM_CONFIRM.solved_n`, and `S_ctrl_max` the maximum solved count among `OPAQUE_CONFIRM`, `COLD_CONFIRM`, `RAW_CONFIRM`, and `RAG_CONFIRM`.

- `PASS_V163_SEMANTIC_CAPABILITY_CAUSALLY_QUALIFIED` iff all five arms have 3 comparable seeds, `S_sem >= 2`, and `S_sem > S_ctrl_max`.
- `V163_CAPABILITY_NOT_SEMANTICALLY_IDENTIFIED` iff all arms are comparable, `S_sem >= 2`, but one or more controls tie or beat `S_sem`.
- `NEGATIVE_V163_SEMANTIC_CAPABILITY_DOES_NOT_REPLICATE` iff all arms are comparable and `S_sem < 2`.
- `OBSTRUCTED_V163_R10_INSUFFICIENT_COMPARABLE` iff any arm has fewer than 3 comparable seeds.

A V163 PASS licenses admission of the frozen capability into replayable developmental state for the already-frozen downstream test `keras/32`. It does not itself establish developmental compounding.
