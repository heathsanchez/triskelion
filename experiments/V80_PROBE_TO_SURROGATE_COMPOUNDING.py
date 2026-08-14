import json, math
import numpy as np
import mpmath as mp

# V80 — developmental consequence of the V79 epistemic primitive.
# Retain SAMPLE_INTERFACE (the PROBE-like operation) learned on source-distinct
# packages in V79. On a held-out implementation family, ask whether this prior
# capability makes a genuinely later capability constructible: a standalone
# surrogate that predicts unseen outputs without further world calls.

FUNCS=[mp.sin,mp.cos,mp.tanh,mp.erf,mp.erfc,mp.expm1]
NODES=np.cos((2*np.arange(17)+1)/(2*17)*np.pi)
TEST=np.linspace(-0.975,0.975,41)
DEG=12
TOL=1e-6

class HiddenWorld:
    def __init__(self,fn): self.fn=fn; self.calls=0
    def sample(self,x):
        self.calls+=1
        return float(self.fn(float(x)))
    def truth(self,x): return float(self.fn(float(x)))

# Frozen constructor K0. It has no target-specific semantics: given enough
# verified (x,y) observations, fit a Chebyshev surrogate. With no observations,
# it cannot emit a target-conditioned capability.
def construct_surrogate(samples):
    if len(samples)<13: return None
    xs=np.array([x for x,_ in samples],dtype=float)
    ys=np.array([y for _,y in samples],dtype=float)
    return np.polynomial.Chebyshev.fit(xs,ys,deg=DEG,domain=[-1,1])

def verify_surrogate(model,w):
    if model is None:return False,None
    errs=[abs(float(model(x))-w.truth(x)) for x in TEST]
    return max(errs)<=TOL,max(errs)

# Cold arm: identical K0 but SAMPLE_INTERFACE absent, so no target-conditioned
# observations are available. This is not counted as a stochastic failure: the
# constructor's input is exactly empty by protocol.
cold=[]
for fn in FUNCS:
    w=HiddenWorld(fn); m=construct_surrogate([]); ok,err=verify_surrogate(m,w)
    cold.append({'constructed':m is not None,'pass':ok,'calls':w.calls,'max_error':err})

# Warm arm: retained O1/SAMPLE_INTERFACE produces evidence; K0 is unchanged.
warm=[]
models=[]
for fn in FUNCS:
    w=HiddenWorld(fn)
    samples=[(float(x),w.sample(float(x))) for x in NODES]
    m=construct_surrogate(samples); ok,err=verify_surrogate(m,w)
    models.append(m)
    warm.append({'constructed':m is not None,'pass':ok,'probe_calls':w.calls,'fresh_test_points':len(TEST),'max_error':err})

# Causal ablation: remove O1 again while keeping K0 and target family fixed.
ablate=[]
for fn in FUNCS:
    w=HiddenWorld(fn); m=construct_surrogate([]); ok,err=verify_surrogate(m,w)
    ablate.append({'constructed':m is not None,'pass':ok,'calls':w.calls,'max_error':err})

# Persistence/independence from the world after construction: serialize only
# polynomial coefficients/domain/window, rebuild in a fresh object, and verify
# with zero calls to the hidden-world sampling interface.
rebuild=[]
for fn,m in zip(FUNCS,models):
    # convert to ordinary polynomial coefficients in the fitted Chebyshev basis
    payload={'coef':[float(x) for x in m.coef], 'domain':[float(x) for x in m.domain], 'window':[float(x) for x in m.window]}
    m2=np.polynomial.Chebyshev(payload['coef'],domain=payload['domain'],window=payload['window'])
    w=HiddenWorld(fn); ok,err=verify_surrogate(m2,w)
    rebuild.append({'pass':ok,'sample_interface_calls':w.calls,'max_error':err,'payload_size':len(payload['coef'])})

# Wrong-lineage control: rotate the constructed capability to the next target.
wrong=[]
for i,fn in enumerate(FUNCS):
    w=HiddenWorld(fn); wrong_model=models[(i+1)%len(models)]; ok,err=verify_surrogate(wrong_model,w)
    wrong.append({'pass':ok,'max_error':err})

result={
 'protocol':'V80_PROBE_TO_SURROGATE_COMPOUNDING',
 'parent_result':'V79_EXTERNAL_BLACKBOX_PROBE',
 'heldout_world_family':'mpmath',
 'constructor':'generic Chebyshev fit degree 12 from verified samples',
 'cold':cold,'warm':warm,'ablation':ablate,'rebuild_from_capability_only':rebuild,'wrong_lineage':wrong,
 'gates':{
   'cold_no_O2':all(not r['constructed'] and not r['pass'] for r in cold),
   'O1_makes_O2_constructible':all(r['constructed'] and r['pass'] for r in warm),
   'O1_ablation_removes_O2':all(not r['constructed'] and not r['pass'] for r in ablate),
   'O2_runs_without_future_probe':all(r['pass'] and r['sample_interface_calls']==0 for r in rebuild),
   'wrong_lineage_fails':all(not r['pass'] for r in wrong),
 }
}
result['verdict']='PASS_EXTERNAL_O1_TO_O2_V80' if all(result['gates'].values()) else 'MIXED_EXTERNAL_O1_TO_O2_V80'
print(json.dumps(result,indent=2))
open('/tmp/v80_result.json','w').write(json.dumps(result,indent=2))
