#!/usr/bin/env python3
import ast, hashlib, importlib.util, json, os, re, subprocess, sys
from collections import Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v89',HERE/'METALOGIC_V89_CONTEXTUAL_CONSTRUCTOR_CONFIRMATION.py'); v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
ROOT=v.ROOT; OUT=Path(os.environ.get('OUT_DIR','results/v91')); OUT.mkdir(parents=True,exist_ok=True)
SEED='V91_VERIFIER_INDUCED_SITE_ONTOLOGY_2026-08-14'; COMMIT=v.COMMIT
def h(x):return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def fail_count(n,text):
 p=ROOT/'python_programs'/f'{n}.py'; old=p.read_text()
 try:
  p.write_text(text); r=subprocess.run([sys.executable,'-m','pytest','-q',f'python_testcases/test_{n}.py','--timeout=4','--tb=no'],cwd=ROOT,capture_output=True,text=True,timeout=20)
  if r.returncode==0:return 0
  s=(r.stdout or '')+' '+(r.stderr or ''); m=re.search(r'(\d+) failed',s)
  return int(m.group(1)) if m else 999
 except Exception:return 999
 finally:p.write_text(old)
def roles(src):
 try:t=ast.parse(src)
 except:return []
 out=set()
 for p in ast.walk(t):
  for f in getattr(p,'_fields',()):
   x=getattr(p,f,None); xs=x if isinstance(x,list) else [x]
   for q in xs:
    if isinstance(q,ast.Name):out.add(('NAME',type(p).__name__,f))
    elif isinstance(q,ast.Constant) and isinstance(q.value,(int,float,bool)):out.add(('CONST',type(p).__name__,f))
    elif isinstance(q,(ast.cmpop,ast.operator,ast.boolop,ast.unaryop)):out.add(('OP',type(p).__name__,f))
 return sorted(out)
def concrete(src,role):
 kind,parent,field=role
 if kind in ('NAME','CONST'):return [(kind,parent,field)]
 try:t=ast.parse(src)
 except:return []
 ops=['Lt','LtE','Gt','GtE','Eq','NotEq','Add','Sub','Mult','Div','FloorDiv','Mod','And','Or','Not','USub']; seen=set(); out=[]
 for p in ast.walk(t):
  if type(p).__name__!=parent:continue
  x=getattr(p,field,None); xs=x if isinstance(x,list) else [x]
  for q in xs:
   if isinstance(q,(ast.cmpop,ast.operator,ast.boolop,ast.unaryop)):
    old=type(q).__name__
    for new in ops:
     if new!=old and (old,new) not in seen: seen.add((old,new)); out.append(('OP',parent,field,old,new))
 return out
def probe_role(n,role,max_mutants=8):
 src=(ROOT/'python_programs'/f'{n}.py').read_text(); base=fail_count(n,src); best=base; tested=0
 for s in concrete(src,role):
  for m in v.mutate(src,s,cap=max_mutants):
   tested+=1; best=min(best,fail_count(n,m))
   if tested>=max_mutants:return base,best,tested
 return base,best,tested
def solve_roles(n,role_set,cap=240):
 src=(ROOT/'python_programs'/f'{n}.py').read_text(); schemas=[]
 for r in role_set:schemas.extend(concrete(src,r))
 return v.solve(n,schemas,cap)
def main():
 names=[p.stem for p in (ROOT/'python_programs').glob('*.py') if (ROOT/'python_testcases'/f'test_{p.stem}.py').exists() and not v.test_prog(p.stem,p.read_text())]; names=sorted(names,key=h); train=names[:12]; test=names[12:]
 support=Counter(); probe_rows=[]
 for n in train:
  src=(ROOT/'python_programs'/f'{n}.py').read_text()
  for r in roles(src)[:30]:
   base,best,k=probe_role(n,r)
   improved=best<base
   if improved:support[r]+=1
   probe_rows.append({'task':n,'role':list(r),'base_fail':base,'best_fail':best,'tested':k,'improved':improved})
 learned=[r for r,c in support.most_common() if c>=2]
 parents=[r[1] for r in learned]; shuffled=[(r[0],parents[(i+1)%len(parents)],r[2]) for i,r in enumerate(learned)] if parents else []
 k0=[('OP','Compare','ops','Lt','LtE'),('OP','Compare','ops','LtE','Lt'),('OP','Compare','ops','Gt','GtE'),('OP','Compare','ops','GtE','Gt')]
 a=[];b=[];q=[]; rows=[]
 for n in test:
  x,_,_=v.solve(n,k0,100); y,sy,_=solve_roles(n,learned,240); z,sz,_=solve_roles(n,shuffled,240)
  if x:a.append(n)
  if y:b.append(n)
  if z:q.append(n)
  rows.append({'task':n,'k0':x,'verifier_roles':y,'shuffled_roles':z,'winner':list(sy) if sy else None})
 new=sorted(set(b)-set(a)); null_new=sorted(set(q)-set(a))
 gates={'preexisting_external_corpus':True,'correct_implementations_never_read':True,'nonempty_verifier_induced_roles':bool(learned),'heldout_closure_strictly_expands':bool(new),'verifier_roles_beat_shuffled_roles':len(new)>len(null_new)}
 res={'protocol':'V91_VERIFIER_INDUCED_SITE_ONTOLOGY','external_commit':COMMIT,'seed':SEED,'train':train,'test':test,'role_support':[{'role':list(r),'support':c} for r,c in support.most_common()],'learned_roles':[list(r) for r in learned],'probe_rows':probe_rows,'k0_solved':a,'verifier_role_solved':b,'shuffled_role_solved':q,'new_closure':new,'shuffle_new_closure':null_new,'rows':rows,'gates':gates,'verdict':'PASS_VERIFIER_INDUCED_SITE_ONTOLOGY_V91' if all(gates.values()) else 'MIXED_VERIFIER_INDUCED_SITE_ONTOLOGY_V91','qualification':'No correct implementations are read. Training constructs operational site-role classes only from whether generic typed perturbations reduce externally verified failing-test counts. Held-out repair search is restricted to learned roles and compared with a matched context shuffle. Bounded natural bridge, not full autonomous constructor genesis.'}
 (OUT/'RESULT.json').write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
if __name__=='__main__':main()
