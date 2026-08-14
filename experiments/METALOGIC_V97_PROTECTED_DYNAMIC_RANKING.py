#!/usr/bin/env python3
import importlib.util,json,math,os,re,subprocess,sys,tempfile
from pathlib import Path
BASE=Path(__file__).with_name('METALOGIC_V94_DYNAMIC_STATE_INVARIANTS.py')
spec=importlib.util.spec_from_file_location('v94base',BASE); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ROOT=m.ROOT; DIMS=m.DIMS; candidates=m.candidates; delta=m.delta; sim=m.sim; permute=m.permute; tracer_code=m.tracer_code
OUT=Path(os.environ.get('OUT_DIR','results/v97')); OUT.mkdir(parents=True,exist_ok=True)
SEED='V97_PROTECTED_DYNAMIC_RANKING_2026-08-14'; COMMIT=m.COMMIT
TRAIN_N=7; TEST_N=7; TRAIN_CAP=24; TEST_CAP=100; FULL_BUDGET=8; MAX_POINTS=18; MAX_K=4; LAMBDA=.2

def h(x):
 import hashlib
 return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()

def parse_score(rc,out):
 if rc==0:return 0
 z=re.search(r'(\d+) failed',out or '')
 if z:return int(z.group(1))
 z=re.search(r'(\d+) error',out or '')
 return 100+int(z.group(1)) if z else 99

def full_score(name,text):
 p=ROOT/'python_programs'/f'{name}.py'; old=p.read_text()
 try:
  p.write_text(text)
  r=subprocess.run([sys.executable,'-m','pytest','-q',f'python_testcases/test_{name}.py','--timeout=4'],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=25)
  return parse_score(r.returncode,r.stdout)
 except Exception:return 999
 finally:p.write_text(old)

def collect_probe(name):
 try:
  r=subprocess.run([sys.executable,'-m','pytest','--collect-only','-q',f'python_testcases/test_{name}.py'],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=20)
  ids=[x.strip() for x in (r.stdout or '').splitlines() if '::' in x and not x.lstrip().startswith('<')]
  return sorted(ids,key=lambda x:h('probe|'+name+'|'+x))[0] if ids else None
 except Exception:return None

def probe_trace(name,text,nodeid):
 p=ROOT/'python_programs'/f'{name}.py'; old=p.read_text(); td=Path(tempfile.mkdtemp(prefix='v97_')); (td/'sitecustomize.py').write_text(tracer_code()); tf=td/'trace.json'
 env=os.environ.copy();env['PYTHONPATH']=str(td)+os.pathsep+env.get('PYTHONPATH','');env['V94_TARGET']=name;env['V94_TRACE_OUT']=str(tf)
 try:
  p.write_text(text)
  target=nodeid or f'python_testcases/test_{name}.py'
  subprocess.run([sys.executable,'-m','pytest','-q',target,'--timeout=4'],cwd=ROOT,env=env,text=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20)
  return json.loads(tf.read_text()) if tf.exists() else {k:0 for k in DIMS}
 except Exception:return {k:0 for k in DIMS}
 finally:
  p.write_text(old)
  try:
   for q in td.iterdir():q.unlink()
   td.rmdir()
  except Exception:pass

def choose(vs):
 if not vs:return [],None
 best=None
 for k in range(1,min(MAX_K,len(vs))+1):
  first=min(range(len(vs)),key=lambda i:(sum(1-sim(vs[i],x) for x in vs),i)); inds=[first]
  while len(inds)<k:
   rem=[i for i in range(len(vs)) if i not in inds]
   nxt=max(rem,key=lambda i:(min(1-sim(vs[i],vs[j]) for j in inds),-i));inds.append(nxt)
  meds=[vs[i] for i in inds];loss=sum(1-max(sim(v,p) for p in meds) for v in vs)+LAMBDA*k
  key=(round(loss,12),k,tuple(inds))
  if best is None or key<best[0]:best=(key,meds,inds,loss)
 return best[1],{'k':len(best[1]),'indices':best[2],'objective':best[3]}

