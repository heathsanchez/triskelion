# Triskelion

Private experimental harness for Metalogic / LOGOS verified-learning research.

The project tests whether externally verified experience can change an explicit capability system: compose what already exists, construct capability when old closure is insufficient, learn applicability, revise/revoke under counterevidence, change future discoverability, and optionally compile verified competence into neural form.

## Evidence policy

**The canonical authority is [`results/ATTESTATION_LEDGER.md`](results/ATTESTATION_LEDGER.md).** A prose summary, successful CI job, V-number, or result filename is not sufficient by itself. Headline claims are classified as `ATTESTED`, `BOUNDED PASS`, `LINEAGE LOCATED / CONTENT AUDIT PENDING`, `RESULT FILE PRESENT / RUN AUDIT PENDING`, `REPORTED / NEEDS ATTESTATION`, `NEGATIVE`, or `INCOMPLETE/HARNESS`.

Bare V-numbers are not unique identifiers. In particular V49/V50/V51 are used by both the sealed-transfer/operator-invention line and an unrelated quotient-refinement sequence. Use descriptive canonical IDs such as `OPERATOR_INVENTION_V51`.

## Current strongest evidence — 2026-08-14

**`TWO_GENERATION_COMPOUNDING_V54` — BOUNDED PASS.** Branch `v54-compounding-ratchet`, run `31761530951`: under the frozen one-new-generator budget O2 had zero cold survivors before O1, became discoverable after O1, and the final target required both. This supports the bounded causal statement `O2 ∉ Discoverable(A0)` but `O2 ∈ Discoverable(A0 + O1)`.

**`VERIFIER_MODEL_LAYER_V56C` — BOUNDED PASS.** On the frozen 12-case small-Qwen applicability task: no-memory 6/12, raw-memory 6/12, structurally verifier-controlled capability layer 12/12. The supported architectural statement is `model proposes -> explicit capability/scope layer -> external verifier -> admit/block`.

**`VERIFIER_INDUCED_INVOCATION_IKKF_V4B` and `VERIFIED_ROUTING_IKKF_V2D` — BOUNDED PASS.** External verification can refine applicability in the bounded V4b setting; on the exact V2c C/J worlds/modules, verifier-controlled routing/execution reached 100%/100% where the learned selector reached 50% routing and 0% joint execution.

**`PORTABLE_CAPABILITY_IKKF_V1` — ATTESTED WITH CORRECTION.** Fresh compilation, a second fresh compilation call, uninstall and reload are separately executed. Do not claim stochastic independence: C1/C2 training trajectories are bit-identical and the implemented `independent_recompile` predicate does not test independence.

**`ADAPTIVE_CONSOLIDATION_V18B` — ATTESTED.** Primary artifact supports bounded protected consolidation and reload persistence on the measured skill set; it does not prove arbitrary regression-free neural editing.

## V49–V51 operator line: provenance repaired, content audit still pending

The earlier README overstated these as settled PASSes. The underlying lineages are real, but the exact headline predicates have not yet been audited to the same standard as IKKF V1/V18b.

- **`SEALED_TRANSFER_V49` — LINEAGE LOCATED / CONTENT AUDIT PENDING.** Branch `v49-sealed-run`; run `31749423209`; artifact `metalogic-v49-sealed`, digest recorded in the attestation ledger.
- **`OUTCOME_LABELED_V50` — LINEAGE LOCATED / CONTENT AUDIT PENDING.** Executable V50 calibration/transfer code and CI lineage exist; exact result-artifact/predicate audit remains open.
- **`OPERATOR_INVENTION_V51` — LINEAGE LOCATED / CONTENT AUDIT PENDING.** Branch `v51-operator-invention`; run `31759857216`; artifact `metalogic-v51-operator-invention`, digest recorded in the ledger. The `< -> <=` obstruction/construction/transfer/ablation/revocation story must not be called ATTESTED until artifact contents and gates are checked directly.

