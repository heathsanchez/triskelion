# OPERATOR_INVENTION_V51 — Primary Artifact Snapshot
- Actions run: `31759857216`
- Head: `f739be68af3cd6695a1674225938961f3b69f7b2`
- Artifact: `metalogic-v51-operator-invention`
- Artifact ZIP digest: `sha256:e3c10a4ba1011876e5df7248de4f3cb468e90195f6c331e625c3bb5d6c2f93d0`
> The JSON below is copied from the audited uploaded Actions artifact. This snapshot makes the repo ZIP self-contained; the artifact digest remains the provenance anchor.

## `COMMITMENT.json`
```json
{"later_counterexample_forbidden_phase_a":true,"operator":{"dst_hash":"t_4ed57986280be42b","dst_posthoc":"<=","kind":"TOKEN_REWRITE","src_hash":"t_6d4ff8e4c1df55d3","src_posthoc":"<"},"operator_hash":"58a32ca35135d99bd135dc1d53b926e4bcacc3e1aaeb11926fb25a00c915392d","protocol":"V51_OPERATOR_INVENTION_20260814","requests_forbidden_phase_a":true,"scope":[0,"t_2813ca55c90c4dea"],"scope_hash":"28d91a5d83d4c27b6e425a8726dbf9fa5ea23b8bf6aefeb4641ec32c1878aeb0"}
```

## `PHASE_A.json`
```json
{"protocol":"V51_OPERATOR_INVENTION_20260814","old_generators":["IDENTITY","REVERSE_WINDOW","ROTATE_LEFT","ROTATE_RIGHT","SWAP_ADJACENT"],"constructor_destination_count":42,"repair_search":[{"id":"p1","line":"if length is None or len(name) <= length:","survivors":["<=","=="]},{"id":"p2","line":"if self.per_page <= self.orphans:","survivors":["&","*","**","+","/","<<","<=","|"]}],"common_repair_tokens":["<="],"constructed_operator":{"kind":"TOKEN_REWRITE","src_hash":"t_6d4ff8e4c1df55d3","dst_hash":"t_4ed57986280be42b","src_posthoc":"<","dst_posthoc":"<="},"old_closure_obstruction":true,"rich_harm_count":1,"scope_candidate_count":16,"scope_survivor_count":1,"scope":[0,"t_2813ca55c90c4dea"],"scope_posthoc":[0,"if"],"commitment":{"protocol":"V51_OPERATOR_INVENTION_20260814","operator":{"kind":"TOKEN_REWRITE","src_hash":"t_6d4ff8e4c1df55d3","dst_hash":"t_4ed57986280be42b","src_posthoc":"<","dst_posthoc":"<="},"scope":[0,"t_2813ca55c90c4dea"],"operator_hash":"58a32ca35135d99bd135dc1d53b926e4bcacc3e1aaeb11926fb25a00c915392d","scope_hash":"28d91a5d83d4c27b6e425a8726dbf9fa5ea23b8bf6aefeb4641ec32c1878aeb0","requests_forbidden_phase_a":true,"later_counterexample_forbidden_phase_a":true},"gates":{"old_closure_invariant_verified":true,"two_external_obstructions":true,"unique_cross_episode_new_token":true,"constructed_operator_not_in_old_closure":true,"operator_posthoc_is_strict_to_nonstrict":true,"independent_harm_found":true,"unique_scope_from_help_harm":true,"scope_posthoc_is_if":true,"requests_sealed":true},"verdict":"PASS_V51_PHASE_A_OPERATOR_CONSTRUCTION"}
```

## `PHASE_B.json`
```json
{"protocol":"V51_OPERATOR_INVENTION_20260814","commitment_sha256":"deab8dca670075a5d449dcd9f73e44ac7a69bca16e945feed49070759b772237","operator":{"dst_hash":"t_4ed57986280be42b","dst_posthoc":"<=","kind":"TOKEN_REWRITE","src_hash":"t_6d4ff8e4c1df55d3","src_posthoc":"<"},"scope":[0,"t_2813ca55c90c4dea"],"sealed_transfer":{"breaking_sites":[{"site":[626,44,46],"line":"if slice_length is None or slice_length <= 0:"}],"member":true,"cold":false,"warm":true,"ablated":false},"later_counterevidence":{"baseline":true,"harm_sites":[{"site":[115,25,26],"line":"if len(password) < self.min_length:"}],"member":true},"refined_scope_candidates":[],"decision":"REVOKE","gates":{"operator_commitment_exists":true,"requests_was_sealed_until_phase_b":true,"unique_unseen_requests_obstruction":true,"unseen_target_matches_learned_scope":true,"cold_target_fails":true,"constructed_operator_repairs_unseen_target":true,"operator_ablation_restores_failure":true,"unique_later_harm":true,"later_harm_inside_learned_scope":true,"revision_attempted_before_revocation":true,"operator_revised_or_revoked":true},"verdict":"PASS_V51_SEALED_OPERATOR_INVENTION_RATCHET","claim_boundary":"Constructed from generic token-emission substrate after old-closure obstruction certified by token-multiset invariant; not invention outside all meta-languages."}
```
