# V156 — FORMAT-MATCHED RAW-T1 SEMANTIC SEPARATOR — PRECOMMIT

## Motivation

V155 was prospectively obstructed because its synchronization gate required call-2 verifier reach in COLD, RAW_T1, and SHAM_RAW. The frozen outcome nevertheless exposed a new arm-specific residual: RAW_T1 reached the call-2 native verifier on 3/3 seeds, whereas COLD, COMPILED_O1, SHAM_O1, and SHAM_RAW reached on 0/3. A zero-call audit found RAW_T1 emitted three valid distinct rivals on every seed; the existing SHAM_RAW is only a length-matched repetitive placeholder. Therefore V155 does not separate semantic developmental evidence from formatting/serialization priming.

V156 prospectively tests that distinction. V155 is not retrospectively upgraded.

## Sole causal change

Keep the complete V155 apparatus, but replace only the content of `D_PLUS_SHAM_RAW` with a deterministic format-matched semantic scrub of the exact RAW_T1 memory.

The matched control is constructed from the same raw evidence object and retains:

- the exact `RETAINED VERIFIED ACQUISITION TRACE:` wrapper;
- the exact JSON keys and nesting;
- exactly the same string lengths;
- punctuation, whitespace, digits, slashes, backslashes, and JSON escape structure;
- list cardinalities and field ordering;
- total character count.

Only ASCII alphabetic characters inside JSON string VALUES are substituted one-for-one using the frozen bijection:

`abcdefghijklmnopqrstuvwxyz -> qwertyuiopasdfghjklzxcvbnm`

Uppercase letters use the corresponding uppercase map. JSON keys are not changed. Non-string values are unchanged. This destroys ordinary lexical/task semantics while preserving the trace's serialization and code-like surface statistics far more closely than the prior repetitive sham.

If exact length equality fails, V156 returns R10 before model sampling.

## Invariants

All V155 variables remain fixed: T1, T2, model/provider, seeds, two-call budget, max tokens, exact source synchronization intervention, current-source window, persistent workspace, rival schema, parser, deterministic rival selection, historical native verifier, O1 arm, cold arm, and protected-evaluation boundary.

The original `D_PLUS_SHAM_RAW` arm name is retained, but in V156 it denotes the format-matched semantic scrub above. Its SHA256 is frozen in the result artifact.

## Prospectively defined intermediate capability

V155 motivates, but does not license, the following measure. V156 freezes it before outcomes.

A seed has `RIVAL_EXECUTION_SUCCESS` iff on call 2:

1. the V155 current-source synchronization block was injected;
2. exactly three alternatives were emitted;
3. all three alternatives are valid structured-edit payloads;
4. all three are distinct from the verifier-disproved call-1 payload;
5. the deterministic selected rival applies to the actual persistent post-call-1 workspace; and
6. the selected rival reaches the native verifier (a verifier verdict object exists).

Solving T2 is recorded separately and remains the stronger endpoint, but is not required for this newly frozen mechanism-level separator.

## Frozen primary comparisons

Let R = RAW_T1 number of `RIVAL_EXECUTION_SUCCESS` seeds out of 3.
Let M = format-matched semantic-scrub number out of 3.
Let C = COLD number out of 3.

Interpretation hierarchy:

1. Any memory-control construction/integrity failure => `R10_INCONCLUSIVE_V156_CONTROL_CONSTRUCTION`.
2. Any arm with fewer than 3 comparable seeds => `R10_INCONCLUSIVE_V156`.
3. If R >= 2, R-M >= 2, and R-C >= 2 => `PASS_V156_RAW_T1_SEMANTIC_RIVAL_EXECUTION_SIGNAL`.
4. Else if M >= 2 and abs(R-M) <= 1 => `NEGATIVE_V156_FORMAT_SERIALIZATION_EXPLAINS_RIVAL_EXECUTION`.
5. Else if R < 2 => `OBSTRUCTED_V156_RAW_T1_RIVAL_EXECUTION_NOT_REPLICATED`.
6. Otherwise => `OBSTRUCTED_V156_INTERMEDIATE_RIVAL_EXECUTION_SEPARATION_INSUFFICIENT`.

A task-level verified solve is separately reported but does not override this hierarchy.

## Anti-cherry-picking

Protocol, runner, workflow, substitution alphabet, seeds, thresholds, and measure are committed before V156 outcomes. No model output from V156 may change them.
