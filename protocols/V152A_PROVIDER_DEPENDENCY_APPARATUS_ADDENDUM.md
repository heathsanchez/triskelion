# V152A — Provider dependency apparatus addendum

Frozen: 2026-08-16 NZST, after V152 run 31943661486 failed before any model call.

V152's sole eligible run failed during pip dependency resolution because the workflow unnecessarily requested both `river-client==0.6.1` and an explicit `transformers>=4.51,<5` constraint. The scientific runner never executed.

V151B had already successfully instantiated the same Qwen chat-tokenizer adapter in the same GitHub Actions substrate while installing only `river-client==0.6.1` and relying on the runner's existing Transformers installation.

V152A changes exactly one apparatus fact:

- install `river-client==0.6.1` only, matching the proven V151B setup.

No V152 scientific parameter changes: temperature remains exactly 0.7; model, T1/T2, frozen O1, raw T1 evidence, shams, seeds, two-call budget, context resolver, structured-edit protocol, exact native verifier, diversity gate, arm classifier, stopping rule, and claim boundary are unchanged.

V152 run 31943661486 remains immutable `R10_INCONCLUSIVE`. V152A receives a separate run identity.