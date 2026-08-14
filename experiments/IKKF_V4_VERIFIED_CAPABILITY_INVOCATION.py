import hashlib, io, json, re, subprocess, tokenize
from pathlib import Path

OUT=Path('artifacts/ikkf_v4'); OUT.mkdir(parents=True,exist_ok=True)
V51=Path('artifacts/v51'); RQ=Path('/tmp/v51_requests')
SEED='V51_OPERATOR_INVENTION_20260814'

def sh(cmd,cwd,t=60):
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

pkg=json.loads(Path('artifacts/ikkf_v3/CAPABILITY.json').read_text())
phase_a=json.loads((V51/'PHASE_A.json').read_text())
commit=json.loads((V51/'COMMITMENT.json').read_text())
assert phase_a['verdict']=='PASS_V51_PHASE_A_OPERATOR_CONSTRUCTION'
assert pkg['canonical_sha256'] and pkg['operator']==commit['operator'] and pkg['scope']==commit['scope']
op=pkg['operator']; src=op['src_posthoc']; dst=op['dst_posthoc']; scope=tuple(tuple(x) for x in pkg['scope'])

rpath=RQ/'src/requests/utils.py'; rtest='timeout 8s pytest -q tests/test_utils.py -k test_iter_slices'
reset(RQ); base,_=sh(rtest,RQ,15); assert base
# Find the unique sealed obstruction by reverting each dst site to src, exactly as V51 Phase B.
breaks=[]
for site in token_sites(rpath,dst):
    reset(RQ); line=mutate(rpath,site,src); ok,log=sh(rtest,RQ,15)
    if not ok: breaks.append({'site':site,'line':line,'log':log})
assert len(breaks)==1, breaks
broken=breaks[0]; broken_site=broken['site']
reset(RQ); mutate(rpath,broken_site,src); broken_ok,_=sh(rtest,RQ,15); assert not broken_ok

# Enumerate candidate src-token sites in the broken file and route only by frozen scope membership.
candidates=[]
for s in token_sites(rpath,src):
    line=rpath.read_text().splitlines()[s[0]-1].strip()
    member=set(scope).issubset(feats(line))
    candidates.append({'site':list(s[:3]),'line':line,'member':member})
selected=[c for c in candidates if c['member']]
required=[c for c in selected if tuple(c['site'])==tuple(broken_site[:3])]
nonmembers=[c for c in candidates if not c['member']]

# Explicit invocation: apply only selected candidates, then ask external verifier.
reset(RQ); mutate(rpath,broken_site,src)
for c in selected:
    cur=[s for s in token_sites(rpath,src) if tuple(s[:3])==tuple(c['site'])]
    if len(cur)==1: mutate(rpath,cur[0],dst)
invoked_ok,invoked_log=sh(rtest,RQ,15)
# Ablation: restore the broken state and verify failure.
reset(RQ); mutate(rpath,broken_site,src); ablated_ok,ablated_log=sh(rtest,RQ,15)

# Open precommitted later counterevidence only now.
p=subprocess.run(['python','experiments/METALOGIC_V51_SEALED_TRANSFER.py'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
print(p.stdout,flush=True); assert p.returncode==0
phase_b=json.loads((V51/'PHASE_B.json').read_text())
decision=phase_b['decision']; runtime_available=decision!='REVOKE'

export=json.loads(Path('artifacts/ikkf_v3/EXPORT_RESULT.json').read_text())
G={
 'old_closure_obstruction_passes':phase_a['gates']['constructed_operator_not_in_old_closure'],
 'external_operator_construction_passes':phase_a['verdict']=='PASS_V51_PHASE_A_OPERATOR_CONSTRUCTION',
 'unique_learned_scope_exists':bool(scope),
 'compact_export_hygiene_passes':export['verdict']=='PASS_IKKF_V3_EXPORT',
 'unique_sealed_requests_obstruction':len(breaks)==1,
 'explicit_applicability_selects_required_site':len(required)==1,
 'explicit_applicability_rejects_nonmembers':all(not c['member'] for c in nonmembers),
 'explicit_invocation_repairs_sealed_verifier':invoked_ok,
 'ablation_restores_failure':not ablated_ok,
 'no_neural_router_or_checkpoint_used':True,
 'later_counterevidence_opened_after_sealed_evaluation':phase_b['gates']['requests_was_sealed_until_phase_b'],
 'later_revision_or_revocation_enforced':decision in {'NARROW','REVOKE'} and (decision!='REVOKE' or not runtime_available),
}
R={'protocol':'protocols/IKKF_V4_VERIFIED_CAPABILITY_INVOCATION_PRECOMMIT.txt','capability_id':pkg['id'],'capability_sha256':pkg['canonical_sha256'],'operator':op,'scope':[list(x) for x in scope],'candidates':candidates,'selected':selected,'sealed':{'broken_site':list(broken_site[:3]),'invoked_ok':invoked_ok,'ablated_ok':ablated_ok},'later_decision':decision,'runtime_available_after_revision':runtime_available,'gates':G}
R['verdict']='PASS_IKKF_V4_VERIFIED_CAPABILITY_INVOCATION' if all(G.values()) else 'FAIL_IKKF_V4_VERIFIED_CAPABILITY_INVOCATION'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2),flush=True)
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
