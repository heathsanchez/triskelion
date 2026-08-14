# Triskelion / LOGOS Full-Stack Checklist

_Last reconciled: 2026-08-14 NZST_

This is the dependency-ordered completion list for a **full scientific + executable LOGOS stack**. Check an item only when its done-condition is satisfied by primary evidence. `results/ATTESTATION_LEDGER.md` remains the authority for scientific claims.

## Completion rule

The stack is complete only when one system can run the whole chain without substituting prose for mechanism:

`task -> verifier -> closure test -> obstruction -> construct/reuse capability -> scope/admit -> execute -> verify -> retain -> later causal reuse -> revise/revoke -> persist -> optional compile -> benchmark`

A historical experiment proving one link does not by itself check off an integrated-stack item.

## 0. Evidence and trust boundary

- [x] **Canonical attestation ledger.** Every headline family is classified as attested, bounded, result-only/no-CI, negative/incomplete, or not repo-attested.
- [x] **Primary evidence retained in repo for key audited claims.** V34 and V49-V51 audited payloads are vendored under `results/attested/`.
- [x] **External verifier is final authority.** Model/system proposals are not admitted solely because the model says they work.
- [x] **Negatives and harness failures are preserved rather than promoted.**

**Gate 0: COMPLETE.**

## 1. Unified explicit Capability OS

- [ ] **One executable state object implements** `A_t = (O_t, L_t, S_t, Pi_t, K_t, D_t, V)` rather than leaving these mechanisms across separate experiment scripts.
- [ ] **Closure-first API:** given target `T`, first test whether `T` is reachable by lawful composition of retained operators before proposing a new primitive.
- [ ] **Operator/Lawbook API:** install, compose, query and ablate operators with provenance and scoped laws.
- [ ] **Scope/lifecycle API:** admit, withhold, refine, revoke and supersede capabilities from verifier evidence.
- [ ] **Distinction/quotient API:** retain operational equivalence classes indexed by verifier/scope and refine them reversibly when evidence separates members.
- [ ] **Constructor API:** represent the machinery that can create new operators, not just the operators it has already created.
- [ ] **Discovery-policy API:** freeze/search budgets and record exactly what was discoverable from the current state.
- [ ] **Single append-only event/provenance log** sufficient to replay why every installed capability exists.

**Done condition:** a single local program can replay a multi-episode history and reconstruct the same capability state and decisions from primary evidence.

**Status: NOT YET COMPLETE AS ONE SYSTEM.** Many components have bounded experimental evidence, but they are not yet one runtime.

## 2. Natural developmental compounding

- [ ] Use **pre-existing heterogeneous external tasks/worlds** rather than authored toy generations.
- [ ] Freeze target selection, old language, search budget, constructor substrate and verifier before seeing protected solutions.
- [ ] Establish a first genuine obstruction `O1` that old closure cannot express.
- [ ] Verify and retain `O1`.
- [ ] On a later independent target, show `O2` is **not discoverable from `A0` under the frozen protocol**.
- [ ] Show `O2` **becomes discoverable from `A0 + O1`**.
- [ ] Show final capability requires the lineage with causal ablation.
- [ ] Replicate across more than one lineage/domain pair.

**Done condition:** a natural-world analogue of V54 passes with sealed solutions and independently authored heterogeneous tasks.

**Status: OPEN.** V54 is the bounded synthetic/protocol precedent; V55A did not reach this gate.

## 3. Constructor-language growth

- [ ] Demonstrate `Constructible(K0) subsetneq Constructible(K1)` on external tasks.
- [ ] Retain `K1` as reusable constructor machinery.
- [ ] Show acquiring `K1` changes what evidence/obstructions can be exposed later.
- [ ] Use that newly visible evidence to make a genuinely later `K2` constructible/discoverable.
- [ ] Causally ablate `K1` and show `K2` disappears from the discoverable set, not merely that the final solution fails.
- [ ] Remove dependence on a host semantic type lattice or hand-named constructor classes.
- [ ] Replicate on structurally different external targets.

**Done condition:** externally verified `K0 -> K1 -> K2` developmental constructor growth under a frozen meta-substrate whose own representational power is explicitly bounded.

**Status: OPEN.** V36/V37 reports a bounded precursor under Python's AST lattice; V55B is a negative for the tested insertion substrate.

