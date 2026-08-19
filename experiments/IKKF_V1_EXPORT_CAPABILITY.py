import hashlib,itertools,json
from pathlib import Path
import IKKF_V1_RUNTIME as rt

OUT=Path('artifacts/ikkf_v1_export');OUT.mkdir(parents=True,exist_ok=True)
rt.prepare()
old_fails=all(not rt.run_source(rt.variant('AB_TEST',k)[0],rt.variant('AB_TEST',k)[1],rt.tests_for(rt.PROGRAMS['AB_TEST'][0]))[0] for k in rt.TRAIN)
plans={'A':rt.PRIMITIVES['A'],'B':rt.PRIMITIVES['B']}
candidates=[]
for r in range(1,3):
    for subset in itertools.combinations(['A','B'],r):
        plan=[]
        for n in subset:plan.extend(plans[n])
        plan=list(dict.fromkeys(plan))
        passes=[rt.verified('AB_TEST',k,plan) for k in rt.TRAIN]
        candidates.append({'subset':list(subset),'plan':plan,'all_pass':all(passes),'pass_count':sum(passes)})
passing=[c for c in candidates if c['all_pass']]
if not passing:raise SystemExit('no verified capability')
chosen=min(passing,key=lambda c:(len(c['plan']),len(c['subset']),c['subset']))
cap={
 'schema':'metalogic.verified_capability.v1',
 'capability_id':'QUIXBUGS_FIND_IN_SORTED_AB_COMPOSITE',
 'version':1,
 'kind':'VERIFIED_COMPOSITE',
 'target_family':'AB_TEST',
 'scope':{'corpus':'jkoppel/QuixBugs','commit':rt.COMMIT,'program':'find_in_sorted','mutation_family':['CMP','BIN']},
 'plan':chosen['plan'],
 'dependencies':chosen['subset'],
 'verifier':{'type':'external_test_suite','authority':'QuixBugs json_testcases at frozen commit','discovery_variants':rt.TRAIN},
 'provenance':{'construction':'minimal subset closure over verified primitives A and B','source_commit':rt.COMMIT},
 'revision':{'status':'active','reverify_before_compile':True}
}
raw=(json.dumps(cap,sort_keys=True,separators=(',',':'))+'\n').encode();sha=hashlib.sha256(raw).hexdigest();cap['package_sha256']=sha
# Hash canonical content excluding its self-hash field.
raw=(json.dumps(cap,sort_keys=True,indent=2)+'\n').encode()
(OUT/'CAPABILITY.json').write_bytes(raw)
result={'protocol':'IKKF_V1_PORTABLE_CAPABILITY','old_target_fails':old_fails,'candidates':candidates,'chosen':chosen,'capability_path':'CAPABILITY.json','canonical_payload_sha256':sha,'package_contains_no_checkpoint_or_trajectory':all(x not in json.dumps(cap).lower() for x in ['river://','checkpoint','trajectory','gradient','optimizer']),'gates':{}}
result['gates']={'export_old_target_fails':old_fails,'export_capability_verified':chosen['all_pass'] and chosen['subset']==['A','B'],'package_contains_no_checkpoint_or_trajectory':result['package_contains_no_checkpoint_or_trajectory']}
result['verdict']='PASS_IKKF_V1_EXPORT' if all(result['gates'].values()) else 'FAIL_IKKF_V1_EXPORT'
(OUT/'EXPORT_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
if result['verdict']!='PASS_IKKF_V1_EXPORT':raise SystemExit(2)