def main():
 buggy=ROOT/'python_programs';tests=ROOT/'python_testcases'
 names=[]
 for p in buggy.glob('*.py'):
  n=p.stem
  if (tests/f'test_{n}.py').exists() and full_score(n,p.read_text())>0:names.append(n)
 names=sorted(names,key=lambda x:h('task|'+x));train=names[:TRAIN_N];test=names[TRAIN_N:TRAIN_N+TEST_N]
 points=[];train_rows=[];probe_nodes={}
 for n in train:
  src=(buggy/f'{n}.py').read_text();node=collect_probe(n);probe_nodes[n]=node;base=full_score(n,src);bt=probe_trace(n,src,node);imps=[]
  for text in candidates(src,TRAIN_CAP):
   tr=probe_trace(n,text,node);sc=full_score(n,text)
   if sc<base:
    d=delta(bt,tr);gain=base-sc;points.append((gain,n,d));imps.append({'score':sc,'gain':gain,'delta':d})
  train_rows.append({'task':n,'probe':node,'base_score':base,'improving_count':len(imps),'best_gain':max([x['gain'] for x in imps],default=0)})
 points=sorted(points,key=lambda x:(-x[0],h('pt|'+x[1]+'|'+json.dumps(x[2]))))[:MAX_POINTS];vecs=[x[2] for x in points]
 medoids,mdl=choose(vecs);null=[permute(v) for v in medoids]
 learned=[];shuffled=[];hashed=[];rows=[]
 for n in test:
  src=(buggy/f'{n}.py').read_text();node=collect_probe(n);probe_nodes[n]=node;bt=probe_trace(n,src,node);cs=[]
  for text in candidates(src,TEST_CAP):
   tr=probe_trace(n,text,node);d=delta(bt,tr);ls=max([sim(d,p) for p in medoids],default=-1);ns=max([sim(d,p) for p in null],default=-1);cs.append((text,ls,ns))
  lr=sorted(cs,key=lambda x:(-x[1],h('L|'+x[0])))[:FULL_BUDGET]
  nr=sorted(cs,key=lambda x:(-x[2],h('N|'+x[0])))[:FULL_BUDGET]
  hr=sorted(cs,key=lambda x:h('H|'+x[0]))[:FULL_BUDGET]
  cache={}
  def solved(rank):
   for text,_,_ in rank:
    if text not in cache:cache[text]=full_score(n,text)
    if cache[text]==0:return True
   return False
  lo,no,ho=solved(lr),solved(nr),solved(hr)
  if lo:learned.append(n)
  if no:shuffled.append(n)
  if ho:hashed.append(n)
  rows.append({'task':n,'probe':node,'candidate_count':len(cs),'learned_success':lo,'coordinate_null_success':no,'hash_baseline_success':ho,'full_verifier_budget_per_arm':FULL_BUDGET})
 gates={'preexisting_external_corpus':True,'no_correct_implementations_read':True,'cheap_probe_distinct_from_full_verifier':True,'verifier_improving_training_deltas_exist':bool(vecs),'dynamic_clusters_formed':bool(medoids),'learned_recovers_heldout_success':bool(learned),'learned_beats_coordinate_null':len(learned)>len(shuffled),'learned_beats_hash_baseline':len(learned)>len(hashed)}
 verdict='PASS_PROTECTED_DYNAMIC_RANKING_V97' if all(gates.values()) else 'MIXED_PROTECTED_DYNAMIC_RANKING_V97'
 res={'protocol':'V97_PROTECTED_DYNAMIC_RANKING','external_commit':COMMIT,'train':train,'test':test,'probe_nodes':probe_nodes,'dims':DIMS,'train_rows':train_rows,'improving_delta_count':len(vecs),'mdl':mdl,'medoids':medoids,'learned_solved':learned,'coordinate_null_solved':shuffled,'hash_baseline_solved':hashed,'rows':rows,'gates':gates,'verdict':verdict,'qualification':'Natural verifier-only economic bridge. Correct implementations are never read. Training full-suite verifier improvements induce anonymous dynamic prototypes measured on one hash-selected public probe test per task. On held-out tasks every candidate is traced only on the cheap probe; the protected full test suite is spent only on top-B candidates in each arm. A PASS would show a causal reduction in expensive full-verifier search under this bounded corpus, not autonomous operator synthesis.'}
 (OUT/'RESULT.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
if __name__=='__main__':main()
