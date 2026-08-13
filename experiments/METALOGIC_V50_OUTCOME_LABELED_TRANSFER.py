import hashlib, io, json, re, subprocess, tokenize
from pathlib import Path

OUT=Path('artifacts/v50'); RQ=Path('/tmp/v50_requests'); DJ=Path('/tmp/v50_django')
SEED='V50_OUTCOME_LABELED_SEALED_20260814'

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

def token_sites(path,old):
    src=path.read_text(); ts=list(tokenize.generate_tokens(io.StringIO(src).readline)); out=[]
    for t in ts:
        if t.type==tokenize.OP and t.string==old: out.append((t.start[0],t.start[1],t.end[1],old))
    return out

def mutate(path,site,new):
    row,c0,c1,_=site; lines=path.read_text().splitlines(True); original=lines[row-1]
    lines[row-1]=original[:c0]+new+original[c1:]; path.write_text(''.join(lines)); return original.strip()

def unique_sensitive(repo,path,old,new,test,timeout,key):
    reset(repo); base=sh(test,repo,timeout); sites=token_sites(path,old); causal=[]
    for i in sorted(range(len(sites)),key=lambda j:H(key+'|'+str(sites[j][:3]))):
        reset(repo); line=mutate(path,sites[i],new); after=sh(test,repo,timeout)
        if base != after: causal.append({'site':list(sites[i][:3]),'line':line,'before':base,'after':after})
    return causal

commit=json.loads((OUT/'COMMITMENT.json').read_text()); sel=tuple(commit['selected']) if commit.get('selected') else None
commit_sha=hashlib.sha256((OUT/'COMMITMENT.json').read_bytes()).hexdigest()

# Requests is first inspected here, after the category commitment exists.
path=RQ/'src/requests/utils.py'; test='timeout 8s pytest -q tests/test_utils.py -k test_iter_slices'
cs=unique_sensitive(RQ,path,'<=','<',test,15,'requests_transfer')
line=cs[0]['line'] if len(cs)==1 else ''
features={(i,th(t)) for i,t in enumerate(lex(line))}; member=bool(sel and sel in features)
# Construct the broken state and test the same widening transform used in calibration.
cold=warm=abl=False
if len(cs)==1:
    site=tuple(cs[0]['site'])+('<=',); reset(RQ); mutate(path,site,'<'); cold=sh(test,RQ,15)
    broken=[s for s in token_sites(path,'<') if s[0]==site[0] and s[1]==site[1]]
    if member and len(broken)==1: mutate(path,broken[0],'<=')
    warm=sh(test,RQ,15)
    reset(RQ); mutate(path,site,'<'); abl=sh(test,RQ,15)
transfer_sign='HELP' if (not cold and warm) else 'OTHER'

# Open later contradiction only now. It starts passing with <; the same widening transform harms it.
cpath=DJ/'django/contrib/auth/password_validation.py'; ctest='python tests/runtests.py auth_tests.test_validators.MinimumLengthValidatorTest.test_validate --verbosity 0'
cc=unique_sensitive(DJ,cpath,'<','<=',ctest,40,'later_counterexample')
cline=cc[0]['line'] if len(cc)==1 else ''; cfeatures={(i,th(t)) for i,t in enumerate(lex(cline))}; chit=bool(sel and sel in cfeatures)
c_before=c_after=False
if len(cc)==1:
    site=tuple(cc[0]['site'])+('<',); reset(DJ); c_before=sh(ctest,DJ,40); mutate(cpath,site,'<='); c_after=sh(ctest,DJ,40)
c_sign='HARM' if (c_before and not c_after) else 'OTHER'
decision='REVOKE' if chit and c_sign=='HARM' else 'WITHHOLD'

R={'protocol':SEED,'phase':'B_SEALED_TRANSFER_THEN_LATER_HARM','commitment_sha256':commit_sha,'selected':list(sel) if sel else None,'requests':{'causal_sites':cs,'member':member,'cold':cold,'warm':warm,'ablated':abl,'sign':transfer_sign},'later_counterexample':{'causal_sites':cc,'member':chit,'before':c_before,'after':c_after,'sign':c_sign},'decision':decision}
R['gates']={'frozen_commitment_exists':bool(sel),'requests_unique_site':len(cs)==1,'requests_matches_frozen_relation':member,'requests_verifier_sign_is_help':transfer_sign=='HELP','requests_ablation_fails':not abl,'later_unique_site':len(cc)==1,'later_matches_same_relation':chit,'later_verifier_sign_is_harm':c_sign=='HARM','revokes':decision=='REVOKE'}
R['verdict']='PASS_V50_OUTCOME_LABELED_SEALED_RATCHET' if all(R['gates'].values()) else 'FAIL_V50_OUTCOME_LABELED_SEALED_RATCHET'
R['claim_boundary']='Calibration class labels are generated solely from executable HELP/HARM transitions under one widening transform; Requests is unseen until after category commitment; later contradiction is unseen until after transfer. Episode files/tests and widening mutation family remain supplied.'
(OUT/'PHASE_B.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2))
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
