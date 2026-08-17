import os,json
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

BASE='Qwen/Qwen3.5-9B'; OUT=Path('artifacts/v156_first_loss_control_rescue'); OUT.mkdir(parents=True,exist_ok=True)
HELD=['violet','hidden','green','crimson','golden','silent','orange','secret']
SPECS=[
 {'seed':20260821,'p':'ka-','s':'-zu','l':'[','r':']','step1':'river://96585daa-ab76-4d7e-94c7-a3a1c1a40b0e/weights/V155_seed20260821_ABC_step1','step2':'river://96585daa-ab76-4d7e-94c7-a3a1c1a40b0e/weights/V155_seed20260821_ABC_step2'},
 {'seed':20260822,'p':'pv-','s':'-xx','l':'{','r':'}','step1':'river://95464919-e343-4995-bf4b-e8f7d701d8a8/weights/V155_seed20260822_ABC_step1','step2':'river://95464919-e343-4995-bf4b-e8f7d701d8a8/weights/V155_seed20260822_ABC_step2'},
 {'seed':20260823,'p':'mo-','s':'-ri','l':'(','r':')','step1':'river://1c965c1a-5c1a-4371-8a15-0995064d64d1/weights/V155_seed20260823_ABC_step1','step2':'river://1c965c1a-5c1a-4371-8a15-0995064d64d1/weights/V155_seed20260823_ABC_step2'},
]
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0); assert client.health_check()
tok=AutoTokenizer.from_pretrained(BASE)

def prompt(task,x): return f'Task: {task}\nInput: {x}\nOutput:'
def norm(s):
 t=s.strip(); return t.splitlines()[0].strip() if t else ''

def targets(spec,x):
 A=spec['p']+x; AB=A+spec['s']; ABC=spec['l']+AB+spec['r']; return {'A':A,'AB':AB,'ABC':ABC}

def probe(m,spec):
 rows=[]
 for task in ['A','AB','ABC']:
  gs=m.sample(prompts=[prompt(task,x) for x in HELD],max_tokens=24,temperature=0.0)
  for x,g in zip(HELD,gs):
   raw=norm(g[0].text); tgt=targets(spec,x)[task]
   # termination-only controller: may stop generation at the target boundary, but may not alter generated content.
   term = raw[:len(tgt)] if raw.startswith(tgt) else raw
   # state-projection controller: may select an already-emitted target state from a longer trajectory, but may not synthesize or edit its characters.
   j=raw.find(tgt); proj=tgt if j>=0 else raw
   rows.append({'task':task,'input':x,'target':tgt,'raw':raw,
                'raw_hit':raw==tgt,
                'target_is_prefix':raw.startswith(tgt),
                'target_is_substring':tgt in raw,
                'termination_only':term,'termination_hit':term==tgt,
                'projection':proj,'projection_hit':proj==tgt})
 out={}
 for task in ['A','AB','ABC']:
  rr=[r for r in rows if r['task']==task]
  out[task]={k:sum(r[k] for r in rr) for k in ['raw_hit','target_is_prefix','target_is_substring','termination_hit','projection_hit']}
 return out,rows

R={'protocol':{
 'claim':'At frozen V155 first-loss checkpoints, test whether external control can recover earlier states without any weight update.',
 'termination_only':'truncate only when the model itself emits the exact target as a prefix; controller cannot change content',
 'state_projection':'select exact target only if it already occurs contiguously in model output; controller cannot synthesize/edit characters',
 'success_standard':'A and/or AB improve from raw under frozen weights; stronger if termination-only succeeds; projection-only indicates state-selection rather than content deletion',
 'held_out':HELD},'replicates':[]}
for spec in SPECS:
 rep={'seed':spec['seed'],'checkpoints':{}}
 for label in ['step1','step2']:
  ck=spec[label]
  with client.session(project=f'v156-{spec["seed"]}-{label}') as sess:
   m=sess.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=spec['seed']),checkpoint=ck)
   summary,rows=probe(m,spec)
  rep['checkpoints'][label]={'checkpoint':ck,'summary':summary,'rows':rows}
  print(json.dumps({'seed':spec['seed'],'checkpoint':label,'summary':summary}),flush=True)
 R['replicates'].append(rep)
json.dump(R,open(OUT/'RESULT.json','w'),indent=2)
print(json.dumps(R,indent=2),flush=True)
