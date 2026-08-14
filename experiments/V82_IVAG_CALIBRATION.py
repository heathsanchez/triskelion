import math, json, itertools, hashlib, statistics
import numpy as np
import scipy.special as sc
import mpmath as mp

# V82 — Independent Verified Algebra Genesis (IVAG) calibration/bridge.
# Tests strict bounded closure growth, minimum-description extensions,
# developmental counterfactuals, and independent quotient convergence.
# External functions are independently implemented; task wrappers/interfaces are authored.
TOL=1e-8
FP_TOL=1e-10
GRID_NUM=[-2.0,-1.0,-0.25,0.25,1.0,2.0]
GRID_STR=['  AbC  ','Straße xY',' hello WORLD ','MiXeD-123',' foo  ']
GRID_BYTES=[b'  AbC  ',b'hello WORLD',b'MiXeD-123',b' foo  ']

FAMILIES={
 'math': [math.sin,math.cos,math.tanh,math.erf,math.expm1],
 'numpy':[np.sin,np.cos,np.tanh,np.square,np.negative,np.absolute],
 'scipy':[sc.erf,sc.erfc,sc.expit,sc.ndtr,sc.expm1],
 'mpmath':[mp.sin,mp.cos,mp.tanh,mp.erf,mp.erfc,mp.expm1],
 'str':[str.lower,str.upper,str.swapcase,str.title,str.casefold],
 'bytes':[bytes.lower,bytes.upper,bytes.swapcase,bytes.title,bytes.strip],
 'math_hold':[math.sinh,math.cosh,math.atan,math.log1p,math.sqrt],
 'numpy_hold':[np.sinh,np.cosh,np.arctan,np.log1p,np.sqrt,np.reciprocal],
 'str_hold':[str.strip,str.capitalize,str.islower,str.isupper,str.isalpha],
}
DOMAINS={'math':GRID_NUM,'numpy':GRID_NUM,'scipy':GRID_NUM,'mpmath':GRID_NUM,'str':GRID_STR,'bytes':GRID_BYTES,
'math_hold':[0.1,0.25,0.5,1.0,2.0,3.0],'numpy_hold':[0.1,0.25,0.5,1.0,2.0,3.0],'str_hold':GRID_STR}

CONTROL_A=[math.cos,math.erf,sc.expit]
CONTROL_B=[lambda x: float(mp.cos(x)),lambda x:float(mp.erf(x)),sc.ndtr]

def safe(fn,x):
    try:
        y=fn(x)
        if hasattr(y,'item'): y=y.item()
        if isinstance(y,(np.floating,mp.mpf)): y=float(y)
        if isinstance(y,(float,int)):
            y=float(y)
            if not math.isfinite(y): return None
        return y
    except Exception:
        return None

def same(a,b,tol=TOL):
    if isinstance(a,(float,int)) and isinstance(b,(float,int)):
        return abs(float(a)-float(b))<=tol*(1+abs(float(a))+abs(float(b)))
    return a==b

class World:
    def __init__(self, family, funcs, target, domain, seed=0.7):
        self.family=family; self.funcs=funcs; self.target=target; self.domain=domain; self.seed=seed; self.calls=0
    def port(self,x):
        self.calls+=1
        return safe(self.funcs[self.target],x)
    def sim(self,i,x): return safe(self.funcs[i],x)

def max_partition(w,survivors):
    best=(-1,None)
    for x in w.domain:
        vals=[w.sim(i,x) for i in survivors]
        reps=[]
        for v in vals:
            if not any(same(v,r) for r in reps): reps.append(v)
        if len(reps)>best[0]: best=(len(reps),x)
    return best[1]

# Extension grammars. All low-level instruction tokens have unit description cost.
EVIDENCE_ACTIONS=['CALL_PORT','SIM0','CONST0','RECORD','WRITE','DISCARD']
RELATION_ACTIONS=['SIM_ALL','MATCH','FILTER','TAKE_FIRST','TAKE_LAST','CLEAR']
CONTROL_ACTIONS=['APPLY_STEP','CHECK_STABLE','LOOP_BACK','RESET','NOOP']

def programs(actions,max_len):
    for L in range(1,max_len+1):
        for p in itertools.product(actions, repeat=L):
            yield p

def run_evidence(program,w):
    surv=list(range(len(w.funcs))); x=max_partition(w,surv); tmp=None; evidence=None; data=None
    for a in program:
        if a=='CALL_PORT': tmp=w.port(x)
        elif a=='SIM0': tmp=w.sim(0,x)
        elif a=='CONST0': tmp=0.0 if not isinstance(x,(str,bytes)) else ('' if isinstance(x,str) else b'')
        elif a=='RECORD':
            if tmp is not None: evidence=(x,tmp)
        elif a=='WRITE':
            if tmp is not None: data=(x,tmp)
        elif a=='DISCARD': tmp=None
    return evidence

