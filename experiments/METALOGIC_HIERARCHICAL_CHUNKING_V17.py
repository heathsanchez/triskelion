import json,importlib.util
from pathlib import Path
# Reuse the complete frozen V16 protocol/functions. Import executes V16 and produces its independent result first.
spec=importlib.util.spec_from_file_location('v16','experiments/METALOGIC_VERIFIED_COMPOSER_V16.py');v16=importlib.util.module_from_spec(spec);spec.loader.exec_module(v16)
OUT=Path('artifacts/hierarchical_chunking_v17');OUT.mkdir(parents=True,exist_ok=True)
# Discover D from the verified AB composition rather than naming its plan in advance.
ab_score,ab_rows=v16.compose_target('AB_TEST',v16.plans)
chosen=[r['chosen'] for r in ab_rows if r['protected_pass'] and r['chosen']]
assert chosen and ab_score>=0.75
canon=json.dumps(chosen[0]['plan'])
assert all(json.dumps(x['plan'])==canon for x in chosen)
D=chosen[0]['plan']
# Promote the passing composite as a new capability chunk. The next search sees D and C, not A/B/C separately.
hier={'D':D,'C':v16.plans['C']}
abc_hier,rows_hier=v16.compose_target('ABC_TEST',hier)
abc_flat,rows_flat=v16.compose_target('ABC_TEST',v16.plans)
minus_D,_=v16.compose_target('ABC_TEST',hier,['C'])
minus_C,_=v16.compose_target('ABC_TEST',hier,['D'])
# Verify promoted D remains a real executable capability on the AB target after promotion.
d_only,_=v16.compose_target('AB_TEST',{'D':D})
flat_candidates=sum(r['candidate_count'] for r in rows_flat);hier_candidates=sum(r['candidate_count'] for r in rows_hier)
R={
 'source_v16_verdict':v16.R['verdict'],
 'promoted_D':D,
 'AB_score_before_promotion':ab_score,
 'D_reuse_on_AB':d_only,
 'ABC_flat_score':abc_flat,
 'ABC_hierarchical_score':abc_hier,
 'ABC_minus_D':minus_D,
 'ABC_minus_C':minus_C,
 'flat_candidate_evaluations':flat_candidates,
 'hierarchical_candidate_evaluations':hier_candidates,
 'compression_ratio':hier_candidates/flat_candidates if flat_candidates else None,
 'hierarchical_rows':rows_hier,
}
R['gates']={
 'v16_passed':v16.R['verdict']=='PASS_VERIFIED_COMPOSITION_LAYER',
 'D_is_verified_reusable':d_only>=0.75,
 'D_plus_C_reaches_ABC':abc_hier>=0.75,
 'D_is_causally_required':minus_D<0.75,
 'C_is_causally_required':minus_C<0.75,
 'hierarchy_reduces_search':hier_candidates<flat_candidates,
 'no_accuracy_loss':abc_hier>=abc_flat,
}
R['verdict']='PASS_HIERARCHICAL_CAPABILITY_CHUNKING' if all(R['gates'].values()) else 'MIXED_HIERARCHICAL_CAPABILITY_CHUNKING'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2),flush=True)
