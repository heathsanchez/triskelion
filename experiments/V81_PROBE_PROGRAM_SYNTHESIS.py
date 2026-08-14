import math, json, itertools, hashlib
import numpy as np
import scipy.special as sc
import mpmath as mp

# V81 — synthesize an epistemic operator as a program over a generic typed
# I/O/dataflow substrate. No PROBE/SAMPLE_INTERFACE candidate is supplied.
# Low-level substrate is analogous to hardware/system calls: choose an allowed
# input, invoke an opaque port, and optionally route the returned value.

NUM_GRID=[-2.0,-1.0,-0.25,0.25,1.0,2.0]
STR_GRID=['aBc','Straße xY','hello WORLD','MiXeD-123']
TOL=1e-8

NUM_FAMILIES={
 'cpython_math':[math.sin,math.cos,math.tanh,math.erf,math.expm1],
 'numpy':[np.sin,np.cos,np.tanh,np.square,np.negative,np.absolute],
 'scipy_special':[sc.erf,sc.erfc,sc.expit,sc.ndtr,sc.expm1],
 'mpmath':[mp.sin,mp.cos,mp.tanh,mp.erf,mp.erfc,mp.expm1],
}
STR_FUNCS=[str.lower,str.upper,str.swapcase,str.title,str.casefold]


def safe(fn,x):
    try:
        y=fn(x)
        if hasattr(y,'item'): y=y.item()
        if isinstance(y,(np.floating,float,int,mp.mpf)):
            y=float(y)
            return None if not math.isfinite(y) else y
        return y
    except Exception:return None

def same(a,b):
    if isinstance(a,(float,int)) and isinstance(b,(float,int)):
        return abs(float(a)-float(b))<=TOL*(1+abs(float(a))+abs(float(b)))
    return a==b

class World:
    def __init__(self,funcs,target,domain,tag):
        self.funcs=funcs; self.target=target; self.domain=domain; self.tag=tag; self.calls=0
    def call_port(self,x): self.calls+=1; return safe(self.funcs[self.target],x)
    def sim(self,i,x): return safe(self.funcs[i],x)

# Generic low-level grammar. Programs are synthesized by exhaustive enumeration;
# there is no single high-level candidate corresponding to PROBE.
SELECTORS=['FIRST','LAST','MIDDLE','MAX_PARTITION']
SOURCES=['OPAQUE_PORT','CANDIDATE_ZERO','CONSTANT_ZERO']
SINKS=['RECORD_EVIDENCE','WRITE_DATA','DISCARD']


