# DI_BLIND_V1 — autonomous constructor challenge precommit

Status: **FROZEN BEFORE DI_V1 SYNTHESIS**

This experiment exists specifically to rule out the failure mode in the earlier demo: a human must not supply the abstraction that later appears to have been learned.

## Scientific question

Can a fixed model/controller, after seeing only one naturally selected executable failure in a fresh independent Lean checker, autonomously propose a new source-level capability that:

1. repairs the exposed failure;
2. survives a hidden regression gate;
3. transfers to at least one protected later case that was never shown to the proposer;
4. loses that transfer when the acquired change is ablated;
5. does all of the above without base-model weight updates or a human-authored target-specific repair rule?

A pass is **bounded autonomous capability construction from experience**. It is not AGI, open-ended self-improvement, or a claim that all memory/RAG baselines fail.

## Frozen external world

- Checker repository: `pmatos/vow-lean-kernel`
- Checker revision: `514ab33fc0262c491a0af1846cc3887f48411e36`
- Vow repository revision: `15c1b933f87eed2b23c176665730baea37706daa`
- Lean Kernel Arena artifact: run `31005978773`, artifact `8931227426`
- Arena revision: `8254ae7dc7d6c10dbea94b6761dcb1e4ccdfdee6`
- Deterministic ordering salt: `TRISKELION_BLIND_VOW_V1`

These are inherited from the already-frozen blind Vow gate, which selected the first unresolved case by hash ordering before semantic inspection.

## Frozen proposer

- Provider/runtime: River
- Base model: `Qwen/Qwen3.5-9B`
- No training or weight update during discovery
- Candidate count: **8**
- Temperature: **0.8**
- Maximum generated tokens per candidate: **1800**
- Candidate edit language: one exact string replacement in one file under `checker/kernel/**/*.vow`
- No target-specific repair primitives, AST patterns, semantic rules, or hand-written candidate transformations are supplied.

The proposer receives only:

- the frozen checker source inside the allowed edit surface;
- the single exposed NDJSON case;
- the baseline checker stdout/stderr/return code for that case;
- a generic instruction to diagnose and propose one minimal edit.

It does **not** receive:

- filenames or contents of the protected suffix;
- protected test outcomes;
- the earlier nanoda representation repair;
- a human-written hypothesis about the Vow failure;
- the manually instrumented `TRISK_DIAG` observations from the earlier diagnostic workflow.

## Blinding

The corpus is downloaded and deterministically ordered. The first unresolved case is extracted. The full corpus is then deleted before model proposal.

The evaluator later downloads the corpus again and recomputes the same commitment. Thus the proposer process has no test files from the protected suffix available to it.

## Candidate generation and selection

All 8 candidates are generated **before any hidden regression result is known**.

A candidate is syntactically admissible only if:

- its path is within `kernel/**/*.vow`;
- `old` occurs exactly once in the frozen source;
- `new != old`;
- it changes no harness/test/corpus file.

Candidates are evaluated in fixed generation order. The first candidate that:

1. builds the checker;
2. changes the exposed case from incorrect to correct; and
3. causes zero regressions on the fixed hidden regression gate

is retained. No further candidates are consulted after retention.

If none pass, the experiment is a valid negative. There is no human rescue.

## Hidden regression gate

After re-downloading and re-verifying the committed corpus, the evaluator selects the first **24** post-exposure cases that the frozen baseline checker already gets correct. Their filenames/content/outcomes are never shown to the proposer.

The retained candidate must preserve all 24.

## Protected transfer set

After retention, evaluate the retained checker on the remaining post-exposure ordered suffix. This occurs only after candidate selection is irrevocable.

A protected transfer success is a case where:

- frozen baseline is incorrect;
- retained checker is correct.

The proposer never sees these cases or their outcomes.

## Causal ablation

For every protected transfer success, restore the exact frozen source (remove the retained candidate) and rerun the case. The behavior must return to the frozen baseline result. Reapply the retained edit and rerun; correctness must return.

## Pass gate

`PASS_DI_BLIND_V1_AUTONOMOUS_CONSTRUCTION` requires all of:

- corpus commitment reproduced;
- exposed baseline genuinely incorrect;
- at least one model-generated syntactically admissible candidate;
- one candidate autonomously fixes the exposed case;
- retained candidate passes 24/24 hidden regressions;
- at least one protected later transfer success;
- all claimed transfer successes pass remove/restore causal ablation;
- no human repair edit occurred after this precommit;
- base model weights unchanged.

If exposed repair succeeds but there is no protected transfer, verdict is `PARTIAL_EXPOSED_ONLY`.

If no candidate fixes the exposed case, verdict is `VALID_NEGATIVE_NO_CONSTRUCTION`.

Infrastructure/build/provider failures are `INFRASTRUCTURE_NULL`, not capability negatives.

## Next gate if V1 passes

Freeze the retained edit as `O1`. Continue through the already committed ordered stream to the next unresolved experience under `D0 + O1`. Run the same proposer under the same rules to attempt `O2`.

The crown-jewel V2 signature is:

`O2` is not discoverable under matched budget from `D0`, but becomes discoverable from `D0 + O1`.

That is the point at which prior autonomous development demonstrably changes later discoverability.
