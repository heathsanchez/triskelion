# Residual-Guided Representation Search (RGRS)

## Purpose

Force the project to respond to failure by changing the problem representation only when the evidence justifies it, then admit the change only if a small causal test and an external verifier both support it.

RGRS is an operating protocol, not a novelty claim. Its job is to make developmental search disciplined across Lean, SAIR, Triskelion capability acquisition, Machine Insight, and future domains.

The invariant loop is:

`attempt -> residual -> hypothesis -> separator -> external verdict -> retained state`

The retained state may be a positive capability, a negative law, a scope restriction, or an unresolved obstruction.

---

## 1. Residual taxonomy

Every failed or suboptimal attempt terminates in exactly one primary residual class.

| Residual | Meaning | Typical signal | Default response |
|---|---|---|---|
| R1 — Search residual | Correct representation, insufficient search | Same representation contains plausible unseen solutions | Search harder/better |
| R2 — Cost residual | Correct result, too expensive | Passes semantics, misses CPU/RSS/time gate | Profile before changing representation |
| R3 — Redundancy residual | Repeated equivalent work | Duplicate normalization, reconstruction, fragmented cache keys | Quotient/canonicalize |
| R4 — Observability residual | Work cannot affect verified result | Eager computation on irrelevant arguments/branches | Make evaluation selective/lazy |
| R5 — Applicability residual | Capability only helps in a subset of contexts | Large win on one workload, loss/failure on another | Learn/certify activation predicate |
| R6 — Representation residual | Required distinction/object absent from current language | Failures survive search/tuning; alternate representation makes simple | Change ontology/IR |
| R7 — Composition residual | Needed result requires lawful combination of known mechanisms | Individual operators insufficient; composition closes gap | Compose before inventing |
| R8 — Access residual | Useful information exists but architecture prevents cheap access | Repeated scans/reconstruction of known structure | Add index/persistent structure |
| R9 — Soundness residual | Gain violates semantics | False accept/reject or dependency/environment invariant broken | Reject immediately |
| R10 — Infrastructure residual | Failure is not about hypothesis | timeout/build/runner/network failure | Repair experiment; no semantic conclusion |
| R11 — Boundary residual | Gain depends on arbitrary language/granularity boundary | “New” becomes old under slight reframing | Test alternate reasonable boundaries |
| R12 — Displacement residual | Complexity moved rather than reduced | Faster core but expensive activation/definition/bookkeeping | Measure total system cost |

Every residual record must have:

`rho = (class, location, evidence, scope, confidence)`

Forbidden labels include vague phrases such as “performance issue”, “didn’t work”, or “weird failure”.

A secondary residual may be recorded, but one primary class must govern the next action.

---

## 2. Representation-change decision rules

Do not change representation merely because an experiment lost.

### Rule A — repeated-residual

If the same residual survives at least two materially different interventions inside the current representation, a representation candidate becomes admissible for testing.

`A1 -> rho` and `A2 -> rho` implies `representation candidate allowed`.

### Rule B — conditional-regime

If two workloads prefer incompatible mechanisms, stop choosing a global winner. Search for a representation exposing the separator that governs applicability.

### Rule C — quotient

If distinctions are repeatedly computed but do not affect verification, collapse them.

If `x ~ y` and `V(x)=V(y)`, prefer work at `[x]` rather than separately at `x` and `y`.

Typical moves: interning, canonical environments, canonical DAG nodes, normal forms, equivalence classes.

### Rule D — non-observation

If a value cannot influence a verified observable, do not force it eagerly.

### Rule E — missing-object

If the current language cannot state the distinction required to explain the residual, add the smallest object that can.

Examples: global kernel -> stabilizer relation; operation -> latent relation; tree -> canonical DAG; unconditional optimization -> optimization + applicability predicate.

### Rule F — composition-before-invention

Before introducing a new primitive, test whether existing retained mechanisms compose to remove the residual.

### Rule G — total-cost

No gain may be admitted on local cost alone.

`C_total = C_construction + C_activation + C_verification + C_runtime + C_memory`.

### Rule H — boundary robustness

A claimed new capability/representation must remain nontrivial under at least one alternate reasonable granularity/boundary.

