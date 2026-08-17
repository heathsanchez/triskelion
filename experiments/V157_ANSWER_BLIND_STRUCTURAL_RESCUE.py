import os,json
from pathlib import Path
import river_client as river

BASE='Qwen/Qwen3.5-9B'; OUT=Path('artifacts/v157_answer_blind_structural_rescue'); OUT.mkdir(parents=True,exist_ok=True)
HELD=['violet','hidden','green','crimson','golden','silent','orange','secret']
SPECS=[
 {'seed':20260821,'p':'ka-','s':'-zu','l':'[','r':']','step2':'river://96585daa-ab76-4d7e-94c7-a3a1c1a40b0e/weights/V155_seed20260821_ABC_step2'},
 {'seed':20260822,'p':'pv-','s':'-xx','l':'{','r':'}','step2':'river://95464919-e343-4995-bf4b-e8f7d701d8a8/weights/V155_seed20260822_ABC_step2'},
 {'seed':20260823,'p':'mo-','s':'-ri','l':'(','r':')','step2':'river://1c965c1a-5c1a-4371-8a15-0995064d64d1/weights/V155_seed20260823_ABC_step2'},
]
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0); assert client.health_check()

def prompt(task,x): return f'Task: {task}\nInput: {x}\nOutput:'
def norm(s):
 t=s.strip(); return t.splitlines()[0].strip() if t else ''
def targets(spec,x):
 A=spec['p']+x; AB=A+spec['s']; ABC=spec['l']+AB+spec['r']; return {'A':A,'AB':AB,'ABC':ABC}
def apply_controller(raw,task,grammar):
 y=raw
 if task in ('A','AB') and y.startswith(grammar['l']) and y.endswith(grammar['r']) and len(y)>=2:
  y=y[len(grammar['l']):len(y)-len(grammar['r'])]
 if task=='A' and y.endswith(grammar['s']):
  y=y[:-len(grammar['s'])]
 return y

R={'protocol':'answer-blind structural projection with permuted-grammar causal ablation; no weight updates','replicates':[]}
for i,spec in enumerate(SPECS):
 wrong=SPECS[(i+1)%len(SPECS)]
 rep={'seed':spec['seed'],'checkpoint':spec['step2'],'rows':[]}
 with client.session(project=f'v157-{spec["seed"]}') as sess:
  m=sess.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=spec['seed']),checkpoint=spec['step2'])
  for task in ['A','AB','ABC']:
   gs=m.sample(prompts=[prompt(task,x) for x in HELD],max_tokens=24,temperature=0.0)
   for x,g in zip(HELD,gs):
    raw=norm(g[0].text)
    controlled=apply_controller(raw,task,spec)
    ablated=apply_controller(raw,task,wrong)
    tgt=targets(spec,x)[task]
    rep['rows'].append({'task':task,'input':x,'raw':raw,'controlled':controlled,'ablated':ablated,
                        'raw_hit':raw==tgt,'controlled_hit':controlled==tgt,'ablated_hit':ablated==tgt})
 summary={}
 for task in ['A','AB','ABC']:
  rr=[r for r in rep['rows'] if r['task']==task]
  summary[task]={k:sum(r[k] for r in rr) for k in ['raw_hit','controlled_hit','ablated_hit']}
 rep['summary']=summary; R['replicates'].append(rep)
 print(json.dumps({'seed':spec['seed'],'summary':summary}),flush=True)
json.dump(R,open(OUT/'RESULT.json','w'),indent=2)
print(json.dumps(R,indent=2),flush=True)