## 4. Integrated applicability and revision

- [ ] Every installed capability carries executable applicability conditions, not only prose.
- [ ] New positive evidence can refine a coarse scope.
- [ ] Protected negative evidence can block over-application.
- [ ] Contradictory later evidence can refine or revoke the capability.
- [ ] Routing among multiple capabilities is verifier-controlled at execution time.
- [ ] Scope decisions survive serialization/reload.
- [ ] All decisions are causally auditable by removing the relevant capability/scope rule.

**Done condition:** the unified runtime passes positive transfer, protected-negative, multi-capability routing and later-revocation tests in one stateful sequence.

**Status: MECHANISMS PROVEN BOUNDED, INTEGRATION OPEN.** V49-V51, IKKF V4b/V2d and V56C support pieces.

## 5. Model adapter / verified execution layer

- [ ] Plug in an arbitrary supported LLM as **proposal engine**, with no model-specific change to the capability authority.
- [ ] Model proposes candidate action/composition/construction/invocation.
- [ ] Explicit Capability OS checks closure, scope and verifier conditions before execution/admission.
- [ ] Same interface works with at least two materially different base models.
- [ ] Raw-memory and no-memory modes can be switched on for controlled comparison.
- [ ] Context-window growth is bounded because retained work is represented as structured capability/law/scope objects rather than replayed raw transcripts.

**Done condition:** `model -> Capability OS -> verifier -> execute/block -> update state` works end-to-end on sequential tasks with interchangeable models.

**Status: PARTIAL.** V56C/IKKF support the architecture in bounded tests; general adapter/runtime remains to build.

## 6. Persistence and portable verified state

- [ ] Serialize operators, laws, scopes, quotients, constructors, provenance and verifier references into a versioned artifact.
- [ ] Unload the runtime completely and restore from the artifact.
- [ ] Re-run protected tests after reload.
- [ ] Reproduce the same closure/scope decisions after reload.
- [ ] Support append/update without replaying the entire raw interaction history.
- [ ] Define artifact versioning and migration rules.

**Done condition:** a capability-state package can move to a clean runtime and reproduce the verified behavior and audit trail.

**Status: PARTIAL.** IKKF V1 and V18b support bounded neural/package persistence, but the complete explicit `A_t` state package is not yet implemented.

## 7. Optional neural proceduralization

- [ ] Compile an explicit verified capability into model weights or another fast neural realization.
- [ ] Verify capability behavior after compilation.
- [ ] Verify **applicability/scope equivalence**, not merely task success.
- [ ] Protected negatives remain protected after compilation.
- [ ] Recompile after revision/revocation and verify the change.
- [ ] Fall back to explicit execution when compiled behavior fails equivalence.
- [ ] Measure whether compilation actually lowers latency/token cost enough to justify it.

**Done condition:** compilation is a verified optimization of the explicit capability state, never the source of truth.

**Status: PARTIAL / CRITICAL OPEN SCOPE GATE.** Capability compilation and consolidation have bounded positives; IKKF V3 shows neural applicability preservation can fail.

## 8. Single end-to-end developmental run

- [ ] Start from a frozen empty/minimal capability state.
- [ ] Process a long sequential stream of independently authored tasks.
- [ ] Include old-closure solves, genuine obstructions, new operator formation, later reuse, scope refinement, revocation and at least one constructor event.
- [ ] Do not skip boring negatives/no-op episodes.
- [ ] Save every verifier result, state transition and artifact.
- [ ] Demonstrate causal ablations for retained capabilities.
- [ ] Restart from persisted state mid-stream and continue identically.
- [ ] Run with solutions/protected tests sealed where required.

**Done condition:** one primary artifact demonstrates the actual full loop rather than assembling the story from separate experiments.

**Status: OPEN.** The current demo is choreographed from separately established mechanisms, not this experiment.

## 9. Matched benchmark against alternatives

- [ ] Freeze a meaningful sequential coding/reasoning benchmark with independent tasks.
- [ ] Compare at minimum: base/no-memory, raw episodic memory, retrieval/RAG memory, ordinary agent adaptation, and LOGOS Capability OS.
- [ ] Match model, task order, call/search budget and verifier access.
- [ ] Measure solved tasks / verifier pass rate.
- [ ] Measure protected-negative / over-application rate.
- [ ] Measure tokens/context consumed per task and cumulative context growth.
- [ ] Measure latency and compute/API cost.
- [ ] Measure later-task improvement attributable to retained capabilities with ablations.
- [ ] Report failures and confidence intervals/statistical tests where appropriate.

