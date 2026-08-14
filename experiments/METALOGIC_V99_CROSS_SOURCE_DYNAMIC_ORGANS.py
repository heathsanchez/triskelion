#!/usr/bin/env python3
import importlib.util, json, math, os
from pathlib import Path
BASE=Path(__file__).with_name('METALOGIC_V98_RICH_K_PROTECTED_DYNAMIC_RANKING.py')
spec=importlib.util.spec_from_file_location('v98base',BASE); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ROOT=m.ROOT; DIMS=m.DIMS; rich_candidates=m.rich_candidates; full_score=m.full_score; collect_probe=m.collect_probe; probe_trace=m.probe_trace; delta=m.delta; sim=m.sim; permute=m.permute
OUT=Path(os.environ.get('OUT_DIR','results/v99')); OUT.mkdir(parents=True,exist_ok=True)
SEED='V99_CROSS_SOURCE_DYNAMIC_ORGANS_2026-08-14'; COMMIT=m.COMMIT
TRAIN_N=10; TEST_N=8; TRAIN_CAP=160; TEST_CAP=220; FULL_BUDGET=10; SIM_THRESHOLD=.82; MIN_SOURCE_SUPPORT=2

def h(x):
 import hashlib
 return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def unit(v):
 z=math.sqrt(sum(x*x for x in v)); return [x/z for x in v] if z else [0.0]*len(v)
def cosine(a,b):return sum(x*y for x,y in zip(a,b))

def cross_source_components(points):
 # points=(task,kind,gain,unit_delta). Components are frozen threshold graph.
 n=len(points); adj=[set() for _ in range(n)]
 for i in range(n):
  for j in range(i+1,n):
   if points[i][0]==points[j][0]:continue
   if cosine(points[i][3],points[j][3])>=SIM_THRESHOLD:adj[i].add(j);adj[j].add(i)
 seen=set();comps=[]
 for i in range(n):
  if i in seen:continue
  stack=[i];idx=[]
  while stack:
   x=stack.pop()
   if x in seen:continue
   seen.add(x);idx.append(x);stack.extend(adj[x]-seen)
  tasks={points[k][0] for k in idx}
  if len(tasks)>=MIN_SOURCE_SUPPORT:
   # medoid maximizes mean cosine, tie by deterministic hash
   med=max(idx,key=lambda k:(sum(cosine(points[k][3],points[j][3]) for j in idx)/len(idx),h('med|'+points[k][0]+'|'+points[k][1])))
   comps.append({'indices':idx,'tasks':sorted(tasks),'medoid':points[med][3],'medoid_task':points[med][0],'medoid_kind':points[med][1]})
 return comps

def main():
 buggy=ROOT/'python_programs'; tests=ROOT/'python_testcases'; names=[]
 for p in buggy.glob('*.py'):
  n=p.stem
  if (tests/f'test_{n}.py').exists() and full_score(n,p.read_text())>0:names.append(n)
 names=sorted(names,key=lambda x:h('task|'+x)); train=names[:TRAIN_N]; test=names[TRAIN_N:TRAIN_N+TEST_N]
 pts=[];train_rows=[];probe_nodes={}
 for n in train:
  src=(buggy/f'{n}.py').read_text(); node=collect_probe(n); probe_nodes[n]=node; base=full_score(n,src); bt=probe_trace(n,src,node); imps=[]
  for kind,text in rich_candidates(src,TRAIN_CAP):
   sc=full_score(n,text)
   if sc<base:
    tr=probe_trace(n,text,node);d=unit(delta(bt,tr));gain=base-sc;pts.append((n,kind,gain,d));imps.append((kind,gain))
  train_rows.append({'task':n,'probe':node,'base_score':base,'improving_count':len(imps),'improving_kinds':sorted({x[0] for x in imps}),'best_gain':max([x[1] for x in imps],default=0)})
 pts=sorted(pts,key=lambda x:(-x[2],h('pt|'+x[0]+'|'+x[1]+'|'+json.dumps(x[3]))))
 comps=cross_source_components(pts);medoids=[c['medoid'] for c in comps];null=[unit(permute(v)) for v in medoids]
 learned=[];nulls=[];hashed=[];reachable=[];rows=[]
 for n in test:
  src=(buggy/f'{n}.py').read_text();node=collect_probe(n);probe_nodes[n]=node;bt=probe_trace(n,src,node);cs=[]
  for kind,text in rich_candidates(src,TEST_CAP):
   tr=probe_trace(n,text,node);d=unit(delta(bt,tr));ls=max([cosine(d,p) for p in medoids],default=-1);ns=max([cosine(d,p) for p in null],default=-1);cs.append((kind,text,ls,ns))
  # independent evaluation ceiling; does not affect rankings
  reach=False
  for _,text,_,_ in cs:
   if full_score(n,text)==0:reach=True;break
  if reach:reachable.append(n)
  lr=sorted(cs,key=lambda x:(-x[2],h('L|'+x[1])))[:FULL_BUDGET];nr=sorted(cs,key=lambda x:(-x[3],h('N|'+x[1])))[:FULL_BUDGET];hr=sorted(cs,key=lambda x:h('H|'+x[1]))[:FULL_BUDGET]
  cache={}
  def solve(rank):
   for _,text,_,_ in rank:
    if text not in cache:cache[text]=full_score(n,text)
    if cache[text]==0:return True
   return False
  lo,no,ho=solve(lr),solve(nr),solve(hr)
  if lo:learned.append(n)
  if no:nulls.append(n)
  if ho:hashed.append(n)
  rows.append({'task':n,'probe':node,'candidate_count':len(cs),'reachable_success':reach,'learned_success':lo,'coordinate_null_success':no,'hash_success':ho})
 gates={'preexisting_external_corpus':True,'no_correct_implementations_read':True,'rich_K_identical_across_arms':True,'cross_source_improving_components_exist':bool(comps),'every_component_has_two_source_tasks':all(len(c['tasks'])>=2 for c in comps),'nonzero_reachability_ceiling':bool(reachable),'learned_recovers_success':bool(learned),'learned_beats_coordinate_null':len(learned)>len(nulls),'learned_beats_hash_baseline':len(learned)>len(hashed)}
 verdict='PASS_CROSS_SOURCE_DYNAMIC_ORGANS_V99' if all(gates.values()) else 'MIXED_CROSS_SOURCE_DYNAMIC_ORGANS_V99'
 res={'protocol':'V99_CROSS_SOURCE_DYNAMIC_ORGANS','external_commit':COMMIT,'train':train,'test':test,'probe_nodes':probe_nodes,'dims':DIMS,'similarity_threshold':SIM_THRESHOLD,'min_source_support':MIN_SOURCE_SUPPORT,'train_rows':train_rows,'improving_point_count':len(pts),'components':[{'tasks':c['tasks'],'size':len(c['indices']),'medoid_task':c['medoid_task'],'medoid_kind':c['medoid_kind'],'medoid':c['medoid']} for c in comps],'learned_solved':learned,'coordinate_null_solved':nulls,'hash_solved':hashed,'reachable_ceiling':reachable,'rows':rows,'gates':gates,'verdict':verdict,'qualification':'Natural verifier-only cross-source organ test. Correct implementations are never read. Candidate K is rich and identical across arms. Training components are admitted only when normalized cheap-probe execution deltas from verifier-improving mutations recur across at least two different source tasks. Held-out full-suite verification is spent only on top-B ranked candidates; exhaustive ceiling is evaluation-only. A PASS would support source-distinct verifier-induced dynamic components that causally reduce protected search, not autonomous constructor genesis.'}
 (OUT/'RESULT.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
if __name__=='__main__':main()
