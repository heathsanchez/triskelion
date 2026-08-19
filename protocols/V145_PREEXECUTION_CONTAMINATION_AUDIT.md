# V145 — Preexecution Contamination Audit

## Status

**BLOCKED BEFORE SCIENTIFIC EXECUTION**

This audit was added after the original V145 preregistration but before any V145 arm execution. It does not rewrite the frozen V145 protocol. It records a newly discovered evidence-boundary problem and prevents a stronger claim from being made with a target whose semantic repair had already been exposed in earlier work.

## Trigger

The original V145 preregistration froze:

- E1 = `httpie/5`
- E2 = `youtube-dl/32`
- E3 = `pandas/66`

A retrospective evidence search conducted before V145 execution found that `pandas/66` had already appeared in prior BugsInPy work as a semantically revealed target. Specifically, prior artifacts had already classified its developer repair as `DEPENDENCY_LIFT` and retained that result as an epistemic event.

Therefore `pandas/66` remains a valid real BugsInPy case and may remain valid for narrower reproduction, eligibility, reuse, or intervention tests, but it is not clean enough to support the strongest claim that V145 prospectively discovered a previously unseen natural O3 from a blind external episode.

## Rigorous classification

V141 is not erased.

The following narrower result remains admissible:

`PASS_V141_THIRD_NATURAL_EPISODE_EXISTS`

meaning a third real pre-existing BugsInPy episode passed the frozen runtime/reproduction/ordering eligibility gate.

The following stronger upgrade is **not** licensed using `pandas/66`:

`pandas/66 is a clean blind natural E3 for prospective O3 discovery`

That statement is withdrawn before V145 execution.

## Evidence rule

For the strongest natural-developmental claim, E3 must satisfy both:

1. the frozen mechanical eligibility rule from the V141 lineage; and
2. a preexecution semantic-exposure audit showing that the task's repair/source/patch semantics were not previously inspected by the experiment-design lineage in a way that could shape the developmental controller, operator language, prompts, hypotheses, or interpretation.

Merely reproducing a buggy runtime/test before the causal experiment is not semantic contamination. Reading or semantically classifying the developer repair is.

## No-rescue rule

Do not replace `pandas/66` by choosing a convenient task after inspecting candidate repair semantics.

A successor must use the same frozen 501-case corpus and the same V141 deterministic ordering/eligibility procedure, augmented only by a pre-frozen exposure denylist/audit. Walk forward mechanically until the first case that is both:

- naturally eligible under the original V141 runtime/reproduction rules; and
- clean under the exposure rule.

Infrastructure-ineligible cases remain infrastructure negatives. Previously exposed cases are `EXPOSURE_INELIGIBLE`, not semantic failures. Neither may be silently skipped without a logged reason.

## Successor experiment

The original V145 protocol is retained unchanged as a preregistration artifact and must not be executed for the strongest blind-natural claim.

After a clean E3 is mechanically identified, create a new numbered/revision protocol with:

- the same six-arm causal design;
- the same matched budgets and verifier boundary;
- the same E1/E2 lineage unless their own exposure audit requires revision;
- the newly frozen clean E3;
- the exposure-manifest SHA-256 included in every run record;
- explicit `EXPOSURE_INELIGIBLE` handling.

No V145 scientific arm should execute until that successor freeze exists.

## Current verdict

- Third real eligible episode exists: **YES**.
- `pandas/66` clean blind natural O3 target: **NO**.
- Original V145 package integrity: **PRESERVED**.
- Original V145 execution for crown-jewel claim: **BLOCKED BEFORE EXECUTION**.
- Next deciding move: **mechanically identify the first contamination-clean eligible E3, then refreeze the six-arm experiment under a new protocol identity**.
