#!/usr/bin/env python3
import hashlib, importlib.util, json, os
from collections import Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v89',HERE/'METALOGIC_V89_CONTEXTUAL_CONSTRUCTOR_CONFIRMATION.py'); v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
ROOT=v.ROOT; OUT=Path(os.environ.get('OUT_DIR','results/v92')); OUT.mkdir(parents=True,exist_ok=True)
COMMIT=v.COMMIT

def role_key(s):
 # Remove concrete replacement payload for OP; retain contextual site + change kind.
 return tuple(s[:3])

def task_roles(n):
 src=(ROOT/'python_programs'/f'{n}.py').read_text(); cor=(ROOT/'correct_python_programs'/f'{n}.py').read_text()
 return set(role_key(s) for s in v.extract(src,cor))

def shuffled_roles(rs):
 rs=sorted(rs)
 if not rs:return set()
 parents=[r[1] for r in rs]
 return {(r[0],parents[(i+1)%len(parents)],r[2]) for i,r in enumerate(rs)}

def main():
 names=sorted([p.stem for p in (ROOT/'python_programs').glob('*.py') if (ROOT/'correct_python_programs'/f'{p.stem}.py').exists() and (ROOT/'python_testcases'/f'test_{p.stem}.py').exists()])
 tr={n:task_roles(n) for n in names}; representable=[n for n in names if tr[n]]
 rows=[]
 for k in range(100):
  seed=f'V92_SPLIT_{k:03d}'
  order=sorted(names,key=lambda x:hashlib.sha256((seed+'|'+x).encode()).hexdigest()); cut=len(order)//2; train,test=order[:cut],order[cut:]
  cnt=Counter(r for n in train for r in tr[n]); learned={r for r,c in cnt.items() if c>=2}; null=shuffled_roles(learned)
  test_rep=[n for n in test if tr[n]]
  covered=[n for n in test_rep if tr[n]&learned]; null_cov=[n for n in test_rep if tr[n]&null]
  rows.append({'split':k,'learned_roles':len(learned),'test_representable':len(test_rep),'covered':len(covered),'null_covered':len(null_cov),'coverage':len(covered)/len(test_rep) if test_rep else 0.0,'null_coverage':len(null_cov)/len(test_rep) if test_rep else 0.0})
 mean=lambda xs:sum(xs)/len(xs) if xs else 0.0
 cov=[r['coverage'] for r in rows]; nul=[r['null_coverage'] for r in rows]
 wins=sum(a>b for a,b in zip(cov,nul)); ties=sum(a==b for a,b in zip(cov,nul))
 allcnt=Counter(r for n in names for r in tr[n]); recurrent=[{'role':list(r),'support':c} for r,c in allcnt.most_common() if c>=2]
 gates={'preexisting_external_corpus':True,'all_roles_extracted_automatically':True,'nonempty_recurrent_roles':bool(recurrent),'mean_coverage_beats_context_shuffle':mean(cov)>mean(nul),'majority_splits_beat_shuffle':wins>50}
 res={'protocol':'V92_CONTEXT_ROLE_CROSSVALIDATION','external_commit':COMMIT,'task_count':len(names),'representable_task_count':len(representable),'recurrent_roles':recurrent,'splits':rows,'summary':{'mean_coverage':mean(cov),'mean_null_coverage':mean(nul),'wins':wins,'ties':ties,'losses':100-wins-ties},'gates':gates,'verdict':'PASS_CONTEXT_ROLE_CROSSVALIDATION_V92' if all(gates.values()) else 'MIXED_CONTEXT_ROLE_CROSSVALIDATION_V92','qualification':'Structural diagnostic only. Human fixes are used on both sides solely to test whether automatically extracted local edit-role ontology recurs across 100 frozen splits. This is not a causal capability or constructor-growth result.'}
 (OUT/'RESULT.json').write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
if __name__=='__main__':main()