**Done condition:** LOGOS shows a practically meaningful advantage on at least one externally meaningful workload without receiving extra model/search budget.

**Status: OPEN.**

## 10. Scale and generality

- [ ] Run across multiple repositories/domains rather than one benchmark family.
- [ ] Demonstrate transfer across independently authored sources.
- [ ] Demonstrate useful accumulation over a long enough horizon that raw-context replay would be materially expensive.
- [ ] Show state growth is compressed/sublinear enough to remain operational.
- [ ] Stress conflict, stale capabilities, version changes and verifier drift.
- [ ] Replicate at least one result with a second model family.

**Done condition:** the advantage survives scale, heterogeneity and model substitution rather than depending on one curated micro-benchmark.

**Status: OPEN.**

## 11. Product/API surface

- [ ] Stable library/runtime API for `observe`, `closure`, `propose`, `verify`, `install`, `invoke`, `revise`, `revoke`, `persist`, `load`.
- [ ] CLI that can run a task stream and inspect the current Lawbook/Capability state.
- [ ] Machine-readable audit trace for every decision.
- [ ] MCP/API wrapper so existing agents can use the capability layer without changing their base model.
- [ ] Minimal UI/demo showing state growth, causal reuse and revocation from one real end-to-end run.
- [ ] Safe isolation/sandbox for executing generated code.
- [ ] Documentation with exact evidence boundaries.

**Done condition:** an external developer can place the layer between an agent and its execution environment and reproduce the reference demo.

**Status: PARTIAL.** A demo PR exists, but it is explicitly not yet one end-to-end scientific run.

## 12. Release-quality full stack

- [ ] Clean install from scratch.
- [ ] Deterministic/reproducible reference run where expected.
- [ ] CI for unit, integration, protected, replay and artifact-integrity tests.
- [ ] Versioned schema and backward-compatible state loading.
- [ ] Security/threat model for malicious tasks, poisoned verifier evidence and unsafe capability reuse.
- [ ] Public reference benchmark + primary evidence bundle.
- [ ] One canonical architecture document and one canonical evidence ledger.
- [ ] Tag a release only after Sections 1-11 required gates are complete or explicitly designated optional (neural proceduralization may remain optional if the explicit runtime wins without it).

**Done condition:** another team can install, reproduce, inspect and extend the system without relying on hidden chat history or unpublished artifacts.

**Status: OPEN.**

# Critical path from here

The shortest dependency path is:

1. **Build Section 1: unified Capability OS.**
2. **Run Section 2: natural developmental compounding through that OS.**
3. **Run Section 3: constructor `K0 -> K1 -> K2` growth through the same OS.**
4. **Integrate Sections 4-6: scope/revision + model adapter + persistence.**
5. **Run Section 8 as one sealed end-to-end developmental stream.**
6. **Run Sections 9-10: matched benchmark and scale/generalization.**
7. **Finish Sections 11-12: API/MCP/demo/release.**
8. **Section 7 neural compilation is an optimization track, not a prerequisite for proving the explicit full stack; promote it only after scope equivalence is verified.**

# Current stack scorecard

- Evidence/trust layer: **DONE**
- Individual operator/transfer/revision mechanisms: **DONE in bounded experiments**
- Source-distinct discoverability: **DONE in bounded experiment**
- Developmental compounding: **DONE only in bounded V54; natural version OPEN**
- Unified Capability OS: **OPEN**
- Natural heterogeneous development: **OPEN**
- Constructor-language growth: **OPEN**
- Integrated scope/routing/revision: **PARTIAL**
- Model adapter: **PARTIAL**
- Persistence of complete explicit state: **PARTIAL**
- Neural proceduralization with scope preservation: **PARTIAL / FAILING CURRENT HARD GATE**
- One end-to-end developmental run: **OPEN**
- Matched practical benchmark/economics: **OPEN**
- Product API/MCP: **PARTIAL**
- Release-quality reproducible stack: **OPEN**
