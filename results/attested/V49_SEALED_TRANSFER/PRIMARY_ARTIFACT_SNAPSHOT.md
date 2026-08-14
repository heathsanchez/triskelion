# SEALED_TRANSFER_V49 — Primary Artifact Snapshot
- Actions run: `31749682731`
- Head: `79799fba8961645bcd20ba6f94bcf34011a8b629`
- Artifact: `metalogic-v49-sealed`
- Artifact ZIP digest: `sha256:1079cae6f06085dc59bfa23cf548807d4219ecae811dd2d424dab5b9d3113a47`
> The JSON below is copied from the audited uploaded Actions artifact. This snapshot makes the repo ZIP self-contained; the artifact digest above remains the provenance anchor.

## `COMMITMENT.json`
```json
{"calibration_roles":["trigger","positive_class","protected_click","protected_rich"],"feature_language":"position-indexed identifier/number lexical tokens; comparator punctuation excluded by construction","forbidden_phase_a":["/tmp/v45_requests","src/requests","requests/utils.py"],"protocol":"V49_SEALED_TRANSFER_20260814","selected":[0,"t_2b8b1d6ecb767807"],"selected_hash":"9cb840a2aabe045c04481d56c66dcfb6f405c16fc790266ba2325a0ca1175c2b"}
```

## `PHASE_A.json`
```json
{"protocol":"V49_SEALED_TRANSFER_20260814","phase":"A_SEALED_CALIBRATION","mined":{"trigger":{"baseline":true,"candidate_count":1,"causal":[{"token_site":[293,35,37],"text":"if length is None or len(name) <= length:"}]},"positive_class":{"baseline":true,"candidate_count":2,"causal":[{"token_site":[58,25,27],"text":"if self.per_page <= self.orphans:"}]},"protected_click":{"baseline":true,"candidate_count":1,"causal":[{"token_site":[664,46,57],"text":"operator.le if self.min_open else operator.lt"}]},"protected_rich":{"baseline":true,"candidate_count":1,"causal":[{"token_site":[133,25,26],"text":"while cursor < len(plain):"}]}},"candidate_count":23,"survivor_count":1,"selected":[0,"t_2b8b1d6ecb767807"],"posthoc_selected":[0,"if"],"commitment":{"protocol":"V49_SEALED_TRANSFER_20260814","selected":[0,"t_2b8b1d6ecb767807"],"selected_hash":"9cb840a2aabe045c04481d56c66dcfb6f405c16fc790266ba2325a0ca1175c2b","calibration_roles":["trigger","positive_class","protected_click","protected_rich"],"forbidden_phase_a":["/tmp/v45_requests","src/requests","requests/utils.py"],"feature_language":"position-indexed identifier/number lexical tokens; comparator punctuation excluded by construction"},"gates":{"calibration_baselines_pass":true,"unique_behavioral_site_each_role":true,"unique_calibration_relation":true,"posthoc_relation_is_position0_if":true,"requests_absent_from_phase_a_code":true},"verdict":"PASS_V49_PHASE_A_SEALED_CALIBRATION"}
```

## `PHASE_B.json`
```json
{"protocol":"V49_SEALED_TRANSFER_20260814","phase":"B_WITHHELD_TRANSFER_THEN_COUNTEREVIDENCE","commitment_sha256":"9e9c8b64941a28ec08fefef125b5895406616052a22fcc590f2af289ae9dd601","selected":[0,"t_2b8b1d6ecb767807"],"transfer":{"baseline":true,"candidate_count":1,"attempts":[{"token_site":[626,44,46],"passes":false}],"causal":[{"token_site":[626,44,46],"text":"if slice_length is None or slice_length <= 0:"}]},"transfer_member":true,"transfer_causal":{"cold":false,"warm":true,"ablated":false},"counterexample":{"baseline":true,"candidate_count":3,"attempts":[{"token_site":[186,26,27],"passes":true},{"token_site":[115,25,26],"passes":false},{"token_site":[167,51,52],"passes":true}],"causal":[{"token_site":[115,25,26],"text":"if len(password) < self.min_length:"}]},"counterexample_hits_selected":true,"counter_base":true,"counter_after":false,"decision":"REVOKE","gates":{"phase_a_commitment_exists":true,"unique_requests_causal_site":true,"requests_matches_frozen_category":true,"cold_fails":true,"warm_passes":true,"ablation_restores_failure":true,"unique_later_counterexample_site":true,"counterexample_hits_frozen_category":true,"counterexample_falsifies_repair":true,"revokes":true},"verdict":"PASS_V49_TEMPORALLY_SEALED_TRANSFER_RATCHET","claim_boundary":"Category is committed before Requests is opened by phase B. Requests is not calibration evidence. Later Django contradiction is opened only after transfer evaluation. Repositories/tests, mutation family, tokenizer, calibration roles, and file choices remain supplied."}
```
