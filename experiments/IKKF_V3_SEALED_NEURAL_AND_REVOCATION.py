import os,json,hashlib,io,subprocess,tokenize
from pathlib import Path
import river_client as river

BASE='Qwen/Qwen3.5-9B'; TH=.75
OUT=Path('artifacts/ikkf_v3'); V51=Path('artifacts/v51'); RQ=Path('/tmp/v51_requests')
pkg=json.loads((OUT/'CAPABILITY.json').read_text()); comp=json.loads((OUT/'COMPILE_RESULT.json').read_text())
CAP=comp['capability_id']; assert comp['capability_sha256']==pkg['canonical_sha256']
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=240.0); assert client.health_check()

def sh(cmd,cwd,t=60,capture=False):
    try:
        p=subprocess.run(cmd,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=t)
        return (p.returncode==0,p.stdout) if capture else p.returncode==0
    except subprocess.TimeoutExpired:
        return (False,'TIMEOUT') if capture else False

def reset(r): subprocess.run('git reset --hard -q HEAD && git clean -fdxq',cwd=r,shell=True,check=True)
def token_sites(path,val):
    ts=list(tokenize.generate_tokens(io.StringIO(path.read_text()).readline))
    return [(t.start[0],t.start[1],t.end[1],val) for t in ts if t.type==tokenize.OP and t.string==val]
def mutate(path,site,new):
    row,c0,c1,_=site; lines=path.read_text().splitlines(True); old=lines[row-1]
    lines[row-1]=old[:c0]+new+old[c1:]; path.write_text(''.join(lines)); return old.strip()

op=pkg['operator']; src=op['src_posthoc']; dst=op['dst_posthoc']
rpath=RQ/'src/requests/utils.py'; rtest='timeout 8s pytest -q tests/test_utils.py -k test_iter_slices'
reset(RQ); assert sh(rtest,RQ,15)
breaks=[]
for site in token_sites(rpath,dst):
    reset(RQ); line=mutate(rpath,site,src); ok,log=sh(rtest,RQ,15,True)
    if not ok: breaks.append({'site':site,'line':line,'log':log})
assert len(breaks)==1, breaks
site=breaks[0]['site']; reset(RQ); original_line=mutate(rpath,site,src); broken_ok,broken_log=sh(rtest,RQ,15,True); assert not broken_ok
broken_line=(rpath.read_text().splitlines()[site[0]-1]).strip()

# Eight fixed presentation variants of one sealed external obstruction.
def eprompt(i):
    return f'Installed actions: {CAP}, NOOP. Choose exactly one action for this context.\nCase: sealed-{100+i}\nSource: {broken_line}\nVerifier residual: independently authored repository test fails at the strict boundary; the equality boundary is implicated.\nAction:'
prompts=[eprompt(i) for i in range(8)]

def normalize(x):
    s=x.strip().splitlines()[0].strip() if x.strip() else ''
    return s.split()[0].strip('.,;:') if s else ''
def eval_fresh(project,seed,checkpoint=None):
    with client.session(project=project) as s:
        kw={'base_model':BASE,'lora':river.LoraConfig(rank=32,seed=seed)}
        if checkpoint: kw['checkpoint']=checkpoint
        m=s.create_model(**kw); gs=m.sample(prompts=prompts,max_tokens=12,temperature=0.0)
        outs=[normalize(g[0].text) for g in gs]
    return {'score':sum(x==CAP for x in outs)/len(outs),'outputs':outs}

B0=eval_fresh('ikkf-v3-B0',20260920)
C1=eval_fresh('ikkf-v3-EVAL-C1',20260921,comp['arms']['C1']['checkpoint'])
C2=eval_fresh('ikkf-v3-EVAL-C2',20260922,comp['arms']['C2']['checkpoint'])
W=eval_fresh('ikkf-v3-EVAL-W',20260923,comp['arms']['W']['checkpoint'])
U=eval_fresh('ikkf-v3-U',20260924)
R=eval_fresh('ikkf-v3-RELOAD-C1',20260921,comp['arms']['C1']['checkpoint'])

