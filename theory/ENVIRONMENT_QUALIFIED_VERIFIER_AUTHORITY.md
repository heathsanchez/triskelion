# Environment-qualified verifier authority

A verifier observation is only admissible developmental evidence when the execution environment is itself qualified for the claim being tested.

## Motivation

V115B exposed a category error that ordinary pass/fail protocols can miss. Historical BugsInPy cases were nominally `baseline failing`, but many failures arose from interpreter/dependency/tooling incompatibility rather than the historical target bug. Treating those failures as scientific residuals would let infrastructure noise update the capability state.

The developmental controller therefore needs an observation boundary stricter than `command returned nonzero`.

## Qualified observation

Let:

- `x` be the target artifact/task;
- `E` be the execution environment;
- `V` be the verifier procedure;
- `c` be the intended claim about the artifact;
- `o = V_E(x)` be the raw observation.

Define an environment qualification predicate:

`Q(E, V, x, c)`.

Only if `Q = true` may `o` enter the developmental evidence set.

The effective verifier authority is therefore not `V` alone but the pair:

`V* = (V, Q)`.

An unqualified observation has epistemic status:

`INFRA / UNKNOWN`,

not `FAIL` and not `PASS` for the scientific claim.

## Historical bug-repair specialization

For a historical regression benchmark with fixed revision `f` and buggy revision `b`, the preferred qualification is:

1. the same environment `E` can provision both revisions;
2. the relevant verifier/test command executes normally in both;
3. `V_E(f) = PASS`;
4. `V_E(b) = FAIL`;
5. the failure on `b` is attributable to the benchmark-relevant assertion/exception or an explicitly accepted equivalent failure signature;
6. dependency/interpreter/tooling failures are classified separately from semantic failure.

Only then may blind repair search begin.

## Developmental-state rule

Let `D_t` be developmental state and `Obs_t` a new raw observation.

If `Q(Obs_t) = false`, then:

`D_{t+1} = D_t`.

No obstruction, scope update, capability extension, retraction, quotient refinement, or negative law may be learned from an unqualified observation.

If `Q = true`, the observation may pass to the ordinary residual / closure / construction / governance loop.

## Relation to verifier-indexed quotients

Earlier theory indexed behavioural identity by verifier authority:

`x ~_V y`.

The corrected object is:

`x ~_(V,Q) y`,

where observational equivalence is formed only over qualified observations.

Otherwise environmental failure can create false separators or false equivalences.

This gives a new failure mode for quotient construction:

- **false split:** two behaviours appear different only because one execution environment is broken;
- **false merge:** both behaviours fail for the same infrastructure reason, hiding a real semantic distinction.

Environment qualification therefore precedes quotient refinement.

## Trust hierarchy

A useful observation hierarchy is:

1. `RAW_OUTPUT` — bytes / exit status only;
2. `EXECUTED` — verifier command actually ran;
3. `ENVIRONMENT_QUALIFIED` — environment supports the intended comparison;
4. `CLAIM_RELEVANT` — result corresponds to the target property/failure signature;
5. `CAUSAL` — intervention changes the qualified result and ablation restores it;
6. `TRANSFERRED` — same retained capability predicts/repairs source-distinct qualified cases;
7. `LAWBOOK_ADMISSIBLE` — governance, provenance, scope, and withdrawal conditions satisfied.

Only levels 3+ may create scientific residuals; stronger developmental claims require the later levels.

## Consequence for the main theory

The current developmental object should be indexed by qualified verifier authority:

`R(A, V*, B; o)`

with `V* = (V,Q)`.

This makes explicit that capability growth is relative not merely to a checker, but to a trusted observational regime.

The core controller becomes:

`world -> qualify environment -> observe -> residual -> closure test -> construct/refine -> causal verify -> retain -> transfer -> revise/collapse/retract`.

This is not extra hygiene around the theory. It is part of the theory's trust boundary: **bad observational worlds must not be allowed to rewrite the system's developmental state.**
