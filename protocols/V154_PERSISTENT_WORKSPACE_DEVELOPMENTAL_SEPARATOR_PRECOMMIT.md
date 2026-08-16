# V154 Persistent-Workspace Developmental Separator — Frozen Precommit

## Question

V153G showed that four of six frozen raw-T1 call-2 rivals were grounded only in the source state produced by call 1, while V153H showed that all six state-aligned rivals were executable but all failed semantically. The original V153 controller told the model that call 1 had been executed and verifier-disproved, yet created a fresh buggy checkout before applying call 2.

V154 asks the causal question left by that mismatch:

**With the V153 developmental comparison otherwise unchanged, does preserving the actual failed call-1 workspace into call 2 reveal a T1-derived advantage over cold and length-matched sham controls?**

## Frozen substrate

- Model: `Qwen/Qwen3.5-9B`
- Provider and model-call parameters: unchanged from V151/V153
- T1: BugsInPy `httpie/5`
- T2: BugsInPy `youtube-dl/32`
- Seeds: `202608161`, `202608162`, `202608163`
- Maximum calls per arm/seed: 2
- Maximum tokens per call: 2048
- Arms:
  - `D_COLD`
  - `D_PLUS_O1_COMPILED`
  - `D_PLUS_RAW_T1`
  - `D_PLUS_SHAM_O1`
  - `D_PLUS_SHAM_RAW`
- T1 intervention identity, O1 identity, T2 visible context, memory construction, sham length matching, exact historical runtime, and advantage function are inherited unchanged from V151.
- Call-2 ranked-rival schema and deterministic first-valid-distinct selection are inherited unchanged from V153.

## Sole intervention

For each arm/seed, create exactly one T2 working checkout before call 1.

- Call 1 structured edits are applied to that checkout and tested by the native verifier.
- If call 1 fails semantically, **do not reset or re-checkout**.
- Call 2 receives the same V153 feedback saying the normalized call-1 edit was executed and verifier-disproved.
- The selected call-2 rival is applied to the same post-call-1 working tree and then tested.

No automatic rollback, fuzzy rebase, state-aware alternative substitution, or search over ranks is allowed. If the deterministic selected rival does not apply to the persistent state, that remains a transport failure.

The reusable precompiled apparatus may only supply the clean initial T2 checkout. V151 `prepare_t2()` must run the untouched buggy baseline before any arm, thereby freezing the reusable template from clean T2 before candidate execution. Within an arm/seed, the workspace itself is persistent and is never written back into the template.

## Primary outcomes

For each arm:

- solved seeds / 3
- comparable seeds / 3
- calls to solve
- generated tokens / output-char proxy for solved cases
- verifier calls
- transport failures

Use the unchanged V151 `advantage()` rule separately for:

- compiled O1 versus `D_COLD` + `D_PLUS_SHAM_O1`
- raw T1 versus `D_COLD` + `D_PLUS_SHAM_RAW`

## Decision rule

If any arm lacks all three comparable seeds: `R10_INCONCLUSIVE_V154`.

Otherwise:

- compiled O1 advantage and raw T1 advantage: `PASS_V154_BOTH_REPRESENTATIONS_SIGNAL_PERSISTENT_STATE`
- compiled O1 advantage only: `PASS_V154_COMPILED_O1_CAUSAL_SIGNAL_PERSISTENT_STATE`
- raw T1 advantage only, with at least one raw-T1 solve: `PASS_V154_RAW_T1_CAUSAL_SIGNAL_PERSISTENT_STATE`
- neither advantage: `NEGATIVE_V154_NO_T1_DEVELOPMENTAL_SIGNAL_PERSISTENT_STATE`

Additionally report but do not use as an outcome-dependent gate:

- number of call-2 selected rivals reaching the verifier per arm
- number of call-2 transport failures per arm
- call-1 and call-2 edit payload hashes

## Interpretation boundary

A positive V154 result would establish a bounded causal developmental signal under this corrected persistent-workspace controller. It would not establish open-ended learning, general intelligence, or O3 compounding.

A negative V154 result is stronger than V153's obstruction because it removes the demonstrated reset-state mismatch while retaining matched cold and sham controls. It remains bounded to this model, task, memories, seeds, and two-call budget.

V153D/E/F standalone replay execution counts are not used as evidence in this decision because their fresh-template diagnostic runs can cache a candidate-mutated workspace. V153G's pure state classification and V153H's immutable state-aligned verifier replay motivate V154 but do not enter its scoring.