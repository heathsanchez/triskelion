import os,json
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

BASE='Qwen/Qwen3.5-9B'; SEED=20260903; RANK=32
CHECKPOINT='river://b3e34bc8-7c23-4294-b59e-91218a2cf239/weights/v69_parents_final'
OUT=Path('artifacts/v69_parent_diagnostic'); OUT.mkdir(parents=True,exist_ok=True)
ROUTES={
'Q54':['Weak-scope parenthesis observation has no negative prefix.','Current parenthesis evidence preserves the coarse equivalence class.'],
'Q57':['Weak-scope palindrome case has no complete carry overflow.','Current palindrome observation preserves the coarse equivalence class.'],
'Q66':['Weak-scope LIS observation preserves the coarse equivalence class.','Current LIS evidence does not reveal the state-regression distinction.']}
VALID=list(ROUTES)
def prompt(text): return 'Route this observation to the correct verified Lawbook node. Return ONLY one node id.\nObservation: '+text+'\nNode:'
def frozen_parse(text):
 s=text.strip().splitlines()[0].strip() if text.strip() else ''; s=s.replace('`','').strip(); return s.split()[0].strip('.,;:') if s else ''
def valid_parse(text):
 clean=text.replace('`',' ').replace('\n',' ')
 hits=[]
 for token in clean.replace(':',' ').replace(',',' ').replace('.',' ').replace(';',' ').split():
  t=token.strip()
  if t in VALID: hits.append(t)
 return hits[-1] if hits else ''
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0); assert client.health_check()
rows=[]
with client.session(project='ml-v69-parent-diagnostic') as s:
 m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=RANK,seed=SEED),checkpoint=CHECKPOINT)
 prompts=[]; truth=[]
 for lab,texts in ROUTES.items():
  for text in texts: prompts.append(prompt(text)); truth.append(lab)
 for budget in [8,32,64]:
  gs=m.sample(prompts=prompts,max_tokens=budget,temperature=0.0)
  raw=[g[0].text for g in gs]
  fp=[frozen_parse(x) for x in raw]; vp=[valid_parse(x) for x in raw]
  rows.append({'budget':budget,'truth':truth,'raw':raw,'frozen':fp,'valid':vp,'frozen_acc':sum(a==b for a,b in zip(fp,truth))/len(truth),'valid_acc':sum(a==b for a,b in zip(vp,truth))/len(truth)})
R={'checkpoint':CHECKPOINT,'no_gradients':True,'rows':rows}
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2),flush=True)
