import os,json,importlib.util,math
from pathlib import Path
import river_client as river

spec=importlib.util.spec_from_file_location('v16','experiments/METALOGIC_VERIFIED_COMPOSER_V16.py');v16=importlib.util.module_from_spec(spec);spec.loader.exec_module(v16)
OUT=Path('artifacts/adaptive_consolidation_v18b');OUT.mkdir(parents=True,exist_ok=True)
BASE=v16.BASE; SEED=v16.SEED; TH=.75; LR=5e-5; EOS=v16.tok.eos_token_id; MAX_STEPS=10; BATCH=16
TRAIN=list(range(16))

def pt(plan): return ';'.join(f'{a}@{b}' for a,b in plan)
def verified(key,k,plan):
    name,mut,_=v16.variant(key,k)
    try: fixed=v16.repair(mut,name,plan)
    except: return False
    return v16.run_source(name,fixed,v16.tests_for(name))[0]
def datum(key,k,plan):
    assert verified(key,k,plan)
    p=v16.tok(v16.prompt(key,k),add_special_tokens=False)['input_ids'];b=v16.tok(' '+pt(plan),add_special_tokens=False)['input_ids']+[EOS];ids=p+b
    return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(p)-1)+[1.0]*(len(b)+1)}
def scores(m,keys): return {k:v16.direct_eval(m,k)[0] for k in keys}
def reload_scores(ck,keys,label):
    with v16.client.session(project='ml-v18b-reload-'+label) as s:
        m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=ck);return scores(m,keys)

def allocate(current,new_key,protected):
    # Preserve forward pressure, but direct the remaining budget to current regression residuals.
    # New skill gets 6-10 examples depending on whether it has crossed threshold.
    new_score=current.get(new_key,0.0); new_n=10 if new_score<TH else 6
    rem=BATCH-new_n
    deficits={k:max(0.0,TH-current.get(k,0.0)) for k in protected}
    # Keep a minimum rehearsal pulse for all protected skills, then allocate by deficit.
    alloc={k:1 for k in protected}; rem2=rem-len(protected)
    if rem2<0:
        alloc={k:0 for k in protected}; rem2=rem
    weights={k:deficits[k]+0.05 for k in protected}; Z=sum(weights.values()) or 1
    raw={k:rem2*weights[k]/Z for k in protected}
    for k in protected: alloc[k]+=int(math.floor(raw[k]))
    left=rem-sum(alloc.values())
    for k in sorted(protected,key=lambda x:(raw[x]-math.floor(raw[x]),deficits[x]),reverse=True)[:left]: alloc[k]+=1
    return new_n,alloc

def adaptive_stage(m,label,new_key,new_plan,protected,plans):
    curve=[]; cursor={k:0 for k in [new_key]+protected}
    current=scores(m,protected+[new_key])
    for st in range(1,MAX_STEPS+1):
        if min(current.values())>=TH:
            ck=m.save_weights(f'v18b_{label}_step{st-1}',mode='training').path;return curve,ck,st-1
        new_n,alloc=allocate(current,new_key,protected)
        batch=[]
        for _ in range(new_n):
            k=TRAIN[cursor[new_key]%len(TRAIN)];cursor[new_key]+=1;batch.append(datum(new_key,k,new_plan))
        for key,n in alloc.items():
            for _ in range(n):
                k=TRAIN[cursor[key]%len(TRAIN)];cursor[key]+=1;batch.append(datum(key,k,plans[key]))
        assert len(batch)==BATCH,(len(batch),new_n,alloc)
        fb=m.forward_backward(batch,loss_fn='cross_entropy');m.optim_step(lr=LR,grad_clip_norm=1.0)
        current=scores(m,protected+[new_key]);row={'step':st,'loss':float(fb.metrics['loss']),'new_n':new_n,'protected_alloc':alloc,'scores':current,'joint':min(current.values())};curve.append(row);print(json.dumps({'stage':label,**row}),flush=True)
    ck=m.save_weights(f'v18b_{label}_final',mode='training').path;return curve,ck,None

R={'source_checkpoint':v16.CHECKPOINT,'v16_verdict':v16.R['verdict'],'stages':{},'generated':{}}
# Discover D explicitly from A+B; never hand-author the composite target.
ab,rows=v16.compose_target('AB_TEST',v16.plans); passing=[r['chosen'] for r in rows if r['protected_pass'] and r['chosen']];assert ab>=TH and passing
D=passing[0]['plan'];assert all(r['plan']==D for r in passing);assert all(verified('AB_TEST',k,D) for k in TRAIN)
R['generated']['D']={'plan':D,'explicit_score':ab}
plans={'A':v16.plans['A'],'B':v16.plans['B'],'C':v16.plans['C']}
with v16.client.session(project='ml-v18b-D') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=v16.CHECKPOINT)
    pre=scores(m,['A','B','C','AB_TEST']);curve,ckD,dose=adaptive_stage(m,'D','AB_TEST',D,['A','B','C'],plans)
post=reload_scores(ckD,['A','B','C','AB_TEST'],'D');R['stages']['D']={'pre':pre,'curve':curve,'dose':dose,'checkpoint':ckD,'post_reload':post}
if dose is None or min(post.values())<TH:
    R['verdict']='FAIL_ADAPTIVE_D';(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2));raise SystemExit
# Promote D, discover E from D+C, then consolidate with A/B/C/D protected.
hier={'D':D,'C':v16.plans['C']};abc,rows=v16.compose_target('ABC_TEST',hier);passing=[r['chosen'] for r in rows if r['protected_pass'] and r['chosen']];assert abc>=TH and passing
E=passing[0]['plan'];assert all(r['plan']==E for r in passing);assert all(verified('ABC_TEST',k,E) for k in TRAIN)
R['generated']['E']={'plan':E,'explicit_score':abc}
plans2={**plans,'AB_TEST':D}
with v16.client.session(project='ml-v18b-E') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=ckD)
    preE=scores(m,['A','B','C','AB_TEST','ABC_TEST']);curveE,ckE,doseE=adaptive_stage(m,'E','ABC_TEST',E,['A','B','C','AB_TEST'],plans2)
postE=reload_scores(ckE,['A','B','C','AB_TEST','ABC_TEST'],'E');R['stages']['E']={'pre':preE,'curve':curveE,'dose':doseE,'checkpoint':ckE,'post_reload':postE}
R['gates']={'D_discovered':ab>=TH,'D_direct':post['AB_TEST']>=TH,'ABC_primitives_survive_D':min(post[k] for k in ['A','B','C'])>=TH,'E_discovered':abc>=TH,'E_direct':postE['ABC_TEST']>=TH,'D_survives_E':postE['AB_TEST']>=TH,'primitives_survive_E':min(postE[k] for k in ['A','B','C'])>=TH}
R['verdict']='PASS_ADAPTIVE_DISCOVER_CONSOLIDATE' if all(R['gates'].values()) else 'MIXED_ADAPTIVE_DISCOVER_CONSOLIDATE'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2),flush=True)