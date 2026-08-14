# Canonical Attestation Ledger

_Last reconciled: 2026-08-14 NZST_

This file is the authoritative evidence index for headline Triskelion / LOGOS claims. Top-level prose must not claim more than this ledger supports.

## Evidence classes

- **ATTESTED** — primary result artifact plus harness/protocol inspected; implemented predicate supports the exact sentence.
- **ATTESTED WITH QUALIFICATION** — core behavioral predicate is supported, but an adjacent property (for example sealing or independence) is established structurally or remains weaker than the gate name suggests.
- **BOUNDED PASS** — frozen run/result located and scientific verdict supports the bounded claim; full predicate-level audit may still be pending.
- **LINEAGE LOCATED / CONTENT AUDIT PENDING** — branch/run/artifact exists, but artifact contents and implemented gates have not yet been checked against the prose claim.
- **RESULT FILE PRESENT / RUN AUDIT PENDING** — result exists in `main`, but branch/run/artifact provenance has not yet been reconciled.
- **REPORTED / NEEDS ATTESTATION** — currently supported by prose and/or scripts only; do not cite as settled.
- **NEGATIVE** — scientific gate was reached and failed.
- **INCOMPLETE / HARNESS / INFRASTRUCTURE** — mechanism was not actually tested to a scientific verdict.

## Naming collision rule

Bare V-numbers are not unique identifiers. In particular, `V49`, `V50`, and `V51` refer to two different experiment families:

- `SEALED_TRANSFER_V49`, `OUTCOME_LABELED_V50`, `OPERATOR_INVENTION_V51`
- `QUOTIENT_REFINEMENT_V49`, `QUOTIENT_REFINEMENT_V50`, `QUOTIENT_REFINEMENT_V51`

All new docs should use the descriptive slug plus V-number.

## Highest-value current claims

| Canonical ID | Current status | Primary evidence currently located | Exact claim allowed now |
|---|---|---|---|
| `TWO_GENERATION_COMPOUNDING_V54` | **BOUNDED PASS** | branch `v54-compounding-ratchet`; run `31761530951`; head `2dd5f41b6c7cec1004b8deaee4f976dd2a9ed21c` | Under the frozen one-new-generator protocol, O2 had zero cold survivors before O1, became discoverable after O1, and final capability required both. |
| `VERIFIER_MODEL_LAYER_V56C` | **BOUNDED PASS** | branch `v56-close-gaps`; suite run `31766446740`; head `14757f481d5873332c72a279c3337aec17d323ab` | On the frozen 12-case task, explicit verifier-controlled applicability scored 12/12 vs 6/12 no-memory and 6/12 raw-memory. |
| `VERIFIER_INDUCED_INVOCATION_IKKF_V4B` | **BOUNDED PASS** | branch `ikkf-v4b-verifier-induced-invocation`; run `31763234925`; head `65be34273d2f717c57e5b4f919c9bad5d955d943` | External verification can refine a coarse admitted scope to the unique valid invocation in this bounded setting; ablation and later revocation pass. |
| `VERIFIED_ROUTING_IKKF_V2D` | **BOUNDED PASS** | branch `ikkf-v2d-verified-capability-os`; run `31763593583`; head `773a73db5a3d4e143c2c0eed658475a2bdfcfe1d` | On the exact V2c worlds/modules, verifier-controlled invocation reached 100% routing/execution vs learned selector 50%/0% joint execution. |
| `PORTABLE_CAPABILITY_IKKF_V1` | **ATTESTED WITH CORRECTION** | primary run `31759600559`; primary result/harness/protocol audited | Fresh capability compilation, second fresh compilation call, uninstall and reload are separately executed. Do **not** claim stochastic independence: C1/C2 curves are bit-identical and the `independent_recompile` predicate does not test independence. |
| `ADAPTIVE_CONSOLIDATION_V18B` | **ATTESTED** | main; run `31740188434`; head `070dd7a14f288481c16c1cb33ca127a588da501f`; primary RESULT audited | Bounded protected consolidation preserves the measured ancestors/composites and reload persistence. |
| `SORRYDB_V77` | **NEGATIVE AT CURRENT SOLVER/BUDGET** | main; repaired run `31761636184` | Exact-commit plumbing/official verifier/repo preparation work; five frozen solver arms solve 0/3 selected tasks. |