def evidence_valid(e,w):
    if e is None:return False
    x,y=e
    truth=safe(w.funcs[w.target],x)
    return same(y,truth)

def run_relation(program,w,evidence):
    if evidence is None:return None
    surv=list(range(len(w.funcs))); preds=None; matches=None; selected=None
    x,y=evidence
    for a in program:
        if a=='SIM_ALL': preds=[w.sim(i,x) for i in surv]
        elif a=='MATCH':
            if preds is not None: matches=[i for i,v in zip(surv,preds) if same(v,y)]
        elif a=='FILTER':
            if matches is not None:
                surv=list(matches)
                if len(surv)==1:selected=surv[0]
        elif a=='TAKE_FIRST':
            if surv:selected=surv[0]
        elif a=='TAKE_LAST':
            if surv:selected=surv[-1]
        elif a=='CLEAR': surv=[]
    return selected

def true_fixed(fn,seed):
    prev=seed
    for _ in range(500):
        cur=safe(fn,prev)
        if cur is None:return None
        if same(cur,prev,FP_TOL): return cur
        prev=cur
    return None

def run_control(program,fn,seed):
    cur=seed; prev=None; stable=False; prefix=[]
    for a in program:
        if a=='APPLY_STEP':
            prev=cur; cur=safe(fn,cur)
            if cur is None:return None
        elif a=='CHECK_STABLE': stable=(prev is not None and same(cur,prev,FP_TOL))
        elif a=='RESET': cur=seed; prev=None; stable=False
        elif a=='NOOP': pass
        elif a=='LOOP_BACK':
            if stable: continue
            if 'APPLY_STEP' not in prefix or 'CHECK_STABLE' not in prefix: return None
            for _ in range(500):
                for b in prefix:
                    if b=='APPLY_STEP':
                        prev=cur; cur=safe(fn,cur)
                        if cur is None:return None
                    elif b=='CHECK_STABLE': stable=(prev is not None and same(cur,prev,FP_TOL))
                    elif b=='RESET': cur=seed; prev=None; stable=False
                if stable: break
            if not stable:return None
        prefix.append(a)
    return cur if stable else None

def solve(task,A):
    kind=task['kind']; w=task['world']
    if kind=='evidence':
        p=A.get('EVIDENCE')
        if p is None:return False
        return evidence_valid(run_evidence(p,World(w.family,w.funcs,w.target,w.domain,w.seed)),w)
    if kind=='identify':
        pe=A.get('EVIDENCE'); pr=A.get('RELATION')
        if pe is None or pr is None:return False
        wc=World(w.family,w.funcs,w.target,w.domain,w.seed)
        e=run_evidence(pe,wc)
        return run_relation(pr,wc,e)==w.target
    if kind=='fixedpoint':
        pe=A.get('EVIDENCE'); pr=A.get('RELATION'); pc=A.get('CONTROL')
        if pe is None or pr is None or pc is None:return False
        wc=World(w.family,w.funcs,w.target,w.domain,w.seed)
        e=run_evidence(pe,wc); idx=run_relation(pr,wc,e)
        if idx is None:return False
        got=run_control(pc,w.funcs[idx],w.seed); truth=true_fixed(w.funcs[w.target],w.seed)
        return got is not None and truth is not None and same(got,truth,1e-7)
    raise ValueError(kind)

def make_tasks(families,control_funcs,tag):
    out=[]
    for fam in families:
        fs=FAMILIES[fam]; dom=DOMAINS[fam]
        for i in range(len(fs)):
            w=World(fam,fs,i,dom)
            out.append({'id':f'{tag}:e:{fam}:{i}','kind':'evidence','world':w,'iface':'EVIDENCE'})
            out.append({'id':f'{tag}:i:{fam}:{i}','kind':'identify','world':w,'iface':'RELATION'})
    dom=[-1.0,-0.25,0.25,0.7,1.0,2.0]
    for i in range(len(control_funcs)):
        w=World(f'{tag}_control',control_funcs,i,dom,0.7)
        out.append({'id':f'{tag}:f:{i}','kind':'fixedpoint','world':w,'iface':'CONTROL'})
    return out

# Frozen probe frontier uses function identities not present in the evidence/identify genesis streams.
H=make_tasks(['math_hold','numpy_hold','str_hold'],[sc.erfc,np.cos,sc.expit],'H')
CANDIDATES={'EVIDENCE':list(programs(EVIDENCE_ACTIONS,2)),'RELATION':list(programs(RELATION_ACTIONS,3)),'CONTROL':list(programs(CONTROL_ACTIONS,3))}

