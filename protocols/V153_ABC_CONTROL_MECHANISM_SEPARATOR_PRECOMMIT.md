# V153 — ABC control mechanism separator

## Status

**PRECOMMITTED BEFORE V153 MODEL OUTCOMES**

## Question

The frozen Qwen3.5-9B ABC checkpoint has previously shown perfect ABC behavior under ordinary prompting while direct natural-language requests for A-only and AB-only returned ABC. Constituent behavior remained partially latent under prefix-completion probes.

V153 asks which control intervention, if any, restores selective A / AB / ABC behavior **without any weight update**.

This is a mechanism separator over the frozen checkpoint. It does not train, fine-tune, edit, or resynthesize weights.

## Frozen substrate

- Base model: `Qwen/Qwen3.5-9B`
- Checkpoint: `river://a25972d0-6711-4c05-8767-be061fc0e6ba/weights/ABC_training`
- Held-out strings: `violet, hidden, green, amber, silver, orange, teal, indigo`
- A target: `ka-{x}`
- AB target: `ka-{x}-zu`
- ABC target: `[ka-{x}-zu]`
- Temperature: 0.0 except the diversified arm, which uses deterministic prompt diversity rather than stochastic sampling.
- No gradient calls or optimizer steps are permitted.

## Important matched-interface control

The original three-skill training code used the exact interface:

```
Task: A
Input: {x}
Output:
```

and analogously for `AB` and `ABC`.

Earlier ABC retention probes instead used natural-language instructions such as “Apply only the original prefix rule A.” Therefore V153 treats exact training-interface recovery as a primary control. A recovery under exact task labels is evidence of an interface/representation mismatch, not evidence that an external controller invented the capability.

## Arms

For each requested stage `A`, `AB`, `ABC` and each held-out string:

1. `A_NL_BASELINE` — prior natural-language request, single greedy generation.
2. `B_EXACT_TASK_INTERFACE` — exact training interface `Task: {stage}\nInput: {x}\nOutput:`.
3. `C_NL_PREFIX_HORIZON` — natural-language request with a stage-compatible prefix seed to test bounded continuation reachability.
4. `D_EXACT_TASK_PREFIX_HORIZON` — exact task interface plus the same stage-compatible prefix seed.
5. `E_EXACT_TASK_PROMPT_ENSEMBLE` — a frozen deterministic set of semantically equivalent exact-task prompt variants; report both first-candidate accuracy and verifier-selected any-hit reachability. This arm is diagnostic for proposal-attractor collapse and must not be compared as equal-cost accuracy to single-call arms.
6. `F_EXACT_TASK_PLUS_STAGE_CONTRACT` — exact task label plus an explicit stop contract describing the requested terminal form without revealing the held-out output.

### Prefix seeds

- A: `ka-`
- AB: `ka-{x}`
- ABC: `[ka-{x}-zu`

The prefix arms score the concatenation of the frozen seed and generated continuation against the exact requested target. They test reachability from a lawful intermediate state and are not ordinary zero-shot generation arms.

## Primary classifications

- `PASS_INTERFACE_MISMATCH`: exact task interface restores A and AB to 8/8 while ABC remains 8/8.
- `PASS_HORIZON_RESCUE`: exact interface does not fully restore A/AB, but a prefix-horizon arm does.
- `PASS_PROPOSAL_RESCUE`: single exact-interface prompting fails, but frozen prompt-ensemble any-hit reaches the exact target on all held-out cases.
- `PASS_STAGE_CONTRACT_RESCUE`: the explicit stage contract restores selective behavior while exact labels alone do not.
- `MIXED_CONTROL_RESCUE`: more than one intervention helps but no single mechanism cleanly separates.
- `NEGATIVE_DEEP_ADDRESSABILITY_RESIDUAL`: none of the interventions restores A and AB despite frozen-weight constituent evidence.
- `R10_INCONCLUSIVE`: provider/checkpoint/apparatus failure invalidates the matched comparison.

## Claim boundary

V153 can identify an access/control mechanism on this frozen synthetic three-skill checkpoint. It cannot establish general neural forgetting, general VDI, open-ended developmental learning, or superiority over fine-tuning.
