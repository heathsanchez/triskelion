# Developmental Controller Constitution V1

## Status

**PRECOMMITTED OPERATING CONSTITUTION**

This document governs the progression from CP3 through CP6. It is a companion to `RGRS_OPERATING_MANUAL_V1.md` and does not rewrite or supersede earlier frozen semantic outcomes, case selections, capability hashes, model freezes, protected splits, or verifier results.

The central rule is:

> **Freeze evidence when necessary; do not freeze intelligence.**

The corresponding asymmetry is:

`E_(t+1) ⊇ E_t`

while admitted operators, laws, representations, routing policies, triggers, and search policies may be narrowed, merged, revised, disabled, or deleted.

Historical evidence is monotone. Interpretation and controller policy are defeasible.

---

## 1. Trust boundary

The controller maintains four conceptually distinct state classes:

`S_t = (E_t, O_t, L_t, D_t)`

where:

- `E_t` — immutable experimental evidence: frozen case identity, manifests, hashes, verifier outputs, measured costs, run artifacts, and outcome records;
- `O_t` — currently admitted operators/capabilities;
- `L_t` — revisable laws about scope, applicability, composition, equivalence, and obstruction;
- `D_t` — revisable developmental/search policy: proposal generation, routing, representation selection, prioritization, and memory policy.

Only `E_t` is monotone.

The proposing mechanism may be an LLM, human, enumerator, search procedure, theorem prover, program synthesizer, or composition of these. Proposal generation has no authority to declare truth.

External verifiers and frozen experimental facts are the hard evidence boundary.

---

## 2. Experimental state machine

Every protected experiment must occupy exactly one state:

`PROPOSED -> PRECOMMITTED -> APPARATUS_VALID -> EXECUTED -> VERDICT -> REPLAYED`

Allowed terminal verdicts are:

- `ADMITTED`
- `REJECTED`
- `NO_TRANSFER`
- `NON_CAUSAL_GAIN`
- `INFRASTRUCTURE_NULL`
- `INCONCLUSIVE`
- `OBSTRUCTED`

### 2.1 Infrastructure-null rule

If the designated historical runtime, native verifier, checkout, adapter, dependency environment, runner, or required instrumentation did not execute as precommitted, the semantic hypothesis is not updated.

The result is recorded permanently as:

`INFRASTRUCTURE_NULL`

It must not later be overwritten by a repaired run. The repaired experiment receives a new run identifier linked to the null result.

### 2.2 No semantic rescue

Infrastructure may be repaired when the infrastructure itself is the residual, provided that protected semantic outcomes are not used as a tuning signal.

Forbidden after protected execution begins:

- changing protected case selection because of correctness outcomes;
- changing the target operator because a protected case exposed a semantic weakness;
- changing the primary success metric after seeing results;
- removing protected failures from the denominator;
- changing the verifier because it rejected the intervention;
- using protected source or protected semantic labels to tune an activation predicate.

---

## 3. Apparatus validity gate

No protected score is scientifically interpretable until all required apparatus checks pass.

A valid evidence object is:

`E = (C, H, A, V, R)`

where:

- `C` — frozen case identity and split membership;
- `H` — environment/harness manifest;
- `A` — arm/intervention/ablation identity;
- `V` — verifier evidence;
- `R` — replay/provenance record.

Minimum gate:

1. expected repository and case commit checked out;
2. expected historical runtime actually launched;
3. buggy baseline reproduces the frozen failing behavior;
4. fixed reference or qualifying condition reproduces where required by the parent protocol;
5. designated native verifier/test command actually executes;
6. model receives only information permitted by the arm;
7. capability/operator hash and enabled-state match the frozen arm;
8. ablation arm proves the relevant intervention is absent;
9. run record includes environment, dependency, command, seed/config, stdout/stderr, verifier status, and artifact identifiers;
10. no required artifact is missing or silently truncated.

Failure of any mandatory apparatus check yields `INFRASTRUCTURE_NULL` unless the parent protocol explicitly defines a different infrastructure status.

---

## 4. CP3 — causal real-artifact competence

### Question

Does a previously acquired verified capability causally improve unfamiliar real software-artifact repair under a protected protocol?

### Frozen inheritance

Existing CP3 acquisition/protected splits, capability/runtime hashes, model/config freezes, verifier definitions, and arm definitions remain authoritative. This constitution does not alter them.

### Required comparisons

At minimum, use the already frozen CP3 arms. Any added diagnostic arm must be declared before protected execution and may not alter the primary comparison.

