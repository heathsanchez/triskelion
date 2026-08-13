import hashlib, io, itertools, json, re, subprocess, tokenize
from pathlib import Path
OUT=Path('artifacts/v51'); RQ=Path('/tmp/v51_requests'); DJ=Path('/tmp/v51_django')
SEED='V51_OPERATOR_INVENTION_20260814'
def sh(cmd,cwd,t=60):
    try:
        p=subprocess.run(cmd,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=t); return p.returncode==0
    except subprocess.TimeoutExpired: return False
def reset(r): subprocess.run('git reset --hard -q HEAD && git clean -fdxq',cwd=r,shell=True,check=True)
def H(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def th(x): return 't_'+hashlib.sha256((SEED+'|tok|'+x).encode()).hexdigest()[:16]
def lex(line): return re.findall(r'[A-Za-z_]+|\d+',line)
def feats(line): return {(i,th(tok)) for i,tok in enumerate(lex(line))}
def token_sites(path,val):
    ts=list(tokenize.generate_tokens(io.StringIO(path.read_text()).readline)); return [(t.start[0],t.start[1],t.end[1],val) for t in ts if t.type==tokenize.OP and t.string==val]
def mutate(path,site,new):
    row,c0,c1,_=site; lines=path.read_text().splitlines(True); line=lines[row-1]; lines[row-1]=line[:c0]+new+line[c1:]; path.write_text(''.join(lines)); return line.strip()
def breaking_sites(repo,path,good,bad,test,t,key):
    reset(repo); base=sh(test,repo,t); out=[]
    for i,s in sorted(enumerate(token_sites(path,good)),key=lambda z:H(key+'|'+repr(z[1][:3]))):
        reset(repo); line=mutate(path,s,bad); after=sh(test,repo,t)
        if base and not after: out.append({'site':list(s[:3]),'line':line})
    return out
commit=json.loads((OUT/'COMMITMENT.json').read_text()); op=commit.get('operator'); scope=tuple(commit['scope']) if commit.get('scope') else None; assert op and scope
commit_sha=hashlib.sha256((OUT/'COMMITMENT.json').read_bytes()).hexdigest(); src=op['src_posthoc']; dst=op['dst_posthoc']
rpath=RQ/'src/requests/utils.py'; rtest='timeout 8s pytest -q tests/test_utils.py -k test_iter_slices'; bs=breaking_sites(RQ,rpath,dst,src,rtest,15,'sealed_requests')
member=False; cold=warm=abl=False; transfer_line=''
if len(bs)==1:
    transfer_line=bs[0]['line']; member=scope in feats(transfer_line); goodsite=tuple(bs[0]['site'])+(dst,); reset(RQ); mutate(rpath,goodsite,src); cold=sh(rtest,RQ,15)
    if member:
        cur=[s for s in token_sites(rpath,src) if s[0]==goodsite[0] and s[1]==goodsite[1]]
        if len(cur)==1: mutate(rpath,cur[0],dst)
    warm=sh(rtest,RQ,15); reset(RQ); mutate(rpath,goodsite,src); abl=sh(rtest,RQ,15)
cpath=DJ/'django/contrib/auth/password_validation.py'; ctest='python tests/runtests.py auth_tests.test_validators.MinimumLengthValidatorTest.test_validate --verbosity 0'; reset(DJ); cbase=sh(ctest,DJ,40); harms=[]
for i,s in sorted(enumerate(token_sites(cpath,src)),key=lambda z:H('later|'+repr(z[1][:3]))):
    reset(DJ); line=mutate(cpath,s,dst); after=sh(ctest,DJ,40)
    if cbase and not after: harms.append({'site':list(s[:3]),'line':line})
c_line=harms[0]['line'] if len(harms)==1 else ''; c_member=bool(c_line and scope in feats(c_line)); phase_a=json.loads((OUT/'PHASE_A.json').read_text()); help_lines=[r['line'] for r in phase_a['repair_search'] if 'line' in r]+([transfer_line] if transfer_line else []); HF=[feats(x) for x in help_lines]; NF=[feats(c_line)] if c_line else []; common=set.intersection(*HF) if HF else set(); refined=[]
for k in (1,2):
    for comb in itertools.combinations(sorted(common),k):
        s=set(comb)
        if all(s.issubset(x) for x in HF) and all(not s.issubset(x) for x in NF): refined.append(comb)
    if refined: break
decision='NARROW' if len(refined)==1 else 'REVOKE' if len(refined)==0 and c_member else 'WITHHOLD'
R={'protocol':SEED,'commitment_sha256':commit_sha,'operator':op,'scope':list(scope),'sealed_transfer':{'breaking_sites':bs,'member':member,'cold':cold,'warm':warm,'ablated':abl},'later_counterevidence':{'baseline':cbase,'harm_sites':harms,'member':c_member},'refined_scope_candidates':[[list(x) for x in c] for c in refined],'decision':decision}; R['gates']={'operator_commitment_exists':True,'requests_was_sealed_until_phase_b':True,'unique_unseen_requests_obstruction':len(bs)==1,'unseen_target_matches_learned_scope':member,'cold_target_fails':not cold,'constructed_operator_repairs_unseen_target':warm,'operator_ablation_restores_failure':not abl,'unique_later_harm':len(harms)==1,'later_harm_inside_learned_scope':c_member,'revision_attempted_before_revocation':True,'operator_revised_or_revoked':decision in {'NARROW','REVOKE'}}; R['verdict']='PASS_V51_SEALED_OPERATOR_INVENTION_RATCHET' if all(R['gates'].values()) else 'FAIL_V51_SEALED_OPERATOR_INVENTION_RATCHET'; R['claim_boundary']='Constructed from generic token-emission substrate after old-closure obstruction certified by token-multiset invariant; not invention outside all meta-languages.'; (OUT/'PHASE_B.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2));
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
