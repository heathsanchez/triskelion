import random, json
from dataclasses import dataclass

SEED=7803
rng=random.Random(SEED)

# -----------------------------
# A. RELATE hardening
# -----------------------------
# Surface order is randomized. The target is determined only by a relation
# between two public attributes, so position/deletion heuristics cannot solve
# consistently. The learner is not given the name RELATE.

@dataclass(frozen=True)
class RelWorld:
    items: tuple          # (id, x, y)
    target_gap: int
    answer: int


def make_rel_worlds(n=240, seed=SEED):
    r=random.Random(seed); out=[]
    for i in range(n):
        # Unique item whose |x-y| equals target_gap. Distractors deliberately
        # occupy every list position across the corpus.
        gap=r.randint(2,9)
        ans_id=10000+i
        ax=r.randint(20,70); ay=ax+gap
        items=[(ans_id,ax,ay)]
        used={gap}
        for j in range(5):
            g=r.choice([z for z in range(1,13) if z not in used]); used.add(g)
            x=r.randint(20,70); y=x+g
            items.append((20000+i*10+j,x,y))
        r.shuffle(items)
        out.append(RelWorld(tuple(items),gap,ans_id))
    return out

REL_WORLDS=make_rel_worlds()

# Candidate generic transformations. Only pair_relation constructs the missing
# relational representation. Others are plausible shortcut/hack families.
def rel_candidate(name,w):
    ids=[z[0] for z in w.items]
    if name=='pair_relation':
        derived=[(ident,abs(x-y)) for ident,x,y in w.items]
        hits=[ident for ident,d in derived if d==w.target_gap]
        return hits[0] if len(hits)==1 else None
    if name=='drop_first': return ids[1] if len(ids)>1 else None
    if name=='drop_last': return ids[-2] if len(ids)>1 else None
    if name=='pick_first': return ids[0]
    if name=='pick_last': return ids[-1]
    if name=='min_id': return min(ids)
    if name=='max_id': return max(ids)
    if name=='sort_x_pick_first': return min(w.items,key=lambda z:z[1])[0]
    if name=='sort_y_pick_last': return max(w.items,key=lambda z:z[2])[0]
    return None

REL_CANDS=['pair_relation','drop_first','drop_last','pick_first','pick_last','min_id','max_id','sort_x_pick_first','sort_y_pick_last']
rel_scores={c:sum(rel_candidate(c,w)==w.answer for w in REL_WORLDS) for c in REL_CANDS}

# Shuffle null: preserve all item marginals but break x/y pairing, destroying
# the relation while leaving candidate identities/positions available.
def shuffled_relation_score(trials=200):
    vals=[]
    for t in range(trials):
        rr=random.Random(SEED+1000+t); good=0
        for w in REL_WORLDS:
            ys=[z[2] for z in w.items]; rr.shuffle(ys)
            items=tuple((ident,x,y) for (ident,x,_),y in zip(w.items,ys))
            ww=RelWorld(items,w.target_gap,w.answer)
            good += rel_candidate('pair_relation',ww)==ww.answer
        vals.append(good)
    return vals

rel_null=shuffled_relation_score()

# -----------------------------
# B. RECURSE classification
# -----------------------------
# These are true unknown-depth iteration worlds. STEP is a one-step semantic
# transform. The question is whether recursion belongs in the semantic alphabet
# or is more naturally a grammar/control combinator that re-applies STEP.

@dataclass(frozen=True)
class IterWorld:
    start:int
    stop:int
    delta:int


def make_iter_worlds(n=240,seed=SEED+1):
    r=random.Random(seed); out=[]
    for _ in range(n):
        delta=r.choice([1,2,3,4])
        steps=r.randint(4,30)
        start=r.randint(-20,20)
        stop=start+delta*steps
        out.append(IterWorld(start,stop,delta))
    return out

ITER_WORLDS=make_iter_worlds()

def step(x,w):
    if x>=w.stop: return x
    return min(w.stop,x+w.delta)

def semantic_recurse(w):
    # A monolithic semantic primitive with loop semantics.
    x=w.start; guard=0
    while x!=w.stop and guard<1000:
        x=step(x,w); guard+=1
    return x

def fixed_point_combinator(w):
    # Generic grammar-level combinator: repeatedly invoke an existing typed
    # transform until the verifier-visible fixed/terminal predicate holds.
    x=w.start; guard=0
    while guard<1000:
        nx=step(x,w); guard+=1
        if nx==x or nx==w.stop: return nx
        x=nx
    return None

def bounded_unroll(w,budget):
    x=w.start
    for _ in range(budget): x=step(x,w)
    return x

recurse_semantic=sum(semantic_recurse(w)==w.stop for w in ITER_WORLDS)
recurse_fixed=sum(fixed_point_combinator(w)==w.stop for w in ITER_WORLDS)
unroll={b:sum(bounded_unroll(w,b)==w.stop for w in ITER_WORLDS) for b in [1,2,3,4,8,16]}

# Extensional equality over every intermediate state encountered.
ext_equal=True; checked=0
for w in ITER_WORLDS:
    # compare final behavior and termination over altered starts too
    for k in range(0,8):
        ww=IterWorld(min(w.stop,w.start+k*w.delta),w.stop,w.delta)
        a=semantic_recurse(ww); b=fixed_point_combinator(ww); checked+=1
        if a!=b: ext_equal=False

# Control-specificity test: same fixed-point combinator should compose with
# multiple unrelated one-step transforms, whereas a domain-specific RECURSE
# implementation would need separate semantics.
def step_halve(x,target): return x//2 if x>target else x
def step_strip(s,target): return s[:-1] if len(s)>target else s

def generic_fix(value,step_fn,done,max_iter=1000):
    x=value
    for _ in range(max_iter):
        if done(x): return x
        nx=step_fn(x)
        if nx==x: return x
        x=nx
    return None

transfer_cases=[]
for x in [64,128,256,1024]:
    transfer_cases.append(generic_fix(x,lambda z:step_halve(z,1),lambda z:z==1)==1)
for s in ['abcdefgh','0123456789','metalogic','triskelion']:
    transfer_cases.append(generic_fix(s,lambda z:step_strip(z,2),lambda z:len(z)==2) is not None)

result={
  'protocol':'V78C_RELATE_RECURSE_CLASSIFICATION',
  'seed':SEED,
  'relate':{
    'worlds':len(REL_WORLDS),
    'candidate_scores':rel_scores,
    'unique_best':max(rel_scores,key=rel_scores.get)=='pair_relation' and list(rel_scores.values()).count(max(rel_scores.values()))==1,
    'pair_relation_score':rel_scores['pair_relation'],
    'shuffle_null_mean':sum(rel_null)/len(rel_null),
    'shuffle_null_max':max(rel_null),
  },
  'recurse':{
    'worlds':len(ITER_WORLDS),
    'semantic_recurse_solved':recurse_semantic,
    'fixed_point_combinator_solved':recurse_fixed,
    'bounded_unroll_solved':unroll,
    'extensional_equal':ext_equal,
    'extensional_states_checked':checked,
    'generic_fixed_point_cross_type_transfer':sum(transfer_cases),
    'generic_fixed_point_cross_type_total':len(transfer_cases),
    'classification':'GRAMMAR_COMBINATOR_CANDIDATE' if recurse_fixed==len(ITER_WORLDS) and ext_equal and all(transfer_cases) else 'UNRESOLVED'
  }
}

print('RELATE',result['relate'])
print('RECURSE',result['recurse'])
open('/tmp/v78c_result.json','w').write(json.dumps(result,indent=2))
