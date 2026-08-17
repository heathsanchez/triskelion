# V155 first-loss localization; frozen protocol
import os,json
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

BASE='Qwen/Qwen3.5-9B'; LR=2e-4; STEPS=6
OUT=Path('artifacts/v155_abc_first_loss'); OUT.mkdir(parents=True,exist_ok=True)
HELD=['violet','hidden','green','crimson','golden','silent','orange','secret']
TRAIN=['amber','quiet','silver','paper','winter','copper','scarlet','gentle','marble','rapid','bright','soft','blue','little','warm','clear']
SPECS=[
 {'seed':20260821,'p':'ka-','s':'-zu','l':'[','r':']','ab':'river://314f2f43-f332-432b-aae6-3a5976d647d7/weights/AB_seed20260821_step3'},
 {'seed':20260822,'p':'pv-','s':'-xx','l':'{','r':'}','ab':'river://8a28f049-7eef-45df-b3df-8097b287e8f6/weights/AB_seed20260822_step4'},
 {'seed':20260823,'p':'mo-','s':'-ri','l':'(','r':')','ab':'river://a82634ad-f87c-4fe5-9366-0c88d71c398d/weights/AB_seed20260823_step4'},
]
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0); assert client.health_check()
tok=AutoTokenizer.from_pretrained(BASE); EOS=tok.eos_token_id

def prompt(task,x): return f'Task: {task}\nInput: {x}\nOutput:'
def norm(s):
 t=s.strip(); return t.splitlines()[0].strip() if t else ''
def datum(task,x,y):
 a=tok(prompt(task,x),add_special_tokens=False)['input_ids']; b=tok(' '+y,add_special_tokens=False)['input_ids']+[EOS]; ids=a+b
 return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(a)-1)+[1.0]*(len(b)+1)}
def eval_direct(m,spec):
 A=lambda x:spec['p']+x; AB=lambda x:spec['p']+x+spec['s']; ABC=lambda x:spec['l']+spec['p']+x+spec['s']+spec['r']
 fns={'A':A,'AB':AB,'ABC':ABC}; out={}
 for task,fn in fns.items():
  gs=m.sample(prompts=[prompt(task,x) for x in HELD],max_tokens=24,temperature=0.0)
  texts=[norm(g[0].text) for g in gs]; out[task]={'hits':sum(t==fn(x) for x,t in zip(HELD,texts)),'texts':texts}
 return out
def eval_prefix(m,spec):
 probes=[]
 for x in HELD:
  probes += [('A_seed_to_AB',x,spec['p']+x,spec['s']),('AB_seed_to_ABC',x,spec['p']+x+spec['s'],spec['r']),('wrapped_A_seed',x,spec['l']+spec['p']+x,spec['s']+spec['r'])]
 gs=m.sample(prompts=[f'Input: {x}\nOutput: {seed}' for _,x,seed,_ in probes],max_tokens=12,temperature=0.0)
 rows=[]
 for (lab,x,seed,exp),g in zip(probes,gs):
  c=g[0].text; rows.append({'probe':lab,'input':x,'seed':seed,'continuation':c,'hit':exp in c})
 return {lab:sum(r['hit'] for r in rows if r['probe']==lab) for lab in ['A_seed_to_AB','AB_seed_to_ABC','wrapped_A_seed']},rows

R={'protocol':'restart from exact successful V10 AB checkpoints; replay identical ABC batch; save+probe every update; no adaptive stopping','replicates':[]}
for spec in SPECS:
 seed=spec['seed']; A=lambda x:spec['p']+x; AB=lambda x:spec['p']+x+spec['s']; ABC=lambda x:spec['l']+spec['p']+x+spec['s']+spec['r']
 batch=[datum('ABC',x,ABC(x)) for x in TRAIN[:12]]+[datum('A',x,A(x)) for x in TRAIN[12:14]]+[datum('AB',x,AB(x)) for x in TRAIN[14:16]]
 rep={'seed':seed,'source_ab':spec['ab'],'steps':[]}
 with client.session(project=f'v155-{seed}') as sess:
  m=sess.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=seed),checkpoint=spec['ab'])
  d0=eval_direct(m,spec); p0,pr0=eval_prefix(m,spec)
  rep['steps'].append({'step':0,'checkpoint':spec['ab'],'direct':d0,'prefix_hits':p0,'prefix_rows':pr0})
  for st in range(1,STEPS+1):
   fb=m.forward_backward(batch,loss_fn='cross_entropy'); m.optim_step(lr=LR,grad_clip_norm=1.0)
   ck=m.save_weights(f'V155_seed{seed}_ABC_step{st}',mode='training').path
   d=eval_direct(m,spec); ph,rows=eval_prefix(m,spec)
   rep['steps'].append({'step':st,'loss':float(fb.metrics['loss']),'checkpoint':ck,'direct':d,'prefix_hits':ph,'prefix_rows':rows})
   print(json.dumps({'seed':seed,'step':st,'A':d['A']['hits'],'AB':d['AB']['hits'],'ABC':d['ABC']['hits'],'prefix':ph,'checkpoint':ck}),flush=True)
 for task in ['A','AB']:
  base_hits=rep['steps'][0]['direct'][task]['hits']
  rep['first_loss_'+task]=next((z['step'] for z in rep['steps'][1:] if z['direct'][task]['hits']<base_hits),None)
 R['replicates'].append(rep)
json.dump(R,open(OUT/'RESULT.json','w'),indent=2)
print(json.dumps(R,indent=2),flush=True)
