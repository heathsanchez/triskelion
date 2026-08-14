#!/usr/bin/env python3
import ast, copy, hashlib, json, os, subprocess, sys
from collections import Counter
from pathlib import Path
ROOT=Path(os.environ.get('QUIXBUGS_DIR','/tmp/QuixBugs')); OUT=Path(os.environ.get('OUT_DIR','results/v88')); OUT.mkdir(parents=True,exist_ok=True)
SEED='V88_CONTEXTUAL_CONSTRUCTOR_2026-08-14'; COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
def h(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def test_prog(n,text):
 p=ROOT/'python_programs'/f'{n}.py'; old=p.read_text()
 try:
  p.write_text(text); r=subprocess.run([sys.executable,'-m','pytest','-q',f'python_testcases/test_{n}.py','--timeout=4'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20); return r.returncode==0
 except Exception:return False
 finally:p.write_text(old)
OPBASE=(ast.cmpop,ast.operator,ast.boolop,ast.unaryop)
OPMAP={x.__name__:x for x in [ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.Eq,ast.NotEq,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv,ast.Mod,ast.And,ast.Or,ast.Not,ast.USub]}
def diff(a,b,parent,field,c):
 if isinstance(a,ast.AST) and isinstance(b,ast.AST):
  if type(a)!=type(b):
   if isinstance(a,OPBASE) and isinstance(b,OPBASE): c[('OP',type(parent).__name__ if parent else 'ROOT',field,type(a).__name__,type(b).__name__)]+=1
   return
  if isinstance(a,ast.Name) and a.id!=b.id: c[('NAME',type(parent).__name__ if parent else 'ROOT',field)]+=1
  if isinstance(a,ast.Constant) and a.value!=b.value and isinstance(a.value,(int,float,bool)): c[('CONST',type(parent).__name__ if parent else 'ROOT',field,type(a.value).__name__)]+=1
  for f in getattr(a,'_fields',()):
   x,y=getattr(a,f),getattr(b,f)
   if isinstance(x,ast.AST) and isinstance(y,ast.AST): diff(x,y,a,f,c)
   elif isinstance(x,list) and isinstance(y,list) and len(x)==len(y):
    for i,(p,q) in enumerate(zip(x,y)):
     if isinstance(p,ast.AST) and isinstance(q,ast.AST): diff(p,q,a,f,c)
def extract(src,cor):
 c=Counter()
 try: diff(ast.parse(src),ast.parse(cor),None,'root',c)
 except Exception:pass
 return c
def positions(tree,parent_name,field):
 out=[]
 for p in ast.walk(tree):
  if type(p).__name__!=parent_name: continue
  v=getattr(p,field,None)
  if isinstance(v,ast.AST): out.append((p,field,None,v))
  elif isinstance(v,list):
   for i,x in enumerate(v):
    if isinstance(x,ast.AST): out.append((p,field,i,x))
 return out
def mutate(src,schema,cap=100):
 try: tree=ast.parse(src)
 except:return []
 kind,parent,field,*rest=schema; pos=positions(tree,parent,field); out=[]
 if kind=='OP':
  old,new=OPMAP.get(rest[0]),OPMAP.get(rest[1]);
  if not old or not new:return []
  valid=[k for k,(_,_,_,x) in enumerate(pos) if isinstance(x,old)]
  for idx in valid:
   z=copy.deepcopy(tree); zp=positions(z,parent,field); p,f,i,x=zp[idx]; nv=new()
   if i is None:setattr(p,f,nv)
   else:getattr(p,f)[i]=nv
   try:out.append(ast.unparse(ast.fix_missing_locations(z)))
   except:pass
 elif kind=='NAME':
  names=sorted({x.id for x in ast.walk(tree) if isinstance(x,ast.Name)})
  valid=[k for k,(_,_,_,x) in enumerate(pos) if isinstance(x,ast.Name)]
  for idx in valid:
   for rep in names:
    if rep==pos[idx][3].id:continue
    z=copy.deepcopy(tree); zp=positions(z,parent,field); p,f,i,x=zp[idx]; nv=copy.deepcopy(x); nv.id=rep
    if i is None:setattr(p,f,nv)
    else:getattr(p,f)[i]=nv
    try:out.append(ast.unparse(ast.fix_missing_locations(z)))
    except:pass
    if len(out)>=cap:return out
 elif kind=='CONST':
  vals=[-1,0,1,2]; valid=[k for k,(_,_,_,x) in enumerate(pos) if isinstance(x,ast.Constant) and isinstance(x.value,(int,float,bool))]
  for idx in valid:
   for rep in vals:
    if rep==pos[idx][3].value:continue
    z=copy.deepcopy(tree); zp=positions(z,parent,field); p,f,i,x=zp[idx]; nv=copy.deepcopy(x); nv.value=rep
    if i is None:setattr(p,f,nv)
    else:getattr(p,f)[i]=nv
    try:out.append(ast.unparse(ast.fix_missing_locations(z)))
    except:pass
    if len(out)>=cap:return out
 return out[:cap]
def solve(n,schemas,cap=180):
 src=(ROOT/'python_programs'/f'{n}.py').read_text(); k=0
 for s in schemas:
  for m in mutate(src,s,80):
   k+=1
   if test_prog(n,m):return True,s,k
   if k>=cap:return False,None,k
 return False,None,k
def main():
 names=[p.stem for p in (ROOT/'python_programs').glob('*.py') if (ROOT/'python_testcases'/f'test_{p.stem}.py').exists() and not test_prog(p.stem,p.read_text())]; names=sorted(names,key=h); cut=max(10,len(names)//2); train,test=names[:cut],names[cut:]
 cnt=Counter()
 for n in train:cnt.update(extract((ROOT/'python_programs'/f'{n}.py').read_text(),(ROOT/'correct_python_programs'/f'{n}.py').read_text()))
 learned=[s for s,_ in cnt.most_common()]
 # context-shuffle null: rotate parent labels among learned schemas, preserving change payloads
 parents=[s[1] for s in learned]; shuffled=[]
 for i,s in enumerate(learned): shuffled.append((s[0],parents[(i+1)%len(parents)],*s[2:])) if parents else None
 k0=[('OP','Compare','ops','Lt','LtE'),('OP','Compare','ops','LtE','Lt'),('OP','Compare','ops','Gt','GtE'),('OP','Compare','ops','GtE','Gt')]
 rows=[]; a=[];b=[];q=[]
 for n in test:
  x,sx,_=solve(n,k0,100); y,sy,_=solve(n,learned,180); z,sz,_=solve(n,shuffled,180)
  if x:a.append(n)
  if y:b.append(n)
  if z:q.append(n)
  rows.append({'task':n,'k0':x,'k1':y,'context_shuffle':z,'schema':list(sy) if sy else None})
 new=sorted(set(b)-set(a)); gates={'preexisting_external_corpus':True,'heldout_correct_files_read':False,'nonempty_contextual_grammar':bool(learned),'heldout_closure_strictly_expands':bool(new),'beats_context_shuffle':len(b)>len(q)}
 res={'protocol':'V88_CONTEXTUAL_CONSTRUCTOR_INDUCTION','external_commit':COMMIT,'train':train,'test':test,'learned_schemas':[{'schema':list(s),'support':cnt[s]} for s in learned],'k0_solved':a,'k1_solved':b,'context_shuffle_solved':q,'new_closure':new,'rows':rows,'gates':gates,'verdict':'PASS_CONTEXTUAL_CONSTRUCTOR_INDUCTION_V88' if all(gates.values()) else 'MIXED_CONTEXTUAL_CONSTRUCTOR_INDUCTION_V88','qualification':'Supervised bridge: contextual AST edit roles are induced from training-side human fixes only; held-out correct implementations remain sealed. Context is parent-type/field plus change kind. Not autonomous constructor invention.'}
 (OUT/'RESULT.json').write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
if __name__=='__main__':main()
