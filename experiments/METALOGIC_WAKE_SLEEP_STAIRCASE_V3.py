import os,json,hashlib,time
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

P={"name":"METALOGIC_WAKE_SLEEP_STAIRCASE_V3","date":"2026-08-13","seed":20260813,"base":"Qwen/Qwen3.5-9B","rank":32,"lr":2e-4,"steps_per_stage":3,"threshold":0.75,"train_n":16,"heldout_n":8,"claim_boundary":"Synthetic confirmatory test of cross-session neural inheritance causing faster acquisition of nested successor capabilities; not external-task or open-ended lifelong learning evidence."}
OUT=Path('artifacts/wake_sleep_staircase_v3'); OUT.mkdir(parents=True,exist_ok=True)
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
def prompt(s): return f'Input: {s}\nOutput:'
def datum(s,fn):
 a=tok(prompt(s),add_special_tokens=False)['input_ids']; b=tok(' '+fn(s),add_special_tokens=False)['input_ids']+[EOS]; ids=a+b
 return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(a)-1)+[1.0]*(len(b)+1)}
def firstline(x):
 t=x.text.strip(); return t.splitlines()[0].strip() if t else ''
def evaluate(m,fn,tag):
 gs=m.sample(prompts=[prompt(s) for s in held],max_tokens=16,temperature=0.0)
 outs=[firstline(g[0]) for g in gs]; rows=[{'input':s,'gold':fn(s),'out':o,'ok':o==fn(s)} for s,o in zip(held,outs)]; acc=sum(r['ok'] for r in rows)/len(rows); log('eval',tag=tag,accuracy=acc,examples=rows[:3]); return acc
def train_curve(m,fn,tag):
 batch=[datum(s,fn) for s in train]; curve=[]
 for st in range(1,P['steps_per_stage']+1):
  log('fb_before',tag=tag,step=st); fb=m.forward_backward(batch,loss_fn='cross_entropy'); m.optim_step(lr=P['lr'],grad_clip_norm=1.0); acc=evaluate(m,fn,f'{tag}_step{st}'); curve.append({'step':st,'loss':float(fb.metrics['loss']),'accuracy':acc}); log('fb_after',tag=tag,step=st,loss=float(fb.metrics['loss']),accuracy=acc)
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
# Generation A + matched wrong ancestor
with client.session(project='ml-v3-A') as s:
 lin=mk(s); w1=mk(s); cA=train_curve(lin,A,'A_lineage'); cW1=train_curve(w1,W1,'W1_wrong'); aacc=evaluate(lin,A,'A_final'); ckA=lin.save_weights('A_training',mode='training'); ckW1=w1.save_weights('W1_training',mode='training'); R['stages']['A']={'curve':cA,'heldout':aacc,'checkpoint':ckA.path,'wrong_checkpoint':ckW1.path}; log('sleep_A',checkpoint=ckA.path)
# Generation AB: correct A ancestry vs cold vs wrong W1 ancestry. Also build independent wrong two-stage W1->W2 lineage for next generation.
with client.session(project='ml-v3-AB') as s:
 lin=mk(s,ckA.path); cold=mk(s); wrong=mk(s,ckW1.path); wrongchain=mk(s,ckW1.path)
 pre={'lineage':evaluate(lin,AB,'AB_lineage_pre'),'cold':evaluate(cold,AB,'AB_cold_pre'),'wrong':evaluate(wrong,AB,'AB_wrong_pre')}
 curves={'lineage':train_curve(lin,AB,'AB_lineage'),'cold':train_curve(cold,AB,'AB_cold'),'wrong':train_curve(wrong,AB,'AB_wrong')}
 _=train_curve(wrongchain,W2,'W2_wrong_chain'); ckAB=lin.save_weights('AB_training',mode='training'); ckW12=wrongchain.save_weights('W1W2_training',mode='training'); R['stages']['AB']={'pre':pre,'curves':curves,'checkpoint':ckAB.path,'wrong_chain_checkpoint':ckW12.path}; log('sleep_AB',checkpoint=ckAB.path)
# Generation ABC: correct AB ancestry vs cold vs matched unrelated two-stage ancestry.
with client.session(project='ml-v3-ABC') as s:
 lin=mk(s,ckAB.path); cold=mk(s); wrong=mk(s,ckW12.path)
 pre={'lineage':evaluate(lin,ABC,'ABC_lineage_pre'),'cold':evaluate(cold,ABC,'ABC_cold_pre'),'wrong':evaluate(wrong,ABC,'ABC_wrong_pre')}
 curves={'lineage':train_curve(lin,ABC,'ABC_lineage'),'cold':train_curve(cold,ABC,'ABC_cold'),'wrong':train_curve(wrong,ABC,'ABC_wrong')}
 retention={'A':evaluate(lin,A,'retention_A'),'AB':evaluate(lin,AB,'retention_AB'),'ABC':evaluate(lin,ABC,'retention_ABC')}; ckABC=lin.save_weights('ABC_training',mode='training'); R['stages']['ABC']={'pre':pre,'curves':curves,'retention':retention,'checkpoint':ckABC.path}
# Precommitted dose-to-threshold gates + AUC tie-break evidence.
def metrics(stage):
 d=R['stages'][stage]; out={}
 for arm in ['lineage','cold','wrong']:
  out[arm]={'dose':dose(d['pre'][arm],d['curves'][arm]),'auc':d['pre'][arm]+sum(x['accuracy'] for x in d['curves'][arm])}
 return out
MAB=metrics('AB'); MABC=metrics('ABC'); R['metrics']={'AB':MAB,'ABC':MABC}
R['gates']={
 'G1_A_acquired':R['stages']['A']['heldout']>=P['threshold'],
 'G2_AB_lineage_faster_cold':better(MAB['lineage']['dose'],MAB['cold']['dose']),
 'G3_AB_lineage_faster_wrong':better(MAB['lineage']['dose'],MAB['wrong']['dose']),
 'G4_ABC_lineage_faster_cold':better(MABC['lineage']['dose'],MABC['cold']['dose']),
 'G5_ABC_lineage_faster_wrong':better(MABC['lineage']['dose'],MABC['wrong']['dose']),
 'G6_A_retained':R['stages']['ABC']['retention']['A']>=0.50,
 'G7_ABC_acquired':R['stages']['ABC']['retention']['ABC']>=P['threshold']}
R['verdict']='PASS_WAKE_SLEEP_STAIRCASE_V3' if all(R['gates'].values()) else 'FAIL_OR_MIXED_WAKE_SLEEP_STAIRCASE_V3'; (OUT/'FINAL_RESULT.json').write_text(json.dumps(R,indent=2)); log('final',verdict=R['verdict'],gates=R['gates']); print(json.dumps(R,indent=2),flush=True)
