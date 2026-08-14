# Next gate: blind autonomous kernel-capability discovery

The current nanoda experiment should not be reused to claim autonomous discovery because the representation repair was designed after inspecting the exposed failure and source.

A clean next experiment must be precommitted before the discovering agent sees protected cases.

## Protocol

1. Freeze a fresh independent checker revision not used in the nanoda experiment.
2. Freeze the Arena/test corpus revision and hash-order the candidate stream before semantic inspection.
3. Split cases into:
   - exposed sequential experience,
   - protected regression set,
   - protected later transfer set.
4. Freeze the allowed source-edit surface and execution budget.
5. For each exposed failure:
   - run the current checker;
   - form a residual from executable evidence;
   - first test whether retained capabilities/patch modules already close the residual;
   - only if closure fails permit synthesis of a new capability;
   - require current-case necessity and protected regression safety before retention.
6. Do not reveal protected transfer cases to the discovering agent.
7. Later evaluate retained capabilities on protected cases.
8. For every claimed reuse, ablate the retained capability and require the later behavior to disappear.
9. Include negative experience and allow scope narrowing/revision if a retained capability becomes overbroad.

## Minimum publishable gate

A fresh run should demonstrate at least two distinct capability events, each with:

- old closure obstruction
- capability synthesis from exposed evidence
- local necessity
- protected regression pass
- retention
- later independently authored causal reuse
- ablation

and at least one closure-only event where apparent novelty is rejected because an existing capability already explains the residual.

The discovering process must not have prior access to protected target semantics or source-specific patches.

## Arms

Use matched budgets:

- no persistent capability memory
- raw textual memory
- always-retain successful patches
- verified capability algebra with closure-before-invention and protected promotion gates

This is the experiment needed to move from “the mechanism works in a real proof checker” to “verified experience autonomously grows a proof checker's capability algebra.”