## Reconciled V49–V51 operator line

| Canonical ID | Current status | Located lineage | Allowed wording now |
|---|---|---|---|
| `SEALED_TRANSFER_V49` | **ATTESTED WITH SEALING QUALIFICATION** | branch `v49-sealed-run`; run `31749423209`; head `8c5797db33db01c4af8448f399fbea37f251e79c`; artifact `metalogic-v49-sealed`, digest `sha256:1b466db0231ed3042842dfb93a4b2794a68e5332084292bd3a54c1eaa66ed3dc`; `PHASE_A.json`, `COMMITMENT.json`, `PHASE_B.json` audited with calibration/transfer harnesses | The artifact records a unique learned lexical category, Requests cold FAIL → warm PASS → ablation FAIL, a unique later Django counterexample inside the category, and `REVOKE`. The transfer/counterexample predicates are implemented from executable tests. Temporal sealing is supported by the two-phase workflow/script structure, but the script field `requests_absent_from_phase_a_code` is hard-coded `True` rather than dynamically checked, so do not cite that boolean itself as the sealing proof. |
| `OUTCOME_LABELED_V50` | **LINEAGE LOCATED / CONTENT AUDIT PENDING** | V50 code/workflow staged on the sealed/operator lineage; completed CI lineage located, but exact V50 result artifact/predicate audit still pending | Verifier-derived HELP/HARM is a reported result with executable lineage, not yet attested. |
| `OPERATOR_INVENTION_V51` | **ATTESTED WITH SEALING QUALIFICATION** | branch `v51-operator-invention`; run `31759857216`; head `f739be68af3cd6695a1674225938961f3b69f7b2`; artifact `metalogic-v51-operator-invention`, digest `sha256:e3c10a4ba1011876e5df7248de4f3cb468e90195f6c331e625c3bb5d6c2f93d0`; `PHASE_A.json`, `COMMITMENT.json`, `PHASE_B.json`, workflow log and both harnesses audited | Under the supplied generic token-emission substrate, two executable obstructions had a unique common repair token `<=`; the frozen old token-position generators preserve token-value multisets, so `< -> <=` is outside that old closure. The committed operator then gives sealed Requests cold FAIL → warm PASS → ablation FAIL, and a later Django harm yields no surviving refined scope so the decision is `REVOKE`. The claim is **not** invention outside all meta-languages. Temporal sealing is supported by workflow order and phase-separated code, while `requests_forbidden_phase_a` / `requests_was_sealed_until_phase_b` are hard-coded fields rather than self-verifying predicates. |

## Natural / constructor frontier

| Canonical ID | Status | Evidence |
|---|---|---|
| `HISTORICAL_COMPOUNDING_V55A` | **INCOMPLETE** | branch `v55-natural-historical-compounding`; run `31764969750`; only two READY worlds, both Black; no unique O1. |
| `CONSTRUCTOR_COMPOUNDING_V55B` | **NEGATIVE under tested substrate** | branch `v55-final-frontiers`; suite run `31764908603`; K0 obstruction reached, insertion meta-substrate failed to synthesize K1. |
| `MODEL_CARD_V55C` | **MIXED / NEGATIVE** | same V55 suite; 6/12 no-memory, 5/12 raw-memory, 5/12 verified-card; protected negatives fail. |
| `HISTORICAL_BLIND_EDIT_V56A` | **HARNESS FAILURE** | branch `v56-close-gaps`; suite run `31766446740`; stale/out-of-range edit coordinates caused `IndexError`. |
| `CONSTRUCTOR_RETRY_V56B` | **HARNESS FAILURE** | same suite; malformed insertion caused `IndentationError`; no scientific verdict. |

