import os,json,hashlib,time
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

P={"name":"METALOGIC_WAKE_SLEEP_STAIRCASE_V6","date":"2026-08-13","seed":20260813,"base":"Qwen/Qwen3.5-9B","rank":32,"lr":2e-4,"A_steps":4,"successor_steps":4,"threshold":0.75,"claim_boundary":"Synthetic cross-session neural inheritance test with calibrated initial acquisition, distinct task contexts, matched wrong-lineage controls, no ancestor rehearsal, and explicit pre/post retention checks. Not external-task or open-ended lifelong learning evidence."}
OUT=Path('artifacts/wake_sleep_staircase_v6'); OUT.mkdir(parents=True,exist_ok=True)
PH=hashlib.sha256(json.dumps(P,sort_keys=True,separators=(',',':')).encode()).hexdigest(); (OUT/'PRECOMMIT.json').write_text(json.dumps({'protocol_sha256':PH,'protocol':P},indent=2))
def log(e,**kw):
 r={'t':time.time(),'event':e,**kw}; print(json.dumps(r),flush=True); open(OUT/'TRACE.jsonl','a').write(json.dumps(r)+'\n')
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0); assert client.health_check()
BASE=P['base']; assert BASE in list(client.get_capabilities())
tok=AutoTokenizer.from_pretrained(BASE); EOS=tok.eos_token_id
train=['amber','quiet','silver','paper','winter','copper','scarlet','gentle','marble','rapid','bright','soft','blue','little','warm','clear']
held=['violet','hidden','green','crimson','golden','silent','orange','secret']
def A(s): return 'ka-'+s
def AB(s): return 'ka-'+s+'-zu'
def ABC(s): return '[ka-'+s+'-zu]'
def W1(s): return s.upper()
def W2(s): return 'xx-'+s
def prompt(task,s): return f'Task: {task}\nInput: {s}\nOutput:'
def datum(task,s,fn):
 a=tok(prompt(task,s),add_special_tokens=False)['input_ids']; b=tok(' '+fn(s),add_special_tokens=False)['input_ids']+[EOS]; ids=a+b
 return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(a)-1)+[1.0]*(len(b)+1)}
def firstline(x):
 t=x.text.strip(); return t.splitlines()[0].strip() if t else ''
def evaluate(m,task,fn,tag):
 gs=m.sample(prompts=[prompt(task,s) for s in held],max_tokens=18,temperature=0.0)
 outs=[firstline(g[0]) for g in gs]; rows=[{'input':s,'gold':fn(s),'out':o,'ok':o==fn(s)} for s,o in zip(held,outs)]; acc=sum(r['ok'] for r in rows)/len(rows); log('eval',tag=tag,task=task,accuracy=acc,examples=rows[:3]); return acc
def train_curve(m,task,fn,tag,steps):
 batch=[datum(task,s,fn) for s in train]; curve=[]
 for st in range(1,steps+1):
  log('fb_before',tag=tag,step=st); fb=m.forward_backward(batch,loss_fn='cross_entropy'); m.optim_step(lr=P['lr'],grad_clip_norm=1.0); acc=evaluate(m,task,fn,f'{tag}_step{st}'); curve.append({'step':st,'loss':float(fb.metrics['loss']),'accuracy':acc}); log('fb_after',tag=tag,step=st,loss=float(fb.metrics['loss']),accuracy=acc)
 return curve
def mk(sess,ck=None):
 kw={'base_model':BASE,'lora':river.LoraConfig(rank=P['rank'],seed=P['seed'])}
 if ck: kw['checkpoint']=ck
 return sess.create_model(**kw)
def dose(pre,curve):
 if pre>=P['threshold']: return 0
 for x in curve:
  if x['accuracy']>=P['threshold']: return x['step']
 return None
def better(a,b): return a is not None and (b is None or a<b)
R={'protocol_sha256':PH,'base':BASE,'stages':{},'gates':{}}
# Generation A: calibrated 4 steps; wrong ancestor matched 4 steps.
with client.session(project='ml-v6-A') as s:
 lin=mk(s); w1=mk(s)
 cA=train_curve(lin,'A',A,'A_lineage',P['A_steps']); cW1=train_curve(w1,'W1',W1,'W1_wrong',P['A_steps'])
 aacc=evaluate(lin,'A',A,'A_final'); wacc=evaluate(w1,'W1',W1,'W1_final')
 ckA=lin.save_weights('A_training',mode='training'); ckW1=w1.save_weights('W1_training',mode='training')
 R['stages']['A']={'curve':cA,'heldout':aacc,'wrong_curve':cW1,'wrong_heldout':wacc,'checkpoint':ckA.path,'wrong_checkpoint':ckW1.path}; log('sleep_A',checkpoint=ckA.path)
