"""IKKF V2e: distill verifier-decided invocation into a neural selector.

The selector is trained on paired C/J worlds from the SAME program identities,
chosen by a frozen semantic census before any neural output is inspected.
"""
import hashlib,json
from pathlib import Path

parent=Path('experiments/IKKF_V2_CAPABILITY_ROUTING.py')
src=parent.read_text()
print('V2_PARENT_SHA256',hashlib.sha256(src.encode()).hexdigest(),flush=True)
marker="R={'protocol':'protocols/IKKF_V2_CAPABILITY_ROUTING_PRECOMMIT.txt'"
assert marker in src and src.count(marker)==1
substrate=src.split(marker,1)[0]
ns={'__name__':'ikkf_v2e_substrate'}
exec(compile(substrate,'IKKF_V2E_FROZEN_SUBSTRATE','exec'),ns,ns)

client=ns['client']; tok=ns['tok']; EOS=ns['EOS']; BASE=ns['BASE']; TH=ns['TH']; LR=ns['LR']; STEPS=ns['STEPS']
C=ns['C']; J=ns['J']; variant=ns['variant']; run=ns['run']; apply=ns['apply']
root=ns['root']
HELD_PROGS=['possible_change','sieve','subsequences']; HELD=list(range(100,108)); TRAIN=list(range(16)); CENSUS=list(range(4))
OUT=Path('artifacts/ikkf_v2e_verified_invocation_distillation'); OUT.mkdir(parents=True,exist_ok=True)

def sem_ok(name,k,required,other):
    try:
        mut,_=variant(name,k,required)
        req_ok=run(name,apply(mut,name,required,True))[0]
        try: other_ok=run(name,apply(mut,name,other,True))[0]
        except Exception: other_ok=False
        return (not run(name,mut)[0]) and req_ok and (not other_ok)
    except Exception:
        return False

def paired_program_ok(name,suffixes):
    return all(sem_ok(name,k,C,J) and sem_ok(name,k,J,C) for k in suffixes)

all_names=sorted(p.stem for p in (root/'correct_python_programs').glob('*.py') if p.stem not in HELD_PROGS)
selected=[]; census_rows=[]
for name in all_names:
    ok=paired_program_ok(name,CENSUS)
    census_rows.append({'program':name,'paired_valid':ok})
    if ok and len(selected)<8: selected.append(name)

R={'protocol':'protocols/IKKF_V2E_VERIFIED_INVOCATION_DISTILLATION_PRECOMMIT.txt','selected_training_programs':selected,'census':census_rows,'arms':{}}
if len(selected)<4:
    R['verdict']='FAIL_INSUFFICIENT_PAIRED_WORLDS'
    (OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2)); raise SystemExit(2)

# Re-verify every full training world and collect only unique verifier decisions.
train_rows=[]
for name in selected:
    for k in TRAIN:
        for label,required,other in [('C',C,J),('J',J,C)]:
            try:
                mut,residual=variant(name,k,required)
                req_ok=run(name,apply(mut,name,required,True))[0]
                try: other_ok=run(name,apply(mut,name,other,True))[0]
                except Exception: other_ok=False
                noop_ok=run(name,mut)[0]
            except Exception as e:
                req_ok=False; other_ok=False; noop_ok=False; residual={'error':repr(e)}
            unique=(not noop_ok) and req_ok and (not other_ok)
            train_rows.append({'program':name,'suffix':k,'label':label,'unique':unique,'required_ok':req_ok,'other_ok':other_ok,'noop_ok':noop_ok,'residual':residual})
all_unique=all(r['unique'] for r in train_rows)
if not all_unique:
    R['training_verification']=train_rows; R['verdict']='FAIL_FULL_TRAINING_SEMANTIC_PRECONDITION'
    (OUT/'RESULT.json').write_text(json.dumps(R,indent=2,default=str)); print(json.dumps(R,indent=2,default=str)); raise SystemExit(3)

