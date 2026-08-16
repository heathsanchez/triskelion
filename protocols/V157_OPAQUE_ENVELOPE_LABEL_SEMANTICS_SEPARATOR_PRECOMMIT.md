# V157 OPAQUE-ENVELOPE LABEL-SEMANTICS SEPARATOR — PRECOMMIT

## Residual
V156 showed that RAW_T1 and a value-scrubbed, length-matched JSON trace both produced 3/3 falsification-driven rival execution while cold produced 0/3. However V156 preserved semantic wrapper/field labels (`RETAINED VERIFIED ACQUISITION TRACE`, `failure_class`, `failing_test_tail`, `changed_files`, `verified_intervention`, `ancestors`). Therefore V156 does not justify the stronger claim that nonsemantic formatting alone caused the search-policy change.

## Frozen question
Are the remaining semantic wrapper/field labels causally required for the V156 rival-execution effect?

## Fixed apparatus
Use the same T1=httpie/5 acquisition, T2=youtube-dl/32 task, Qwen/Qwen3.5-9B provider, seeds [202608161,202608162,202608163], two-call/2048-token budget, structured-edit protocol, persistent workspace, post-call-1 source synchronization, exact historical native verifier/runtime, and rival-execution endpoint as V155/V156.

## Arms
1. `COLD`: no retained trace.
2. `MATCHED_LABELLED`: exact V156 value-scrubbed control. Values are alphabet-substituted; wrapper and JSON keys remain readable.
3. `OPAQUE_ENVELOPE`: same evidence object and same serialized character length/JSON nesting/punctuation/whitespace order as MATCHED_LABELLED, but every ASCII letter in the wrapper, every JSON key, and every string value is replaced by a deterministic position/path-dependent pseudorandom ASCII letter of the same case. The replacement is not a monoalphabetic substitution: repeated letters at different positions need not map alike. Numbers/non-string literals and JSON punctuation are unchanged. Opaque JSON must parse successfully.

No task semantics, new diagnosis, repair hints, additional model calls, or verifier calls may be introduced by V157.

## Primary endpoint
Per seed, `rival_execution_success` is exactly the V156 endpoint: synchronized call 2 emitted 3 alternatives, all 3 valid, all 3 distinct from call 1, a rival was selected, no transport error occurred, and the selected rival reached the native verifier.

Let L, O, C be success counts (0..3) for MATCHED_LABELLED, OPAQUE_ENVELOPE, and COLD.

## Frozen verdict hierarchy
1. Construction/parse/length invariant failure -> `R10_INCONCLUSIVE_V157_CONTROL_CONSTRUCTION`.
2. Any arm not comparable on all 3 seeds -> `R10_INCONCLUSIVE_V157`.
3. L < 2 -> `OBSTRUCTED_V157_V156_EFFECT_NOT_REPLICATED`.
4. L-O >= 2 and L-C >= 2 -> `PASS_V157_SEMANTIC_LABELS_CAUSAL_FOR_RIVAL_EXECUTION`.
5. O >= 2 and abs(L-O) <= 1 and O-C >= 2 -> `NEGATIVE_V157_LABEL_SEMANTICS_NOT_REQUIRED_OPAQUE_ENVELOPE_SUFFICIENT`.
6. Otherwise -> `OBSTRUCTED_V157_INTERMEDIATE_SEPARATION`.

Task solving remains a downstream endpoint and is recorded, but is not required for this mechanism separator.

This protocol is frozen before any V157 model outcome is sampled.