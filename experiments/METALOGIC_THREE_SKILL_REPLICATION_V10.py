import os,json
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

BASE='Qwen/Qwen3.5-9B'; LR=2e-4; TH=0.75; MAX_STEPS=6
OUT=Path('artifacts/three_skill_v10'); OUT.mkdir(parents=True,exist_ok=True)
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0); assert client.health_check()
tok=AutoTokenizer.from_pretrained(BASE); EOS=tok.eos_token_id
train=['amber','quiet','silver','paper','winter','copper','scarlet','gentle','marble','rapid','bright','soft','blue','little','warm','clear']
held=['violet','hidden','green','crimson','golden','silent','orange','secret']
SPECS=[
 {'seed':20260821,'p':'ka-','s':'-zu','l':'[','r':']'},
 {'seed':20260822,'p':'pv-','s':'-xx','l':'{','r':'}'},
 {'seed':20260823,'p':'mo-','s':'-ri','l':'(','r':')'},
]

def prompt(task,s): return f'Task: {task}\nInput: {s}\nOutput:'
def datum(task,s,fn):
    a=tok(prompt(task,s),add_special_tokens=False)['input_ids']; b=tok(' '+fn(s),add_special_tokens=False)['input_ids']+[EOS]; ids=a+b
    return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(a)-1)+[1.0]*(len(b)+1)}
def ev(m,task,fn):
    gs=m.sample(prompts=[prompt(task,s) for s in held],max_tokens=20,temperature=0.0)
    outs=[g[0].text.strip().splitlines()[0].strip() if g[0].text.strip() else '' for g in gs]
    return sum(o==fn(s) for s,o in zip(held,outs))/len(held)

def stage(sess,m,tag,batch,checks,seed):
    curve=[]; ck=None
    for st in range(1,MAX_STEPS+1):
        fb=m.forward_backward(batch,loss_fn='cross_entropy'); m.optim_step(lr=LR,grad_clip_norm=1.0)
        scores={name:ev(m,name,fn) for name,fn in checks}
        row={'step':st,'loss':float(fb.metrics['loss']),**scores,'joint':min(scores.values())}; curve.append(row)
        print(json.dumps({'seed':seed,'stage':tag,**row}),flush=True)
        if all(v>=TH for v in scores.values()):
            ck=m.save_weights(f'{tag}_seed{seed}_step{st}',mode='training').path
            return curve,ck,st
    ck=m.save_weights(f'{tag}_seed{seed}_final',mode='training').path
    return curve,ck,None

def reload_scores(ck,checks,seed,tag):
    with client.session(project=f'ml-v10-{seed}-{tag}-reload') as sess:
        m=sess.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=seed),checkpoint=ck)
        return {name:ev(m,name,fn) for name,fn in checks}

R={'replicates':[]}
for spec in SPECS:
    seed=spec['seed']; p=spec['p']; suf=spec['s']; L=spec['l']; RR=spec['r']
    A=lambda x,p=p:p+x
    AB=lambda x,p=p,suf=suf:p+x+suf
    ABC=lambda x,p=p,suf=suf,L=L,RR=RR:L+p+x+suf+RR
    rep={'seed':seed,'spec':spec,'stages':{}}
    # A from fresh model
    with client.session(project=f'ml-v10-{seed}-A') as sess:
        m=sess.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=seed))
        batch=[datum('A',x,A) for x in train]
        curve,ckA,doseA=stage(sess,m,'A',batch,[('A',A)],seed)
    postA=reload_scores(ckA,[('A',A)],seed,'A')
    rep['stages']['A']={'curve':curve,'dose':doseA,'checkpoint':ckA,'post_reload':postA}
    if doseA is None or postA['A']<TH:
        rep['pass']=False; rep['failure']='A'; R['replicates'].append(rep); continue
    # AB: 12 new + 4 protected A replay (25%)
    with client.session(project=f'ml-v10-{seed}-AB') as sess:
        m=sess.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=seed),checkpoint=ckA)
        batch=[datum('AB',x,AB) for x in train[:12]]+[datum('A',x,A) for x in train[12:16]]
        curve,ckAB,doseAB=stage(sess,m,'AB',batch,[('A',A),('AB',AB)],seed)
    postAB=reload_scores(ckAB,[('A',A),('AB',AB)],seed,'AB')
    rep['stages']['AB']={'curve':curve,'dose':doseAB,'checkpoint':ckAB,'post_reload':postAB}
    if doseAB is None or min(postAB.values())<TH:
        rep['pass']=False; rep['failure']='AB'; R['replicates'].append(rep); continue
    # ABC: 12 new + 2 A + 2 AB replay (25%)
    with client.session(project=f'ml-v10-{seed}-ABC') as sess:
        m=sess.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=seed),checkpoint=ckAB)
        batch=[datum('ABC',x,ABC) for x in train[:12]]+[datum('A',x,A) for x in train[12:14]]+[datum('AB',x,AB) for x in train[14:16]]
        curve,ckABC,doseABC=stage(sess,m,'ABC',batch,[('A',A),('AB',AB),('ABC',ABC)],seed)
    postABC=reload_scores(ckABC,[('A',A),('AB',AB),('ABC',ABC)],seed,'ABC')
    rep['stages']['ABC']={'curve':curve,'dose':doseABC,'checkpoint':ckABC,'post_reload':postABC}
    rep['pass']=doseABC is not None and min(postABC.values())>=TH
    rep['failure']=None if rep['pass'] else 'ABC'
    R['replicates'].append(rep)

R['passes']=sum(r.get('pass',False) for r in R['replicates'])
R['verdict']='PASS_REPLICATED_THREE_SKILL' if R['passes']==len(SPECS) else 'MIXED_REPLICATION'
print(json.dumps(R,indent=2),flush=True)
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2))
