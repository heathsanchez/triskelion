import random, json
from dataclasses import dataclass

SEED=7804

# V78D: two falsification questions.
# (A) Is a relation-forming transform genuinely necessary once position/ID leaks are removed?
# (B) Is RECURSE better classified as a semantic atom or as a generic control combinator?

@dataclass(frozen=True)
class RelWorld:
    items: tuple          # opaque_id, x, y
    target_gap: int
    answer: int


def make_rel_worlds(n=400, seed=SEED):
    r=random.Random(seed); out=[]
    for _ in range(n):
        gap=r.randint(2,11)
        ids=r.sample(range(100000,999999),7)
        answer_pos=r.randrange(7)
        items=[]; used={gap}
        for j in range(7):
            g=gap if j==answer_pos else r.choice([z for z in range(1,16) if z not in used])
            used.add(g)
            x=r.randint(-100,100); y=x+r.choice([-1,1])*g
            items.append((ids[j],x,y))
        answer=ids[answer_pos]
        r.shuffle(items)
        out.append(RelWorld(tuple(items),gap,answer))
    return out

REL_WORLDS=make_rel_worlds()

def candidate(name,w):
    ids=[z[0] for z in w.items]
    if name=='PAIR_METRIC':
        hits=[ident for ident,x,y in w.items if abs(x-y)==w.target_gap]
        return hits[0] if len(hits)==1 else None
    if name=='PICK_FIRST': return ids[0]
    if name=='PICK_LAST': return ids[-1]
    if name=='MIN_ID': return min(ids)
    if name=='MAX_ID': return max(ids)
    if name=='MIN_X': return min(w.items,key=lambda z:z[1])[0]
    if name=='MAX_X': return max(w.items,key=lambda z:z[1])[0]
    if name=='MIN_Y': return min(w.items,key=lambda z:z[2])[0]
    if name=='MAX_Y': return max(w.items,key=lambda z:z[2])[0]
    if name=='MIN_RAW_DIFF': return min(w.items,key=lambda z:(z[2]-z[1]))[0]
    if name=='MAX_RAW_DIFF': return max(w.items,key=lambda z:(z[2]-z[1]))[0]
    return None

CANDS=['PAIR_METRIC','PICK_FIRST','PICK_LAST','MIN_ID','MAX_ID','MIN_X','MAX_X','MIN_Y','MAX_Y','MIN_RAW_DIFF','MAX_RAW_DIFF']
scores={c:sum(candidate(c,w)==w.answer for w in REL_WORLDS) for c in CANDS}

# Pair-breaking null preserves opaque IDs and all x/y marginals but destroys the
# within-item relation. If PAIR_METRIC is causal, its advantage should collapse.
null=[]
for t in range(300):
    rr=random.Random(SEED+1000+t); good=0
    for w in REL_WORLDS:
        ys=[z[2] for z in w.items]; rr.shuffle(ys)
        ww=RelWorld(tuple((ident,x,y) for (ident,x,_),y in zip(w.items,ys)),w.target_gap,w.answer)
        good += candidate('PAIR_METRIC',ww)==ww.answer
    null.append(good)

# Cross-family transfer: a distinct relational predicate (sum rather than gap)
# tests whether the useful abstraction is 'form a relation over paired fields'
# rather than memorizing absolute difference.
@dataclass(frozen=True)
class SumWorld:
    items:tuple
    target_sum:int
    answer:int

def make_sum_worlds(n=200, seed=SEED+2):
    r=random.Random(seed); out=[]
    for _ in range(n):
        ids=r.sample(range(100000,999999),6); pos=r.randrange(6)
        target=r.randint(-50,50); items=[]; used={target}
        for j in range(6):
            if j==pos:
                x=r.randint(-60,60); y=target-x
            else:
                s=r.choice([z for z in range(-90,91) if z not in used]); used.add(s)
                x=r.randint(-60,60); y=s-x
            items.append((ids[j],x,y))
        ans=ids[pos]; r.shuffle(items); out.append(SumWorld(tuple(items),target,ans))
    return out
