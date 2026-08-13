import hashlib, io, json, re, subprocess, tokenize
from pathlib import Path

OUT=Path('artifacts/v49'); RQ=Path('/tmp/v45_requests'); DJ=Path('/tmp/v45_django')
SEED='V49_SEALED_TRANSFER_20260814'

def sh(cmd,cwd,t=60):
    try:
        p=subprocess.run(cmd,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=t)
        return p.returncode==0
    except subprocess.TimeoutExpired:
        return False

def reset(r): subprocess.run('git reset --hard -q HEAD && git clean -fdxq',cwd=r,shell=True,check=True)
def H(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def th(x): return 't_'+hashlib.sha256((SEED+'|tok|'+x).encode()).hexdigest()[:16]
def lex(line): return re.findall(r'[A-Za-z_]+|\d+',line)

def token_sites(path, old):
    src=path.read_text(); ts=list(tokenize.generate_tokens(io.StringIO(src).readline)); out=[]
    for t in ts:
        if t.type==tokenize.OP and t.string==old: out.append((t.start[0],t.start[1],t.end[1],old))
    return out

def mutate_site(path,site,new):
    row,c0,c1,_=site; lines=path.read_text().splitlines(True); line=lines[row-1]
    lines[row-1]=line[:c0]+new+line[c1:]; path.write_text(''.join(lines)); return line.strip()

def mine(repo,path,old,new,test,timeout,role):
    reset(repo); baseline=sh(test,repo,timeout); sites=token_sites(path,old)
    order=sorted(range(len(sites)),key=lambda i:H(role+'|'+str(sites[i][:3]))); causal=[]; attempts=[]
    for i in order:
        reset(repo); line=mutate_site(path,sites[i],new); ok=sh(test,repo,timeout)
        attempts.append({'token_site':list(sites[i][:3]),'passes':ok})
        if baseline and not ok: causal.append({'token_site':list(sites[i][:3]),'text':line})
    return {'baseline':baseline,'candidate_count':len(sites),'attempts':attempts,'causal':causal}

commitment=json.loads((OUT/'COMMITMENT.json').read_text()); sel=tuple(commitment['selected']) if commitment.get('selected') else None
phase_a_hash=hashlib.sha256((OUT/'COMMITMENT.json').read_bytes()).hexdigest()

transfer_path=RQ/'src/requests/utils.py'
transfer=mine(RQ,transfer_path,'<=','<','timeout 8s pytest -q tests/test_utils.py -k test_iter_slices',15,'transfer')
transfer_line=transfer['causal'][0]['text'] if len(transfer['causal'])==1 else ''
transfer_features={(i,th(t)) for i,t in enumerate(lex(transfer_line))}
member=bool(sel and sel in transfer_features)

# cold/warm/ablation after commitment is already frozen
reset(RQ); sites=token_sites(transfer_path,'<='); causal_site=None
for s in sites:
    reset(RQ); mutate_site(transfer_path,s,'<');
    if not sh('timeout 8s pytest -q tests/test_utils.py -k test_iter_slices',RQ,15): causal_site=s; break
cold=False; warm=False; ablated=False
if causal_site:
    reset(RQ); mutate_site(transfer_path,causal_site,'<'); cold=sh('timeout 8s pytest -q tests/test_utils.py -k test_iter_slices',RQ,15)
    if member:
        row,c0,c1,_=causal_site; lines=transfer_path.read_text().splitlines(True); line=lines[row-1]; lines[row-1]=line[:c0]+'<='+line[c1:]; transfer_path.write_text(''.join(lines))
    warm=sh('timeout 8s pytest -q tests/test_utils.py -k test_iter_slices',RQ,15)
    reset(RQ); mutate_site(transfer_path,causal_site,'<'); ablated=sh('timeout 8s pytest -q tests/test_utils.py -k test_iter_slices',RQ,15)

# withheld contradiction opened only after transfer decision
contra_path=DJ/'django/contrib/auth/password_validation.py'
contra=mine(DJ,contra_path,'<','<=','python tests/runtests.py auth_tests.test_validators.MinimumLengthValidatorTest.test_validate --verbosity 0',40,'counterexample')
contra_line=contra['causal'][0]['text'] if len(contra['causal'])==1 else ''
contra_features={(i,th(t)) for i,t in enumerate(lex(contra_line))}
counter_hit=bool(sel and sel in contra_features)
base=contra['baseline']; after=False
if len(contra['causal'])==1:
    reset(DJ); site=tuple(contra['causal'][0]['token_site'])+('<',)
    mutate_site(contra_path,site,'<='); after=sh('python tests/runtests.py auth_tests.test_validators.MinimumLengthValidatorTest.test_validate --verbosity 0',DJ,40)
decision='REVOKE' if counter_hit and base and not after else 'WITHHOLD'

R={'protocol':SEED,'phase':'B_WITHHELD_TRANSFER_THEN_COUNTEREVIDENCE','commitment_sha256':phase_a_hash,'selected':list(sel) if sel else None,'transfer':transfer,'transfer_member':member,'transfer_causal':{'cold':cold,'warm':warm,'ablated':ablated},'counterexample':contra,'counterexample_hits_selected':counter_hit,'counter_base':base,'counter_after':after,'decision':decision}
R['gates']={'phase_a_commitment_exists':bool(sel),'unique_requests_causal_site':len(transfer['causal'])==1,'requests_matches_frozen_category':member,'cold_fails':not cold,'warm_passes':warm,'ablation_restores_failure':not ablated,'unique_later_counterexample_site':len(contra['causal'])==1,'counterexample_hits_frozen_category':counter_hit,'counterexample_falsifies_repair':base and not after,'revokes':decision=='REVOKE'}
R['verdict']='PASS_V49_TEMPORALLY_SEALED_TRANSFER_RATCHET' if all(R['gates'].values()) else 'FAIL_V49_TEMPORALLY_SEALED_TRANSFER_RATCHET'
R['claim_boundary']='Category is committed before Requests is opened by phase B. Requests is not calibration evidence. Later Django contradiction is opened only after transfer evaluation. Repositories/tests, mutation family, tokenizer, calibration roles, and file choices remain supplied.'
(OUT/'PHASE_B.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2))
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
