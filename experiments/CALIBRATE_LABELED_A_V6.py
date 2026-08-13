import os,json
import river_client as river
from transformers import AutoTokenizer
BASE='Qwen/Qwen3.5-9B'; rank=32; lr=2e-4; seed=20260813
train=['amber','quiet','silver','paper','winter','copper','scarlet','gentle','marble','rapid','bright','soft','blue','little','warm','clear']
held=['violet','hidden','green','crimson','golden','silent','orange','secret']
def A(s): return 'ka-'+s
def prompt(s): return f'Task: A\nInput: {s}\nOutput:'
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0); tok=AutoTokenizer.from_pretrained(BASE); EOS=tok.eos_token_id
def datum(s):
 a=tok(prompt(s),add_special_tokens=False)['input_ids']; b=tok(' '+A(s),add_special_tokens=False)['input_ids']+[EOS]; ids=a+b
 return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(a)-1)+[1.0]*(len(b)+1)}
def first(g):
 t=g[0].text.strip(); return t.splitlines()[0].strip() if t else ''
with client.session(project='ml-v6-cal-A') as s:
 m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=rank,seed=seed)); batch=[datum(x) for x in train]
 for st in range(1,7):
  fb=m.forward_backward(batch,loss_fn='cross_entropy'); m.optim_step(lr=lr,grad_clip_norm=1.0)
  gs=m.sample(prompts=[prompt(x) for x in held],max_tokens=18,temperature=0.0); outs=[first(g) for g in gs]; acc=sum(o==A(x) for x,o in zip(held,outs))/len(held)
  print(json.dumps({'step':st,'loss':float(fb.metrics['loss']),'accuracy':acc,'examples':list(zip(held[:3],outs[:3]))}),flush=True)
  if acc>=1.0:
   ck=m.save_weights('A_labeled_calibrated',mode='training'); print('CALIBRATED',st,ck.path,flush=True); break