### CP3 pass conditions

`CP3_PASS` requires all of:

1. apparatus-valid protected runs;
2. frozen verifier decides semantic correctness;
3. intervention improves the precommitted primary endpoint over the designated cold/baseline arm;
4. causal ablation removes or materially weakens the gain according to the frozen threshold;
5. no protected-semantic retuning occurred;
6. replay succeeds from recorded manifests/artifacts.

### CP3 classified outcomes

- acquisition success + protected regression -> `NO_TRANSFER` or RGRS P6 as appropriate;
- protected gain without successful causal ablation -> `NON_CAUSAL_GAIN`;
- invalid environment/runner/verifier -> `INFRASTRUCTURE_NULL`;
- semantically invalid gain -> `REJECTED` with R9 Soundness;
- insufficient deciding evidence -> `INCONCLUSIVE`.

Passing CP3 permits escalation to CP4. Failing CP3 does not permit redefining CP3 post hoc.

---

## 5. CP4 — source-distinct operator transfer

### Question

Does an admitted operator/abstraction survive beyond the artifact or source from which it was acquired?

### Required separation

The transfer target must be source-distinct enough that the original patch, exact target-specific solution, or source text cannot directly solve the new target.

### CP4 pass conditions

`CP4_PASS` requires all of:

1. operator `O1` was frozen before exposure to the protected transfer target;
2. source/project B is distinct from acquisition source/project A by the precommitted separation rule;
3. `O1` improves the primary protected endpoint on B;
4. ablating `O1` selectively removes/materially weakens that benefit;
5. a matched raw-history/transcript arm does not fully explain the gain, or the protocol records that retrieval remains an unresolved alternative explanation;
6. verifier and apparatus gates pass;
7. replay succeeds.

### CP4 verdicts

- passes all gates -> `ADMITTED` and `CP4_PASS`;
- transfer gain disappears under source separation -> `NO_TRANSFER`;
- gain survives but ablation does not matter -> `NON_CAUSAL_GAIN`;
- invalid apparatus -> `INFRASTRUCTURE_NULL`.

---

## 6. CP5 — developmental acceleration

### Question

Does verified developmental state causally reduce the cost of discovering a subsequent capability that the prior capability cannot directly solve?

### Direct-solution exclusion

`O1` must be unable, by itself, to satisfy the verifier for the `O2` discovery target under the frozen test. Otherwise the experiment measures reuse rather than developmental acceleration.

### Discovery-cost vector

Record, at minimum:

`C = (model_calls, verifier_calls, candidate_count, tokens, wall_time)`

One primary cost measure and its aggregation rule must be frozen before protected execution. All other components remain reported secondary measures and may not replace the primary measure post hoc.

### Required arms

Where feasible, freeze matched arms corresponding to:

- `A` — COLD;
- `B` — RAW_HISTORY;
- `C` — `O1_ONLY`;
- `D` — `L1_ONLY`;
- `E` — `O1_PLUS_L1`;
- `F` — FULL_DEVELOPMENTAL_STATE;
- `G` — SHUFFLED_EQUAL_SIZE_STATE.

If a domain makes one arm impossible, the omission and reason must be precommitted.

### CP5 primary hypothesis

For the precommitted primary discovery-cost measure:

`Cost(P2 | FULL_DEVELOPMENTAL_STATE) < Cost(P2 | COLD)`

and the target must still satisfy the external verifier.

### Causal decomposition

The result must separately test whether the advantage is carried by:

- possession of `O1`;
- a developmental law `L1`;
- their composition;
- structured developmental history beyond equal-sized shuffled state.

### CP5 pass conditions

`CP5_PASS` requires:

1. direct-solution exclusion holds;
2. full developmental state reaches the verified `O2` target under the frozen budget;
3. primary discovery cost improves over COLD by the frozen rule;
4. at least one prespecified ablation/decomposition comparison identifies a causal carrier;
5. shuffled equal-size state does not erase the claimed trajectory-specific effect if trajectory structure is part of the claim;
6. apparatus/replay gates pass.

A speedup that comes only from giving the model more tokens, more attempts, more source information, or a larger unmatched tool set is not a developmental result.

---

## 7. CP5-R — counterexample-driven revision

### Question

Can the controller withdraw permission to generalize when a retained law meets genuine counterevidence?

Given admitted law `L1`, expose a precommitted counterexample world/case outside the evidence used to admit `L1`.

Correct controller responses include:

- narrow applicability;
- split `L1` into scoped laws;
- demote confidence/status;
- disable activation;
- reject/delete `L1` while retaining its historical evidence.

