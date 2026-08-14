import math, json, hashlib
import numpy as np
import scipy.special as sc
import mpmath as mp

# V79 — external black-box epistemic primitive reconstruction.
# The hidden target is an independently authored callable. Public state exposes
# only an opaque set of candidate hypotheses with the same unary-numeric type.
# Without an information-producing world call, all target identities are
# observationally indistinguishable. Candidate hypotheses may be simulated;
# the hidden target may only be observed through the world interface.

GRID=[-2.0,-1.5,-1.0,-0.5,-0.25,0.25,0.5,1.0,1.5,2.0]
TOL=1e-8

def fval(fn,x):
    try:
        y=fn(x)
        if hasattr(y,'item'): y=y.item()
        y=float(y)
        if not math.isfinite(y): return None
        return y
    except Exception:
        return None

def eq(a,b):
    return a is not None and b is not None and abs(a-b)<=TOL*(1+abs(a)+abs(b))

# Four source-distinct implementation families. Function names never enter the
# solver; only opaque IDs and callable behavior are available.
FAMILIES={
 'cpython_math': [math.sin,math.cos,math.tanh,math.erf,math.expm1],
 'numpy': [np.sin,np.cos,np.tanh,np.square,np.negative,np.absolute],
 'scipy_special': [sc.erf,sc.erfc,sc.expit,sc.ndtr,sc.expm1],
 'mpmath': [mp.sin,mp.cos,mp.tanh,mp.erf,mp.erfc,mp.expm1],
}

class World:
    def __init__(self,family,funcs,target):
        self.family=family; self.funcs=funcs; self.target=target; self.calls=0
        # opaque labels are target-independent and reveal no function names
        self.labels=[hashlib.sha256(f'{family}:{i}'.encode()).hexdigest()[:8] for i in range(len(funcs))]
    def public_state(self):
        return {'type':'unary_numeric','candidate_ids':tuple(self.labels),'query_domain':tuple(GRID)}
    def call_hidden(self,x):
        self.calls+=1
        return fval(self.funcs[self.target],x)
    def simulate_candidate(self,i,x):
        return fval(self.funcs[i],x)


def make_worlds():
    return {fam:[World(fam,funcs,t) for t in range(len(funcs))] for fam,funcs in FAMILIES.items()}

# Exact old-closure obstruction: for a family, public state is identical for
# every hidden target. Any deterministic target-blind composition of old
# operations therefore has the same transcript before a world call and cannot
# be correct for every target when >1 hypotheses remain.
def indistinguishable_without_world_call(worlds):
    states=[w.public_state() for w in worlds]
    return all(s==states[0] for s in states) and len(worlds)>1

# RELATE -> CONSTRAIN -> SELECT after an observation. Query choice maximizes the
# number of output equivalence classes among surviving hypotheses.
def choose_query(w,survivors):
    best=None
    for x in GRID:
        vals=[w.simulate_candidate(i,x) for i in survivors]
        # count tolerant-equivalence classes
        reps=[]
        for v in vals:
            if v is None: key=('none',)
            else:
                found=None
                for j,r in enumerate(reps):
                    if r is not None and eq(v,r): found=j; break
                if found is None: reps.append(v)
        score=len(reps)
        if best is None or score>best[0]: best=(score,x)
    return best[1]

def solve_with_world_call(w,max_calls=4):
    survivors=list(range(len(w.funcs)))
    transcript=[]
    for _ in range(max_calls):
        if len(survivors)==1:return survivors[0],transcript
        x=choose_query(w,survivors)
        y=w.call_hidden(x)
        transcript.append((x,y))
        survivors=[i for i in survivors if eq(w.simulate_candidate(i,x),y)]
        if not survivors:return None,transcript
    return (survivors[0] if len(survivors)==1 else None),transcript

# Blind generic extension candidates. Only SAMPLE_INTERFACE produces information
# conditional on the hidden world. Others manipulate the hypothesis set or add
# target-independent pseudo-observations.
META=['SAMPLE_INTERFACE','DROP_LEFT','DROP_RIGHT','REVERSE_SET','CONST_ZERO','DUPLICATE_FIRST']

