# V159 — Natural Longitudinal Development Capstone — PRECOMMIT

Status: **FROZEN BEFORE OUTCOME** once committed on the execution branch.

## Question

Can one verifier-governed developmental runtime process a pre-existing heterogeneous task stream and show that an externally verified earlier state change causally changes what becomes discoverable later, while retaining exact provenance, scope/revision state and restart equivalence?

This protocol tests the integrated system. It does not infer success from the V158 unit self-test or from any historical V-number.

## Fixed architecture

All arms use the same base model/provider, task order, external verifiers, source snapshots, attempt budget and structured action interface.

The developmental arm uses `developmental_runtime.DevelopmentalState` as the only retained authority. Raw model transcripts are not authoritative state.

State:

`A_t = (Omega_t, O_t, L_t, S_t, Pi_t, G_t, K_t, D_t, V)`

Every retained mutation must carry a `VERIFIED` `EvidenceRef`. Refuted/obstructed model proposals may be logged outside retained state but may not mutate `A_t`.

## Corpus

Use only pre-existing independently authored tasks whose target solutions are sealed from the model/controller until the arm terminates that task.

Primary stream source: frozen BugsInPy candidates already qualified by the current CP3 lineage, supplemented only if necessary by a second pre-existing repository family selected and frozen before source-body inspection.

No authored bridge task may count toward the primary developmental claim.

## Arms

1. `BASE` — same model, no retained cross-task memory.
2. `RAW` — same model with bounded raw episodic retrieval under the same total token/call budget.
3. `RAG` — retrieval over prior raw episodes under the same total budget.
4. `ADAPT` — ordinary allowed adaptation/fine-tuning mechanism, if available under the same information boundary; otherwise preregister as unavailable and do not substitute after outcomes.
5. `DEV` — unified verifier-governed developmental state.
6. `DEV_ANCESTOR_MINUS` — identical to DEV except the prospectively nominated causal ancestor is ablated before the downstream episode.

The primary causal comparison is `DEV` vs `DEV_ANCESTOR_MINUS`; the practical comparison is DEV against BASE/RAW/RAG/ADAPT.

## Per-episode controller

For each task and arm:

1. run closure/reuse against current allowed state;
2. attempt under the frozen budget;
3. obtain native external verifier result;
4. classify the residual using the frozen RGRS taxonomy;
5. if old closure is insufficient, propose the smallest distinction-changing representation/capability/constructor change;
6. run the smallest deciding test;
7. admit only if semantic + causal + resource + reproducibility gates pass;
8. persist exact event/state hashes;
9. continue to the next task without reopening prior outcomes.

Closure-before-invention is mandatory.

## Prospective developmental event

The first event eligible to become causal ancestor `A*` must satisfy all of:

- old frozen closure cannot reach the verified intervention under the fixed search budget;
- a new retained object is externally verified;
- causal ablation restores or materially worsens the acquisition failure;
- scope is executable, not prose-only;
- the object survives serialization/reload with identical state hash.

The identity of `A*` is fixed immediately when the first event satisfies these gates; it cannot be chosen retrospectively for downstream success.

## Downstream discoverability gate

A later task `T_j` supports developmental compounding only if, under the same frozen search protocol:

- the downstream verified object/solution is not discoverable in `DEV_ANCESTOR_MINUS`;
- it is discoverable in `DEV`;
- the difference is attributable to retained state available before `T_j`, not extra calls/tokens or protected information;
- an ancestor ablation shifts the downstream reachable frontier before the final answer is known.

Preferred strongest form:

`X_j notin Discoverable(A_{j-1} - A*)`

and

`X_j in Discoverable(A_{j-1})`.

Task success alone is insufficient; the reachable frontier must differ prospectively.

## Restart gate

At a precommitted midpoint, terminate the DEV process, serialize only the developmental-state package and required verifier references, start a fresh process, reload, and continue.

Required:

- exact pre/post reload state hash equality;
- exact closure/scope/revocation decisions on a frozen replay probe;
- no raw conversation replay needed for retained-state recovery.

## Revision / counterevidence gate

At least one later protected negative or contradictory case must exercise one of:

- scope refinement;
- explicit conflict;
- revocation;
- supersession.

If no natural counterevidence occurs in the frozen stream, this gate is reported `NOT_REACHED`; no authored negative may be inserted into the primary stream after outcomes.

## Metrics

Per arm and cumulatively:

- native verifier solves;
- calls and generated tokens;
- context/retrieval tokens;
- verifier calls;
- wall time and API cost when measurable;
- retained-state bytes;
- raw-history bytes/tokens;
- protected-negative / over-application failures;
- number of admitted/rejected/obstructed state changes;
- reachable-frontier size under the frozen bounded discovery procedure;
- causal descendants per retained ancestor.

Primary efficiency metric:

`verified downstream discoveries / total model+verifier cost`.

Primary developmental metric:

`count of downstream discoveries lost under prospectively fixed ancestor ablation`.

## Decision table

### PASS_NATURAL_LONGITUDINAL_DEVELOPMENT

Requires all:

- at least one prospectively fixed natural causal ancestor;
- at least one later source-distinct downstream discovery present in DEV and absent in DEV_ANCESTOR_MINUS under matched budget;
- native verifier acceptance of both acquisition and downstream result;
- exact restart gate pass;
- no protected information leak;
- no apparatus mismatch capable of explaining the separation.

### PRACTICAL_ADVANTAGE

Separately requires DEV to beat the strongest available non-developmental comparator on a precommitted cost/solve measure without extra verifier/model budget.

A scientific developmental PASS does not imply practical advantage, and practical advantage does not imply developmental compounding.

### NEGATIVE

Valid execution with the developmental gate reached but no qualifying downstream causal difference.

### OBSTRUCTED

The decisive gate is not reached because of corpus ceiling, constructor reachability, infrastructure, source-state synchronization, parser/adapter distortion, or another named residual. An obstructed run is not converted into a developmental negative.

## Forbidden interpretations

Even a PASS does not establish AGI, open-ended recursive self-improvement, unrestricted constructor invention, universal capability installation, or model-independent scaling.

Allowed strongest wording:

> Under a frozen sequential protocol on pre-existing independently authored tasks, externally verified retained state causally changed a later bounded discoverability frontier, survived restart, and did so under matched information and search budgets.