def candidate_solve(task,A,iface,p):
    B=dict(A); B[iface]=p
    return solve(task,B)

def discover(iface,residuals,A):
    rs=[t for t in residuals if t['iface']==iface]
    distinct_targets=len(set((t['world'].family,t['world'].target) for t in rs))
    if distinct_targets < (3 if iface=='CONTROL' else 4): return None
    scored=[]
    for p in CANDIDATES[iface]:
        support=sum(candidate_solve(t,A,iface,p) for t in rs)
        if support: scored.append((len(p),-support,p,support))
    if not scored:return None
    threshold=max((3 if iface=='CONTROL' else 4), math.ceil(0.8*len(rs)))
    admiss=[x for x in scored if x[3]>=threshold]
    if not admiss:return None
    best_dl=min(x[0] for x in admiss); dlset=[x for x in admiss if x[0]==best_dl]
    best_support=max(x[3] for x in dlset); winners=[x for x in dlset if x[3]==best_support]
    sigs={}
    for x in winners:
        p=x[2]; sig=tuple(candidate_solve(t,A,iface,p) for t in rs); sigs.setdefault(sig,[]).append(p)
    if len(sigs)!=1:return None
    _,ps=next(iter(sigs.items())); canonical=min(ps)
    support_by_dl={}
    for x in scored: support_by_dl[str(x[0])]=max(support_by_dl.get(str(x[0]),0),x[3])
    return {'iface':iface,'program':canonical,'dl':best_dl,'support':best_support,'residuals':len(rs),
            'syntax_winners':len(winners),'extensional_classes':len(sigs),'support_threshold':threshold,
            'max_support_by_dl':support_by_dl,
            'no_shorter_admissible':all(v<threshold for k,v in support_by_dl.items() if int(k)<best_dl)}

def closure(A,H): return {t['id'] for t in H if solve(t,A)}

def run_genesis(tasks,salt,banned=None):
    banned=set() if banned is None else set(banned)
    order=sorted(tasks,key=lambda t:hashlib.sha256((salt+'|'+t['id']).encode()).hexdigest())
    A={}; residuals=[]; events=[]; states=[{}]; closures=[closure(A,H)]; queue=list(order); i=0
    while queue:
        t=queue.pop(0)
        if solve(t,A):
            events.append({'task':t['id'],'event':'CLOSURE_SOLVE','state':sorted(A)}); continue
        residuals.append(t); events.append({'task':t['id'],'event':'OBSTRUCTION','iface':t['iface'],'state':sorted(A)})
        for iface in ['EVIDENCE','RELATION','CONTROL']:
            if iface in A or iface in banned: continue
            d=discover(iface,residuals,A)
            if d:
                A[iface]=d['program']; events.append({'event':'EXTEND','extension':d})
                states.append(dict(A)); closures.append(closure(A,H)); old=residuals; residuals=[]; queue=old+queue; break
        i+=1
        if i>500: raise RuntimeError('loop')
    return {'A':A,'events':events,'states':states,'closures':closures,'order':[t['id'] for t in order]}

STREAM1=make_tasks(['math','numpy','str'],CONTROL_A,'S1')
STREAM2=make_tasks(['scipy','mpmath','bytes'],CONTROL_B,'S2')
R1=run_genesis(STREAM1,'IVAG-CURRICULUM-A'); R2=run_genesis(STREAM2,'IVAG-CURRICULUM-B')

def extension_events(R): return [e['extension'] for e in R['events'] if e.get('event')=='EXTEND']

def matched_controls(R):
    exts=extension_events(R); rows=[]
    for idx,d in enumerate(exts, start=1):
        iface=d['iface']; learned=tuple(d['program']); base=R['states'][idx-1]; c0=closure(base,H); c1=closure(R['states'][idx],H)
        correct=len(c1-c0); alts=[]; correct_sig=frozenset(c1-c0)
        for p in CANDIDATES[iface]:
            if len(p)!=len(learned) or tuple(p)==learned: continue
            B=dict(base); B[iface]=p; sig=frozenset(closure(B,H)-c0)
            if sig==correct_sig: continue
            alts.append(len(sig))
        rows.append({'iface':iface,'dl':len(learned),'correct_gain':correct,'DG':correct/len(learned),
                     'null_mean_gain':statistics.mean(alts) if alts else 0.0,'null_max_gain':max(alts) if alts else 0,'null_programs':len(alts)})
    return rows