The `results/V49_EXTERNAL_QUOTIENT_REFINEMENT_RESULT.*`, `V50...`, and `V51_RESULT.txt` files belong to a **different quotient-refinement experiment family** and must not be cited for the operator line.

## Natural / constructor frontier

**`HISTORICAL_COMPOUNDING_V55A` — INCOMPLETE.** Only two usable frozen BugsInPy worlds survived, both Black; neither yielded a unique O1. Natural compounding was never reached.

**`CONSTRUCTOR_COMPOUNDING_V55B` — NEGATIVE under the tested meta-substrate.** K0 could not repair the deletion obstruction and the frozen insertion meta-substrate failed to synthesize K1.

**`HISTORICAL_BLIND_EDIT_V56A` and `CONSTRUCTOR_RETRY_V56B` — HARNESS FAILURES.** They crashed before scientific verdicts and do not supersede V55A/V55B.

**`MODEL_CARD_V55C` — MIXED/NEGATIVE.** Describing verified scope in prompt text did not control applicability: 5/12 and protected negatives failed.

**`SORRYDB_V77` — NEGATIVE at current solver/budget.** Exact-commit plumbing, official verifier and repository preparation work; five frozen solver arms solve 0/3 selected tasks.

## Historical claims awaiting full reconciliation

The following are intentionally not promoted beyond their present evidence state until branch/run/artifact/predicate reconciliation is completed in the canonical ledger:

- source-distinct V33/V34 discoverability;
- ffmpeg→SHAP `EXCEPTION_FLOW` external stream;
- V36 meta-constructor claim;
- parts of V40–V43 scope/ontology progression;
- V70–V74 grammar/motif sequence (result files exist, run-level audit pending);
- older V15–V17 and V19–V23 conclusions (scripts/workflows exist, current attestation audit incomplete);
- portions of V45–V68 quotient/refinement sequence (result/precommit files exist; run/predicate audit still being canonicalized).

See the attestation ledger for exact allowed wording.

## Current thesis

A useful research state is

`A_t = (O_t, L_t, S_t, Π_t, K_t, D_t, V)`

where `O` are capabilities, `L` scoped laws, `S` applicability/revision/lifecycle conditions, `Π` operational distinctions/quotients, `K` constructor machinery, `D` discovery policy and `V` external authority. Neural realizations are downstream implementations rather than automatically authoritative state.

The strongest current bounded developmental result is V54-shaped compounding: verified capability structure can change which later capability is discoverable under a frozen search protocol.

## Remaining capstone gates

1. **Natural development:** reproduce V54-shaped compounding on pre-existing heterogeneous worlds with solutions sealed.
2. **Constructor development:** establish `Constructible(K0) ⊊ Constructible(K1)` and ideally a K1→K2 lineage.
3. **Scale/economic value:** compare base, memory, ordinary adaptation and LOGOS under matched sequential budgets on meaningful coding workloads.

**Attestation is a precondition for all three counting.**

## Canonical navigation

- [`results/ATTESTATION_LEDGER.md`](results/ATTESTATION_LEDGER.md) — **authoritative claim/evidence ledger**.
- [`RESEARCH_STATE.md`](RESEARCH_STATE.md) — current synthesis and open questions; must defer to the ledger.
- [`results/CURRENT_FRONTIER_2026-08-14.md`](results/CURRENT_FRONTIER_2026-08-14.md) — concise frontier summary; must defer to the ledger.
- [`results/BRANCH_RUN_INDEX_2026-08-14.md`](results/BRANCH_RUN_INDEX_2026-08-14.md) — branch/run pointers, not a scientific verdict source.
- [`results/PROGRESS_V49_V56_2026-08-14.md`](results/PROGRESS_V49_V56_2026-08-14.md) — chronology, subordinate to the ledger.
- `results/`, `protocols/`, `experiments/`, `.github/workflows/` — primary/reproducibility material.

## Research discipline

Closure first. Preserve negatives. Do not infer scientific success from CI success or scientific failure from harness failure. A gate name cannot claim more than its implemented predicate. If the canonical ledger says `NEEDS ATTESTATION`, all downstream prose must say so too.
