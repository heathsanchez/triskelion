"""IKKF V2C: modular explicit capability modules + learned router.

Frozen before V2C neural outputs. Reuses V2's exact executable mutation/verifier
substrate with V2B's semantic-valid heldout universe. The modular arm trains only
C-vs-J selection; selected explicit modules remain external and unchanged.
"""
import json, hashlib
from pathlib import Path

# Load only the frozen V2 substrate/definitions, not its experiment execution.
parent=Path('experiments/IKKF_V2_CAPABILITY_ROUTING.py')
src=parent.read_text()
print('V2_PARENT_SHA256',hashlib.sha256(src.encode()).hexdigest(),flush=True)
src=src.replace("HELD_PROGS=['possible_change','quicksort','sieve','subsequences']","HELD_PROGS=['possible_change','sieve','subsequences']")
marker="R={'protocol':'protocols/IKKF_V2_CAPABILITY_ROUTING_PRECOMMIT.txt'"
assert marker in src and src.count(marker)==1
substrate=src.split(marker,1)[0]
ns={'__name__':'ikkf_v2c_substrate'}
exec(compile(substrate,'IKKF_V2C_FROZEN_SUBSTRATE','exec'),ns,ns)

# Bind frozen substrate names.
client=ns['client']; tok=ns['tok']; EOS=ns['EOS']; BASE=ns['BASE']; TH=ns['TH']; LR=ns['LR']; STEPS=ns['STEPS']
TRAIN=ns['TRAIN']; HELD=ns['HELD']; C_TRAIN=ns['C_TRAIN']; J_TRAIN=ns['J_TRAIN']; HELD_PROGS=ns['HELD_PROGS']; C=ns['C']; J=ns['J']
variant=ns['variant']; run=ns['run']; apply=ns['apply']; verify=ns['verify']; eval_model=ns['eval_model']; compile_arm=ns['compile_arm']
OUT=Path('artifacts/ikkf_v2c_modular_router'); OUT.mkdir(parents=True,exist_ok=True)

# The router sees the same mutated source and verified residual as the repair model,
# but its action space is only the installed module IDs C and J.
def router_prompt(name,k,required):
    mutated,residual=variant(name,k,required)
    return f'''Two verified capability modules are installed.
C = CMP@0;BIN@0
J = CMP@0;CONST@0
Choose exactly one installed module for this case. Return ONLY C or J.
Program: {name}
Verified residual: {residual}

{mutated}'''

def router_datum(name,k,required,target_label):
    q=tok(router_prompt(name,k,required),add_special_tokens=False)['input_ids']
    a=tok(' '+target_label,add_special_tokens=False)['input_ids']+[EOS]
    ids=q+a
    return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(q)-1)+[1.0]*(len(a)+1)}

def parse_label(text):
    s=text.strip().splitlines()[0].strip() if text.strip() else ''
    x=s.split()[0].strip('.,;:') if s else ''
    return x if x in {'C','J'} else None

def eval_router(model):
    prompts=[]; meta=[]
    for name in HELD_PROGS:
        for k in HELD:
            for label,required in [('C',C),('J',J)]:
                prompts.append(router_prompt(name,k,required)); meta.append((name,k,label,required))
    generations=model.sample(prompts=prompts,max_tokens=8,temperature=0.0)
    rows=[]
    for (name,k,label,required),g in zip(meta,generations):
        output=g[0].text; pred=parse_label(output)
        selected=C if pred=='C' else J if pred=='J' else None
        mutated,_=variant(name,k,required)
        try: repair_ok=run(name,apply(mutated,name,selected,True))[0] if selected else False
        except Exception: repair_ok=False
        rows.append({'program':name,'suffix':k,'required':label,'output':output.strip().splitlines()[0] if output.strip() else '',
                     'selected':pred,'route_ok':pred==label,'repair_ok':repair_ok})
    def score(label,key):
        z=[r for r in rows if r['required']==label]
        return sum(bool(r[key]) for r in z)/len(z)
    c=score('C','repair_ok'); j=score('J','repair_ok')
    route=sum(bool(r['route_ok']) for r in rows)/len(rows)
    return {'C':c,'J':j,'joint':min(c,j),'route_accuracy':route,'rows':rows}

def fresh_router(project,seed):
    import river_client as river
    with client.session(project=project) as s:
        m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=seed))
        return eval_router(m)

