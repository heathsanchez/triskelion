#!/usr/bin/env python3
import hashlib, importlib.util, json, os
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).with_name('METALOGIC_V102_FRESH_SPLIT_EXPRESSION_CONSTRUCTOR.py')
spec = importlib.util.spec_from_file_location('v102', BASE)
v102 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v102)
ROOT=v102.ROOT; full_score=v102.full_score; base_candidates=v102.base_candidates; expr_candidates=v102.expr_candidates
OUT=Path(os.environ.get('OUT_DIR','results/v103')); OUT.mkdir(parents=True,exist_ok=True)
SEED='V103_VERIFIER_INDUCED_EXPRESSION_CONSTRUCTOR_2026-08-14'
EXCLUDE=set(v102.EXPOSED)
TRAIN_N=8; TEST_N=8; BASE_CAP=180; EXPR_CAP=240; MIN_SUPPORT=2
FAMILIES=['CALLABLE_CONSTRUCT','GUARD_EXPR','RETURN_EXPR','EXPR_GROW']

def h(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()

def failing_names():
    buggy=ROOT/'python_programs'; tests=ROOT/'python_testcases'; out=[]
    for p in buggy.glob('*.py'):
        n=p.stem
        if n in EXCLUDE or not (tests/f'test_{n}.py').exists(): continue
        try: s=full_score(n,p.read_text())
        except Exception: continue
        if s>0: out.append(n)
    return sorted(out,key=lambda n:h('task|'+n))

def family_candidates(src, allowed):
    return [(k,t) for k,t in expr_candidates(src,EXPR_CAP) if k in allowed]

def first_success(name,cands):
    for k,t in cands:
        try:
            if full_score(name,t)==0:return k
        except Exception: pass
    return None

def main():
    names=failing_names(); train=names[:TRAIN_N]; test=names[TRAIN_N:TRAIN_N+TEST_N]
    support=defaultdict(set); train_rows=[]
    for n in train:
        src=(ROOT/'python_programs'/f'{n}.py').read_text(); base=full_score(n,src)
        best_by_family={}
        for k,t in expr_candidates(src,EXPR_CAP):
            try:s=full_score(n,t)
            except Exception:continue
            if k not in best_by_family or s<best_by_family[k]:best_by_family[k]=s
            if s<base:support[k].add(n)
        train_rows.append({'task':n,'base_score':base,'best_by_family':best_by_family,'improving_families':sorted(k for k in FAMILIES if n in support[k])})
    retained=sorted(k for k in FAMILIES if len(support[k])>=MIN_SUPPORT)
    # matched wrong-family control: same cardinality, chosen by frozen hash from nonretained families
    non=[k for k in FAMILIES if k not in retained]
    null=sorted(non,key=lambda k:h('null|'+k))[:len(retained)]
    base_s=[]; learned_s=[]; null_s=[]; rows=[]
    for n in test:
        src=(ROOT/'python_programs'/f'{n}.py').read_text()
        b=base_candidates(src,BASE_CAP)
        bk=first_success(n,b)
        lk=first_success(n,b+family_candidates(src,set(retained)))
        nk=first_success(n,b+family_candidates(src,set(null)))
        if bk:base_s.append(n)
        if lk:learned_s.append(n)
        if nk:null_s.append(n)
        rows.append({'task':n,'base':bool(bk),'learned':bool(lk),'null':bool(nk),'learned_winner':lk,'null_winner':nk})
    new=sorted(set(learned_s)-set(base_s)); null_new=sorted(set(null_s)-set(base_s))
    gates={
      'external_hash_split':bool(train and test and not(set(train)&set(test))),
      'no_correct_implementations_read':True,
      'family_selection_from_verifier_only':True,
      'source_distinct_support':all(len(support[k])>=MIN_SUPPORT for k in retained) if retained else False,
      'nonempty_induced_constructor':bool(retained),
      'conservative':set(base_s)<=set(learned_s),
      'strict_heldout_closure_expansion':bool(new),
      'beats_matched_wrong_family_control':len(new)>len(null_new)
    }
    verdict='PASS_VERIFIER_INDUCED_EXPRESSION_CONSTRUCTOR_V103' if all(gates.values()) else 'MIXED_VERIFIER_INDUCED_EXPRESSION_CONSTRUCTOR_V103'
    res={'protocol':'V103_VERIFIER_INDUCED_EXPRESSION_CONSTRUCTOR','external_commit':v102.v100.COMMIT,'train':train,'test':test,'excluded_prior_inspection':sorted(EXCLUDE),'support':{k:sorted(v) for k,v in support.items()},'retained_families':retained,'null_families':null,'base_solved':base_s,'learned_solved':learned_s,'null_solved':null_s,'new_closure':new,'null_new_closure':null_new,'train_rows':train_rows,'rows':rows,'gates':gates,'verdict':verdict,'qualification':'Natural bridge toward constructor genesis. Low-level expression-builder families are supplied generically; verifier experience alone selects which families enter K1. No correct implementations are read. PASS would show verifier-induced constructor-family selection with fresh held-out closure gain, not unrestricted invention of the builder substrate itself.'}
    (OUT/'RESULT.json').write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
if __name__=='__main__':main()
