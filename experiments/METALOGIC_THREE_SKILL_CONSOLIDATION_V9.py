import os,json
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

BASE='Qwen/Qwen3.5-9B'; SEED=20260813; LR=2e-4; TH=0.75; STEPS=4
CK_AB='river://d7cbfd59-3486-4e95-b03c-52fa17ce17e2/weights/joint_AB_r12'
OUT=Path('artifacts/three_skill_v9'); OUT.mkdir(parents=True,exist_ok=True)
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0); assert client.health_check()
tok=AutoTokenizer.from_pretrained(BASE); EOS=tok.eos_token_id
train=['amber','quiet','silver','paper','winter','copper','scarlet','gentle','marble','rapid','bright','soft','blue','little','warm','clear']
held=['violet','hidden','green','crimson','golden','silent','orange','secret']

def A(s): return 'ka-'+s
def AB(s): return 'ka-'+s+'-zu'
def ABC(s): return '[ka-'+s+'-zu]'
def prompt(task,s): return f'Task: {task}\nInput: {s}\nOutput:'
def datum(task,s,fn):
    a=tok(prompt(task,s),add_special_tokens=False)['input_ids']; b=tok(' '+fn(s),add_special_tokens=False)['input_ids']+[EOS]; ids=a+b
    return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(a)-1)+[1.0]*(len(b)+1)}
def ev(m,task,fn):
    gs=m.sample(prompts=[prompt(task,s) for s in held],max_tokens=20,temperature=0.0)
    outs=[g[0].text.strip().splitlines()[0].strip() if g[0].text.strip() else '' for g in gs]
    return sum(o==fn(s) for s,o in zip(held,outs))/len(held)

def make_batch(replay_total):
    # fixed total batch size 16; replay is split as evenly as possible over A and AB
    newn=16-replay_total
    ra=replay_total//2; rab=replay_total-ra
    xs=list(train)
    batch=[datum('ABC',x,ABC) for x in xs[:newn]]
    batch += [datum('A',x,A) for x in xs[newn:newn+ra]]
    batch += [datum('AB',x,AB) for x in xs[newn+ra:newn+ra+rab]]
    return batch

R={'source':CK_AB,'arms':{}}
for replay in [0,4,8,12]:
    project=f'ml-v9-r{replay}'
    ck_path=None; curve=[]; passed=False
    with client.session(project=project) as sess:
        m=sess.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=CK_AB)
        pre={'A':ev(m,'A',A),'AB':ev(m,'AB',AB),'ABC':ev(m,'ABC',ABC)}
        print(json.dumps({'replay':replay,'pre':pre}),flush=True)
        batch=make_batch(replay)
        for st in range(1,STEPS+1):
            fb=m.forward_backward(batch,loss_fn='cross_entropy'); m.optim_step(lr=LR,grad_clip_norm=1.0)
            a=ev(m,'A',A); ab=ev(m,'AB',AB); abc=ev(m,'ABC',ABC); joint=min(a,ab,abc)
            row={'step':st,'loss':float(fb.metrics['loss']),'A':a,'AB':ab,'ABC':abc,'joint':joint}
            curve.append(row); print(json.dumps({'replay':replay,**row}),flush=True)
            if a>=TH and ab>=TH and abc>=TH:
                ck=m.save_weights(f'joint_ABC_r{replay}_step{st}',mode='training'); ck_path=ck.path; passed=True
                print(json.dumps({'replay':replay,'protected_stop':st,'checkpoint':ck_path}),flush=True)
                break
        if not passed:
            ck=m.save_weights(f'joint_ABC_r{replay}_final',mode='training'); ck_path=ck.path
    # true wake/sleep boundary: close then reload and re-evaluate
    with client.session(project=project+'-reload') as sess2:
        mr=sess2.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=ck_path)
        post={'A':ev(mr,'A',A),'AB':ev(mr,'AB',AB),'ABC':ev(mr,'ABC',ABC)}
    R['arms'][str(replay)]={'replay_fraction':replay/16,'curve':curve,'checkpoint':ck_path,'passed_before_reload':passed,'post_reload':post,'passed_after_reload':all(v>=TH for v in post.values())}

passes=[(int(k),v) for k,v in R['arms'].items() if v['passed_after_reload']]
R['selected']=min(passes,key=lambda kv:kv[0])[0] if passes else None
R['verdict']='PASS_THREE_SKILL_WAKE_SLEEP' if R['selected'] is not None else 'NO_THREE_SKILL_STABLE_REGION'
print(json.dumps(R,indent=2),flush=True)
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2))
