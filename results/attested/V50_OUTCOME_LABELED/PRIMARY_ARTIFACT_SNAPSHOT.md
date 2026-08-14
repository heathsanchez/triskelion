# OUTCOME_LABELED_V50 — Primary Artifact Snapshot
- Actions run: `31749833138`
- Head: `929461fe989592f40f2e15cb0105d81785281817`
- Artifact: `metalogic-v50-outcome-labeled`
- Artifact ZIP digest: `sha256:6a97a3e5978d03c5f495f01ca11c0620c822b12e13c963f7df31e01a7cdebddd`
> The JSON below is copied from the audited uploaded Actions artifact. This snapshot makes the repo ZIP self-contained; the artifact digest remains the provenance anchor.

## `COMMITMENT.json`
```json
{"labels_generated_by":"verifier transition sign HELP/HARM","protocol":"V50_OUTCOME_LABELED_SEALED_20260814","requests_forbidden_in_phase_a":true,"selected":[0,"t_05af66cb75d32b5a"],"selected_hash":"b6ae7c5d735971188174a1d12afca85a09289bbb22ec7c7c27abd3c72c2cfd12"}
```

## `PHASE_A.json`
```json
{"protocol":"V50_OUTCOME_LABELED_SEALED_20260814","phase":"A_OUTCOME_LABELED_CALIBRATION","episodes":[{"id":"e1","site":[293,35,37],"line":"if length is None or len(name) <= length:","before":false,"after":true,"sign":"HELP"},{"id":"e2","site":[58,25,27],"line":"if self.per_page <= self.orphans:","before":false,"after":true,"sign":"HELP"},{"id":"e3","site":[664,46,57],"line":"operator.le if self.min_open else operator.lt","before":true,"after":false,"sign":"HARM"},{"id":"e4","site":[133,25,26],"line":"while cursor < len(plain):","before":true,"after":false,"sign":"HARM"}],"help_count":2,"harm_count":2,"candidate_count":23,"survivor_count":1,"selected":[0,"t_05af66cb75d32b5a"],"posthoc_selected":[0,"if"],"commitment":{"protocol":"V50_OUTCOME_LABELED_SEALED_20260814","selected":[0,"t_05af66cb75d32b5a"],"selected_hash":"b6ae7c5d735971188174a1d12afca85a09289bbb22ec7c7c27abd3c72c2cfd12","labels_generated_by":"verifier transition sign HELP/HARM","requests_forbidden_in_phase_a":true},"gates":{"all_four_sites_resolved":true,"labels_not_supplied":true,"two_help_two_harm":true,"unique_relation_from_verifier_signs":true,"posthoc_relation_is_position0_if":true,"requests_unseen":true},"verdict":"PASS_V50_PHASE_A_OUTCOME_LABELED"}
```

The original artifact also contains the per-episode hashed feature arrays; they are omitted from this human-facing compact snapshot because they do not change the transition/gate record. The artifact digest above pins the complete uploaded bytes.

## `PHASE_B.json`
```json
{"protocol":"V50_OUTCOME_LABELED_SEALED_20260814","phase":"B_SEALED_TRANSFER_THEN_LATER_HARM","commitment_sha256":"be88adc967f3349da8b39e3177a93dfcd32dc74f641a1cb57aa557794afd19f5","selected":[0,"t_05af66cb75d32b5a"],"requests":{"causal_sites":[{"site":[626,44,46],"line":"if slice_length is None or slice_length <= 0:","before":true,"after":false}],"member":true,"cold":false,"warm":true,"ablated":false,"sign":"HELP"},"later_counterexample":{"causal_sites":[{"site":[115,25,26],"line":"if len(password) < self.min_length:","before":true,"after":false}],"member":true,"before":true,"after":false,"sign":"HARM"},"decision":"REVOKE","gates":{"frozen_commitment_exists":true,"requests_unique_site":true,"requests_matches_frozen_relation":true,"requests_verifier_sign_is_help":true,"requests_ablation_fails":true,"later_unique_site":true,"later_matches_same_relation":true,"later_verifier_sign_is_harm":true,"revokes":true},"verdict":"PASS_V50_OUTCOME_LABELED_SEALED_RATCHET","claim_boundary":"Calibration class labels are generated solely from executable HELP/HARM transitions under one widening transform; Requests is unseen until after category commitment; later contradiction is unseen until after transfer. Episode files/tests and widening mutation family remain supplied."}
```
