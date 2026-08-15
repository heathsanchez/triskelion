# Checkpoint 3 — Frozen Success / Failure Contract

Status: **PRE-PROTECTED-EVALUATION CONTRACT**

This document freezes interpretation before any protected semantic evaluation. It supplements, and does not override, `ACQUISITION_BOUNDARY.json`, `PROTECTED_EVAL_MATRIX.json`, `FOUR_ARM_PROTOCOL.json`, and the sanitization policy.

## 0. Scientific question

Can bounded verified acquisition on source-disjoint BugsInPy cases be compressed into one frozen executable capability that changes protected repair performance for a frozen Qwen3.5-9B model, while verifier/scoping control preserves useful competence and reduces inappropriate activation relative to exposing the same capability indiscriminately?

This is a causal runtime claim. It is not a model-weight-learning claim.

## 1. Hard preconditions

A protected run is **inadmissible** unless every item below is satisfied.

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
13. Infrastructure failures remain `INFRASTRUCTURE_UNKNOWN/NEGATIVE`; they are never reclassified as semantic failures or successes.
14. The historical acquisition-count hard gate is resolved from authoritative pre-protected protocol evidence.

### Acquisition-count gate

Current recovery has two known qualified acquisition cases (`httpie/5`, `youtube-dl/32`) and five protected cases. A recovery workflow used `acquisition >= 2` as an operational merge gate, but historical notes also refer to a target of five acquisition cases.

Therefore the scientific gate is currently:

```text
ACQUISITION_HARD_GATE = UNRESOLVED
PROTECTED_SEMANTIC_EVALUATION = BLOCKED
```

The protected run may begin only after authoritative historical protocol material establishes either:

- two acquisition cases were already sufficient under the frozen design; or
- the five-case acquisition requirement is met by infrastructure-only recovery preserving the frozen ordering and information boundary.

No new semantic criterion may be invented merely to unblock execution.

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

The primary competence observable is binary native-verifier success after the arm's proposed patch under the frozen cell budget.

For every cell record at least:

- native verifier result;
- local regression result;
- capability availability;
- capability invocation;
- activation reason/scope decision;
- calls and tokens used;
- elapsed time;
- input/output/patch hashes;
- infrastructure status.

No model self-rating counts as success.

## 4. Primary causal contrasts

### Contrast A — passive experience

```text
RAW MEMORY - COLD
```

Interpretation: effect of non-executable acquisition-derived memory/context.

This contrast is descriptive, not required to be positive for the central Triskelion claim.

### Contrast B — executable capability

```text
ALWAYS-ON - RAW MEMORY
```

Interpretation: causal effect of making the frozen executable capability available independent of applicability filtering.

Evidence for executable competence requires at least one protected case where:

```text
ALWAYS-ON = native PASS
RAW MEMORY = native FAIL
```

with identical case input and budget, and where the capability was actually invoked in ALWAYS-ON.

A stronger result has a positive aggregate pass-count delta across the five protected cases.

### Contrast C — applicability / scope

```text
VERIFIED - ALWAYS-ON
```

This is not simply a raw pass-rate comparison. VERIFIED exists to change **activation behavior** while retaining useful capability.

A strong applicability result requires both:

1. **preserved useful competence:** every protected case on which ALWAYS-ON succeeds because of an invoked capability also succeeds under VERIFIED when the scope rule admits the capability; and
2. **reduced bad activation:** at least one protected case where ALWAYS-ON invokes the capability inappropriately or produces a capability-induced native failure/regression, while VERIFIED withholds it and avoids that harm.

The strongest bounded pattern is therefore:

```text
ALWAYS-ON: competence gain + at least one false/harmful activation
VERIFIED:  retains the useful gains + fewer false/harmful activations
```

## 5. Result classes

### `CP3_STRONG_PASS`

All hard preconditions hold, and protected results show:

- at least one causal executable-capability win (`ALWAYS-ON PASS`, `RAW MEMORY FAIL`, capability invoked);
- no loss of the capability-attributable successful cases when VERIFIED admits the capability;
- at least one inappropriate/harmful ALWAYS-ON activation prevented by VERIFIED;
- zero protected-specific tuning or information-boundary violations.

This supports the bounded claim:

> a frozen model can acquire a portable executable capability from verified experience, and verifier/scoping control can preserve the acquired competence while reducing misuse on protected real-world tasks.

### `CP3_COMPETENCE_PASS_SCOPE_NULL`

Hard preconditions hold and executable capability causes at least one protected win over RAW MEMORY, but there is no observed false/harmful ALWAYS-ON activation for VERIFIED to prevent.

Interpretation: evidence for portable executable competence, but the protected sample does not establish the applicability-control advantage.

Do not promote this to the full scoped-plasticity claim.

### `CP3_SCOPE_PASS_COMPETENCE_NULL`

VERIFIED prevents bad ALWAYS-ON activations, but ALWAYS-ON never creates a protected native-verifier success beyond RAW MEMORY.

Interpretation: evidence for routing/scope selectivity only; no protected evidence that the executable capability adds competence.

### `CP3_NULL`

Hard preconditions hold, but neither executable competence nor applicability benefit is observed.

This is a valid negative result. Preserve it unchanged.

### `CP3_HARMFUL`

Hard preconditions hold and the frozen executable capability reduces protected native-verifier success or creates regressions without compensating capability-attributable wins.

This is a valid negative law about the acquired capability or construction method. Do not tune against protected cases to rescue it.

### `CP3_INVALID`

Any information-boundary breach, protected-specific tuning, capability mutation after freeze, unequal arm budgets, warm-state contamination, semantic rerun outside precommitted infra rules, or unresolved acquisition hard gate invalidates the causal claim.

An invalid run may be useful for debugging but is not evidence.

### `CP3_INFRA_BLOCKED`

The scientific protocol remains intact but the required historical runtime/environment cannot be reproduced sufficiently to reach the semantic cells.

This is neither pass nor fail of the capability hypothesis.

## 6. What is deliberately NOT required

Because the protected set is only five cases and was frozen for a bounded causal demonstration, this contract does **not** retrofit a significance threshold, p-value, confidence interval target, or arbitrary percentage gate after seeing outcomes.

Likewise, `RAW MEMORY > COLD` is not necessary for the central executable-capability claim. Passive memory may help, hurt, or be neutral.

The central evidence is paired causal behavior under identical protected inputs and budgets.

## 7. Claim ceiling

Even `CP3_STRONG_PASS` supports only a bounded claim over this frozen model, runtime, capability and protected corpus.

It does not establish:

- general continual learning for arbitrary models;
- universal software repair;
- autonomous unrestricted self-improvement;
- neural weight acquisition;
- global superiority to fine-tuning or RL.

Those require additional prospective experiments.

## 8. Decision rule

After a protocol-clean run, publish the result class exactly as determined above. Negative and null outcomes are retained in the developmental ledger. No threshold or category may be changed after protected outcomes are known.
