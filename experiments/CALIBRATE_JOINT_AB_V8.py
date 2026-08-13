import os,json,time
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer
BASE='Qwen/Qwen3.5-9B'; SEED=20260813; LR=2e-4; TH=0.75; STEPS=4
CK_A='river://4e63854c-1980-486b-ba72-4b45ed0c5e96/weights/A_training'
OUT=Path('artifacts/joint_ab_v8'); OUT.mkdir(parents=True,exist_ok=True)
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0); assert client.health_check(); tok=AutoTokenizer.from_pretrained(BASE); EOS=tok.eos_token_id
train=['amber','quiet','silver','paper','winter','copper','scarlet','gentle','marble','rapid','bright','soft','blue','little','warm','clear']; held=['violet','hidden','green','crimson','golden','silent','orange','secret']
def A(s): return 'ka-'+s
def AB(s): return 'ka-'+s+'-zu'
def prompt(task,s): return f'Task: {task}\nInput: {s}\nOutput:'
def datum(task,s,fn):
 a=tok(prompt(task,s),add_special_tokens=False)['input_ids']; b=tok(' '+fn(s),add_special_tokens=False)['input_ids']+[EOS]; ids=a+b
 return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(a)-1)+[1.0]*(len(b)+1)}
def ev(m,task,fn):
 gs=m.sample(prompts=[prompt(task,s) for s in held],max_tokens=18,temperature=0.0); outs=[g[0].text.strip().splitlines()[0].strip() if g[0].text.strip() else '' for g in gs]; return sum(o==fn(s) for s,o in zip(held,outs))/len(held)
R={'source':CK_A,'arms':{}}
for replay in [4,8,12]:
 with client.session(project=f'ml-v8-r{replay}') as sess:
  m=sess.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=CK_A)
  newn=16-replay; batch=[datum('AB',x,AB) for x in train[:newn]]+[datum('A',x,A) for x in train[newn:]]
  curve=[]
  for st in range(1,STEPS+1):
   fb=m.forward_backward(batch,loss_fn='cross_entropy'); m.optim_step(lr=LR,grad_clip_norm=1.0); a=ev(m,'A',A); ab=ev(m,'AB',AB); row={'step':st,'loss':float(fb.metrics['loss']),'A':a,'AB':ab,'joint':min(a,ab)}; curve.append(row); print(json.dumps({'replay':replay,**row}),flush=True)
  best=max(curve,key=lambda x:(x['joint'],x['AB'],x['A'])); ck=m.save_weights(f'joint_AB_r{replay}',mode='training'); R['arms'][str(replay)]={'replay_fraction':replay/16,'curve':curve,'best':best,'checkpoint':ck.path,'pass_any':any(x['A']>=TH and x['AB']>=TH for x in curve)}
passes=[(int(k),v) for k,v in R['arms'].items() if v['pass_any']]
R['selected']=min(passes,key=lambda kv:kv[0])[0] if passes else None; R['verdict']='PASS_JOINT_REGION_FOUND' if R['selected'] is not None else 'NO_JOINT_REGION_IN_GRID'; print(json.dumps(R,indent=2),flush=True); (OUT/'RESULT.json').write_text(json.dumps(R,indent=2))
