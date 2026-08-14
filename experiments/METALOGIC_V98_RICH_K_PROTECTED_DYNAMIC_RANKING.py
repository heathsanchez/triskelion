#!/usr/bin/env python3
import ast, copy, importlib.util, json, math, os, re, subprocess, sys, tempfile
from pathlib import Path
BASE=Path(__file__).with_name('METALOGIC_V97_PROTECTED_DYNAMIC_RANKING.py')
spec=importlib.util.spec_from_file_location('v97base',BASE); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ROOT=m.ROOT; DIMS=m.DIMS; delta=m.delta; sim=m.sim; permute=m.permute; tracer_code=m.tracer_code
OUT=Path(os.environ.get('OUT_DIR','results/v98')); OUT.mkdir(parents=True,exist_ok=True)
SEED='V98_RICH_K_PROTECTED_DYNAMIC_RANKING_2026-08-14'; COMMIT=m.COMMIT
TRAIN_N=8; TEST_N=8; TRAIN_CAP=180; TEST_CAP=260; FULL_BUDGET=10; MAX_POINTS=24; MAX_K=5; LAMBDA=.2

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
  p.write_text(text); r=subprocess.run([sys.executable,'-m','pytest','-q',f'python_testcases/test_{name}.py','--timeout=4'],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=25)
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
 p=ROOT/'python_programs'/f'{name}.py'; old=p.read_text(); td=Path(tempfile.mkdtemp(prefix='v98_')); (td/'sitecustomize.py').write_text(tracer_code()); tf=td/'trace.json'
 env=os.environ.copy();env['PYTHONPATH']=str(td)+os.pathsep+env.get('PYTHONPATH','');env['V94_TARGET']=name;env['V94_TRACE_OUT']=str(tf)
 try:
  p.write_text(text); target=nodeid or f'python_testcases/test_{name}.py'
  subprocess.run([sys.executable,'-m','pytest','-q',target,'--timeout=4'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20)
  return json.loads(tf.read_text()) if tf.exists() else {k:0 for k in DIMS}
 except Exception:return {k:0 for k in DIMS}
 finally:
  p.write_text(old)
  try:
   for q in td.iterdir():q.unlink()
   td.rmdir()
  except Exception:pass

CMP={ast.Lt:[ast.LtE,ast.Gt,ast.GtE,ast.Eq,ast.NotEq],ast.LtE:[ast.Lt,ast.Gt,ast.GtE,ast.Eq],ast.Gt:[ast.GtE,ast.Lt,ast.LtE,ast.Eq],ast.GtE:[ast.Gt,ast.Lt,ast.LtE,ast.Eq],ast.Eq:[ast.NotEq,ast.Lt,ast.LtE,ast.Gt,ast.GtE],ast.NotEq:[ast.Eq]}
BIN={ast.Add:[ast.Sub,ast.Mult,ast.FloorDiv,ast.Mod],ast.Sub:[ast.Add,ast.Mult],ast.Mult:[ast.Add,ast.Sub,ast.FloorDiv],ast.Div:[ast.FloorDiv,ast.Mult],ast.FloorDiv:[ast.Div,ast.Mult,ast.Mod],ast.Mod:[ast.FloorDiv,ast.Mult,ast.Add]}
BOOL={ast.And:[ast.Or],ast.Or:[ast.And]}

def rich_candidates(src,cap):
 try:t=ast.parse(src)
 except:return []
 names=sorted({n.id for n in ast.walk(t) if isinstance(n,ast.Name)}); out=[]; seen=set()
 def emit(z,kind):
  try:s=ast.unparse(ast.fix_missing_locations(z))
  except:return
  if s!=src and s not in seen:
   seen.add(s);out.append((kind,s))
 def mutate_nodes(cls,make_reps,kind):
  nodes=[n for n in ast.walk(t) if isinstance(n,cls)]
  for i,n in enumerate(nodes):
   for rep in make_reps(n):
    z=copy.deepcopy(t); zn=[x for x in ast.walk(z) if isinstance(x,cls)]
    if i>=len(zn):continue
    target=zn[i]
    if isinstance(target,ast.Name) and isinstance(rep,ast.Name):target.id=rep.id
    elif isinstance(target,ast.Constant) and isinstance(rep,ast.Constant):target.value=rep.value
    else:target.__class__=rep.__class__
    emit(z,kind)
    if len(out)>=cap:return True
  return False
 if mutate_nodes(ast.Name,lambda n:[ast.Name(id=x,ctx=copy.deepcopy(n.ctx)) for x in names if x!=n.id][:8],'NAME_SUB'):return out
 if mutate_nodes(ast.Constant,lambda n:[ast.Constant(v) for v in (-1,0,1,2) if isinstance(n.value,(int,float,bool)) and v!=n.value],'CONST_SUB'):return out
 for mapping,basekind in ((CMP,'CMP_OP'),(BIN,'BIN_OP'),(BOOL,'BOOL_OP')):
  types=tuple(mapping)
  nodes=[n for n in ast.walk(t) if isinstance(n,types)]
  for i,n in enumerate(nodes):
   for alt in mapping.get(type(n),[]):
    z=copy.deepcopy(t);zn=[x for x in ast.walk(z) if isinstance(x,types)];zn[i].__class__=alt;emit(z,basekind)
    if len(out)>=cap:return out
 # swap call args
 calls=[n for n in ast.walk(t) if isinstance(n,ast.Call) and len(n.args)>=2]
 for i,c in enumerate(calls):
  for a in range(len(c.args)):
   for b in range(a+1,len(c.args)):
    z=copy.deepcopy(t);zc=[x for x in ast.walk(z) if isinstance(x,ast.Call) and len(x.args)>=2];zc[i].args[a],zc[i].args[b]=zc[i].args[b],zc[i].args[a];emit(z,'CALL_ARG_SWAP')
    if len(out)>=cap:return out
 # replace any call arg Name with another in-scope name
 for i,c in enumerate([n for n in ast.walk(t) if isinstance(n,ast.Call)]):
  for j,arg in enumerate(c.args):
   if isinstance(arg,ast.Name):
    for nm in names:
     if nm==arg.id:continue
     z=copy.deepcopy(t);zc=[x for x in ast.walk(z) if isinstance(x,ast.Call)]
     if i<len(zc) and j<len(zc[i].args) and isinstance(zc[i].args[j],ast.Name):zc[i].args[j].id=nm;emit(z,'CALL_ARG_NAME')
     if len(out)>=cap:return out
 # negate if/while conditions
 guards=[n for n in ast.walk(t) if isinstance(n,(ast.If,ast.While))]
 for i,g in enumerate(guards):
  z=copy.deepcopy(t);zg=[n for n in ast.walk(z) if isinstance(n,(ast.If,ast.While))];zg[i].test=ast.UnaryOp(op=ast.Not(),operand=zg[i].test);emit(z,'NEGATE_GUARD')
  if len(out)>=cap:return out
 # insert set.add(name) before Return inside functions if an existing set-like variable is inferable from `.add`
 attrs=[n for n in ast.walk(t) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='add' and isinstance(n.func.value,ast.Name)]
 setnames=sorted({n.func.value.id for n in attrs})
 if setnames:
  for sn in setnames:
   for nm in names:
    class Ins(ast.NodeTransformer):
     def __init__(self):self.done=False
     def visit_Return(self,node):
      if self.done:return node
      self.done=True
      call=ast.Expr(value=ast.Call(func=ast.Attribute(value=ast.Name(id=sn,ctx=ast.Load()),attr='add',ctx=ast.Load()),args=[ast.Name(id=nm,ctx=ast.Load())],keywords=[]))
      return [call,node]
    z=Ins().visit(copy.deepcopy(t));emit(z,'STATE_UPDATE_INSERT')
    if len(out)>=cap:return out
 return out

def choose(vs):
 if not vs:return [],None
 best=None
 for k in range(1,min(MAX_K,len(vs))+1):
  first=min(range(len(vs)),key=lambda i:(sum(1-sim(vs[i],x) for x in vs),i));inds=[first]
  while len(inds)<k:
   rem=[i for i in range(len(vs)) if i not in inds];nxt=max(rem,key=lambda i:(min(1-sim(vs[i],vs[j]) for j in inds),-i));inds.append(nxt)
  meds=[vs[i] for i in inds];loss=sum(1-max(sim(v,p) for p in meds) for v in vs)+LAMBDA*k;key=(round(loss,12),k,tuple(inds))
  if best is None or key<best[0]:best=(key,meds,inds,loss)
 return best[1],{'k':len(best[1]),'indices':best[2],'objective':best[3]}

def main():
 buggy=ROOT/'python_programs';tests=ROOT/'python_testcases';names=[]
 for p in buggy.glob('*.py'):
  n=p.stem
  if (tests/f'test_{n}.py').exists() and full_score(n,p.read_text())>0:names.append(n)
 names=sorted(names,key=lambda x:h('task|'+x));train=names[:TRAIN_N];test=names[TRAIN_N:TRAIN_N+TEST_N]
 pts=[];train_rows=[];probe_nodes={}
 for n in train:
  src=(buggy/f'{n}.py').read_text();node=collect_probe(n);probe_nodes[n]=node;base=full_score(n,src);bt=probe_trace(n,src,node);imps=[]
  for kind,text in rich_candidates(src,TRAIN_CAP):
   sc=full_score(n,text)
   if sc<base:
    tr=probe_trace(n,text,node);d=delta(bt,tr);gain=base-sc;pts.append((gain,n,kind,d));imps.append((gain,kind))
  train_rows.append({'task':n,'probe':node,'base_score':base,'improving_count':len(imps),'best_gain':max([x[0] for x in imps],default=0),'improving_kinds':sorted({x[1] for x in imps})})
 pts=sorted(pts,key=lambda x:(-x[0],h('pt|'+x[1]+'|'+x[2]+'|'+json.dumps(x[3]))))[:MAX_POINTS];vecs=[x[3] for x in pts];medoids,mdl=choose(vecs);null=[permute(v) for v in medoids]
 learned=[];nulls=[];hashed=[];reachable=[];rows=[]
 for n in test:
  src=(buggy/f'{n}.py').read_text();node=collect_probe(n);probe_nodes[n]=node;bt=probe_trace(n,src,node);cs=[]
  for kind,text in rich_candidates(src,TEST_CAP):
   tr=probe_trace(n,text,node);d=delta(bt,tr);ls=max([sim(d,p) for p in medoids],default=-1);ns=max([sim(d,p) for p in null],default=-1);cs.append((kind,text,ls,ns))
  # reachability ceiling is audited by full verifier but kept separate from ranking economics
  reachable_any=False
  for _,text,_,_ in cs:
   if full_score(n,text)==0:reachable_any=True;break
  if reachable_any:reachable.append(n)
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
  rows.append({'task':n,'probe':node,'candidate_count':len(cs),'reachable_success':reachable_any,'learned_success':lo,'coordinate_null_success':no,'hash_success':ho})
 gates={'preexisting_external_corpus':True,'no_correct_implementations_read':True,'rich_K_identical_across_arms':True,'nonzero_reachability_ceiling':bool(reachable),'verifier_improving_training_deltas_exist':bool(vecs),'learned_recovers_success':bool(learned),'learned_beats_coordinate_null':len(learned)>len(nulls),'learned_beats_hash_baseline':len(learned)>len(hashed)}
 verdict='PASS_RICH_K_PROTECTED_DYNAMIC_RANKING_V98' if all(gates.values()) else 'MIXED_RICH_K_PROTECTED_DYNAMIC_RANKING_V98'
 res={'protocol':'V98_RICH_K_PROTECTED_DYNAMIC_RANKING','external_commit':COMMIT,'train':train,'test':test,'probe_nodes':probe_nodes,'dims':DIMS,'train_rows':train_rows,'improving_delta_count':len(vecs),'mdl':mdl,'learned_solved':learned,'coordinate_null_solved':nulls,'hash_solved':hashed,'reachable_ceiling':reachable,'rows':rows,'gates':gates,'verdict':verdict,'qualification':'Natural verifier-only ranking bridge with a richer generic constructor K fixed identically across all arms. Correct implementations are never read. Cheap probe traces rank candidates; protected full-suite calls are spent only on top-B per ranking arm. An exhaustive reachability ceiling is computed separately and must be nonzero before ranking is interpreted. A PASS would support causal expensive-verifier savings from verifier-induced dynamic structure, not autonomous constructor or operator genesis.'}
 (OUT/'RESULT.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
if __name__=='__main__':main()
