import importlib.util, sys, random, heapq, itertools, json
import types
m=types.SimpleNamespace()
ns={}
src=open('/tmp/alphabet_collider.py').read().split('W=make_worlds()')[0]
exec(src,ns)
for k,v in ns.items(): setattr(m,k,v)
OPS=m.OPS; W=m.make_worlds(seed=7,n_per=20)

def solve_forbid(w, forbidden, max_depth=8):
    s0=m.init_state(w); q=[(s0,[])]; seen={m.canon(s0)}
    while q:
        s,path=q.pop(0)
        if m.goal(s,w): return path
        if len(path)>=max_depth: continue
        for op in OPS:
            if path and (path[-1],op) in forbidden: continue
            ns=m.apply(op,s,w)
            if ns is None: continue
            c=m.canon(ns)
            if c in seen: continue
            np=path+[op]
            if m.goal(ns,w): return np
            seen.add(c); q.append((ns,np))
    return None

base=[m.solve(w,OPS) for w in W]
from collections import Counter
mot=Counter()
for p in base:
    for e in zip(p,p[1:]): mot[e]+=1
edge_effect=[]
for e,count in mot.items():
    solved=sum(solve_forbid(w,{e}) is not None for w in W)
    edge_effect.append({'edge':e,'trace_count':count,'solved_when_forbidden':solved,'loss':len(W)-solved})
edge_effect.sort(key=lambda x:(-x['loss'],-x['trace_count']))
print('EDGE EFFECTS')
for x in edge_effect: print(x)

# Macro planner: an action can be one primitive (cost 1) or a whole sequence (cost 1).
def apply_seq(seq,s,w):
    cur=s
    for op in seq:
        cur=m.apply(op,cur,w)
        if cur is None: return None
    return cur

def min_cost(w, macros=(), max_steps=8):
    s0=m.init_state(w); start=m.canon(s0)
    pq=[(0,0,s0,[])] ; best={start:0}; uid=0
    actions=[(op,(op,)) for op in OPS] + [(f'MACRO:{"->".join(seq)}',tuple(seq)) for seq in macros]
    while pq:
        cost,_,s,path=heapq.heappop(pq)
        if m.goal(s,w): return cost,path
        if len(path)>=max_steps: continue
        if cost>best.get(m.canon(s),999): continue
        for name,seq in actions:
            ns=apply_seq(seq,s,w)
            if ns is None: continue
            nc=m.canon(ns); new=cost+1
            if new<best.get(nc,999):
                best[nc]=new; uid+=1; heapq.heappush(pq,(new,uid,ns,path+[name]))
    return None,None

base_cost=[]
for w in W:
    c,_=min_cost(w,()); base_cost.append(c)

cands=[('CONSTRAIN','SELECT'),('PROBE','DISTINGUISH'),('PROBE','TRANSDUCE'),('DISTINGUISH','CONSTRAIN'),('TRANSDUCE','CONSTRAIN'),('RELATE','CONSTRAIN'),('SELECT','RETAIN'),('RECURSE','COMPOSE'),('COMPOSE','RETAIN')]
macro_results=[]
for seq in cands:
    costs=[min_cost(w,(seq,))[0] for w in W]
    savings=sum(b-c for b,c in zip(base_cost,costs) if b is not None and c is not None)
    helped=sum(c<b for b,c in zip(base_cost,costs) if b is not None and c is not None)
    macro_results.append((savings,helped,seq))
print('MACROS',sorted(macro_results,reverse=True))

# Random/shuffled length-2 macro nulls; exclude real edges and self-pairs.
rng=random.Random(123)
observed=set(mot.keys())
allpairs=[p for p in itertools.permutations(OPS,2) if p not in observed]
null=[]
for seq in rng.sample(allpairs,min(60,len(allpairs))):
    costs=[min_cost(w,(seq,))[0] for w in W]
    savings=sum(b-c for b,c in zip(base_cost,costs) if b is not None and c is not None)
    helped=sum(c<b for b,c in zip(base_cost,costs) if b is not None and c is not None)
    null.append((savings,helped,seq))
print('NULL mean savings',sum(x[0] for x in null)/len(null),'max',max(x[0] for x in null))

# Multi-macro basis using top useful macros simultaneously.
use=[x[2] for x in sorted(macro_results,reverse=True) if x[0]>0]
costs=[min_cost(w,use)[0] for w in W]
print('multi_macro', 'macros',use,'base_cost',sum(base_cost),'macro_cost',sum(costs),'saving',sum(base_cost)-sum(costs))

out={'n':len(W),'edge_effects':edge_effect,'macro_results':[{'seq':x[2],'savings':x[0],'helped':x[1]} for x in sorted(macro_results,reverse=True)],'null_mean_savings':sum(x[0] for x in null)/len(null),'null_max_savings':max(x[0] for x in null),'multi_macros':use,'base_cost':sum(base_cost),'multi_macro_cost':sum(costs)}
open('/tmp/v78b_result.json','w').write(json.dumps(out,indent=2))
