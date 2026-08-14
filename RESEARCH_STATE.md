# Triskelion / Metalogic Research State

_Last reconciled: 2026-08-14 NZST_

> **Evidence authority:** [`results/ATTESTATION_LEDGER.md`](results/ATTESTATION_LEDGER.md). This file is synthesis only. If wording here conflicts with the attestation ledger, the ledger wins.

## Current synthesis

Triskelion is testing a verified developmental capability system: externally checked experience can alter an explicit state of capabilities, laws, scopes, distinctions and constructors, and those changes may alter what becomes reachable or discoverable later.

A useful state is:

`A_t = (O_t, L_t, S_t, Π_t, K_t, D_t, V)`

where `O` are capabilities/operators, `L` scoped laws, `S` applicability/conflict/revision/lifecycle conditions, `Π` operational distinctions/quotients, `K` constructor machinery, `D` discovery policy/budget and `V` external verifier authority.

The governing loop is:

`seek/act -> external result -> residual -> closure test -> obstruction -> construction -> verification -> install/retain -> invoke -> revise/revoke -> changed future discoverability`

Neural proceduralization is downstream:

`explicit verified capability/state -> compiler Γ(model) -> optional neural realization`

The explicit representation is the intended source of truth; whether a given compiled realization preserves its scope must itself be verified.

## Strongest currently supported claims

### `TWO_GENERATION_COMPOUNDING_V54` — BOUNDED PASS

Branch `v54-compounding-ratchet`; run `31761530951`; head `2dd5f41b6c7cec1004b8deaee4f976dd2a9ed21c`.

Under the frozen one-new-generator protocol, the later target had zero cold one-rewrite survivors before O1. After lawful reuse of O1, O2 became discoverable; the final target required both. Supported bounded statement:

`O2 ∉ Discoverable(A0)` but `O2 ∈ Discoverable(A0 + O1)`.

This is the strongest current developmental result.

### `VERIFIER_MODEL_LAYER_V56C` — BOUNDED PASS

Branch `v56-close-gaps`; suite run `31766446740`.

On the frozen 12-case applicability task with Qwen2.5-Coder-0.5B:

- no memory: 6/12;
- raw memory: 6/12;
- verifier-controlled capability layer: 12/12.

Supported architectural statement:

`model proposes -> explicit capability/scope layer -> external verifier -> admit/block`.

### `VERIFIER_INDUCED_INVOCATION_IKKF_V4B` — BOUNDED PASS

Branch `ikkf-v4b-verifier-induced-invocation`; run `31763234925`.

External target/protected verification refined a coarse admitted scope to the unique valid invocation in the bounded test; ablation and later revocation passed.

### `VERIFIED_ROUTING_IKKF_V2D` — BOUNDED PASS

Branch `ikkf-v2d-verified-capability-os`; run `31763593583`.

On the exact V2c worlds and same C/J modules, verifier-controlled routing/execution reached 100%/100% where the learned selector reached 50% routing and 0% joint execution.

### `PORTABLE_CAPABILITY_IKKF_V1` — ATTESTED WITH CORRECTION

Primary result, harness and protocol have been audited directly. Fresh compilation, a second fresh compilation call, uninstall and reload are separately executed. Do not claim stochastic independence: C1/C2 loss curves are bit-identical and the `independent_recompile` gate does not test weight/config/hash independence.

### `ADAPTIVE_CONSOLIDATION_V18B` — ATTESTED

Primary artifact supports bounded protected consolidation and reload persistence on the measured skill set. This is not proof of arbitrary regression-free neural editing.

## V49–V51 operator lineage — real lineage, exact claims not yet attested

The previous state file overstated these as settled PASSes.

### `SEALED_TRANSFER_V49` — LINEAGE LOCATED / CONTENT AUDIT PENDING

Branch `v49-sealed-run`; run `31749423209`; head `8c5797db33db01c4af8448f399fbea37f251e79c`; artifact `metalogic-v49-sealed` with digest recorded in the attestation ledger.

A real primary lineage exists. The cold→warm→ablation→later-revocation sentence remains content-audit pending.

### `OUTCOME_LABELED_V50` — LINEAGE LOCATED / CONTENT AUDIT PENDING

V50 calibration/transfer scripts and CI lineage exist, but the exact result artifact and implemented HELP/HARM predicates have not yet been reconciled into the canonical ledger. Treat verifier-derived HELP/HARM as reported, not attested.

### `OPERATOR_INVENTION_V51` — LINEAGE LOCATED / CONTENT AUDIT PENDING

Branch `v51-operator-invention`; run `31759857216`; head `f739be68af3cd6695a1674225938961f3b69f7b2`; artifact `metalogic-v51-operator-invention` with digest recorded in the attestation ledger.

The `< -> <=` old-closure obstruction, construction, sealed transfer, ablation and later revocation story remains content-audit pending until that artifact and implemented gates are checked directly.

