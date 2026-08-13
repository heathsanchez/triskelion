import os,json,hashlib,time
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

P={"name":"METALOGIC_PROTECTED_CONSOLIDATION_V7","date":"2026-08-13","seed":20260813,"base":"Qwen/Qwen3.5-9B","rank":32,"lr":2e-4,"steps":4,"threshold":0.75,"batch_n":16,"replay_AB":2,"replay_ABC_A":2,"replay_ABC_AB":2,"claim_boundary":"Synthetic matched-budget test of whether sparse verified ancestor replay preserves callable prior capabilities during cross-session neural successor acquisition. Same gradient-step count and batch size per arm; protected arm trades a small fraction of new-task examples for verified ancestor examples. Not external-task lifelong learning evidence."}
OUT=Path('artifacts/protected_consolidation_v7'); OUT.mkdir(parents=True,exist_ok=True)
PH=hashlib.sha256(json.dumps(P,sort_keys=True,separators=(',',':')).encode()).hexdigest(); (OUT/'PRECOMMIT.json').write_text(json.dumps({'protocol_sha256':PH,'protocol':P},indent=2))
def log(e,**kw):
 r={'t':time.time(),'event':e,**kw}; print(json.dumps(r),flush=True); open(OUT/'TRACE.jsonl','a').write(json.dumps(r)+'\n')
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0); assert client.health_check()
BASE=P['base']; assert BASE in list(client.get_capabilities()); tok=AutoTokenizer.from_pretrained(BASE); EOS=tok.eos_token_id
train=['amber','quiet','silver','paper','winter','copper','scarlet','gentle','marble','rapid','bright','soft','blue','little','warm','clear']
held=['violet','hidden','green','crimson','golden','silent','orange','secret']
def A(s): return 'ka-'+s
def AB(s): return 'ka-'+s+'-zu'
def ABC(s): return '[ka-'+s+'-zu]'
def prompt(task,s): return f'Task: {task}\nInput: {s}\nOutput:'
def datum(task,s,fn):
 a=tok(prompt(task,s),add_special_tokens=False)['input_ids']; b=tok(' '+fn(s),add_special_tokens=False)['input_ids']+[EOS]; ids=a+b
 return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(a)-1)+[1.0]*(len(b)+1)}
def firstline(g):
 t=g.text.strip(); return t.splitlines()[0].strip() if t else ''
def evaluate(m,task,fn,tag):
 gs=m.sample(prompts=[prompt(task,s) for s in held],max_tokens=18,temperature=0.0)
 outs=[firstline(g[0]) for g in gs]; acc=sum(o==fn(s) for s,o in zip(held,outs))/len(held); log('eval',tag=tag,task=task,accuracy=acc,examples=[{'input':s,'gold':fn(s),'out':o} for s,o in list(zip(held,outs))[:3]]); return acc
def mk(sess,ck=None):
 kw={'base_model':BASE,'lora':river.LoraConfig(rank=P['rank'],seed=P['seed'])}
 if ck: kw['checkpoint']=ck
 return sess.create_model(**kw)
def run_steps(m,batch,newtask,newfn,tag,ancestors):
 curve=[]
 for st in range(1,P['steps']+1):
  log('fb_before',tag=tag,step=st); fb=m.forward_backward(batch,loss_fn='cross_entropy'); m.optim_step(lr=P['lr'],grad_clip_norm=1.0)
  newacc=evaluate(m,newtask,newfn,f'{tag}_new_step{st}'); ret={name:evaluate(m,task,fn,f'{tag}_{name}_step{st}') for name,task,fn in ancestors}; curve.append({'step':st,'loss':float(fb.metrics['loss']),'new_accuracy':newacc,'retention':ret}); log('fb_after',tag=tag,step=st,loss=float(fb.metrics['loss']),new_accuracy=newacc,retention=ret)
 return curve
def dose(curve):
 for x in curve:
  if x['new_accuracy']>=P['threshold']: return x['step']
 return None

# Use the calibrated V6 A checkpoint: A=100% held-out and survives a save/close/reload boundary.
CK_A='river://4e63854c-1980-486b-ba72-4b45ed0c5e96/weights/A_training'
R={'protocol_sha256':PH,'base':BASE,'source_A_checkpoint':CK_A,'stages':{},'gates':{}}

