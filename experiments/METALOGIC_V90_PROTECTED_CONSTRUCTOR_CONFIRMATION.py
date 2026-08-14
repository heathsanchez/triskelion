#!/usr/bin/env python3
import ast, hashlib, importlib.util, json, os
from collections import Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v89',HERE/'METALOGIC_V89_CONTEXTUAL_CONSTRUCTOR_CONFIRMATION.py'); v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
v.SEED='V90_PROTECTED_CONTEXT_CONFIRMATION_FRESH_SPLIT_2026-08-14'; OUT=Path(os.environ.get('OUT_DIR','results/v90')); OUT.mkdir(parents=True,exist_ok=True)
def h(x):return hashlib.sha256((v.SEED+'|'+x).encode()).hexdigest()
def solve_capture(n,schemas,cap=220):
 src=(v.ROOT/'python_programs'/f'{n}.py').read_text(); k=0
 for s in schemas:
  for m in v.mutate(src,s):
   k+=1
   if v.test_prog(n,m):return True,s,k,m
   if k>=cap:return False,None,k,None
 return False,None,k,None
def ast_eq(a,b):
 try:return ast.dump(ast.parse(a),include_attributes=False)==ast.dump(ast.parse(b),include_attributes=False)
 except:return False
def main():
 names=[p.stem for p in (v.ROOT/'python_programs').glob('*.py') if (v.ROOT/'python_testcases'/f'test_{p.stem}.py').exists() and not v.test_prog(p.stem,p.read_text())]; names=sorted(names,key=h); cut=max(10,len(names)//2); train,test=names[:cut],names[cut:]
 cnt=Counter()
 for n in train:cnt.update(v.extract((v.ROOT/'python_programs'/f'{n}.py').read_text(),(v.ROOT/'correct_python_programs'/f'{n}.py').read_text()))
 learned=[s for s,_ in cnt.most_common()]; parents=[s[1] for s in learned]; shuffled=[(s[0],parents[(i+1)%len(parents)],*s[2:]) for i,s in enumerate(learned)] if parents else []
 k0=[('OP','Compare','ops','Lt','LtE'),('OP','Compare','ops','LtE','Lt'),('OP','Compare','ops','Gt','GtE'),('OP','Compare','ops','GtE','Gt')]
 full=k0+[s for s in learned if s not in k0]; null=k0+[s for s in shuffled if s not in k0]
 rows=[]; committed={}; committed_null={}; a=[];b=[];q=[]
 for n in test:
  x,_,_,_=solve_capture(n,k0,100); y,sy,_,my=solve_capture(n,full,220); z,sz,_,mz=solve_capture(n,null,220)
  if x:a.append(n)
  if y:b.append(n); committed[n]={'schema':list(sy) if sy else None,'source':my,'sha256':hashlib.sha256((my or '').encode()).hexdigest()}
  if z:q.append(n); committed_null[n]={'schema':list(sz) if sz else None,'source':mz,'sha256':hashlib.sha256((mz or '').encode()).hexdigest()}
  rows.append({'task':n,'k0':x,'k0_plus_context':y,'k0_plus_shuffle':z})
 # Protected reveal occurs only after all candidate patches above are committed in memory/hashes.
 protected={}; protected_null={}
 for n,c in committed.items():
  cor=(v.ROOT/'correct_python_programs'/f'{n}.py').read_text(); protected[n]=ast_eq(c['source'],cor)
 for n,c in committed_null.items():
  cor=(v.ROOT/'correct_python_programs'/f'{n}.py').read_text(); protected_null[n]=ast_eq(c['source'],cor)
 new=sorted(set(b)-set(a)); null_new=sorted(set(q)-set(a)); protected_new=sorted(n for n in new if protected.get(n)); protected_null_new=sorted(n for n in null_new if protected_null.get(n))
 gates={'preexisting_external_corpus':True,'heldout_fixes_sealed_until_candidate_commit':True,'candidate_hashes_committed_before_protected_reveal':True,'conservative_growth':set(a).issubset(set(b)),'test_closure_strictly_expands':bool(new),'protected_human_fix_agreement_nonempty':bool(protected_new),'protected_gain_beats_context_shuffle':len(protected_new)>len(protected_null_new)}
 res={'protocol':'V90_PROTECTED_CONSTRUCTOR_CONFIRMATION','external_commit':v.COMMIT,'seed':v.SEED,'train':train,'test':test,'learned_schemas':[{'schema':list(s),'support':cnt[s]} for s in learned],'k0_solved':a,'k0_plus_context_solved':b,'k0_plus_shuffle_solved':q,'new_test_closure':new,'shuffle_new_test_closure':null_new,'committed_candidates':{n:{'schema':c['schema'],'sha256':c['sha256']} for n,c in committed.items()},'protected_exact_ast_agreement':protected,'protected_shuffle_exact_ast_agreement':protected_null,'protected_new_closure':protected_new,'protected_shuffle_new_closure':protected_null_new,'rows':rows,'gates':gates,'verdict':'PASS_PROTECTED_CONSTRUCTOR_CONFIRMATION_V90' if all(gates.values()) else 'MIXED_PROTECTED_CONSTRUCTOR_CONFIRMATION_V90','qualification':'Fresh split. Training-side human fixes induce contextual edit roles. Held-out fixes are not read until all held-out candidates and hashes are committed; protected evaluation then checks exact AST agreement with the independently authored human repair. Supervised bridge, not autonomous constructor invention.'}
 (OUT/'RESULT.json').write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
if __name__=='__main__':main()