## Historical claims that remain unaudited to the current standard

These claims may be real and many have scripts/workflows/result summaries, but they should not be called ATTESTED until their primary evidence is reconciled.

| Claim family | Current evidence state | Required action |
|---|---|---|
| `SOURCE_DISTINCT_DISCOVERABILITY_V33_V34` | scripts on `main`; no indexed branch/run/result currently tied to headline | Locate Actions run/artifact or downgrade to `REPORTED / NEEDS ATTESTATION`. |
| `EXCEPTION_FLOW_EXTERNAL_STREAM` | repeatedly reported in synthesis; no canonical result/run pointer in current ZIP | Locate the ffmpeg→SHAP primary artifact or retain as `REPORTED / NEEDS ATTESTATION`. |
| `META_CONSTRUCTOR_V36` | `results/V36_V37_META_CONSTRUCTOR.txt` summary present | Locate run/artifact and audit the constructor-discoverability predicates. |
| `SCOPE_ONTOLOGY_V40_V43` | scripts and partial summaries/results present | Reconcile each headline step V40/V41/V42/V43 to run/result; do not compress the chain into one settled claim until done. |
| `GRAMMAR_V70_V72` | quantitative result summary files present | Mark `RESULT FILE PRESENT / RUN AUDIT PENDING` until workflow provenance and predicates are reconciled. |
| `GRAMMAR_NEGATIVE_V73`, `MATH_TRANSFER_V74` | result files present | Same: result present, run provenance not yet canonicalized. |
| `COMPOSITION_V15_V17`, `OPERATORS_V19_V23` | scripts/workflows present; V18b separately attested | Historical conclusions remain `REPORTED / NEEDS ATTESTATION` until result/run audit. |
| `QUOTIENT_REFINEMENT_V45_V68` | many result files + precommits on `main`; V68 result file present | Stronger than prose-only, but run-level provenance/predicate audit still needed before `ATTESTED`. |

## Result-file namespaces that must not be confused

The following files on `main` belong to the **external quotient-refinement** sequence, not the sealed-transfer/operator-invention sequence:

- `results/V49_EXTERNAL_QUOTIENT_REFINEMENT_RESULT.md`
- `results/V50_EXTERNAL_QUOTIENT_REFINEMENT_RESULT.txt`
- `results/V51_RESULT.txt`

Those filenames must never be cited as primary evidence for `SEALED_TRANSFER_V49`, `OUTCOME_LABELED_V50`, or `OPERATOR_INVENTION_V51`.

## Citation policy

A headline is allowed in README/paper/demo only if this ledger supplies one of:

1. **ATTESTED / ATTESTED WITH QUALIFICATION** exact sentence;
2. **BOUNDED PASS** with explicit bounded wording and branch/run pointer;
3. **NEGATIVE/INCOMPLETE** with exact failure boundary.

Anything else must carry `REPORTED / NEEDS ATTESTATION`, `LINEAGE LOCATED / CONTENT AUDIT PENDING`, or `RESULT FILE PRESENT / RUN AUDIT PENDING` in the same paragraph.

## Next evidence work, before new capstones

1. Locate and audit the exact `OUTCOME_LABELED_V50` result artifact and its HELP/HARM predicates.
2. Locate primary run/artifact for `SOURCE_DISTINCT_DISCOVERABILITY_V33_V34` and `EXCEPTION_FLOW_EXTERNAL_STREAM`.
3. Reconcile V36, V40–V43, V70–V74, V15–V23, and V45–V68 into this ledger.
4. Only after those are classified should top-level docs promote any of them beyond the current evidence class.

The purpose of this ledger is to make evidence boring: one claim, one canonical ID, one evidence chain, one exact allowed sentence.