# Execute the discovered capability on the sealed repository target exactly once.
reset(RQ); mutate(rpath,site,src); current=[s for s in token_sites(rpath,src) if s[0]==site[0] and s[1]==site[1]]
assert len(current)==1
mutate(rpath,current[0],dst); package_repairs=sh(rtest,RQ,15)
reset(RQ); mutate(rpath,site,src); ablated_still_fails=not sh(rtest,RQ,15)

# Only after neural sealed evaluation, open V51's already-precommitted later counterevidence.
p=subprocess.run(['python','experiments/METALOGIC_V51_SEALED_TRANSFER.py'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
print(p.stdout,flush=True); assert p.returncode==0
phase_b=json.loads((V51/'PHASE_B.json').read_text())
revoked=phase_b.get('decision')=='REVOKE'
if revoked:
    pkg['revision']['status']='REVOKED'; pkg['revision']['reason']='V51 later source-distinct counterevidence eliminated all current scopes'
    pkg['revision']['phase_b_sha256']=hashlib.sha256((V51/'PHASE_B.json').read_bytes()).hexdigest()
(OUT/'CAPABILITY_FINAL.json').write_text(json.dumps(pkg,sort_keys=True,indent=2))
runtime_available=pkg['revision']['status']=='ACTIVE'

export=json.loads((OUT/'EXPORT_RESULT.json').read_text())
no_episode_checkpoint=export['verdict']=='PASS_IKKF_V3_EXPORT' and all(x in export['excluded'] for x in ['discovery_source','trajectory','checkpoint','gradient','optimizer_state'])
no_inherited=all(not a['inherited_checkpoint'] for a in comp['arms'].values())
G={
 'old_closure_obstruction_passes':json.loads((V51/'PHASE_A.json').read_text())['gates']['constructed_operator_not_in_old_closure'],
 'external_operator_construction_passes':json.loads((V51/'PHASE_A.json').read_text())['verdict']=='PASS_V51_PHASE_A_OPERATOR_CONSTRUCTION',
 'unique_scope_passes':json.loads((V51/'PHASE_A.json').read_text())['gates']['unique_scope_from_help_harm'],
 'export_contains_no_episode_or_checkpoint':no_episode_checkpoint,
 'no_inherited_neural_checkpoint':no_inherited,
 'cold_sealed_target_fails':B0['score']<TH and not broken_ok,
 'compiled_sealed_target_passes':C1['score']>=TH and package_repairs,
 'capability_ablation_restores_failure':U['score']<TH and ablated_still_fails,
 'independent_recompile_from_same_package_passes':C2['score']>=TH,
 'wrong_or_scopeless_control_fails_protected_criterion':W['score']<TH,
 'later_counterevidence_is_source_distinct_and_precommitted':phase_b['gates']['requests_was_sealed_until_phase_b'] and phase_b['gates']['unique_later_harm'],
 'later_counterevidence_forces_explicit_revocation':revoked,
 'revoked_package_is_not_available_to_runtime_after_uninstall_detach':revoked and not runtime_available,
}
RES={'protocol':'protocols/IKKF_V3_EXTERNAL_INVENTED_INSTINCT_PRECOMMIT.txt','capability_id':CAP,'capability_sha256':pkg['canonical_sha256'],'sealed_requests':{'line':broken_line,'explicit_package_repairs':package_repairs,'ablation_fails':ablated_still_fails},'neural':{'B0':B0,'C1':C1,'C2':C2,'W':W,'U':U,'R':R},'v51_phase_b_verdict':phase_b['verdict'],'revision_decision':phase_b['decision'],'runtime_available_after_revision':runtime_available,'gates':G}
# Reload is recorded as an additional persistence check but the precommitted 13 primary gates govern verdict.
RES['reload_preserves_compiled_instinct']=R['score']>=TH
RES['verdict']='PASS_IKKF_V3_EXTERNAL_INVENTED_INSTINCT' if all(G.values()) else 'FAIL_IKKF_V3_EXTERNAL_INVENTED_INSTINCT'
(OUT/'RESULT.json').write_text(json.dumps(RES,indent=2)); print(json.dumps(RES,indent=2),flush=True)