**Naming collision:** the files `results/V49_EXTERNAL_QUOTIENT_REFINEMENT_RESULT.*`, `results/V50_EXTERNAL_QUOTIENT_REFINEMENT_RESULT.txt`, and `results/V51_RESULT.txt` belong to the separate quotient-refinement sequence and must not be cited for the operator line.

## Natural / constructor frontier

### `HISTORICAL_COMPOUNDING_V55A` — INCOMPLETE

Only two usable frozen BugsInPy worlds survived, both Black, and neither produced a unique O1. Natural V54-shaped compounding was never reached.

### `CONSTRUCTOR_COMPOUNDING_V55B` — NEGATIVE under tested substrate

The frozen insert-by-token-type meta-substrate failed to synthesize K1 after the K0 obstruction was reached. This is a real negative for that substrate, not a falsification of operator-level compounding.

### `HISTORICAL_BLIND_EDIT_V56A` / `CONSTRUCTOR_RETRY_V56B` — HARNESS FAILURES

V56A crashed on stale/out-of-range edit coordinates; V56B crashed when malformed intermediate syntax raised `IndentationError`. Neither produced a scientific verdict.

### `MODEL_CARD_V55C` — MIXED / NEGATIVE

A prompt-level verified capability card did not control applicability: 5/12 and protected negatives failed. This motivates explicit execution-path verification rather than scope as prose.

## Neural / model line

The current reliable distinction is:

- explicit capability-to-neural compilation has bounded positive evidence (`PORTABLE_CAPABILITY_IKKF_V1`), with the independence correction above;
- protected consolidation has attested bounded evidence (`ADAPTIVE_CONSOLIDATION_V18B`);
- learned multi-capability applicability has strong negatives (IKKF V2b/V2c, IKKF V3);
- explicit verifier-controlled applicability has bounded positives (IKKF V2d/V4b, V56C).

Therefore the strongest present architecture is not “put everything into weights”; it is `model proposes -> explicit capability/scope authority -> verifier -> execute/block`, with compilation as an optional fast implementation whose scope must be reverified.

## Historical lines not yet reconciled to current Gate-3 standard

The following may have genuine positive evidence, but top-level docs must not present them as ATTESTED until the canonical ledger is completed:

- `SOURCE_DISTINCT_DISCOVERABILITY_V33_V34` — scripts exist, current branch/run/result pointer not canonicalized;
- `EXCEPTION_FLOW_EXTERNAL_STREAM` — repeatedly reported ffmpeg→SHAP causal reuse, but no canonical primary pointer located in the current ZIP yet;
- `META_CONSTRUCTOR_V36` — summary file present, run/predicate audit pending;
- `SCOPE_ONTOLOGY_V40_V43` — scripts and partial result summaries exist, each step still needs run/result reconciliation;
- `GRAMMAR_V70_V74` — result summary files exist; run-level provenance/predicate audit pending;
- older V15–V17 and V19–V23 — scripts/workflows exist, but present headline conclusions have not all been primary-artifact audited;
- portions of the V45–V68 quotient/refinement line — precommits/results exist, but canonical run/predicate reconciliation remains incomplete.

Use `results/ATTESTATION_LEDGER.md` for exact status and allowed wording.

## SorryDB / theorem frontier

`SORRYDB_V77` is a bounded negative at the current solver/budget: repaired exact-commit plumbing and official verification work, all three external repos prepare, and five frozen solver arms solve 0/3 selected tasks.

## Remaining capstone questions

1. **Natural development:** V54-shaped developmental compounding on pre-existing heterogeneous worlds with solutions sealed until termination.
2. **Constructor development:** establish `Constructible(K0) ⊊ Constructible(K1)` and ideally a K1→K2 lineage.
3. **Scale/economic value:** matched sequential comparison of base, episodic memory, ordinary adaptation and LOGOS on meaningful coding-agent workloads.

### Attestation is a precondition

Every Discover→Verify→Install→Invoke→Compile→Revise headline must be mechanically traceable to primary evidence. Before another capstone is promoted, finish the open attestation work listed in the canonical ledger.

## Current claim boundary

Current evidence supports bounded developmental compounding (V54), bounded explicit verifier-controlled model augmentation (V56C), bounded verifier-induced invocation/routing (IKKF V4b/V2d), attested bounded protected consolidation (V18b), and attested fresh capability compilation with an independence correction (IKKF V1).

Do **not** currently claim as settled: natural-world developmental compounding, unrestricted constructor invention, open-ended recursive self-improvement, universal/model-independent capability installation, stochastic independent recompilation, cheap reliable learned multi-capability routing, arbitrary neural scope preservation, or any historical headline that the attestation ledger marks `NEEDS ATTESTATION`.

## Canonical files

- `results/ATTESTATION_LEDGER.md` — authoritative evidence status and allowed sentences.
- `RESEARCH_STATE.md` — this synthesis.
- `results/CURRENT_FRONTIER_2026-08-14.md` — concise frontier summary.
- `results/BRANCH_RUN_INDEX_2026-08-14.md` — branch/run index, not a verdict source.
- `results/PROGRESS_V49_V56_2026-08-14.md` — chronology, subordinate to the attestation ledger.