# Generation AB: verify A survived reload before any new training; no A rehearsal thereafter.
with client.session(project='ml-v6-AB') as s:
 lin=mk(s,ckA.path); cold=mk(s); wrong=mk(s,ckW1.path); wrongchain=mk(s,ckW1.path)
 inherited_A_pre=evaluate(lin,'A',A,'A_after_reload_before_AB')
 pre={'lineage':evaluate(lin,'AB',AB,'AB_lineage_pre'),'cold':evaluate(cold,'AB',AB,'AB_cold_pre'),'wrong':evaluate(wrong,'AB',AB,'AB_wrong_pre')}
 curves={'lineage':train_curve(lin,'AB',AB,'AB_lineage',P['successor_steps']),'cold':train_curve(cold,'AB',AB,'AB_cold',P['successor_steps']),'wrong':train_curve(wrong,'AB',AB,'AB_wrong',P['successor_steps'])}
 retention_after_AB={'A':evaluate(lin,'A',A,'retention_A_after_AB'),'AB':evaluate(lin,'AB',AB,'retention_AB_after_AB')}
 _=train_curve(wrongchain,'W2',W2,'W2_wrong_chain',P['successor_steps'])
 ckAB=lin.save_weights('AB_training',mode='training'); ckW12=wrongchain.save_weights('W1W2_training',mode='training')
 R['stages']['AB']={'inherited_A_pre':inherited_A_pre,'pre':pre,'curves':curves,'retention':retention_after_AB,'checkpoint':ckAB.path,'wrong_chain_checkpoint':ckW12.path}; log('sleep_AB',checkpoint=ckAB.path)
# Generation ABC: verify A and AB survived reload before any C training; no ancestor rehearsal.
with client.session(project='ml-v6-ABC') as s:
 lin=mk(s,ckAB.path); cold=mk(s); wrong=mk(s,ckW12.path)
 inherited_before_ABC={'A':evaluate(lin,'A',A,'A_after_reload_before_ABC'),'AB':evaluate(lin,'AB',AB,'AB_after_reload_before_ABC')}
 pre={'lineage':evaluate(lin,'ABC',ABC,'ABC_lineage_pre'),'cold':evaluate(cold,'ABC',ABC,'ABC_cold_pre'),'wrong':evaluate(wrong,'ABC',ABC,'ABC_wrong_pre')}
 curves={'lineage':train_curve(lin,'ABC',ABC,'ABC_lineage',P['successor_steps']),'cold':train_curve(cold,'ABC',ABC,'ABC_cold',P['successor_steps']),'wrong':train_curve(wrong,'ABC',ABC,'ABC_wrong',P['successor_steps'])}
 retention={'A':evaluate(lin,'A',A,'retention_A_final'),'AB':evaluate(lin,'AB',AB,'retention_AB_final'),'ABC':evaluate(lin,'ABC',ABC,'retention_ABC_final')}
 ckABC=lin.save_weights('ABC_training',mode='training'); R['stages']['ABC']={'inherited_before_ABC':inherited_before_ABC,'pre':pre,'curves':curves,'retention':retention,'checkpoint':ckABC.path}
def metrics(stage):
 d=R['stages'][stage]; return {arm:{'dose':dose(d['pre'][arm],d['curves'][arm]),'auc':d['pre'][arm]+sum(x['accuracy'] for x in d['curves'][arm])} for arm in ['lineage','cold','wrong']}
MAB=metrics('AB'); MABC=metrics('ABC'); R['metrics']={'AB':MAB,'ABC':MABC}
R['gates']={
 'G1_A_acquired':R['stages']['A']['heldout']>=1.0,
 'G2_A_survives_sleep_reload':R['stages']['AB']['inherited_A_pre']>=P['threshold'],
 'G3_AB_lineage_faster_cold':better(MAB['lineage']['dose'],MAB['cold']['dose']),
 'G4_AB_lineage_faster_wrong':better(MAB['lineage']['dose'],MAB['wrong']['dose']),
 'G5_A_retained_after_AB':R['stages']['AB']['retention']['A']>=P['threshold'],
 'G6_AB_acquired':R['stages']['AB']['retention']['AB']>=P['threshold'],
 'G7_A_AB_survive_second_reload':R['stages']['ABC']['inherited_before_ABC']['A']>=P['threshold'] and R['stages']['ABC']['inherited_before_ABC']['AB']>=P['threshold'],
 'G8_ABC_lineage_faster_cold':better(MABC['lineage']['dose'],MABC['cold']['dose']),
 'G9_ABC_lineage_faster_wrong':better(MABC['lineage']['dose'],MABC['wrong']['dose']),
 'G10_all_three_retained_final':all(R['stages']['ABC']['retention'][k]>=P['threshold'] for k in ['A','AB','ABC'])}
R['verdict']='PASS_WAKE_SLEEP_STAIRCASE_V6' if all(R['gates'].values()) else 'FAIL_OR_MIXED_WAKE_SLEEP_STAIRCASE_V6'
(OUT/'FINAL_RESULT.json').write_text(json.dumps(R,indent=2)); log('final',verdict=R['verdict'],gates=R['gates']); print(json.dumps(R,indent=2),flush=True)
