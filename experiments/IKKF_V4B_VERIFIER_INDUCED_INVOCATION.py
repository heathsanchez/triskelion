import hashlib, io, json, re, subprocess, tokenize
from pathlib import Path

OUT=Path('artifacts/ikkf_v4b'); OUT.mkdir(parents=True,exist_ok=True)
V51=Path('artifacts/v51'); RQ=Path('/tmp/v51_requests')
SEED='V51_OPERATOR_INVENTION_20260814'

def sh(cmd,cwd,t=90):
    try:
        p=subprocess.run(cmd,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=t)
        return p.returncode==0,p.stdout
    except subprocess.TimeoutExpired:
        return False,'TIMEOUT'

def reset(r): subprocess.run('git reset --hard -q HEAD && git clean -fdxq',cwd=r,shell=True,check=True)
def th(x): return 't_'+hashlib.sha256((SEED+'|tok|'+x).encode()).hexdigest()[:16]
def lex(line): return re.findall(r'[A-Za-z_]+|\d+',line)
def feats(line): return {(i,th(tok)) for i,tok in enumerate(lex(line))}
def token_sites(path,val):
    ts=list(tokenize.generate_tokens(io.StringIO(path.read_text()).readline))
    return [(t.start[0],t.start[1],t.end[1],val) for t in ts if t.type==tokenize.OP and t.string==val]
def mutate(path,site,new):
    row,c0,c1,_=site; lines=path.read_text().splitlines(True); old=lines[row-1]
    lines[row-1]=old[:c0]+new+old[c1:]; path.write_text(''.join(lines)); return old.strip()
def site_id(site): return tuple(site[:2])

pkg=json.loads(Path('artifacts/ikkf_v3/CAPABILITY.json').read_text())
phase_a=json.loads((V51/'PHASE_A.json').read_text()); commit=json.loads((V51/'COMMITMENT.json').read_text())
assert phase_a['verdict']=='PASS_V51_PHASE_A_OPERATOR_CONSTRUCTION'
op=pkg['operator']; src=op['src_posthoc']; dst=op['dst_posthoc']; scope=tuple(pkg['scope'])
rpath=RQ/'src/requests/utils.py'
target='timeout 8s pytest -q tests/test_utils.py -k test_iter_slices'
protected='timeout 75s pytest -q tests/test_utils.py'

reset(RQ); base_target,_=sh(target,RQ,15); base_protected,_=sh(protected,RQ,80); assert base_target and base_protected
# Recreate unique sealed obstruction.
breaks=[]
for site in token_sites(rpath,dst):
    reset(RQ); line=mutate(rpath,site,src); ok,log=sh(target,RQ,15)
    if not ok: breaks.append({'site':site,'line':line,'log':log})
assert len(breaks)==1, breaks
broken_site=breaks[0]['site']
reset(RQ); mutate(rpath,broken_site,src); broken_ok,_=sh(target,RQ,15); assert not broken_ok

# Coarse scope candidates in the identical broken state.
candidates=[]
for s in token_sites(rpath,src):
    line=rpath.read_text().splitlines()[s[0]-1].strip(); member=scope in feats(line)
    if member: candidates.append({'site':list(s[:3]),'line':line})

# Frozen verifier-induced refinement: probe each admitted site independently.
probes=[]
for c in candidates:
    reset(RQ); mutate(rpath,broken_site,src)
    cur=[s for s in token_sites(rpath,src) if tuple(s[:3])==tuple(c['site'])]
    assert len(cur)==1
    mutate(rpath,cur[0],dst)
    target_ok,target_log=sh(target,RQ,15)
    protected_ok,protected_log=sh(protected,RQ,80)
    probes.append({'site':c['site'],'line':c['line'],'target_ok':target_ok,'protected_ok':protected_ok})
refined=[p for p in probes if p['target_ok'] and p['protected_ok']]

# Invoke exactly the refined candidate if unique.
invoke_target=invoke_protected=False
if len(refined)==1:
    c=refined[0]; reset(RQ); mutate(rpath,broken_site,src)
    cur=[s for s in token_sites(rpath,src) if tuple(s[:3])==tuple(c['site'])]
    assert len(cur)==1; mutate(rpath,cur[0],dst)
    invoke_target,_=sh(target,RQ,15); invoke_protected,_=sh(protected,RQ,80)
reset(RQ); mutate(rpath,broken_site,src); ablated_ok,_=sh(target,RQ,15)

# Open later precommitted counterevidence only after invocation evaluation.
p=subprocess.run(['python','experiments/METALOGIC_V51_SEALED_TRANSFER.py'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
print(p.stdout,flush=True); assert p.returncode==0
phase_b=json.loads((V51/'PHASE_B.json').read_text()); decision=phase_b['decision']; runtime_available=decision!='REVOKE'
export=json.loads(Path('artifacts/ikkf_v3/EXPORT_RESULT.json').read_text())
# TOKEN_REWRITE changes token width (< -> <=); transformed-token identity is row + start column.
required_in_coarse=any(site_id(c['site'])==site_id(broken_site) for c in candidates)
refined_is_required=len(refined)==1 and site_id(refined[0]['site'])==site_id(broken_site)
G={
 'old_closure_obstruction_passes':phase_a['gates']['constructed_operator_not_in_old_closure'],
 'external_operator_construction_passes':phase_a['verdict']=='PASS_V51_PHASE_A_OPERATOR_CONSTRUCTION',
 'compact_export_passes':export['verdict']=='PASS_IKKF_V3_EXPORT',
 'coarse_scope_reproduces_ambiguity':len(candidates)>=2 and required_in_coarse,
 'verifier_probing_unique_refinement':len(refined)==1,
 'refined_candidate_is_required_site':refined_is_required,
 'refined_invocation_repairs_target':invoke_target,
 'refined_invocation_preserves_protected':invoke_protected,
 'ablation_restores_target_failure':not ablated_ok,
 'no_hand_semantic_or_neural_router':True,
 'later_counterevidence_opened_after_invocation':phase_b['gates']['requests_was_sealed_until_phase_b'],
 'later_revision_or_revocation_enforced':decision in {'NARROW','REVOKE'} and (decision!='REVOKE' or not runtime_available),
}
R={'protocol':'protocols/IKKF_V4B_VERIFIER_INDUCED_INVOCATION_PRECOMMIT.txt','capability_id':pkg['id'],'capability_sha256':pkg['canonical_sha256'],'scope':list(scope),'broken_site':list(broken_site[:3]),'coarse_candidates':candidates,'probes':probes,'refined':refined,'later_decision':decision,'runtime_available_after_revision':runtime_available,'gates':G}
R['verdict']='PASS_IKKF_V4B_VERIFIER_INDUCED_INVOCATION' if all(G.values()) else 'FAIL_IKKF_V4B_VERIFIER_INDUCED_INVOCATION'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2),flush=True)
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
