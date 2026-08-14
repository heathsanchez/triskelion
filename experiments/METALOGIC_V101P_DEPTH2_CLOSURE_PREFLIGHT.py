#!/usr/bin/env python3
import importlib.util, json, os, hashlib
from pathlib import Path

BASE=Path(__file__).with_name('METALOGIC_V100_BALANCED_K_CROSS_SOURCE_ORGANS.py')
spec=importlib.util.spec_from_file_location('v100base',BASE)
v100=importlib.util.module_from_spec(spec); spec.loader.exec_module(v100)
ROOT=v100.v99.ROOT
full_score=v100.v99.full_score
balanced=v100.balanced_rich_candidates
OUT=Path(os.environ.get('OUT_DIR','results/v101p')); OUT.mkdir(parents=True,exist_ok=True)
SEED='V101P_DEPTH2_CLOSURE_PREFLIGHT_2026-08-14'
TASKS=['breadth_first_search','sieve','subsequences','find_in_sorted']
FIRST_CAP=60
SECOND_PER_PARENT=24
TOTAL_CAP=240

def h(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()

def depth2(src):
    first=balanced(src,FIRST_CAP)
    out=[]; seen={src}
    for k1,s1 in first:
        for k2,s2 in balanced(s1,SECOND_PER_PARENT):
            if s2 in seen: continue
            seen.add(s2); out.append((k1+'>'+k2,s2))
    out=sorted(out,key=lambda z:h(z[0]+'|'+z[1]))[:TOTAL_CAP]
    return first,out

def main():
    rows=[]
    for n in TASKS:
        src=(ROOT/'python_programs'/f'{n}.py').read_text()
        base=full_score(n,src)
        first,second=depth2(src)
        d1=[]; d2=[]
        for kind,text in first:
            sc=full_score(n,text)
            if sc==0: d1.append(kind)
        for kind,text in second:
            sc=full_score(n,text)
            if sc==0: d2.append(kind)
        rows.append({'task':n,'base_score':base,'depth1_candidates':len(first),'depth2_candidates':len(second),'depth1_successes':d1,'depth2_successes':d2,'depth1_reachable':bool(d1),'depth2_reachable':bool(d2)})
    res={'protocol':'V101P_DEPTH2_CLOSURE_PREFLIGHT_NONCLAIM','status':'NONCLAIM_DIAGNOSTIC_ONLY','external_commit':v100.v99.COMMIT,'tasks':TASKS,'first_cap':FIRST_CAP,'second_per_parent':SECOND_PER_PARENT,'total_depth2_cap':TOTAL_CAP,'rows':rows,'depth1_reachable':[r['task'] for r in rows if r['depth1_reachable']],'depth2_reachable':[r['task'] for r in rows if r['depth2_reachable']],'qualification':'Closure-before-invention diagnostic only. Tests whether bounded depth-2 composition of the existing balanced generic edit families reaches held-out tasks that were unreachable under depth 1. No new primitive or learned semantic category is added.'}
    (OUT/'RESULT.json').write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
if __name__=='__main__': main()
