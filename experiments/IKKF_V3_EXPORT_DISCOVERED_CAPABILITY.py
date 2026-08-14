import hashlib,json
from pathlib import Path

V51=Path('artifacts/v51'); OUT=Path('artifacts/ikkf_v3'); OUT.mkdir(parents=True,exist_ok=True)
phase=json.loads((V51/'PHASE_A.json').read_text()); commit=json.loads((V51/'COMMITMENT.json').read_text())
assert phase['verdict']=='PASS_V51_PHASE_A_OPERATOR_CONSTRUCTION'
assert all(phase['gates'].values())
assert commit.get('operator') and commit.get('scope')

pkg={
 'schema':'metalogic.verified_capability.v1',
 'id':'V51_'+commit['operator_hash'][:16],
 'kind':'SCOPED_TOKEN_REWRITE',
 'operator':commit['operator'],
 'scope':commit['scope'],
 'dependencies':[],
 'verification':{
   'authority':'independently authored executable repository tests at fixed commits',
   'old_closure_obstruction':True,
   'phase_a_verdict':phase['verdict']
 },
 'provenance':{
   'protocol':commit['protocol'],
   'operator_hash':commit['operator_hash'],
   'scope_hash':commit['scope_hash'],
   'source_commitment_sha256':hashlib.sha256((V51/'COMMITMENT.json').read_bytes()).hexdigest()
 },
 'revision':{'status':'ACTIVE','reverify_before_compile':True},
 'excluded':['discovery_source','test_log','trajectory','checkpoint','gradient','optimizer_state']
}
canon=json.dumps(pkg,sort_keys=True,separators=(',',':')).encode(); pkg['canonical_sha256']=hashlib.sha256(canon).hexdigest()
text=json.dumps(pkg,sort_keys=True,indent=2)
for banned in ['checkpoint_uri','optimizer_state','gradient_buffer','trajectory_text','test_log_text']:
 assert banned not in text
(OUT/'CAPABILITY.json').write_text(text)
R={'verdict':'PASS_IKKF_V3_EXPORT','capability_id':pkg['id'],'canonical_sha256':pkg['canonical_sha256'],'excluded':pkg['excluded'],'source_phase_a':phase['verdict']}
(OUT/'EXPORT_RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2))
