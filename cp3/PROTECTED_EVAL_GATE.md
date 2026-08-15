# CP3 protected-evaluation gate

Do not inspect protected fixed implementations, developer patches, or protected outcome traces during acquisition capability construction.

Protected evaluation is permitted only after qualification evidence is merged and the acquisition capability artifact is frozen.

Four arms are fixed:

1. COLD
2. RAW MEMORY
3. ALWAYS-ON
4. VERIFIED

Model and budget are fixed: Qwen3.5-9B, temperature 0, identical seeds and budgets, maximum two calls per case-arm, 2,048 tokens per call, one protected evaluation per case-arm, no post-hoc exclusions or tuning.

Primary causal comparison: ALWAYS-ON versus VERIFIED, with explicit activation / false-activation accounting.