def select_input(sel,w,survivors):
    if sel=='FIRST': return w.domain[0]
    if sel=='LAST': return w.domain[-1]
    if sel=='MIDDLE': return w.domain[len(w.domain)//2]
    if sel=='MAX_PARTITION':
        best=None
        for x in w.domain:
            vals=[w.sim(i,x) for i in survivors]
            reps=[]
            for v in vals:
                if not any(same(v,r) for r in reps): reps.append(v)
            score=len(reps)
            if best is None or score>best[0]: best=(score,x)
        return best[1]
    raise ValueError(sel)

def execute_program(program,w,survivors):
    sel,src,sink=program
    x=select_input(sel,w,survivors)
    if src=='OPAQUE_PORT': y=w.call_port(x)
    elif src=='CANDIDATE_ZERO': y=w.sim(0,x)
    elif src=='CONSTANT_ZERO': y=0.0 if not isinstance(x,str) else ''
    else:return None
    if sink=='DISCARD': return None
    if sink=='WRITE_DATA': return ('data',x,y)
    if sink=='RECORD_EVIDENCE': return ('evidence',x,y)
    return None

def identify(program,w,max_steps=3):
    survivors=list(range(len(w.funcs)))
    for _ in range(max_steps):
        if len(survivors)==1:return survivors[0]
        out=execute_program(program,w,survivors)
        if out is None:return None
        kind,x,y=out
        # Existing downstream RELATE/CONSTRAIN can consume evidence only.
        if kind!='evidence': return None
        survivors=[i for i in survivors if same(w.sim(i,x),y)]
        if not survivors:return None
    return survivors[0] if len(survivors)==1 else None

PROGRAMS=list(itertools.product(SELECTORS,SOURCES,SINKS))
TRAIN=['cpython_math','numpy','scipy_special']

def numeric_worlds(families):
    out=[]
    for fam in families:
        fs=NUM_FAMILIES[fam]
        out += [World(fs,t,NUM_GRID,fam) for t in range(len(fs))]
    return out

train=numeric_worlds(TRAIN)
scores={p:sum(identify(p,w)==w.target for w in train) for p in PROGRAMS}
best_score=max(scores.values()); best=[p for p,v in scores.items() if v==best_score]

# Quotient away the query-selection parameter to discover the reusable program
# schema rather than overfit a particular numeric query coordinate.
def schema(p): return ('SELECT_QUERY',p[1],p[2])
schema_scores={}
for p,v in scores.items(): schema_scores[schema(p)]=max(schema_scores.get(schema(p),-1),v)
best_schema_score=max(schema_scores.values()); best_schemas=[s for s,v in schema_scores.items() if v==best_schema_score]
constructed=best_schemas[0] if len(best_schemas)==1 else None

# Instantiate constructed schema with MAX_PARTITION on unseen numeric package.
def instantiate(s,selector='MAX_PARTITION'):
    return (selector,s[1],s[2])

hold=numeric_worlds(['mpmath'])
hold_prog=instantiate(constructed) if constructed else None
hold_good=sum(identify(hold_prog,w)==w.target for w in hold) if hold_prog else 0

# Cross-type transfer: same constructed schema, different typed query domain and
# independently implemented string transformations. Only selector is typed to
# the domain; source/sink control program is unchanged.
str_worlds=[World(STR_FUNCS,t,STR_GRID,'python_str') for t in range(len(STR_FUNCS))]
str_good=sum(identify(instantiate(constructed),w)==w.target for w in str_worlds) if constructed else 0

# Ablations of constructed program slots.
source_ablation=('MAX_PARTITION','CANDIDATE_ZERO','RECORD_EVIDENCE')
sink_ablation=('MAX_PARTITION','OPAQUE_PORT','DISCARD')
source_ablate_good=sum(identify(source_ablation,w)==w.target for w in numeric_worlds(['mpmath']))
sink_ablate_good=sum(identify(sink_ablation,w)==w.target for w in numeric_worlds(['mpmath']))

# Semantic shuffle: swap the port result against rotated candidate semantics.
def shuffled_identify(program,w):
    survivors=list(range(len(w.funcs))); mapping=list(range(1,len(w.funcs)))+[0]
    for _ in range(3):
        if len(survivors)==1:return survivors[0]
        x=select_input(program[0],w,survivors); y=w.call_port(x)
        survivors=[i for i in survivors if same(w.sim(mapping[i],x),y)]
        if not survivors:return None
    return survivors[0] if len(survivors)==1 else None
shuffle_good=sum(shuffled_identify(hold_prog,w)==w.target for w in numeric_worlds(['mpmath'])) if hold_prog else 0

result={
 'protocol':'V81_PROBE_PROGRAM_SYNTHESIS',
 'program_space_size':len(PROGRAMS),
 'low_level_grammar':{'selectors':SELECTORS,'sources':SOURCES,'sinks':SINKS},
 'train_targets':len(train),'best_program_score':best_score,'best_programs':[list(x) for x in best],
 'schema_scores':{'|'.join(k):v for k,v in schema_scores.items()},
 'constructed_schema':list(constructed) if constructed else None,
 'unique_best_schema':constructed is not None,
 'heldout_numeric_package':'mpmath','heldout_numeric_success':[hold_good,len(hold)],
 'cross_type_string_success':[str_good,len(str_worlds)],
 'source_ablation_success':[source_ablate_good,len(hold)],
 'sink_ablation_success':[sink_ablate_good,len(hold)],
 'semantic_shuffle_success':[shuffle_good,len(hold)],
 'gates':{
   'schema_constructed_without_probe_candidate':constructed==('SELECT_QUERY','OPAQUE_PORT','RECORD_EVIDENCE'),
   'unique_best_schema':constructed is not None,
   'source_distinct_numeric_transfer':hold_good==len(hold),
   'cross_type_transfer':str_good==len(str_worlds),
   'source_is_causal':source_ablate_good<hold_good,
   'evidence_recording_is_causal':sink_ablate_good<hold_good,
   'semantic_mapping_matters':shuffle_good<hold_good,
 }
}
result['verdict']='PASS_EPISTEMIC_PROGRAM_SYNTHESIS_V81' if all(result['gates'].values()) else 'MIXED_EPISTEMIC_PROGRAM_SYNTHESIS_V81'
print(json.dumps(result,indent=2,default=str))
open('/tmp/v81_result.json','w').write(json.dumps(result,indent=2,default=str))
