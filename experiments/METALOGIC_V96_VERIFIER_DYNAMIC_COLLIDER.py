#!/usr/bin/env python3
import importlib.util,json,math,os,re,subprocess,sys,tempfile
from pathlib import Path
BASE=Path(__file__).with_name('METALOGIC_V94_DYNAMIC_STATE_INVARIANTS.py')
spec=importlib.util.spec_from_file_location('v94base',BASE); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ROOT=m.ROOT; DIMS=m.DIMS; candidates=m.candidates; delta=m.delta; sim=m.sim; permute=m.permute; h=m.h; tracer_code=m.tracer_code
OUT=Path(os.environ.get('OUT_DIR','results/v96')); OUT.mkdir(parents=True,exist_ok=True)
COMMIT=m.COMMIT; TRAIN_N=8; TEST_N=8; TRAIN_CAP=30; TEST_CAP=40; VERIFY_BUDGET=8; MAX_POINTS=20; MAX_K=5; LAMBDA=.2

def run_score(name,text):
    p=ROOT/'python_programs'/f'{name}.py'; old=p.read_text(); td=Path(tempfile.mkdtemp(prefix='v96_')); (td/'sitecustomize.py').write_text(tracer_code()); tf=td/'trace.json'
    env=os.environ.copy(); env['PYTHONPATH']=str(td)+os.pathsep+env.get('PYTHONPATH',''); env['V94_TARGET']=name; env['V94_TRACE_OUT']=str(tf)
    try:
        p.write_text(text)
        r=subprocess.run([sys.executable,'-m','pytest','-q',f'python_testcases/test_{name}.py','--timeout=4'],cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=25)
        out=r.stdout or ''
        if r.returncode==0: score=0
        else:
            z=re.search(r'(\d+) failed',out)
            if z: score=int(z.group(1))
            else:
                z=re.search(r'(\d+) error',out); score=100+int(z.group(1)) if z else 99
        tr=json.loads(tf.read_text()) if tf.exists() else {k:0 for k in DIMS}
        return score,tr
    except Exception:
        return 999,{k:0 for k in DIMS}
    finally:
        p.write_text(old)
        try:
            for q in td.iterdir(): q.unlink()
            td.rmdir()
        except Exception: pass

def choose(vs):
    if not vs:return [],None
    pts=vs[:]
    best=None
    for k in range(1,min(MAX_K,len(pts))+1):
        # deterministic greedy k-medoids approximation, frozen before results
        first=min(range(len(pts)),key=lambda i:(sum(1-sim(pts[i],x) for x in pts),i)); inds=[first]
        while len(inds)<k:
            rem=[i for i in range(len(pts)) if i not in inds]
            nxt=max(rem,key=lambda i:(min(1-sim(pts[i],pts[j]) for j in inds),-i)); inds.append(nxt)
        meds=[pts[i] for i in inds]
        loss=sum(1-max(sim(v,p) for p in meds) for v in pts)+LAMBDA*k
        key=(round(loss,12),k,tuple(inds))
        if best is None or key<best[0]:best=(key,meds,inds,loss)
    return best[1],{'k':len(best[1]),'indices':best[2],'objective':best[3]}

def main():
    buggy=ROOT/'python_programs'; tests=ROOT/'python_testcases'
    names=[]
    for p in buggy.glob('*.py'):
        n=p.stem
        if not (tests/f'test_{n}.py').exists():continue
        s,_=run_score(n,p.read_text())
        if s>0:names.append(n)
    names=sorted(names,key=lambda x:h('v96|'+x)); train=names[:TRAIN_N]; test=names[TRAIN_N:TRAIN_N+TEST_N]
    improving=[]; probe_rows=[]
    for n in train:
        src=(buggy/f'{n}.py').read_text(); base,bt=run_score(n,src); found=[]
        for text in candidates(src,TRAIN_CAP):
            sc,tr=run_score(n,text)
            if sc<base:
                d=delta(bt,tr); found.append({'score':sc,'gain':base-sc,'delta':d})
                improving.append((base-sc,n,d))
        probe_rows.append({'task':n,'base_score':base,'improving_count':len(found),'best_gain':max([x['gain'] for x in found],default=0)})
    improving=sorted(improving,key=lambda x:(-x[0],h('pt|'+x[1]+'|'+json.dumps(x[2]))))[:MAX_POINTS]
    vecs=[x[2] for x in improving]; medoids,mdl=choose(vecs); null=[permute(v) for v in medoids]
    learned=[]; shuffled=[]; reachable=[]; rows=[]
    for n in test:
        src=(buggy/f'{n}.py').read_text(); base,bt=run_score(n,src); cs=[]
        for text in candidates(src,TEST_CAP):
            sc,tr=run_score(n,text); d=delta(bt,tr)
            ls=max([sim(d,p) for p in medoids],default=-1); ns=max([sim(d,p) for p in null],default=-1)
            cs.append((text,sc,ls,ns))
        if any(x[1]==0 for x in cs): reachable.append(n)
        lr=sorted(cs,key=lambda x:(-x[2],h('L|'+x[0])))[:VERIFY_BUDGET]
        nr=sorted(cs,key=lambda x:(-x[3],h('N|'+x[0])))[:VERIFY_BUDGET]
        lo=any(x[1]==0 for x in lr); no=any(x[1]==0 for x in nr)
        if lo:learned.append(n)
        if no:shuffled.append(n)
        rows.append({'task':n,'base_score':base,'reachable_success':any(x[1]==0 for x in cs),'learned_budget_success':lo,'null_budget_success':no,'best_candidate_score':min([x[1] for x in cs],default=999)})
    gates={'preexisting_external_corpus':True,'no_correct_implementations_read_anywhere':True,'verifier_improving_training_deltas_exist':bool(vecs),'anonymous_dynamic_clusters_formed':bool(medoids),'reachable_heldout_success_exists':bool(reachable),'learned_clusters_recover_heldout_success':bool(learned),'learned_clusters_beat_coordinate_null':len(learned)>len(shuffled)}
    verdict='PASS_VERIFIER_DYNAMIC_COLLIDER_V96' if all(gates.values()) else 'MIXED_VERIFIER_DYNAMIC_COLLIDER_V96'
    res={'protocol':'V96_VERIFIER_DYNAMIC_COLLIDER','external_commit':COMMIT,'train':train,'test':test,'dims':DIMS,'probe_rows':probe_rows,'improving_delta_count':len(vecs),'mdl':mdl,'medoids':medoids,'null_medoids':null,'learned_solved':learned,'null_solved':shuffled,'unrestricted_reachable':reachable,'rows':rows,'gates':gates,'verdict':verdict,'qualification':'Natural verifier-only bridge. No correct implementation is read on training or held-out tasks. Training structure comes only from execution-state deltas of generic mutations that reduce externally measured test failures. Anonymous dynamic medoids are chosen by a frozen MDL objective; held-out candidate syntax and verifier budgets are identical in learned/null arms. A PASS would support verifier-induced transferable dynamic structure, not yet unrestricted operator synthesis.'}
    (OUT/'RESULT.json').write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
if __name__=='__main__':main()