def train_router(project,seed,shuffle=False):
    import river_client as river
    cex=[router_datum(name,k,C,'J' if shuffle else 'C') for name in C_TRAIN for k in TRAIN]
    jex=[router_datum(name,k,J,'C' if shuffle else 'J') for name in J_TRAIN for k in TRAIN]
    curve=[]
    with client.session(project=project) as s:
        m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=seed))
        for st in range(STEPS):
            batch=[]
            for i in range(8):
                batch.append(cex[(st*8+i)%len(cex)]); batch.append(jex[(st*8+i)%len(jex)])
            fb=m.forward_backward(batch,loss_fn='cross_entropy')
            m.optim_step(lr=LR,grad_clip_norm=1.0)
            loss=float(fb.metrics['loss']); curve.append(loss)
            print(json.dumps({'arm':project,'step':st+1,'loss':loss}),flush=True)
        ev=eval_router(m); ck=m.save_weights(project+'-final',mode='training').path
    return {'eval':ev,'curve':curve,'checkpoint':ck,'inherited_checkpoint':False}

def reload_router(checkpoint):
    import river_client as river
    with client.session(project='ikkf-v2c-router-reload') as s:
        m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=20260932),checkpoint=checkpoint)
        return eval_router(m)

R={'protocol':'protocols/IKKF_V2C_MODULAR_CAPABILITY_ROUTER_PRECOMMIT.txt','arms':{},'verification':{}}
okC,rC=verify(C_TRAIN,TRAIN,C); okJ,rJ=verify(J_TRAIN,TRAIN,J)
okHC,rHC=verify(HELD_PROGS,HELD,C); okHJ,rHJ=verify(HELD_PROGS,HELD,J)
R['verification']={'practice_C':{'ok':okC},'practice_J':{'ok':okJ},'heldout_C':{'ok':okHC},'heldout_J':{'ok':okHJ}}
if not all([okC,okJ,okHC,okHJ]):
    R['verdict']='FAIL_SEMANTIC_PRECONDITION'
    R['verification']['rows']={'C':rHC,'J':rHJ}
    (OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2)); raise SystemExit(2)

# Freeze all arms before inspecting any V2C outputs.
B0=fresh_router('ikkf-v2c-B0',20260930)
# Matched monolithic arm is the unchanged V2 compiler with V2B's heldout universe.
MONO=compile_arm('ikkf-v2c-MONO',20260931,False)
ROUTER=train_router('ikkf-v2c-ROUTER',20260932,False)
SHUFFLE=train_router('ikkf-v2c-SHUFFLE',20260933,True)
RR=reload_router(ROUTER['checkpoint'])

R['arms']={'B0':B0,'MONO':MONO,'ROUTER':ROUTER,'SHUFFLE':SHUFFLE,'R':RR}
me=MONO['eval']; re=ROUTER['eval']; se=SHUFFLE['eval']
R['gates']={
 'practice_C_verified':okC,
 'practice_J_verified':okJ,
 'heldout_C_semantically_verified':okHC,
 'heldout_J_semantically_verified':okHJ,
 'cold_router_fails':B0['route_accuracy']<TH or B0['joint']<TH,
 'modular_C_passes':re['C']>=TH,
 'modular_J_passes':re['J']>=TH,
 'modular_routes':re['route_accuracy']>=TH,
 'selected_modules_execute':re['joint']>=TH,
 'shuffled_router_fails':se['route_accuracy']<TH or se['joint']<TH,
 'reload_preserves_modular_routing':RR['C']>=TH and RR['J']>=TH and RR['route_accuracy']>=TH,
 'matched_monolithic_does_not_dominate':me['joint']<TH or me['route_accuracy']<TH or re['route_accuracy']>me['route_accuracy'],
 'heldout_never_trained':set(HELD_PROGS).isdisjoint(C_TRAIN+J_TRAIN) and set(HELD).isdisjoint(TRAIN),
 'no_inherited_checkpoint':True,
}
R['comparison']={'modular_route_minus_monolithic':re['route_accuracy']-me['route_accuracy'],
                 'modular_joint_minus_monolithic':re['joint']-me['joint']}
R['verdict']='PASS_IKKF_V2C_MODULAR_CAPABILITY_ROUTER' if all(R['gates'].values()) else 'FAIL_IKKF_V2C_MODULAR_CAPABILITY_ROUTER'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2),flush=True)
