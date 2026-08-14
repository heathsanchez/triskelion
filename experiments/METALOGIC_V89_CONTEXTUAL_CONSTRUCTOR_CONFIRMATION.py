#!/usr/bin/env python3
import ast, copy, hashlib, json, os, subprocess, sys
from collections import Counter
from pathlib import Path
ROOT=Path(os.environ.get('QUIXBUGS_DIR','/tmp/QuixBugs')); OUT=Path(os.environ.get('OUT_DIR','results/v89')); OUT.mkdir(parents=True,exist_ok=True)
SEED='V89_CONTEXTUAL_CONFIRMATION_FRESH_SPLIT_2026-08-14'; COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
def h(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def test_prog(n,text):
 p=ROOT/'python_programs'/f'{n}.py'; old=p.read_text()
 try:
  p.write_text(text); r=subprocess.run([sys.executable,'-m','pytest','-q',f'python_testcases/test_{n}.py','--timeout=4'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20); return r.returncode==0
 except Exception:return False
 finally:p.write_text(old)
OPBASE=(ast.cmpop,ast.operator,ast.boolop,ast.unaryop)
OPS=[ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.Eq,ast.NotEq,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv,ast.Mod,ast.And,ast.Or,ast.Not,ast.USub]; OPMAP={x.__name__:x for x in OPS}
def diff(a,b,parent,field,c):
 if isinstance(a,ast.AST) and isinstance(b,ast.AST):
  if type(a)!=type(b):
   if isinstance(a,OPBASE) and isinstance(b,OPBASE): c[('OP',type(parent).__name__ if parent else 'ROOT',field,type(a).__name__,type(b).__name__)]+=1
   return
  if isinstance(a,ast.Name) and a.id!=b.id:c[('NAME',type(parent).__name__ if parent else 'ROOT',field)]+=1
  if isinstance(a,ast.Constant) and a.value!=b.value and isinstance(a.value,(int,float,bool)):c[('CONST',type(parent).__name__ if parent else 'ROOT',field,type(a.value).__name__)]+=1
  for f in getattr(a,'_fields',()):
   x,y=getattr(a,f),getattr(b,f)
   if isinstance(x,ast.AST) and isinstance(y,ast.AST):diff(x,y,a,f,c)
   elif isinstance(x,list) and isinstance(y,list) and len(x)==len(y):
    for p,q in zip(x,y):
     if isinstance(p,ast.AST) and isinstance(q,ast.AST):diff(p,q,a,f,c)
def extract(src,cor):
 c=Counter()
 try:diff(ast.parse(src),ast.parse(cor),None,'root',c)
 except Exception:pass
 return c
def positions(tree,parent,field):
 out=[]
 for p in ast.walk(tree):
  if type(p).__name__!=parent:continue
  v=getattr(p,field,None)
  if isinstance(v,ast.AST):out.append((p,field,None,v))
  elif isinstance(v,list):
   for i,x in enumerate(v):
    if isinstance(x,ast.AST):out.append((p,field,i,x))
 return out
def mutate(src,s,cap=80):
 try:t=ast.parse(src)
 except:return []
 kind,parent,field,*rest=s; pos=positions(t,parent,field); out=[]
 if kind=='OP':
  old,new=OPMAP.get(rest[0]),OPMAP.get(rest[1])
  if not old or not new:return []
  for idx,(_,_,_,x) in enumerate(pos):
   if not isinstance(x,old):continue
   z=copy.deepcopy(t); p,f,i,_=positions(z,parent,field)[idx]; nv=new(); setattr(p,f,nv) if i is None else getattr(p,f).__setitem__(i,nv)
   try:out.append(ast.unparse(ast.fix_missing_locations(z)))
   except:pass
 elif kind=='NAME':
  names=sorted({x.id for x in ast.walk(t) if isinstance(x,ast.Name)})
  for idx,(_,_,_,x) in enumerate(pos):
   if not isinstance(x,ast.Name):continue
   for rep in names:
    if rep==x.id:continue
    z=copy.deepcopy(t); p,f,i,q=positions(z,parent,field)[idx]; nv=copy.deepcopy(q); nv.id=rep; setattr(p,f,nv) if i is None else getattr(p,f).__setitem__(i,nv)
    try:out.append(ast.unparse(ast.fix_missing_locations(z)))
    except:pass
    if len(out)>=cap:return out
 elif kind=='CONST':
  for idx,(_,_,_,x) in enumerate(pos):
   if not (isinstance(x,ast.Constant) and isinstance(x.value,(int,float,bool))):continue
   for rep in [-1,0,1,2]:
    if rep==x.value:continue
    z=copy.deepcopy(t); p,f,i,q=positions(z,parent,field)[idx]; nv=copy.deepcopy(q); nv.value=rep; setattr(p,f,nv) if i is None else getattr(p,f).__setitem__(i,nv)
    try:out.append(ast.unparse(ast.fix_missing_locations(z)))
    except:pass
    if len(out)>=cap:return out
 return out[:cap]
def solve(n,schemas,cap=220):
 src=(ROOT/'python_programs'/f'{n}.py').read_text(); k=0
 for s in schemas:
  for m in mutate(src,s):
   k+=1
   if test_prog(n,m):return True,s,k
   if k>=cap:return False,None,k
 return False,None,k
def main():
 names=[p.stem for p in (ROOT/'python_programs').glob('*.py') if (ROOT/'python_testcases'/f'test_{p.stem}.py').exists() and not test_prog(p.stem,p.read_text())]; names=sorted(names,key=h); cut=max(10,len(names)//2); train,test=names[:cut],names[cut:]
 cnt=Counter()
 for n in train:cnt.update(extract((ROOT/'python_programs'/f'{n}.py').read_text(),(ROOT/'correct_python_programs'/f'{n}.py').read_text()))
 learned=[s for s,_ in cnt.most_common()]
 parents=[s[1] for s in learned]; shuffled=[(s[0],parents[(i+1)%len(parents)],*s[2:]) for i,s in enumerate(learned)] if parents else []
 k0=[('OP','Compare','ops','Lt','LtE'),('OP','Compare','ops','LtE','Lt'),('OP','Compare','ops','Gt','GtE'),('OP','Compare','ops','GtE','Gt')]
 full=k0+[s for s in learned if s not in k0]; null=k0+[s for s in shuffled if s not in k0]
 a=[];b=[];q=[]; rows=[]
 for n in test:
  x,_,_=solve(n,k0,100); y,sy,_=solve(n,full,220); z,_,_=solve(n,null,220)
  if x:a.append(n)
  if y:b.append(n)
  if z:q.append(n)
  rows.append({'task':n,'k0':x,'k0_plus_context':y,'k0_plus_context_shuffle':z,'winning_schema':list(sy) if sy else None})
 new=sorted(set(b)-set(a)); null_new=sorted(set(q)-set(a)); conservative=set(a).issubset(set(b))
 gates={'preexisting_external_corpus':True,'heldout_correct_files_sealed':True,'nonempty_contextual_grammar':bool(learned),'conservative_growth':conservative,'heldout_closure_strictly_expands':bool(new),'contextual_gain_beats_shuffle':len(new)>len(null_new)}
 res={'protocol':'V89_CONTEXTUAL_CONSTRUCTOR_CONFIRMATION','external_commit':COMMIT,'seed':SEED,'train':train,'test':test,'learned_schemas':[{'schema':list(s),'support':cnt[s]} for s in learned],'k0_solved':a,'k0_plus_context_solved':b,'k0_plus_context_shuffle_solved':q,'new_closure':new,'shuffle_new_closure':null_new,'rows':rows,'gates':gates,'verdict':'PASS_CONTEXTUAL_CONSTRUCTOR_CONFIRMATION_V89' if all(gates.values()) else 'MIXED_CONTEXTUAL_CONSTRUCTOR_CONFIRMATION_V89','qualification':'Fresh-split confirmation after V88. Supervised bridge only: contextual AST edit roles are learned from training-side human fixes; held-out correct implementations are never read. K1 is monotonic K0 plus learned schemas.'}
 (OUT/'RESULT.json').write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
if __name__=='__main__':main()
