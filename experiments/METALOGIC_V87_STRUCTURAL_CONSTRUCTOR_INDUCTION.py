#!/usr/bin/env python3
import ast, copy, hashlib, json, os, subprocess, sys
from collections import Counter
from pathlib import Path
ROOT=Path(os.environ.get('QUIXBUGS_DIR','/tmp/QuixBugs')); OUT=Path(os.environ.get('OUT_DIR','results/v87')); OUT.mkdir(parents=True,exist_ok=True)
SEED='V87_STRUCTURAL_CONSTRUCTOR_2026-08-14'; COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
def h(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def test_prog(n,text):
 p=ROOT/'python_programs'/f'{n}.py'; old=p.read_text()
 try:
  p.write_text(text); r=subprocess.run([sys.executable,'-m','pytest','-q',f'python_testcases/test_{n}.py','--timeout=4'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20); return r.returncode==0
 except Exception:return False
 finally:p.write_text(old)
OPS=(ast.cmpop,ast.operator,ast.boolop,ast.unaryop)
def diff_nodes(a,b,c):
 if type(a)!=type(b):
  if isinstance(a,OPS) and isinstance(b,OPS): c[('NODETYPE',type(a).__name__,type(b).__name__)]+=1
  return
 if isinstance(a,ast.Name) and a.id!=b.id: c[('NAME_ROLE',)]+=1
 if isinstance(a,ast.Constant) and a.value!=b.value: c[('CONST_ROLE',type(a.value).__name__)]+=1
 for f in getattr(a,'_fields',()):
  x,y=getattr(a,f),getattr(b,f)
  if isinstance(x,ast.AST) and isinstance(y,ast.AST): diff_nodes(x,y,c)
  elif isinstance(x,list) and isinstance(y,list) and len(x)==len(y):
   for p,q in zip(x,y):
    if isinstance(p,ast.AST) and isinstance(q,ast.AST): diff_nodes(p,q,c)
def schemas(bug,cor):
 c=Counter();
 try: diff_nodes(ast.parse(bug),ast.parse(cor),c)
 except Exception: pass
 return c
OPCLASSES={x.__name__:x for x in [ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.Eq,ast.NotEq,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv,ast.Mod,ast.And,ast.Or,ast.Not,ast.USub]}
def candidates(src,sch,cap=180):
 try: tree=ast.parse(src)
 except:return []
 out=[]
 if sch[0]=='NODETYPE':
  old,new=OPCLASSES.get(sch[1]),OPCLASSES.get(sch[2])
  if not old or not new:return []
  for target in [x for x in ast.walk(tree) if isinstance(x,old)]:
   z=copy.deepcopy(tree); zs=[x for x in ast.walk(z) if isinstance(x,old)]
   idx=[x for x in ast.walk(tree) if isinstance(x,old)].index(target); zs[idx].__class__=new
   try: out.append(ast.unparse(ast.fix_missing_locations(z)))
   except:pass
 elif sch[0]=='NAME_ROLE':
  names=sorted({x.id for x in ast.walk(tree) if isinstance(x,ast.Name)})
  ns=[x for x in ast.walk(tree) if isinstance(x,ast.Name)]
  for i,node in enumerate(ns):
   for rep in names:
    if rep==node.id:continue
    z=copy.deepcopy(tree); zn=[x for x in ast.walk(z) if isinstance(x,ast.Name)]; zn[i].id=rep
    try: out.append(ast.unparse(ast.fix_missing_locations(z)))
    except:pass
    if len(out)>=cap:return out
 elif sch[0]=='CONST_ROLE':
  vals=[-1,0,1,2]; cs=[x for x in ast.walk(tree) if isinstance(x,ast.Constant) and isinstance(x.value,int)]
  for i,node in enumerate(cs):
   for rep in vals:
    if rep==node.value:continue
    z=copy.deepcopy(tree); zc=[x for x in ast.walk(z) if isinstance(x,ast.Constant) and isinstance(x.value,int)]; zc[i].value=rep
    try: out.append(ast.unparse(ast.fix_missing_locations(z)))
    except:pass
    if len(out)>=cap:return out
 return out[:cap]
def solve(n,ss,cap=240):
 src=(ROOT/'python_programs'/f'{n}.py').read_text(); k=0
 for s in ss:
  for m in candidates(src,s,cap):
   k+=1
   if test_prog(n,m):return True,s,k
   if k>=cap:return False,None,k
 return False,None,k
def main():
 names=[p.stem for p in (ROOT/'python_programs').glob('*.py') if (ROOT/'python_testcases'/f'test_{p.stem}.py').exists() and not test_prog(p.stem,p.read_text())]; names=sorted(names,key=h); cut=max(10,len(names)//2); train,test=names[:cut],names[cut:]
 cnt=Counter()
 for n in train:
  cnt.update(schemas((ROOT/'python_programs'/f'{n}.py').read_text(),(ROOT/'correct_python_programs'/f'{n}.py').read_text()))
 learned=[s for s,_ in cnt.most_common()]
 # wrong-pair structural control
 wrongc=Counter(); perm=train[1:]+train[:1]
 for n,c in zip(train,perm): wrongc.update(schemas((ROOT/'python_programs'/f'{n}.py').read_text(),(ROOT/'correct_python_programs'/f'{c}.py').read_text()))
 wrong=[s for s,_ in wrongc.most_common()]
 k0=[('NODETYPE','Lt','LtE'),('NODETYPE','LtE','Lt'),('NODETYPE','Gt','GtE'),('NODETYPE','GtE','Gt')]
 rows=[]; a=[];b=[];w=[]
 for n in test:
  x,sx,_=solve(n,k0,120); y,sy,_=solve(n,learned,240); z,sz,_=solve(n,wrong,240)
  if x:a.append(n)
  if y:b.append(n)
  if z:w.append(n)
  rows.append({'task':n,'k0':x,'k1':y,'wrong':z,'schema':list(sy) if sy else None})
 new=sorted(set(b)-set(a)); gates={'preexisting_external_corpus':True,'heldout_correct_files_read':False,'nonempty_structural_grammar':bool(learned),'heldout_closure_strictly_expands':bool(new),'beats_wrong_pair_control':len(b)>len(w)}
 res={'protocol':'V87_STRUCTURAL_CONSTRUCTOR_INDUCTION','external_commit':COMMIT,'train':train,'test':test,'learned_schemas':[{'schema':list(s),'support':cnt[s]} for s in learned],'k0_solved':a,'k1_solved':b,'wrong_pair_solved':w,'new_closure':new,'rows':rows,'gates':gates,'verdict':'PASS_STRUCTURAL_CONSTRUCTOR_INDUCTION_V87' if all(gates.values()) else 'MIXED_STRUCTURAL_CONSTRUCTOR_INDUCTION_V87','qualification':'Supervised bridge: structural edit schemas are induced from training-side human fixes only; held-out correct implementations remain sealed. Not autonomous constructor invention.'}
 (OUT/'RESULT.json').write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
if __name__=='__main__':main()
