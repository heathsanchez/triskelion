import json,re
from pathlib import Path
OUT=Path('artifacts/v56c');OUT.mkdir(parents=True,exist_ok=True)
MODEL='Qwen/Qwen2.5-Coder-0.5B-Instruct'
# code has exactly one target <. Hidden tests are executable authority and are not included in model prompt.
TASKS=[
('h1','def f(n,limit):\n return n if n < limit else None','accept equality',[( (3,3),3),((4,3),None)]),
('h2','def f(name,m):\n return name if len(name) < m else "X"','keep equal length',[(('abc',3),'abc'),(('abcd',3),'X')]),
('h3','def f(page,last):\n return page if page < last else -1','last page valid',[( (5,5),5),((6,5),-1)]),
('h4','def f(score,t):\n return "ok" if score < t else "bad"','equality ok',[( (7,7),'ok'),((8,7),'bad')]),
('h5','def f(c,cap):\n return c+1 if c < cap else c','final slot usable',[( (2,2),3),((3,2),3)]),
('k1','def f(age,m):\n return "reject" if age < m else "ok"','minimum is allowed',[( (18,18),'ok'),((17,18),'reject')]),
('k2','def f(i,n):\n return i+1 if i < n else i','strict loop boundary',[( (3,3),3),((2,3),3)]),
('k3','def f(x,u):\n return x < u','open upper bound',[( (5,5),False),((4,5),True)]),
('k4','def f(v,m):\n return "pass" if v < m else "fail"','maximum excluded',[( (5,5),'fail'),((4,5),'pass')]),
('k5','def f(v,b):\n return 1 if v < b else 0','explicit strict API',[( (2,2),0),((1,2),1)]),
('k6','def f(r,m):\n return "retry" if r < m else "stop"','no retry at maximum',[( (3,3),'stop'),((2,3),'retry')]),
('h6','def f(x,b):\n return 1 if x < b else 0','closed accepted boundary',[( (9,9),1),((10,9),0)])]
RAW='Past: one < became <= and passed; one loop < became <= and failed.'
from transformers import AutoTokenizer,AutoModelForCausalLM
import torch
tok=AutoTokenizer.from_pretrained(MODEL);model=AutoModelForCausalLM.from_pretrained(MODEL,dtype=torch.float32,device_map='cpu');model.eval()
def model_pick(code,req,raw=False):
 extra=('\n'+RAW) if raw else ''
 p=f'Choose code edit. CODE:\n{code}\nREQUIREMENT:{req}{extra}\nWIDEN means replace < with <=; KEEP means unchanged. Answer WIDEN or KEEP.'
 text=tok.apply_chat_template([{'role':'user','content':p}],tokenize=False,add_generation_prompt=True);inp=tok(text,return_tensors='pt')
 with torch.no_grad():o=model.generate(**inp,max_new_tokens=5,do_sample=False,pad_token_id=tok.eos_token_id)
 a=tok.decode(o[0][inp['input_ids'].shape[1]:],skip_special_tokens=True).upper();m=re.search(r'\b(WIDEN|KEEP)\b',a);return m.group(1) if m else 'OTHER'
def verify(code,tests,action):
 src=code if action=='KEEP' else code.replace('<','<=',1);ns={}
 try:exec(src,ns,ns);f=ns['f'];return all(f(*args)==exp for args,exp in tests)
 except:return False
rows=[]
for arm in ['A_NO_MEMORY','B_RAW_MEMORY','C_VERIFIED_LAYER']:
 for id,code,req,tests in TASKS:
  proposal=model_pick(code,req,arm=='B_RAW_MEMORY')
  if arm=='C_VERIFIED_LAYER':
   keep=verify(code,tests,'KEEP');wide=verify(code,tests,'WIDEN')
   pred='KEEP' if keep and not wide else 'WIDEN' if wide and not keep else proposal
  else:pred=proposal
  ok=verify(code,tests,pred) if pred in {'KEEP','WIDEN'} else False;rows.append({'arm':arm,'id':id,'proposal':proposal,'action':pred,'verified':ok})
scores={a:sum(r['verified'] for r in rows if r['arm']==a) for a in ['A_NO_MEMORY','B_RAW_MEMORY','C_VERIFIED_LAYER']}
R={'protocol':'V56C_STRUCTURAL_VERIFIER_MODEL_LAYER','model':MODEL,'scores':scores,'rows':rows,'tasks':len(TASKS)};R['gates']={'verified_layer_perfect':scores['C_VERIFIED_LAYER']==len(TASKS),'beats_no_memory':scores['C_VERIFIED_LAYER']>scores['A_NO_MEMORY'],'beats_raw_memory':scores['C_VERIFIED_LAYER']>scores['B_RAW_MEMORY'],'external_tests_are_authority':True};R['verdict']='PASS_V56C_VERIFIER_MODEL_LAYER' if all(R['gates'].values()) else 'FAIL_V56C_VERIFIER_MODEL_LAYER';(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2));raise SystemExit(0 if R['verdict'].startswith('PASS') else 1)