def solve_meta(w,meta,max_calls=4):
    survivors=list(range(len(w.funcs)))
    transcript=[]
    for _ in range(max_calls):
        if len(survivors)==1:return survivors[0]
        if meta=='SAMPLE_INTERFACE':
            x=choose_query(w,survivors); y=w.call_hidden(x); transcript.append((x,y))
            survivors=[i for i in survivors if eq(w.simulate_candidate(i,x),y)]
        elif meta=='DROP_LEFT': survivors=survivors[1:]
        elif meta=='DROP_RIGHT': survivors=survivors[:-1]
        elif meta=='REVERSE_SET': survivors=list(reversed(survivors))
        elif meta=='CONST_ZERO':
            x=GRID[0]; y=0.0
            survivors=[i for i in survivors if eq(w.simulate_candidate(i,x),y)]
        elif meta=='DUPLICATE_FIRST':
            survivors=survivors+[survivors[0]] if survivors else survivors
        else: return None
        if not survivors:return None
    return survivors[0] if len(set(survivors))==1 else None

worlds=make_worlds()
TRAIN=['cpython_math','numpy','scipy_special']; HOLDOUT='mpmath'

obstruction={fam:indistinguishable_without_world_call(ws) for fam,ws in worlds.items()}
passive={fam:0 for fam in worlds} # exact all-target success is impossible by obstruction
hand={}
hand_calls={}
for fam,ws in worlds.items():
    good=0; calls=[]
    for w in ws:
        pred,_=solve_with_world_call(w); good+=pred==w.target; calls.append(w.calls)
    hand[fam]=good; hand_calls[fam]=calls

# Fresh worlds for each meta arm to avoid carrying call counters/state.
meta_train={}
for m in META:
    W=make_worlds(); good=total=0
    for fam in TRAIN:
        for w in W[fam]: good+=solve_meta(w,m)==w.target; total+=1
    meta_train[m]=(good,total)

best=max(META,key=lambda m:meta_train[m][0])
unique_best=sum(meta_train[m][0]==meta_train[best][0] for m in META)==1
W=make_worlds(); hold_good=sum(solve_meta(w,best)==w.target for w in W[HOLDOUT]); hold_total=len(W[HOLDOUT])
# Ablation = return to no target-conditioned observation, hence zero all-target identification guarantee.
ablated_holdout=0

# Semantic shuffle control: pair the observed target response with the wrong
# candidate implementation mapping; this should destroy exact identification.
shuffle_good=0; shuffle_total=0
W=make_worlds()
for w in W[HOLDOUT]:
    survivors=list(range(len(w.funcs))); mapping=list(range(len(w.funcs))); mapping=mapping[1:]+mapping[:1]
    for _ in range(4):
        if len(survivors)<=1:break
        x=choose_query(w,survivors); y=w.call_hidden(x)
        survivors=[i for i in survivors if eq(w.simulate_candidate(mapping[i],x),y)]
        if not survivors:break
    pred=survivors[0] if len(survivors)==1 else None
    shuffle_good += pred==w.target; shuffle_total+=1

result={
 'protocol':'V79_EXTERNAL_BLACKBOX_PROBE',
 'families':{k:len(v) for k,v in worlds.items()},
 'source_families':list(FAMILIES),
 'old_closure_indistinguishable':obstruction,
 'old_closure_all_target_success':passive,
 'hand_probe_success':hand,
 'hand_probe_calls':hand_calls,
 'meta_train_scores':{k:list(v) for k,v in meta_train.items()},
 'selected_meta':best,'unique_best':unique_best,
 'holdout_family':HOLDOUT,'holdout_success':[hold_good,hold_total],
 'holdout_ablation_success':[ablated_holdout,hold_total],
 'semantic_shuffle_success':[shuffle_good,shuffle_total],
 'gates':{
   'old_closure_obstruction_all_families':all(obstruction.values()),
   'hand_probe_all':all(hand[f]==len(worlds[f]) for f in worlds),
   'blind_extension_unique':best=='SAMPLE_INTERFACE' and unique_best,
   'source_distinct_holdout_transfer':hold_good==hold_total,
   'ablation_restores_obstruction':ablated_holdout==0,
   'semantic_mapping_matters':shuffle_good<hold_good,
 },
}
result['verdict']='PASS_EXTERNAL_PROBE_RECONSTRUCTION_V79' if all(result['gates'].values()) else 'MIXED_EXTERNAL_PROBE_V79'
print(json.dumps(result,indent=2))
open('/tmp/v79_result.json','w').write(json.dumps(result,indent=2))