def quotient_signatures(R):
    sig=[]
    for i,d in enumerate(extension_events(R),start=1):
        inc=sorted(R['closures'][i]-R['closures'][i-1])
        sig.append({'interface':d['iface'],'dl':d['dl'],'heldout_increment_kinds':sorted([x.split(':')[1] for x in inc]),'heldout_increment_size':len(inc)})
    return sig

def strict_chain(R): return all(R['closures'][i-1] < R['closures'][i] for i in range(1,len(R['closures'])))
def conservative(R): return all(R['closures'][i-1] <= R['closures'][i] for i in range(1,len(R['closures'])))

CF1_E1=run_genesis(STREAM1,'IVAG-CURRICULUM-A',banned={'EVIDENCE'}); CF1_E2=run_genesis(STREAM1,'IVAG-CURRICULUM-A',banned={'RELATION'})
CF2_E1=run_genesis(STREAM2,'IVAG-CURRICULUM-B',banned={'EVIDENCE'}); CF2_E2=run_genesis(STREAM2,'IVAG-CURRICULUM-B',banned={'RELATION'})
Q1=quotient_signatures(R1); Q2=quotient_signatures(R2)
result={
 'protocol':'V82_INDEPENDENT_VERIFIED_ALGEBRA_GENESIS_CALIBRATION',
 'boundary':'bounded external-function IVAG calibration; external callable semantics are independently authored, while task interfaces/dependency classes and low-level synthesis grammars are authored',
 'initial_algebra':{'extensions':[],'typed_interfaces':['Evidence','SelectedHypothesis','StableValue'],
                    'low_level_substrates':{'EVIDENCE':EVIDENCE_ACTIONS,'RELATION':RELATION_ACTIONS,'CONTROL':CONTROL_ACTIONS}},
 'description_length':'uniform unit cost per low-level instruction token',
 'stream_1':{'source_families':['math','numpy','str'],'task_count':len(STREAM1),'order_sha256':hashlib.sha256('\n'.join(R1['order']).encode()).hexdigest(),
             'extensions':extension_events(R1),'heldout_closure_sizes':[len(x) for x in R1['closures']],'matched_DL_controls':matched_controls(R1),'quotient_signatures':Q1},
 'stream_2':{'source_families':['scipy','mpmath','bytes'],'task_count':len(STREAM2),'order_sha256':hashlib.sha256('\n'.join(R2['order']).encode()).hexdigest(),
             'extensions':extension_events(R2),'heldout_closure_sizes':[len(x) for x in R2['closures']],'matched_DL_controls':matched_controls(R2),'quotient_signatures':Q2},
 'heldout_probe':{'task_count':len(H),'families':['math_hold','numpy_hold','str_hold','heldout_control'],
                  'note':'function identities in the evidence/identify frontier are not used in either genesis stream; control frontier includes independent callable implementations but is a weaker holdout'},
 'developmental_counterfactuals':{'stream1_ban_E1_final_extensions':sorted(CF1_E1['A']),'stream1_ban_E2_final_extensions':sorted(CF1_E2['A']),
                                  'stream2_ban_E1_final_extensions':sorted(CF2_E1['A']),'stream2_ban_E2_final_extensions':sorted(CF2_E2['A'])},
 'gates':{
   'strict_closure_growth_stream1':strict_chain(R1) and len(R1['closures'])==4,
   'strict_closure_growth_stream2':strict_chain(R2) and len(R2['closures'])==4,
   'minimal_extensions_stream1':len(extension_events(R1))==3 and all(d['no_shorter_admissible'] for d in extension_events(R1)),
   'minimal_extensions_stream2':len(extension_events(R2))==3 and all(d['no_shorter_admissible'] for d in extension_events(R2)),
   'conservative_growth_stream1':conservative(R1),'conservative_growth_stream2':conservative(R2),
   'developmental_E1_causes_descendants':sorted(CF1_E1['A'])==[] and sorted(CF2_E1['A'])==[],
   'developmental_E2_causes_E3':sorted(CF1_E2['A'])==['EVIDENCE'] and sorted(CF2_E2['A'])==['EVIDENCE'],
   'independent_quotient_convergence':Q1==Q2,
   'matched_DL_advantage':all(r['correct_gain']>r['null_mean_gain'] for r in matched_controls(R1)+matched_controls(R2)),
 }
}
result['verdict']='PASS_IVAG_CALIBRATION_V82' if all(result['gates'].values()) else 'MIXED_IVAG_CALIBRATION_V82'
print(json.dumps(result,indent=2,default=str))
open('/tmp/v82_result.json','w').write(json.dumps(result,indent=2,default=str))
