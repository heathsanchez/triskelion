#!/usr/bin/env python3
import ast, difflib, hashlib, json, os
from collections import Counter
from pathlib import Path
ROOT=Path(os.environ.get('QUIXBUGS_DIR','/tmp/QuixBugs')); OUT=Path(os.environ.get('OUT_DIR','results/v93')); OUT.mkdir(parents=True,exist_ok=True)
COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'

def fp(x): return ast.dump(x,include_attributes=False) if isinstance(x,ast.AST) else repr(x)
def pathctx(path,d): return tuple(path[-d:]) if d else tuple()
def add(ev,kind,payload,path): ev.append({'kind':kind,'payload':tuple(payload),'path':tuple(path)})
def diff(a,b,path,ev):
 if isinstance(a,ast.AST) and isinstance(b,ast.AST):
  if type(a)!=type(b): add(ev,'TYPE',(type(a).__name__,type(b).__name__),path); return
  if isinstance(a,ast.Name) and a.id!=b.id:add(ev,'NAME_CHANGE',(),path)
  if isinstance(a,ast.Constant) and a.value!=b.value:add(ev,'CONST_CHANGE',(type(a.value).__name__,type(b.value).__name__),path)
  for f in getattr(a,'_fields',()):
   x,y=getattr(a,f),getattr(b,f); p2=path+(f'{type(a).__name__}.{f}',)
   if isinstance(x,ast.AST) and isinstance(y,ast.AST): diff(x,y,p2,ev)
   elif isinstance(x,list) and isinstance(y,list):
    xa=[q for q in x if isinstance(q,ast.AST)]; ya=[q for q in y if isinstance(q,ast.AST)]
    sm=difflib.SequenceMatcher(a=[fp(q) for q in xa],b=[fp(q) for q in ya],autojunk=False)
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
     if tag=='equal':
      for q,r in zip(xa[i1:i2],ya[j1:j2]): diff(q,r,p2,ev)
     elif tag=='replace' and (i2-i1)==(j2-j1):
      for q,r in zip(xa[i1:i2],ya[j1:j2]): diff(q,r,p2,ev)
     elif tag=='insert': add(ev,'INSERT',tuple(type(q).__name__ for q in ya[j1:j2]),p2)
     elif tag=='delete': add(ev,'DELETE',tuple(type(q).__name__ for q in xa[i1:i2]),p2)
     else: add(ev,'REPLACE_LIST',(tuple(type(q).__name__ for q in xa[i1:i2]),tuple(type(q).__name__ for q in ya[j1:j2])),p2)
   elif not isinstance(x,(ast.AST,list)) and x!=y and f not in ('lineno','col_offset','end_lineno','end_col_offset'):
    # Ignore literal identifier/value content; retain only field-level change type.
    add(ev,'FIELD_CHANGE',(type(a).__name__,f),p2)

def events_for(n):
 try:
  a=ast.parse((ROOT/'python_programs'/f'{n}.py').read_text()); b=ast.parse((ROOT/'correct_python_programs'/f'{n}.py').read_text()); ev=[]; diff(a,b,(),ev); return ev
 except Exception:return []
def key(e,d): return (e['kind'],e['payload'],pathctx(e['path'],d))
def shuffle_keys(keys,d):
 ks=sorted(keys,key=repr)
 if d==0:return set(ks)
 ctx=[k[2] for k in ks]
 return {(k[0],k[1],ctx[(i+1)%len(ctx)]) for i,k in enumerate(ks)} if ks else set()
def main():
 names=sorted([p.stem for p in (ROOT/'python_programs').glob('*.py') if (ROOT/'correct_python_programs'/f'{p.stem}.py').exists() and (ROOT/'python_testcases'/f'test_{p.stem}.py').exists()])
 raw={n:events_for(n) for n in names}; out={}
 for d in range(4):
  tr={n:set(key(e,d) for e in raw[n]) for n in names}; rep=[n for n in names if tr[n]]; rows=[]
  for s in range(100):
   seed=f'V93_D{d}_S{s:03d}'; order=sorted(names,key=lambda x:hashlib.sha256((seed+'|'+x).encode()).hexdigest()); cut=len(order)//2; train,test=order[:cut],order[cut:]
   cnt=Counter(k for n in train for k in tr[n]); learned={k for k,c in cnt.items() if c>=2}; null=shuffle_keys(learned,d); testrep=[n for n in test if tr[n]]
   cov=sum(bool(tr[n]&learned) for n in testrep); ncov=sum(bool(tr[n]&null) for n in testrep); den=len(testrep)
   rows.append({'split':s,'learned':len(learned),'test_representable':den,'coverage':cov/den if den else 0.0,'null_coverage':ncov/den if den else 0.0})
  mc=sum(r['coverage'] for r in rows)/100; mn=sum(r['null_coverage'] for r in rows)/100; wins=sum(r['coverage']>r['null_coverage'] for r in rows); ties=sum(r['coverage']==r['null_coverage'] for r in rows)
  cntall=Counter(k for n in names for k in tr[n]); recurrent=[{'event':repr(k),'support':c} for k,c in cntall.most_common() if c>=2]
  out[str(d)]={'representable_tasks':len(rep),'mean_coverage':mc,'mean_null_coverage':mn,'wins':wins,'ties':ties,'losses':100-wins-ties,'recurrent_count':len(recurrent),'top_recurrent':recurrent[:15],'splits':rows}
 best=max(range(4),key=lambda d:out[str(d)]['mean_coverage']-out[str(d)]['mean_null_coverage']); b=out[str(best)]
 gates={'preexisting_external_corpus':True,'automatic_tree_diff_includes_insert_delete':True,'most_tasks_representable':max(out[str(d)]['representable_tasks'] for d in range(4))>=30,'some_nonlocal_scale_beats_shuffle':any(out[str(d)]['mean_coverage']>out[str(d)]['mean_null_coverage'] for d in (1,2,3)),'best_scale_advantage_positive':b['mean_coverage']>b['mean_null_coverage']}
 res={'protocol':'V93_MULTISCALE_EDIT_ONTOLOGY','external_commit':COMMIT,'task_count':len(names),'scales':out,'best_depth':best,'gates':gates,'verdict':'PASS_MULTISCALE_EDIT_ONTOLOGY_V93' if all(gates.values()) else 'MIXED_MULTISCALE_EDIT_ONTOLOGY_V93','qualification':'Structural diagnostic, not causal constructor growth. Buggy/correct external pairs are used only to ask at what generic AST path scale automatically extracted repair events recur across 100 frozen splits. No semantic repair labels are supplied.'}
 (OUT/'RESULT.json').write_text(json.dumps(res,indent=2)); print(json.dumps({k:res[k] for k in ['task_count','best_depth','gates','verdict']},indent=2)); print(json.dumps({d:{k:v for k,v in out[d].items() if k!='splits'} for d in out},indent=2))
if __name__=='__main__':main()
