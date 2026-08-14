# Branch / Run Index — 2026-08-14

This file preserves branch/run pointers for scientifically relevant work. It is **not** the evidence authority. Scientific status and allowed wording live in [`ATTESTATION_LEDGER.md`](ATTESTATION_LEDGER.md).

| Canonical ID | Status | Branch | Workflow run / head | Current interpretation |
|---|---|---|---|---|
| `SEALED_TRANSFER_V49` | LINEAGE LOCATED / CONTENT AUDIT PENDING | `v49-sealed-run` | run `31749423209`, head `8c5797db33db01c4af8448f399fbea37f251e79c` | Artifact `metalogic-v49-sealed`, digest `sha256:1b466db0231ed3042842dfb93a4b2794a68e5332084292bd3a54c1eaa66ed3dc`. Exact scientific predicates still need content audit. |
| `OUTCOME_LABELED_V50` | LINEAGE LOCATED / CONTENT AUDIT PENDING | staged across sealed/operator lineage | completed CI lineage exists; exact result-artifact pointer still to be canonicalized | Do not call verifier-derived HELP/HARM attested yet. |
| `OPERATOR_INVENTION_V51` | LINEAGE LOCATED / CONTENT AUDIT PENDING | `v51-operator-invention` | run `31759857216`, head `f739be68af3cd6695a1674225938961f3b69f7b2` | Artifact `metalogic-v51-operator-invention`, digest `sha256:e3c10a4ba1011876e5df7248de4f3cb468e90195f6c331e625c3bb5d6c2f93d0`. `< -> <=` story remains content-audit pending. |
| `TWO_GENERATION_COMPOUNDING_V54` | BOUNDED PASS | `v54-compounding-ratchet` | run `31761530951`, head `2dd5f41b6c7cec1004b8deaee4f976dd2a9ed21c` | O2 not cold-discoverable under frozen budget, discoverable after O1; lineage ablation destroys final capability. |
| `HISTORICAL_COMPOUNDING_V55A` | INCOMPLETE | `v55-natural-historical-compounding` | run `31764969750`, head `5863f4d92bfbd535205e49fbe12b1f29fd463a4d` | Only two READY BugsInPy worlds, both Black; no unique O1; natural compounding not reached. |
| `CONSTRUCTOR_COMPOUNDING_V55B` | NEGATIVE under tested substrate | `v55-final-frontiers` | suite run `31764908603`, head `89ad8010dccbe55c8549c06098cbbedadd580ac5` | K0 obstruction reached; frozen insertion substrate failed to synthesize K1. |
| `MODEL_CARD_V55C` | MIXED / NEGATIVE | `v55-final-frontiers` | suite run `31764908603`, head `89ad8010dccbe55c8549c06098cbbedadd580ac5` | no memory 6/12, raw memory 5/12, verified card 5/12; protected negatives fail. |
| `HISTORICAL_BLIND_EDIT_V56A` | HARNESS FAILURE | `v56-close-gaps` | suite run `31766446740`, head `14757f481d5873332c72a279c3337aec17d323ab` | `IndexError`; no scientific verdict. |
| `CONSTRUCTOR_RETRY_V56B` | HARNESS FAILURE | `v56-close-gaps` | suite run `31766446740`, head `14757f481d5873332c72a279c3337aec17d323ab` | `IndentationError`; no scientific verdict. |
| `VERIFIER_MODEL_LAYER_V56C` | BOUNDED PASS | `v56-close-gaps` | suite run `31766446740`, head `14757f481d5873332c72a279c3337aec17d323ab` | Frozen 12-case task: 6/12 no-memory, 6/12 raw-memory, 12/12 verifier-controlled layer. Overall suite CI failed because V56A/B crashed. |
| `VERIFIER_INDUCED_INVOCATION_IKKF_V4B` | BOUNDED PASS | `ikkf-v4b-verifier-induced-invocation` | run `31763234925`, head `65be34273d2f717c57e5b4f919c9bad5d955d943` | Verifier refines coarse scope to unique valid invocation; ablation and later revocation pass. |
| `VERIFIED_ROUTING_IKKF_V2D` | BOUNDED PASS | `ikkf-v2d-verified-capability-os` | run `31763593583`, head `773a73db5a3d4e143c2c0eed658475a2bdfcfe1d` | Same C/J modules and worlds: verifier-controlled route/execution 100%/100% vs learned selector 50%/0% joint. |
| `PORTABLE_CAPABILITY_IKKF_V1` | ATTESTED WITH CORRECTION | `ikkf-v1-portable-capability` / related packaging branch | primary run `31759600559` | Fresh compile, second fresh compile call, uninstall and reload separately executed. Do not claim stochastic independence. |
| `ADAPTIVE_CONSOLIDATION_V18B` | ATTESTED | `main` | run `31740188434`, head `070dd7a14f288481c16c1cb33ca127a588da501f` | Primary RESULT supports bounded protected consolidation and reload persistence. |
| `IKKF_V3_SCOPE_BRIDGE` | NEGATIVE | `ikkf-v3-external-invented-instinct` | run `31761470384` | Frozen neural compiler fails to preserve applicability distinction. |
| `SORRYDB_V77` | NEGATIVE AT CURRENT SOLVER/BUDGET | `main` | repaired run `31761636184` | Plumbing/verifier/repo preparation pass; five arms solve 0/3. |
| `LOGOS_IKKF_DEMO` | DEMO / NOT SINGLE END-TO-END SCIENTIFIC RUN | `agent/logos-ikkf-demo` | draft PR #2 | Choreographed UI combining separate mechanisms; keep evidence boundary explicit. |

## Not yet indexed to run-level provenance

These are tracked in `ATTESTATION_LEDGER.md` and must not be promoted just because scripts/result summaries exist:

- `SOURCE_DISTINCT_DISCOVERABILITY_V33_V34`
- `EXCEPTION_FLOW_EXTERNAL_STREAM`
- `META_CONSTRUCTOR_V36`
- `SCOPE_ONTOLOGY_V40_V43`
- `GRAMMAR_V70_V74`
- older V15–V17 / V19–V23
- portions of `QUOTIENT_REFINEMENT_V45_V68`

## Naming collision warning

`V49`, `V50`, and `V51` are used by two unrelated experiment families. Result files named `V49_EXTERNAL_QUOTIENT_REFINEMENT_RESULT.*`, `V50_EXTERNAL_QUOTIENT_REFINEMENT_RESULT.txt`, and `V51_RESULT.txt` are **not** evidence for `SEALED_TRANSFER_V49`, `OUTCOME_LABELED_V50`, or `OPERATOR_INVENTION_V51`.

## Integrity rules

- GitHub Actions `conclusion=success` means workflow completion, not automatically scientific success.
- Overall suite `failure` does not automatically invalidate a subexperiment if another subexperiment crashed; use the primary result.
- A gate name cannot claim more than its predicate.
- Branch/run provenance is necessary but not sufficient for `ATTESTED`: artifact contents and implemented predicates must support the exact sentence.