# AB: exact same starting checkpoint, 4 gradient steps, batch size 16.
# Naive = 16 AB examples. Protected = 14 AB + 2 verified A replay examples.
with client.session(project='ml-v7-AB') as s:
 naive=mk(s,CK_A); prot=mk(s,CK_A)
 pre={'naive_A':evaluate(naive,'A',A,'AB_naive_A_pre'),'prot_A':evaluate(prot,'A',A,'AB_prot_A_pre')}
 b_naive=[datum('AB',x,AB) for x in train]
 b_prot=[datum('AB',x,AB) for x in train[:14]]+[datum('A',x,A) for x in train[14:16]]
 c_naive=run_steps(naive,b_naive,'AB',AB,'AB_naive',[('A','A',A)])
 c_prot=run_steps(prot,b_prot,'AB',AB,'AB_protected',[('A','A',A)])
 final_naive={'A':evaluate(naive,'A',A,'AB_naive_A_final'),'AB':evaluate(naive,'AB',AB,'AB_naive_AB_final')}
 final_prot={'A':evaluate(prot,'A',A,'AB_prot_A_final'),'AB':evaluate(prot,'AB',AB,'AB_prot_AB_final')}
 ckN=naive.save_weights('AB_naive_training',mode='training'); ckP=prot.save_weights('AB_protected_training',mode='training')
 R['stages']['AB']={'pre':pre,'naive_curve':c_naive,'protected_curve':c_prot,'final_naive':final_naive,'final_protected':final_prot,'naive_checkpoint':ckN.path,'protected_checkpoint':ckP.path,'dose_naive':dose(c_naive),'dose_protected':dose(c_prot)}

# Close session, reload both independently. ABC: same 4 gradient steps and batch size 16.
# Naive = 16 ABC. Protected = 12 ABC + 2 A + 2 AB verified replay examples.
with client.session(project='ml-v7-ABC') as s:
 naive=mk(s,ckN.path); prot=mk(s,ckP.path)
 reloads={'naive_A':evaluate(naive,'A',A,'ABC_naive_A_reload'),'naive_AB':evaluate(naive,'AB',AB,'ABC_naive_AB_reload'),'prot_A':evaluate(prot,'A',A,'ABC_prot_A_reload'),'prot_AB':evaluate(prot,'AB',AB,'ABC_prot_AB_reload')}
 b_naive=[datum('ABC',x,ABC) for x in train]
 b_prot=[datum('ABC',x,ABC) for x in train[:12]]+[datum('A',x,A) for x in train[12:14]]+[datum('AB',x,AB) for x in train[14:16]]
 c_naive=run_steps(naive,b_naive,'ABC',ABC,'ABC_naive',[('A','A',A),('AB','AB',AB)])
 c_prot=run_steps(prot,b_prot,'ABC',ABC,'ABC_protected',[('A','A',A),('AB','AB',AB)])
 final_naive={'A':evaluate(naive,'A',A,'ABC_naive_A_final'),'AB':evaluate(naive,'AB',AB,'ABC_naive_AB_final'),'ABC':evaluate(naive,'ABC',ABC,'ABC_naive_ABC_final')}
 final_prot={'A':evaluate(prot,'A',A,'ABC_prot_A_final'),'AB':evaluate(prot,'AB',AB,'ABC_prot_AB_final'),'ABC':evaluate(prot,'ABC',ABC,'ABC_prot_ABC_final')}
 ckNP=naive.save_weights('ABC_naive_training',mode='training'); ckPP=prot.save_weights('ABC_protected_training',mode='training')
 R['stages']['ABC']={'reloads':reloads,'naive_curve':c_naive,'protected_curve':c_prot,'final_naive':final_naive,'final_protected':final_prot,'naive_checkpoint':ckNP.path,'protected_checkpoint':ckPP.path,'dose_naive':dose(c_naive),'dose_protected':dose(c_prot)}

T=P['threshold']; ab=R['stages']['AB']; abc=R['stages']['ABC']
R['gates']={
 'G1_same_A_start_healthy':ab['pre']['naive_A']>=T and ab['pre']['prot_A']>=T,
 'G2_naive_AB_forgets_A':ab['final_naive']['AB']>=T and ab['final_naive']['A']<T,
 'G3_protected_AB_acquires_and_retains':ab['final_protected']['AB']>=T and ab['final_protected']['A']>=T,
 'G4_protected_AB_survives_reload':abc['reloads']['prot_A']>=T and abc['reloads']['prot_AB']>=T,
 'G5_naive_ABC_forgets_ancestors':abc['final_naive']['ABC']>=T and (abc['final_naive']['A']<T or abc['final_naive']['AB']<T),
 'G6_protected_ABC_acquires_all_three':abc['final_protected']['ABC']>=T and abc['final_protected']['A']>=T and abc['final_protected']['AB']>=T,
 'G7_protected_new_task_within_budget':ab['dose_protected'] is not None and abc['dose_protected'] is not None
}
R['verdict']='PASS_PROTECTED_CONSOLIDATION_V7' if all(R['gates'].values()) else 'FAIL_OR_MIXED_PROTECTED_CONSOLIDATION_V7'
(OUT/'FINAL_RESULT.json').write_text(json.dumps(R,indent=2)); log('final',verdict=R['verdict'],gates=R['gates']); print(json.dumps(R,indent=2),flush=True)
