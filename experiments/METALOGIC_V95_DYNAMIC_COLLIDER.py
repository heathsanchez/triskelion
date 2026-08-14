#!/usr/bin/env python3
import importlib.util,itertools,json,math,os
from pathlib import Path
BASE=Path(__file__).with_name('METALOGIC_V94_DYNAMIC_STATE_INVARIANTS.py')
spec=importlib.util.spec_from_file_location('v94base',BASE); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ROOT=m.ROOT; DIMS=m.DIMS; run=m.run; candidates=m.candidates; delta=m.delta; sim=m.sim; permute=m.permute; h=m.h
OUT=Path(os.environ.get('OUT_DIR','results/v95')); OUT.mkdir(parents=True,exist_ok=True)
COMMIT=m.COMMIT; TRAIN_N=10; TEST_N=8; CAND_CAP=40; VERIFY_BUDGET=8; MAX_K=5; LAMBDA=.18

def choose_medoids(vs):
    if not vs:return [],None
    best=None
    n=len(vs)
    for k in range(1,min(MAX_K,n)+1):
        for inds in itertools.combinations(range(n),k):
            meds=[vs[i] for i in inds]
            loss=sum(1-max(sim(v,p) for p in meds) for v in vs)+LAMBDA*k
            key=(round(loss,12),k,inds)
            if best is None or key<best[0]:best=(key,meds,inds,loss)
    return best[1],{'k':len(best[1]),'indices':list(best[2]),'objective':best[3]}

def main():
    buggy=ROOT/'python_programs'; correct=ROOT/'correct_python_programs'; tests=ROOT/'python_testcases'
    names=[]
    for p in buggy.glob('*.py'):
        n=p.stem
        if not (tests/f'test_{n}.py').exists() or not (correct/f'{n}.py').exists():continue
        ok,_=run(n,p.read_text())
        if not ok:names.append(n)
    names=sorted(names,key=lambda x:h('v95|'+x)); train=names[:TRAIN_N]; test=names[TRAIN_N:TRAIN_N+TEST_N]
    train_vecs=[]; train_rows=[]
    for n in train:
        b=(buggy/f'{n}.py').read_text(); c=(correct/f'{n}.py').read_text()
        bok,bt=run(n,b); cok,ct=run(n,c); d=delta(bt,ct)
        if cok and any(abs(x)>0 for x in d):train_vecs.append(d)
        train_rows.append({'task':n,'bug_pass':bok,'correct_pass':cok,'delta':d})
    medoids,mdl=choose_medoids(train_vecs); null=[permute(v) for v in medoids]
    learned=[]; shuffled=[]; unrestricted=[]; rows=[]
    for n in test:
        src=(buggy/f'{n}.py').read_text(); _,base=run(n,src); cs=[]
        for text in candidates(src,CAND_CAP):
            ok,tr=run(n,text); d=delta(base,tr)
            ls=max([sim(d,p) for p in medoids],default=-1); ns=max([sim(d,p) for p in null],default=-1)
            cs.append((text,ok,ls,ns))
        anyok=any(x[1] for x in cs)
        if anyok:unrestricted.append(n)
        lr=sorted(cs,key=lambda x:(-x[2],h('L|'+x[0])))[:VERIFY_BUDGET]
        nr=sorted(cs,key=lambda x:(-x[3],h('N|'+x[0])))[:VERIFY_BUDGET]
        lo=any(x[1] for x in lr); no=any(x[1] for x in nr)
        if lo:learned.append(n)
        if no:shuffled.append(n)
        rows.append({'task':n,'reachable':anyok,'learned_budget_success':lo,'null_budget_success':no,'candidate_count':len(cs),'top_learned':[round(x[2],5) for x in lr[:4]],'top_null':[round(x[3],5) for x in nr[:4]]})
    gates={'external_corpus_preexisting':True,'heldout_correct_never_read':True,'nonempty_training_deltas':bool(train_vecs),'anonymous_mdl_clusters_formed':bool(medoids),'reachable_heldout_repairs_exist':bool(unrestricted),'learned_clusters_recover_success':bool(learned),'learned_clusters_beat_coordinate_null':len(learned)>len(shuffled)}
    verdict='PASS_DYNAMIC_COLLIDER_V95' if all(gates.values()) else 'MIXED_DYNAMIC_COLLIDER_V95'
    res={'protocol':'V95_DYNAMIC_COLLIDER','external_commit':COMMIT,'train':train,'test':test,'dims':DIMS,'train_rows':train_rows,'training_delta_count':len(train_vecs),'mdl':mdl,'medoids':medoids,'null_medoids':null,'learned_solved':learned,'null_solved':shuffled,'unrestricted_reachable':unrestricted,'rows':rows,'gates':gates,'verdict':verdict,'qualification':'Natural supervised bridge. Independently authored correct implementations are opened only on the frozen training split to produce anonymous execution-delta vectors. Cluster number and medoids are selected by a frozen MDL objective with no semantic labels. Held-out correct implementations are never read. A PASS would show transferable anonymous dynamic structure under a matched verification budget, not autonomous genesis from verifier residuals alone.'}
    (OUT/'RESULT.json').write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
if __name__=='__main__':main()
