# CONSEQUENCE × WHAKAPAPA × FORM V1 — implementation addendum for retry

Status: **FROZEN AFTER TWO HARNESS CANCELLATIONS AND BEFORE RETRY IMPLEMENTATION**

The scientific precommit at `37daa6bf746d57aa8f5dc295f16d14eb44393190` remains unchanged.

Both earlier runs terminated before producing any scientific result because the implementation attempted to enumerate too much of the six-input Boolean expression space while constructing the bounded transparent-form candidate set.

This addendum fixes only the computational realization of the already-precommitted phrase:

> "independently search a bounded transparent-form candidate set"

The bounded candidate set for the retry is now made explicit.

## Exact candidate set

For each verified capability C, the optimizer compares only these transparent exact candidates:

1. its inherited fully expanded construction form;
2. the same constructor rebuilt from the **current verified optimized forms of its two parents**;
3. an environmental D+GROUND bank generated prospectively as follows.

### Environmental bank

Start from the six input variables and GROUND.

For D-costs 1 through 12, generate candidates by SHA256-deterministic pairing of already admitted lower-cost bank expressions.

At each exact cost c:

- examine exactly 4,096 pair proposals, indexed by j=0..4095;
- choose left and right source expressions by SHA256("CWF-V1-BANK"|c|j|"L/R") modulo the already-admitted pool of compatible lower total cost;
- form D(left,right);
- verify its exact 64-row consequence;
- retain the lexicographically least serialization for each new consequence at that exact cost;
- never replace a consequence by a higher-cost form.

The bank is constructed once before the developmental stream and is therefore finite, deterministic, and independent of observed outcomes.

This is a **sampled bounded candidate bank**, not a claim to enumerate every six-input D formula of cost <=12.

## Form installation

A candidate form may replace the current form iff exhaustive 64-row evaluation proves exact equality with the protected consequence.

Changing form never changes:

- consequence;
- parent edges;
- verifier digest;
- birth event;
- ancestry depth.

## Scientific interpretation

No gate threshold changes.

The retry still tests the same architectural hypothesis:

[
oxed{	ext{deep provenance can coexist with shallow verified current form}}
]

The addendum narrows only the implementation of the precommitted bounded search so the harness can terminate on hosted CI.