---

## 3. Smallest deciding test

Every representation proposal is reduced to one separator question:

> What is the smallest experiment whose outcomes distinguish the new representation hypothesis from the strongest old-representation explanation?

Required structure:

1. one representation/mechanism intervention;
2. at least two opposing discriminators;
3. frozen baseline, runner, compiler mode, corpus, and verifier;
4. causal ablation;
5. precommitted metric and decision table;
6. no target-specific rescue after seeing outcome.

The experiment must be cheap enough to fail early and strong enough that every outcome changes the next action.

---

## 4. Outcome interpretation

### P1 — clean mechanism win

New representation recovers or dominates the best prior regime across opposing discriminators.

Action: escalate to protected-suite and external-verifier gates.

### P2 — no effect

Intervention behaves like baseline.

Action: reject mechanism and retain negative law.

### P3 — partial conditional win

Helps some workloads and hurts others.

Action: classify primary residual R5 Applicability and search for the separator. Do not globally tune the intervention.

### P4 — fast but semantically invalid

Action: R9 Soundness; immediate rejection.

### P5 — faster locally, worse total cost

Action: R12 Displacement; reject unless displaced cost itself is causally eliminated.

### P6 — causal acquisition, protected regression

The intervention solves the acquisition discriminator and ablation restores failure, but protected behavior regresses.

Action: retain the causal fact but reject admission. Reclassify the remaining problem as an applicability/representation distinction and build a new separator. V128 -> V129 is the canonical example.

---

## 5. External-verifier admission gate

Nothing enters retained architecture because internal metrics look good.

Admission requires:

`G = G_semantic AND G_causal AND G_resource AND G_reproducible`.

### Semantic

Independent checker/corpus confirms no false accept/reject inside frozen scope.

### Causal

Ablation removes or materially weakens the gain.

### Resource

Predeclared metric improves. No metric switching after results.

### Reproducible

Same commit/config/corpus/runner procedure reproduces result.

State machine:

`PROPOSED -> SEPARATED -> VERIFIED -> ADMITTED`

or

`REJECTED / OBSTRUCTED`.

Rejected and obstructed results remain first-class knowledge.

---

## 6. Project operating loop

1. Run strongest current representation.
2. Extract and classify residual.
3. Decide whether residual is search-level or representation-level.
4. Generate the smallest distinction-changing representation.
5. State its predicted separator.
6. Freeze the smallest deciding test.
7. Run baseline + intervention + ablation.
8. Send outcome through independent verifier/protected corpus.
9. Admit, reject, or refine applicability.
10. Write result into Lawbook / Obstruction Atlas / ledger.

Governing rule:

> Never search harder inside a representation after the residual says the missing information lives outside it.

Companion rule:

> Never admit a representation merely because it fixes the acquisition case; protected counterevidence outranks acquisition success.

---

## 7. Mandatory experiment record

Every RGRS experiment gets one immutable ledger row containing:

- experiment id;
- date;
- domain/repo/commit;
- baseline representation;
- intervention;
- ablation;
- primary residual before test;
- separator question;
- opposing discriminators;
- frozen semantic verifier;
- frozen resource metric;
- result;
- post-result residual;
- verdict;
- retained law/capability;
- evidence level: exploratory / precommitted / hosted / externally verified;
- artifact/run identifiers.

The ledger is append-only except for correcting infrastructure metadata. Scientific outcome fields are never rewritten after later experiments.

---

## 8. Lean-specific current map

Current working progression:

`evaluation-regime residual -> observability/applicability -> canonical identity/DAG -> identity-level reuse -> Arena gate`.

The key discipline is that canonical-DAG work is not automatically justified by a cache miss or a slow workload. It is justified only where evidence shows repeated equivalent reconstruction or identity fragmentation (R3/R8), after separating those from eager evaluation (R4) and workload-specific applicability (R5).

A canonical DAG candidate should therefore answer a concrete separator question: whether making semantically equivalent proof/environment structures share stable identity removes repeated reconstruction/normalization **without** merely shifting cost into interning, canonicalization, activation, memory, or GC.

That is an R3/R8 hypothesis with explicit R12 and R9 rejection gates.