SUM_WORLDS=make_sum_worlds()
def generic_pair_relation(items,target,relation_fn):
    hits=[ident for ident,x,y in items if relation_fn(x,y)==target]
    return hits[0] if len(hits)==1 else None
sum_transfer=sum(generic_pair_relation(w.items,w.target_sum,lambda x,y:x+y)==w.answer for w in SUM_WORLDS)

# -------------------- RECURSION --------------------
@dataclass(frozen=True)
class IterWorld:
    start:int
    stop:int
    delta:int

def make_iter_worlds(n=400, seed=SEED+1):
    r=random.Random(seed); out=[]
    for _ in range(n):
        d=r.choice([1,2,3,4,5]); steps=r.randint(5,60); a=r.randint(-100,100)
        out.append(IterWorld(a,a+d*steps,d))
    return out
ITER=make_iter_worlds()
def step(x,w): return x if x>=w.stop else min(w.stop,x+w.delta)
def semantic_recurse(w):
    x=w.start
    for _ in range(10000):
        if x==w.stop:return x
        x=step(x,w)
    return None
def fixed_point(value, step_fn, done, cap=10000):
    x=value
    for _ in range(cap):
        if done(x):return x
        nx=step_fn(x)
        if nx==x:return x
        x=nx
    return None
def grammar_recurse(w): return fixed_point(w.start,lambda x:step(x,w),lambda x:x==w.stop)
def unroll(w,k):
    x=w.start
    for _ in range(k):x=step(x,w)
    return x
sem=sum(semantic_recurse(w)==w.stop for w in ITER)
gram=sum(grammar_recurse(w)==w.stop for w in ITER)
unroll_scores={k:sum(unroll(w,k)==w.stop for w in ITER) for k in [1,2,4,8,16,32]}
extensional=all(semantic_recurse(w)==grammar_recurse(w) for w in ITER)

# Same fixed-point controller transferred without modification across distinct
# state types and step semantics.
transfer=[]
for x in [64,128,256,1024,4096]:
    transfer.append(fixed_point(x,lambda z:max(1,z//2),lambda z:z==1)==1)
for s in ['abcdefgh','0123456789','metalogic','triskelion','verification']:
    transfer.append(len(fixed_point(s,lambda z:z[:-1] if len(z)>2 else z,lambda z:len(z)==2))==2)
for xs in [[1,2,3,4,5],[9,8,7,6],[3,1,4,1,5,9]]:
    transfer.append(len(fixed_point(xs,lambda z:z[:-1] if len(z)>1 else z,lambda z:len(z)==1))==1)

result={
 'protocol':'V78D_RELATE_RECURSE_HARDENED',
 'seed':SEED,
 'relate':{
   'worlds':len(REL_WORLDS),'candidate_scores':scores,
   'unique_best':scores['PAIR_METRIC']==len(REL_WORLDS) and sum(v==scores['PAIR_METRIC'] for v in scores.values())==1,
   'pair_break_null_mean':sum(null)/len(null),'pair_break_null_max':max(null),
   'cross_relation_family_transfer':sum_transfer,'cross_relation_family_total':len(SUM_WORLDS),
   'classification':'SEMANTIC_RELATION_OPERATOR_SUPPORTED' if scores['PAIR_METRIC']==len(REL_WORLDS) and sum_transfer==len(SUM_WORLDS) else 'UNRESOLVED'
 },
 'recurse':{
   'worlds':len(ITER),'semantic_recurse_solved':sem,'generic_fixed_point_solved':gram,
   'extensional_equal':extensional,'bounded_unroll_solved':unroll_scores,
   'cross_type_transfer':sum(transfer),'cross_type_total':len(transfer),
   'classification':'CONTROL_GRAMMAR_COMBINATOR_SUPPORTED' if gram==len(ITER) and extensional and all(transfer) else 'UNRESOLVED'
 }
}
print('RELATE',result['relate'])
print('RECURSE',result['recurse'])
open('/tmp/v78d_result.json','w').write(json.dumps(result,indent=2))
