# Branch / Run Index — 2026-08-14 16:15 NZST

This file exists so a download of `main` preserves pointers to scientifically relevant work that has not yet been merged into `main`. It is an index, not a substitute for primary artifacts.

| Line | Status | Branch | Workflow run / head | Current interpretation |
|---|---|---|---|---|
| V54 two-generation compounding | BOUNDED PASS | `v54-compounding-ratchet` | run `31761530951`, head `2dd5f41b6c7cec1004b8deaee4f976dd2a9ed21c` | O1 outside old closure; O2 not cold-discoverable but discoverable after O1; O1 ablation destroys final capability. |
| V55A natural historical compounding | INCOMPLETE | `v55-natural-historical-compounding` | run `31764969750`, head `5863f4d92bfbd535205e49fbe12b1f29fd463a4d` | Only two READY BugsInPy worlds, both Black; no unique O1; natural compounding not reached. |
| V55B constructor-level compounding | NEGATIVE under tested substrate | `v55-final-frontiers` | suite run `31764908603`, head `89ad8010dccbe55c8549c06098cbbedadd580ac5` | K0 obstruction established; frozen insertion meta-substrate failed to synthesize K1, so no K2 lineage. |
| V55C naive model-layer capability card | MIXED / NEGATIVE | `v55-final-frontiers` | suite run `31764908603`, head `89ad8010dccbe55c8549c06098cbbedadd580ac5` | Qwen2.5-Coder-0.5B: no memory 6/12, raw memory 5/12, verified card 5/12; card over-applies and fails protected negatives. |
| V56A historical blind-edit retry | HARNESS FAILURE | `v56-close-gaps` | suite run `31766446740`, head `14757f481d5873332c72a279c3337aec17d323ab` | `IndexError` from stale/out-of-range edit coordinates; no scientific verdict. |
| V56B constructor retry | HARNESS FAILURE | `v56-close-gaps` | suite run `31766446740`, head `14757f481d5873332c72a279c3337aec17d323ab` | malformed intermediate insertion raised `IndentationError`; no scientific verdict. |
| V56C verifier-controlled model layer | BOUNDED PASS | `v56-close-gaps` | suite run `31766446740`, head `14757f481d5873332c72a279c3337aec17d323ab` | Same bounded 12-case task: no memory 6/12, raw memory 6/12, verifier-controlled capability layer 12/12. Overall suite CI failed because V56A/B crashed; V56C status comes from the result ledger. |
| IKKF V4b verifier-induced invocation | BOUNDED PASS | `ikkf-v4b-verifier-induced-invocation` | run `31763234925`, head `65be34273d2f717c57e5b4f919c9bad5d955d943` | External verification refines a coarse scope to the unique valid invocation; ablation and later revocation pass. |
| IKKF V2d Verified Capability OS | BOUNDED PASS | `ikkf-v2d-verified-capability-os` | run `31763593583`, head `773a73db5a3d4e143c2c0eed658475a2bdfcfe1d` | Same C/J modules and V2c worlds; verifier-controlled invocation reaches 100% route + execution vs V2c learned router 50% route / 0% joint execution. |
| IKKF V1 portable capability | ATTESTED WITH CORRECTION | `ikkf-v1-portable-capability` / related PR branch `agent/ikkf-portable-capability-v1` | primary run `31759600559`; draft PR #1 contains related capstone packaging | Fresh compilation, second fresh compilation call, uninstall and reload are separately executed. Do not call C1/C2 stochastically independent: loss curves are bit-identical and the gate does not test weight/hash independence. |
| V18b adaptive consolidation | ATTESTED | `main` | run `31740188434`, head `070dd7a14f288481c16c1cb33ca127a588da501f` | Primary RESULT attests bounded protected consolidation and reload persistence on the measured skill set. |
| IKKF V3 external invented instinct | NEGATIVE | `ikkf-v3-external-invented-instinct` | run `31761470384` | Explicit V51 path passes; frozen neural compiler fails scope preservation. Preserve unchanged. |
| V77 SorryDB preflight | NEGATIVE AT CURRENT SOLVER/BUDGET | `main` | repaired run `31761636184` | Exact-commit plumbing/official verifier pass; all three repos prepare; five solver arms solve 0/3 tasks. |
| LOGOS “I Know Kung Fu” demo | DEMO / NOT SINGLE END-TO-END SCIENTIFIC RUN | `agent/logos-ikkf-demo` | draft PR #2 | Choreographed UI combining separately established mechanisms. Keep evidence boundary explicit until wired to one live runtime. |

## Experimental-integrity notes

- GitHub Actions `conclusion=success` means the workflow completed, not automatically that the scientific hypothesis passed; likewise an overall suite `failure` can coexist with a valid positive subexperiment if another subexperiment crashes.
- Branch-only result claims should be audited against uploaded primary artifacts before being upgraded to `ATTESTED`.
- IKKF V1 is the current precedent for gate-name auditing: `independent_recompile` is stronger language than its implemented predicate.
- V2f's first explicit-law evaluator may consult both candidates before claiming selected-only execution; do not promote that version without a hardened select-before-consult rerun.
- V2e tests verifier-certified invocation distillation; treat its status from the primary artifact only, not from a workflow name or prose summary.
