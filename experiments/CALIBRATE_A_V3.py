import os,json,time
import river_client as river
from transformers import AutoTokenizer
BASE='Qwen/Qwen3.5-9B'; API=os.environ['RIVER_API_KEY']
client=river.Client(api_key=API,timeout=180.0); tok=AutoTokenizer.from_pretrained(BASE); EOS=tok.eos_token_id
train=['amber','quiet','silver','paper','winter','copper','scarlet','gentle','marble','rapid','bright','soft','blue','little','warm','clear']
held=['violet','hidden','green','crimson','golden','silent','orange','secret']
def A(s): return 'ka-'+s
def p(s): return f'Input: {s}\nOutput:'
def datum(s):
 a=tok(p(s),add_special_tokens=False)['input_ids']; b=tok(' '+A(s),add_special_tokens=False)['input_ids']+[EOS]; ids=a+b
 return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(a)-1)+[1.0]*(len(b)+1)}
def firstline(x):
 t=x.text.strip(); return t.splitlines()[0].strip() if t else ''
batch=[datum(s) for s in train]
with client.session(project='metalogic-calibrate-a-v3') as sess:
 m=sess.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=20260813))
 for step in range(1,9):
  fb=m.forward_backward(batch,loss_fn='cross_entropy'); m.optim_step(lr=2e-4,grad_clip_norm=1.0)
  groups=m.sample(prompts=[p(s) for s in held],max_tokens=12,temperature=0.0)
  outs=[firstline(g[0]) for g in groups]; acc=sum(o==A(s) for o,s in zip(outs,held))/len(held)
  print(json.dumps({'step':step,'loss':fb.metrics['loss'],'accuracy':acc,'examples':list(zip(held,outs))[:3]}),flush=True)
  if acc>=0.75:
   ck=m.save_weights('A_calibrated',mode='training'); print('CALIBRATED',step,ck.path,flush=True); break
