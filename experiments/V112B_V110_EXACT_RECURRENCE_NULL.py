from __future__ import annotations
from collections import Counter, defaultdict
from itertools import combinations
import json
from pathlib import Path

TOKENS=['<','>','<=','>=','==','!=']
DUAL={'<':'>','>':'<','<=':'>=','>=':'<='}
OBS_COUNTS={'knapsack':2,'next_permutation':4,'quicksort':4}
SOURCE_OPS={'knapsack':['<'],'next_permutation':['<','<'],'quicksort':['<','>']}
OUT=Path('artifacts/v112b_v110_exact_recurrence_null'); OUT.mkdir(parents=True,exist_ok=True)

def qkey(sig):
    s,t,sw=sig
    if s not in DUAL or t not in DUAL:return ('NON_ORDER',s,t,int(sw))
    a=(s,t,int(sw)); b=(DUAL[s],DUAL[t],int(sw))
    return ('ORDER',)+min(a,b)

def universe(ops):
    U=[]
    for site,s in enumerate(ops):
        for sw in (False,True):
            for t in TOKENS:
                if not sw and t==s: continue
                sig=(s,t,int(sw))
                U.append((site,sig,qkey(sig)))
    return U

def compressed_states(U,k):
    c=Counter()
    for inds in combinations(range(len(U)),k):
        m=defaultdict(set)
        for i in inds:
            _,sig,q=U[i]
            if q[0]=='ORDER': m[q].add(sig)
        state=tuple(sorted((q,tuple(sorted(sigs))) for q,sigs in m.items()))
        c[state]+=1
    return c

def event(states):
    byq=defaultdict(list)
    for pi,st in enumerate(states):
        for q,sigs in st: byq[q].append((pi,set(sigs)))
    recurrent=0; diverse=0
    for q,arr in byq.items():
        if len({p for p,_ in arr})>=2:
            recurrent+=1
            lits=set()
            for _,ss in arr:lits |= ss
            if len(lits)>=2: diverse+=1
    return recurrent>=2 and diverse>=2

def main():
    U={p:universe(SOURCE_OPS[p]) for p in OBS_COUNTS}
    C={p:compressed_states(U[p],OBS_COUNTS[p]) for p in OBS_COUNTS}
    total=0; hits=0
    for sk,wk in C['knapsack'].items():
        for sn,wn in C['next_permutation'].items():
            for sq,wq in C['quicksort'].items():
                w=wk*wn*wq; total += w
                if event((sk,sn,sq)): hits += w
    p=hits/total
    R={
      'canonical_id':'V112B_V110_EXACT_RECURRENCE_NULL',
      'conditioned_program_pass_counts':OBS_COUNTS,
      'candidate_universe_sizes':{p:len(U[p]) for p in U},
      'raw_combination_space':total,
      'event_count':hits,
      'exact_probability':p,
      'event_definition':'recurrent_count>=2 AND diverse_recurrent_count>=2',
      'significant_at_0_05':p<=0.05,
      'compressed_state_counts':{p:len(C[p]) for p in C},
      'interpretation':'Exact conditional identity-randomization audit of the V112 event. This removes Monte Carlo error but remains conditioned on the three V110 repaired programs and their observed pass counts; it is not a population-level p-value.'
    }
    (OUT/'RESULT.json').write_text(json.dumps(R,indent=2,sort_keys=True)+'\n')
    print(json.dumps(R,indent=2,sort_keys=True))
if __name__=='__main__': main()
