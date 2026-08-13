import ast,hashlib,json,subprocess,tempfile
from pathlib import Path
OUT=Path('artifacts/source_distinct_ratchet_v34');OUT.mkdir(parents=True,exist_ok=True)
SEED='V34_20260814'
REPOS=[('requests','https://github.com/psf/requests.git','8068356288978c4f54661ae6f95afe0e0831885e'),('flask','https://github.com/pallets/flask.git','2a8a38b051fc248865730bf3511bf2e2ea325e81'),('rich','https://github.com/Textualize/rich.git','9d8f9a372cc5916fd4781fec207ced7ddac2f08f')]
BARRIER=(ast.Try,ast.Raise,ast.With,ast.AsyncWith,ast.ListComp,ast.SetComp,ast.DictComp,ast.GeneratorExp,ast.Match,ast.Lambda,ast.Yield,ast.YieldFrom,ast.Await)
def key(n):return type(n).__name__ if isinstance(n,BARRIER) else None
def frontier(n,A):
 k=key(n)
 if k and k not in A:return k
 for c in ast.iter_child_nodes(n):
  z=frontier(c,A)
  if z:return z
 return None
def seq(fn,limit=5):
 A=set();s=[]
 for _ in range(limit):
  z=frontier(fn,A)
  if not z:return tuple(s)
  s.append(z);A.add(z)
 return tuple(s) if frontier(fn,A) is None else None
def funs(t):return [n for n in ast.walk(t) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
rows=[]
for rn,url,commit in REPOS:
 root=Path(tempfile.mkdtemp())/rn;subprocess.run(['git','clone','-q',url,str(root)],check=True);subprocess.run(['git','checkout','-q',commit],cwd=root,check=True)
 for p in sorted(root.rglob('*.py')):
  try:
   if p.stat().st_size>300000:continue
   tr=ast.parse(p.read_text(encoding='utf-8'))
  except:continue
  for fn in funs(tr):
   s=seq(fn)
   if s:
    sid=f'{rn}|{commit}|{p.relative_to(root)}|{fn.name}|{getattr(fn,"lineno",0)}';rows.append({'repo':rn,'commit':commit,'path':str(p.relative_to(root)),'function':fn.name,'line':getattr(fn,'lineno',0),'seq':s,'rank':hashlib.sha256((SEED+'|'+sid).encode()).hexdigest(),'node':fn})
# Find source-distinct lineage: T1 closes with O1; T2 has prefix O1,O2 and closes there; T3 has prefix O1,O2,O3 and closes there.
triples=[]
for a in rows:
 if len(a['seq'])!=1:continue
 o1=a['seq'][0]
 for b in rows:
  if b['repo']==a['repo'] or len(b['seq'])!=2 or b['seq'][0]!=o1 or b['seq'][1]==o1:continue
  o2=b['seq'][1]
  for c in rows:
   if c['repo'] in {a['repo'],b['repo']} or len(c['seq'])!=3 or c['seq'][:2]!=(o1,o2) or c['seq'][2] in {o1,o2}:continue
   triples.append((a,b,c))
pairs=[]
if not triples:
 for a in rows:
  if len(a['seq'])!=1:continue
  o1=a['seq'][0]
  for b in rows:
   if b['repo']!=a['repo'] and len(b['seq'])==2 and b['seq'][0]==o1 and b['seq'][1]!=o1:pairs.append((a,b))
def rk(items):return hashlib.sha256((SEED+'|'+'|'.join(x['rank'] for x in items)).encode()).hexdigest()
chosen=None;mode=None
if triples:chosen=min(triples,key=rk);mode='THREE_GENERATION'
elif pairs:chosen=min(pairs,key=rk);mode='TWO_GENERATION'
R={'protocol':'V34 generic exact-frontier constructor; source-distinct fixed repositories','seed':SEED,'function_count':len(rows),'triple_candidates':len(triples),'pair_candidates':len(pairs),'mode':mode}
if not chosen:
 R['verdict']='NO_SOURCE_DISTINCT_LINEAGE';(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2));raise SystemExit
pub=[]
for x in chosen:
 y={k:v for k,v in x.items() if k!='node'};pub.append(y)
R['lineage']=pub
A=set();steps=[]
for i,x in enumerate(chosen):
 before=frontier(x['node'],A);A.add(before);after=frontier(x['node'],A)
 steps.append({'generation':i+1,'repo':x['repo'],'before':before,'after_one_extension':after,'algebra_after':sorted(A)})
R['steps']=steps
# Causal discoverability: later target before prior lineage exposes only earlier operator; with prior lineage it exposes the new one.
controls=[];A=set()
for i,x in enumerate(chosen):
 cold=frontier(x['node'],set())
 warm=frontier(x['node'],A)
 controls.append({'generation':i+1,'cold_frontier':cold,'warm_frontier':warm,'prior_algebra':sorted(A)})
 A.add(warm)
R['controls']=controls
# Ablate each ancestor from the algebra immediately before the deepest target.
deep=chosen[-1]['node'];full_prior=set(x['seq'][-1] for x in chosen[:-1]);abl=[]
for op in sorted(full_prior):
 z=frontier(deep,full_prior-{op});abl.append({'removed':op,'frontier_after_ablation':z})
R['ablations']=abl
expected=[x['seq'][-1] for x in chosen]
R['gates']={'source_distinct':len({x['repo'] for x in chosen})==len(chosen),'each_generation_discovers_expected_new_frontier':all(c['warm_frontier']==expected[i] for i,c in enumerate(controls)),'cold_later_targets_hide_new_frontier':all(i==0 or controls[i]['cold_frontier']!=expected[i] for i in range(len(controls))),'ancestor_ablation_changes_deep_frontier':all(a['frontier_after_ablation']!=expected[-1] for a in abl)}
R['verdict']='PASS_SOURCE_DISTINCT_DISCOVERABILITY_RATCHET_V34' if all(R['gates'].values()) else 'MIXED_SOURCE_DISTINCT_DISCOVERABILITY_RATCHET_V34'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))