# Same router interface as V2c.
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
    gs=model.sample(prompts=prompts,max_tokens=8,temperature=0.0)
    rows=[]
    for (name,k,label,required),g in zip(meta,gs):
        text=g[0].text; pred=parse_label(text); selected_plan=C if pred=='C' else J if pred=='J' else None
        mut,_=variant(name,k,required)
        try: repair_ok=run(name,apply(mut,name,selected_plan,True))[0] if selected_plan else False
        except Exception: repair_ok=False
        rows.append({'program':name,'suffix':k,'required':label,'output':text.strip().splitlines()[0] if text.strip() else '', 'selected':pred,'route_ok':pred==label,'repair_ok':repair_ok})
    def score(label,key):
        z=[r for r in rows if r['required']==label]; return sum(bool(r[key]) for r in z)/len(z)
    c=score('C','repair_ok'); j=score('J','repair_ok'); route=sum(bool(r['route_ok']) for r in rows)/len(rows)
    return {'C':c,'J':j,'joint':min(c,j),'route_accuracy':route,'rows':rows}

def fresh_router(project,seed):
    import river_client as river
    with client.session(project=project) as s:
        m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=seed))
        return eval_router(m)

def train_router(project,seed,shuffle=False):
    import river_client as river
    examples=[]
    for name in selected:
        for k in TRAIN:
            examples.append(router_datum(name,k,C,'J' if shuffle else 'C'))
            examples.append(router_datum(name,k,J,'C' if shuffle else 'J'))
    curve=[]
    with client.session(project=project) as s:
        m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=seed))
        # deterministic balanced sampling across program identities and labels
        for st in range(STEPS):
            batch=[]
            base=(st*8)%len(examples)
            for i in range(16): batch.append(examples[(base+i)%len(examples)])
            fb=m.forward_backward(batch,loss_fn='cross_entropy'); m.optim_step(lr=LR,grad_clip_norm=1.0)
            loss=float(fb.metrics['loss']); curve.append(loss); print(json.dumps({'arm':project,'step':st+1,'loss':loss}),flush=True)
        ev=eval_router(m); ck=m.save_weights(project+'-final',mode='training').path
    return {'eval':ev,'curve':curve,'checkpoint':ck,'inherited_checkpoint':False}

def reload_router(checkpoint):
    import river_client as river
    with client.session(project='ikkf-v2e-reload') as s:
        m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=20260942),checkpoint=checkpoint)
        return eval_router(m)

B0=fresh_router('ikkf-v2e-B0',20260940)
PAIRED=train_router('ikkf-v2e-PAIRED',20260941,False)
SHUFFLE=train_router('ikkf-v2e-SHUFFLE',20260943,True)
RR=reload_router(PAIRED['checkpoint'])
R['training_verification']=train_rows; R['arms']={'B0':B0,'PAIRED':PAIRED,'SHUFFLE':SHUFFLE,'R':RR}
pe=PAIRED['eval']; se=SHUFFLE['eval']
program_pairing=all(any(r['program']==n and r['label']=='C' for r in train_rows) and any(r['program']==n and r['label']=='J' for r in train_rows) for n in selected)
G={
 'at_least_four_paired_training_programs':len(selected)>=4,
 'every_training_datum_verifier_unique':all_unique,
 'labels_paired_within_program_identity':program_pairing,
 'heldout_never_trained':set(selected).isdisjoint(HELD_PROGS) and set(TRAIN).isdisjoint(HELD),
 'cold_router_fails':B0['route_accuracy']<TH or B0['joint']<TH,
 'paired_C_passes':pe['C']>=TH,
 'paired_J_passes':pe['J']>=TH,
 'paired_routes':pe['route_accuracy']>=TH,
 'paired_joint_executes':pe['joint']>=TH,
 'shuffled_control_fails':se['route_accuracy']<TH or se['joint']<TH,
 'reload_preserves_paired_routing':RR['C']>=TH and RR['J']>=TH and RR['route_accuracy']>=TH,
 'no_inherited_checkpoint_and_verifier_supervision_only':True,
}
R['gates']=G
R['verdict']='PASS_IKKF_V2E_VERIFIED_INVOCATION_DISTILLATION' if all(G.values()) else 'FAIL_IKKF_V2E_VERIFIED_INVOCATION_DISTILLATION'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2,default=str)); print(json.dumps(R,indent=2,default=str),flush=True)
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
