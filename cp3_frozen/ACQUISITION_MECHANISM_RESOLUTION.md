# CP3 acquisition mechanism resolution

Status: **RESOLVED BEFORE PROTECTED SEMANTIC EVALUATION**

## Decision

Checkpoint 3 acquisition is **verified-experience acquisition**, not a requirement that the frozen base model autonomously rediscover each acquisition repair.

The authoritative frozen boundary `ACQUISITION_BOUNDARY.json` explicitly permits these capability inputs:

- buggy source/context from acquisition cases;
- acquisition failing-test evidence;
- acquisition verifier outcomes;
- **acquisition-only successful intervention traces**.

It forbids developer patches/fixed implementations only on the **protected** side. Therefore the BugsInPy acquisition-case developer interventions may be used as acquisition-only successful traces after they are independently replayed against the buggy revision and accepted by the native historical verifier.

## Why this matters

The four-arm protected protocol limits model calls per **case-arm**. It does not impose an autonomous-discovery requirement on acquisition. Requiring Qwen to rediscover both acquisition fixes was a recovery implementation choice, not a frozen scientific precondition.

The causal CP3 question remains unchanged:

> Can bounded verified acquisition experience be compressed into a frozen portable capability whose executable/scoped availability causally changes performance on source-disjoint protected cases?

Using verified acquisition interventions tests this question more directly by separating:

1. acquisition evidence quality;
2. capability compression;
3. executable availability;
4. applicability/scoping;
5. protected transfer.

It does **not** support the stronger claim that Qwen autonomously discovered the acquisition repairs.

## Admissible acquisition procedure

For each frozen acquisition case (`httpie/5`, `youtube-dl/32`):

1. checkout the frozen buggy revision;
2. reproduce the failing native test in the exact historical Python runtime;
3. load the acquisition-only BugsInPy intervention patch;
4. reject it if it touches tests;
5. apply it to the buggy checkout;
6. run the same native verifier;
7. admit the intervention trace only if the verifier passes;
8. give only these two verified acquisition traces to the capability-synthesis step.

No protected source, patch, fixed implementation, outcome label, prior solution, or verifier feedback may be used during this process.

## Claim boundary

If this route succeeds, CP3 may claim **verified capability acquisition from successful intervention traces and causal protected transfer**. It may not claim autonomous acquisition-case bug discovery.

This resolution occurs before any protected semantic exposure and therefore does not constitute post-hoc protected tuning.