Incorrect response:

- retaining the original unqualified law solely because it previously passed.

### CP5-R pass conditions

1. counterexample is externally verified;
2. controller revises or withdraws the contradicted claim;
3. historical evidence remains unchanged;
4. earlier valid replay obligations still pass where the revised scope says they should;
5. the new law/state is itself replayable.

This establishes the invariant:

`evidence monotone; beliefs defeasible`.

---

## 8. CP6 — verified recompression

### Question

Can accumulated operators/laws be compressed without losing frozen verified capability, and does compression improve future search or system cost?

### Operator-inflation control

Track at minimum:

- retained operator count;
- retained law count;
- description/serialization size;
- activation complexity;
- verifier cost;
- memory/runtime overhead;
- future discovery cost.

### Recompression proposal

A compression such as:

`{O1, O2, ..., Ok} -> O*`

is admissible only if the proposed replacement is tested against the frozen replay obligation set.

### CP6 pass conditions

1. all protected semantic replay obligations covered by the compression still pass;
2. causal tests that established the original capabilities are not silently removed from the replay set;
3. at least one precommitted complexity/system-cost measure strictly improves;
4. no displaced activation/verifier/memory cost invalidates the total-cost gate;
5. if claiming search acceleration, subsequent discovery cost improves under a separately protected test.

Recompression that merely hides complexity in routing, activation predicates, prompts, or verifier work is R12 Displacement, not compression.

---

## 9. Developmental-chain capstone

The strongest bounded experiment is a prospective chain:

`P0 -> O1 -> changed search -> P1 -> O2 -> changed search -> P2 -> O3`

Before execution, freeze:

- problem sequence or sampling mechanism;
- base model(s);
- verifier(s);
- information boundary;
- budgets;
- baseline/ablation arms;
- protected cases;
- stopping rules;
- primary discovery-cost metric;
- admission criteria;
- source-separation criteria;
- replay requirements.

The target operators `O1`, `O2`, `O3` must not be selected after inspecting protected outcomes merely to make the chain succeed.

A chain may stop at any failed gate. A partial pass retains its narrower result; it must not be narrated as having passed later stages.

---

## 10. Claims discipline

Allowed claims are bounded by the highest passed checkpoint.

- CP3: causal verified competence on protected real artifacts;
- CP4: source-distinct verified operator transfer;
- CP5: causal reduction in subsequent verified discovery cost;
- CP5-R: externally driven revision of retained developmental law/state;
- CP6: verified recompression, optionally with separately demonstrated downstream search benefit.

Forbidden without additional evidence:

- AGI;
- autonomous open-ended self-improvement;
- human-level general intelligence;
- global proof of understanding;
- unbounded recursive improvement;
- claims outside the tested verifier/domain/scope.

The preferred strongest bounded statement after CP5 is:

> Under a frozen bounded protocol, an unmodified base model embedded in a verifier-governed developmental controller constructed a capability absent from its admitted repertoire, retained it only after external verification, transferred it to source-distinct tasks, and the resulting verified developmental state causally reduced the cost of discovering a subsequent capability. Removing the relevant acquired state removed that advantage.

Use only the clauses whose gates actually passed.

---

## 11. Ledger immutability

Every run must append a new record. Scientific outcome fields are never rewritten after later experiments.

Corrections are permitted only for demonstrable metadata/infrastructure transcription mistakes and must retain an audit trail.

A repaired infrastructure run never replaces its invalid predecessor.

Negative results, rejected operators, counterexamples, nulls, and obstructions are first-class retained evidence.

---

## 12. Governing laws

1. **Verifier authority:** proposal mechanisms do not certify themselves.
2. **Evidence monotonicity:** observations are retained; beliefs may change.
3. **No semantic rescue:** protected outcomes cannot be used to retune the hypothesis under test.
4. **Infrastructure separation:** invalid apparatus yields no semantic conclusion.
5. **Causal admission:** useful correlation without intervention/ablation evidence is not operator admission.
6. **Transfer before generality:** acquisition success is narrower than source-distinct reuse.
7. **Development before self-improvement claims:** future-discovery cost must be measured, not inferred.
8. **Counter-ratchet:** counterexamples can narrow or withdraw permission to generalize.
9. **Compression with replay:** forgetting is allowed only after frozen obligations survive.
10. **Total cost:** complexity moved elsewhere is not a gain.

This constitution remains revisable as controller policy. Any revision must preserve prior evidence and receive a new version rather than silently altering V1.
