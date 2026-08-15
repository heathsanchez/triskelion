# Checkpoint 3 — Frozen Success / Failure Contract

Status: **PRE-PROTECTED-EVALUATION CONTRACT**

This document freezes interpretation before any protected semantic evaluation. It supplements, and does not override, `ACQUISITION_BOUNDARY.json`, `PROTECTED_EVAL_MATRIX.json`, `FOUR_ARM_PROTOCOL.json`, `SANITIZATION_POLICY.md`, and `ACQUISITION_GATE_RESOLUTION.md`.

## 0. Scientific question

Can bounded verified acquisition on source-disjoint BugsInPy cases be compressed into one frozen executable capability that changes protected repair performance for a frozen Qwen3.5-9B model, while verifier/scoping control preserves useful competence and reduces inappropriate activation relative to exposing the same capability indiscriminately?

This is a causal runtime claim, not a model-weight-learning claim.

## 1. Hard preconditions

A protected run is inadmissible unless all of the following hold:

1. Base model is exactly `Qwen3.5-9B`, temperature `0`.
2. Acquisition and protected project/case identities remain frozen.
3. Capability construction uses acquisition evidence only.
4. No protected fixed source, developer patch, prior solution, outcome trace, or verifier feedback enters capability construction.
5. The final executable capability and RAW-memory control are serialized and SHA-256 frozen before protected semantic exposure.
6. ALWAYS-ON and VERIFIED receive the exact same frozen capability payload; only routing/scoping differs.
7. COLD receives neither acquisition memory nor executable capability.
8. RAW MEMORY receives non-executable acquisition-derived text only and no executable capability artifact.
9. Every protected cell starts from isolated fresh runtime/model task state.
10. Same sanitized case input, model seed policy, call limit, token limit, verifier budget, and task environment are used across all four arms for a given protected case.
11. Maximum two model calls per cell, maximum 2,048 tokens per call, one protected evaluation repetition per cell.
12. No post-hoc exclusions, target-specific tuning, semantic reruns, or capability edits after the freeze.
13. Infrastructure failures remain infrastructure outcomes; they are never reclassified as semantic failures or successes.
14. Acquisition-count gate is satisfied under the recovered frozen protocol: at least 2 qualified acquisition cases and at least 5 qualified protected cases. See `ACQUISITION_GATE_RESOLUTION.md`.

### Acquisition-count gate

Resolved before protected semantic evaluation:

```text
ACQUISITION_HARD_GATE = acquisition >= 2 and protected >= 5
CURRENT_QUALIFIED = 2 acquisition + 5 protected
COUNT_GATE = SATISFIED
```

The historical language referring to a target of five acquisition cases is retained as a non-binding target unless stronger pre-protected protocol material is later recovered. The explicit frozen recovery workflow uses the 2+5 threshold and transitions from qualification merge to capability freeze/protected sanitization on that basis.

Protected semantic evaluation is nevertheless blocked until the acquisition-only capability itself is successfully frozen and its information-boundary checks pass.

## 2. Frozen protected matrix

Protected cases:

- `thefuck/32`
- `keras/32`
- `spacy/2`
- `fastapi/5`
- `black/18`

Arms:

- `COLD`
- `RAW MEMORY`
- `ALWAYS-ON`
- `VERIFIED`

Total planned semantic cells: `5 x 4 = 20`.

## 3. Primary observable per cell

Primary competence observable: binary native-verifier success after the arm's proposed patch under the frozen cell budget.

Record at least: native verifier result, local regression result, capability availability/invocation, activation reason/scope decision, calls/tokens, elapsed time, input/output/patch hashes, and infrastructure status. Model self-rating never counts as success.

## 4. Primary causal contrasts

### A — passive experience

`RAW MEMORY - COLD`

Descriptive only; it need not be positive for the central claim.

### B — executable capability

`ALWAYS-ON - RAW MEMORY`

Evidence for executable competence requires at least one protected case with:

```text
ALWAYS-ON = native PASS
RAW MEMORY = native FAIL
capability invoked in ALWAYS-ON
```

A positive aggregate pass-count delta is stronger but not required.

### C — applicability / scope

`VERIFIED - ALWAYS-ON`

A strong applicability result requires both:

1. preserved useful competence: successful capability-attributable ALWAYS-ON cases also succeed under VERIFIED when scope admits the capability; and
2. reduced bad activation: at least one protected case where ALWAYS-ON invokes the capability inappropriately or causes a native failure/regression, while VERIFIED withholds it and avoids that harm.

## 5. Result classes

### `CP3_STRONG_PASS`

All hard preconditions hold; there is at least one executable-capability win over RAW MEMORY, VERIFIED preserves useful capability-attributable wins, and VERIFIED prevents at least one inappropriate/harmful ALWAYS-ON activation.

### `CP3_COMPETENCE_PASS_SCOPE_NULL`

Executable capability creates at least one protected win over RAW MEMORY, but no false/harmful ALWAYS-ON activation is observed for VERIFIED to prevent.

### `CP3_SCOPE_PASS_COMPETENCE_NULL`

VERIFIED prevents bad ALWAYS-ON activations, but ALWAYS-ON never creates a protected native-verifier success beyond RAW MEMORY.

### `CP3_NULL`

Hard preconditions hold, but neither executable competence nor applicability benefit is observed.

### `CP3_HARMFUL`

Hard preconditions hold and the executable capability reduces protected native-verifier success or creates regressions without compensating capability-attributable wins.

### `CP3_INVALID`

Any information-boundary breach, protected-specific tuning, capability mutation after freeze, unequal arm budgets, warm-state contamination, or non-precommitted semantic rerun invalidates the causal claim.

### `CP3_INFRA_BLOCKED`

The scientific protocol remains intact but required runtime/environment infrastructure prevents reaching semantic cells. This is neither a pass nor fail of the capability hypothesis.

## 6. Deliberately not required

No significance threshold, p-value, confidence interval target, arbitrary percentage gate, or requirement that `RAW MEMORY > COLD` may be added after outcomes are seen.

## 7. Claim ceiling

Even `CP3_STRONG_PASS` supports only a bounded claim over this frozen model, runtime, capability and protected corpus. It does not establish universal continual learning, universal software repair, unrestricted self-improvement, neural weight acquisition, or superiority to fine-tuning/RL.

## 8. Decision rule

After a protocol-clean run, publish the result class exactly as determined above. Negative and null outcomes remain in the developmental ledger. No category or threshold may be changed after protected outcomes are known.
