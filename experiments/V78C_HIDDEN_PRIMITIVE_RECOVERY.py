import types,itertools,json,random
ns={}; src=open('experiments/V78_ALPHABET_COLLIDER_CALIBRATION.py').read().split('W=make_worlds()')[0]; exec(src,ns)
m=types.SimpleNamespace(**ns); OPS=m.OPS

# deterministic decoy state transformations independent of operator labels
def clone(s):
    return m.State(dict(s.data),list(s.candidates),dict(s.evidence),set(s.relations),list(s.constraints),dict(s.classes),s.selected,s.composed,s.retained,s.depth)

def decoy(name,s,w):
    s=clone(s)
    if name=='DUP_CAND' and s.candidates: s.candidates=s.candidates+[s.candidates[0]]; return s
    if name=='DROP_LAST' and len(s.candidates)>1: s.candidates=s.candidates[:-1]; return s
    if name=='REVERSE' and len(s.candidates)>1: s.candidates=list(reversed(s.candidates)); return s
    if name=='CLEAR_REL' and s.relations: s.relations.clear(); return s
    if name=='CLEAR_CLASS' and s.classes: s.classes.clear(); return s
    if name=='COPY_EVID' and s.evidence: s.data['copy']=next(iter(s.evidence.values())); return s
    if name=='INC_DEPTH': s.depth+=1; return s
    if name=='DEC_DEPTH' and s.depth>0: s.depth-=1; return s
    if name=='ADD_ZERO' and 0 not in s.candidates: s.candidates.append(0); return s
    if name=='SORT' and s.candidates!=sorted(s.candidates): s.candidates=sorted(s.candidates); return s
    return None
DECOYS=['DUP_CAND','DROP_LAST','REVERSE','CLEAR_REL','CLEAR_CLASS','COPY_EVID','INC_DEPTH','DEC_DEPTH','ADD_ZERO','SORT']

def canon(s): return m.canon(s)

def solve_with_extra(w, allowed, extra_name=None, extra_impl=None, max_depth=8):
    s0=m.init_state(w); q=[(s0,[])]; seen={canon(s0)}
    actions=[('BASE:'+op,lambda s,op=op:m.apply(op,s,w)) for op in allowed]
    if extra_name:
        if extra_impl in OPS:
            actions.append((extra_name,lambda s,op=extra_impl:m.apply(op,s,w)))
        else:
            actions.append((extra_name,lambda s,n=extra_impl:decoy(n,s,w)))
    while q:
        s,path=q.pop(0)
        if m.goal(s,w): return path
        if len(path)>=max_depth: continue
        for name,fn in actions:
            ns=fn(s)
            if ns is None: continue
            c=canon(ns)
            if c in seen: continue
            np=path+[name]
            if m.goal(ns,w): return np
            seen.add(c); q.append((ns,np))
    return None

def recover(seed):
    W=m.make_worlds(seed=seed,n_per=8)
    rr=random.Random(seed+999)
    W=[m.World(w.family, tuple((k,(rr.sample(v,len(v)) if k=='candidates' and w.family=='relation' else v)) for k,v in w.payload), w.hidden) for w in W]
    rows=[]
    for missing in OPS:
        allowed=[x for x in OPS if x!=missing]
        gaps=[w for w in W if m.solve(w,OPS) is not None and m.solve(w,allowed) is None]
        pool=[('omega_true',missing)]+[(f'decoy_{i}',d) for i,d in enumerate(DECOYS)]
        scores=[]
        for opaque,impl in pool:
            score=sum(solve_with_extra(w,allowed,opaque,impl) is not None for w in gaps)
            scores.append((score,opaque,impl))
        scores.sort(reverse=True)
        rows.append({'missing':missing,'gaps':len(gaps),'best':scores[0],'runner_up':scores[1], 'unique_correct':scores[0][2]==missing and scores[0][0]>scores[1][0]})
    return rows

runs={seed:recover(seed) for seed in range(200,205)}
print('all_unique_recovery',all(r['unique_correct'] for rows in runs.values() for r in rows))
for r in runs[200]: print(r)

# Short-composition equivalence audit on encountered pre-states from one seed.
W=m.make_worlds(seed=7,n_per=8)
rr=random.Random(1006)
W=[m.World(w.family, tuple((k,(rr.sample(v,len(v)) if k=='candidates' and w.family=='relation' else v)) for k,v in w.payload), w.hidden) for w in W]
prestates={op:[] for op in OPS}
for w in W:
    p=m.solve(w,OPS)
    if p is None: continue
    s=m.init_state(w)
    for op in p:
        prestates[op].append((w,s))
        s=m.apply(op,s,w)

def find_equiv(missing,maxlen=3):
    cases=prestates[missing]
    others=[x for x in OPS if x!=missing]
    # only require exact same result on every encountered applicable case
    for L in range(1,maxlen+1):
        for seq in itertools.product(others, repeat=L):
            ok=True
            for w,s in cases:
                target=m.apply(missing,s,w)
                cur=s
                for op in seq:
                    cur=m.apply(op,cur,w)
                    if cur is None: break
                if target is None or cur is None or canon(target)!=canon(cur): ok=False; break
            if ok: return seq
    return None

equiv={op:find_equiv(op,3) for op in OPS}
print('short_equiv',equiv)
out={'seeds':list(runs),'all_unique_recovery':all(r['unique_correct'] for rows in runs.values() for r in rows),'example_seed':runs[200],'short_composition_equivalence_depth3':equiv}
open('/tmp/v78c_result.json','w').write(json.dumps(out,indent=2))
