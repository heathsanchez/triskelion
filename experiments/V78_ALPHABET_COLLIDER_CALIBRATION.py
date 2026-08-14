from dataclasses import dataclass, replace
from collections import defaultdict
import random, itertools, json, math

OPS = ['DISTINGUISH','GENERATE','RELATE','CONSTRAIN','SELECT','COMPOSE','RETAIN','TRANSDUCE','RECURSE','PROBE']
OMEGA9=[x for x in OPS if x!='PROBE']

@dataclass(frozen=True)
class World:
    family:str
    payload:tuple
    hidden:tuple=()

@dataclass
class State:
    data:dict
    candidates:list
    evidence:dict
    relations:set
    constraints:list
    classes:dict
    selected:object=None
    composed:object=None
    retained:object=None
    depth:int=0


def init_state(w):
    fam=w.family
    p=dict(w.payload)
    return State(data=p.copy(), candidates=list(p.get('candidates',[])), evidence={}, relations=set(), constraints=list(p.get('constraints',[])), classes={})

# Each operation has concrete state semantics; labels are not used by the goal tests.
def apply(op,s,w):
    s=State(dict(s.data),list(s.candidates),dict(s.evidence),set(s.relations),list(s.constraints),dict(s.classes),s.selected,s.composed,s.retained,s.depth)
    fam=w.family
    if op=='PROBE':
        # generic information-producing action: reveal one externally queryable hidden datum
        if w.hidden:
            for k,v in w.hidden:
                if k not in s.evidence:
                    s.evidence[k]=v; return s
        return None
    if op=='TRANSDUCE':
        if fam=='decode' and isinstance(s.data.get('raw'),str) and 'decoded' not in s.data:
            base=s.data.get('base',10); s.data['decoded']=int(s.data['raw'],base); return s
        if fam=='hidden_decode' and 'cipher' in s.data and 'key' in s.evidence and 'decoded' not in s.data:
            s.data['decoded']=s.data['cipher'] ^ s.evidence['key']; return s
        return None
    if op=='GENERATE':
        if 'target_hint' in s.data and not s.candidates:
            h=s.data['target_hint']; s.candidates=[h-2,h-1,h,h+1,h+2]; return s
        if fam=='compose' and not s.candidates:
            s.candidates=[s.data['a'],s.data['b']]; return s
        return None
    if op=='RELATE':
        if len(s.candidates)>=1 and not s.relations:
            if fam=='relation' and 'anchor' in s.data:
                a=s.data['anchor']
                for x in s.candidates:
                    s.relations.add((x,a,abs(x-a)))
            else:
                for a,b in itertools.combinations(s.candidates,2):
                    s.relations.add((a,b,abs(a-b)))
            return s
        return None
    if op=='DISTINGUISH':
        if s.candidates and not s.classes:
            key=None
            if 'parity' in s.evidence: key=s.evidence['parity']
            elif 'class_mod' in s.data: key=s.data['class_mod']
            mod=s.data.get('mod',2)
            if key is not None:
                s.classes={x:(x%mod==key) for x in s.candidates}; return s
        return None
    if op=='CONSTRAIN':
        old=list(s.candidates)
        if not old: return None
        new=old
        if s.classes:
            new=[x for x in new if s.classes.get(x,False)]
        if 'threshold' in s.data:
            new=[x for x in new if x<=s.data['threshold']]
        if 'decoded' in s.data and fam in ('decode','hidden_decode'):
            new=[x for x in new if x==s.data['decoded']]
        if fam=='relation' and s.relations:
            gap=s.data['gap']; good=set()
            anchor=s.data.get('anchor')
            for a,b,d in s.relations:
                if d==gap:
                    if anchor is not None: good.add(a)
                    else: good|={a,b}
            new=[x for x in new if x in good]
        if new!=old:
            s.candidates=new; return s
        return None
    if op=='SELECT':
        if s.selected is None and len(s.candidates)==1:
            s.selected=s.candidates[0]; return s
        return None
    if op=='COMPOSE':
        if fam=='compose' and s.composed is None and len(s.candidates)>=2:
            s.composed=tuple(s.candidates[:2]); return s
        if fam=='nested' and s.selected is not None and s.depth>0 and s.composed is None:
            s.composed=('nested',s.selected,s.depth); return s
        return None
    if op=='RETAIN':
        val=s.composed if s.composed is not None else s.selected
        if val is not None and s.retained is None:
            s.retained=val; return s
        return None
    if op=='RECURSE':
        if fam=='nested' and s.depth==0:
            s.depth=s.data.get('nest_depth',1); return s
        return None
    return None


def goal(s,w):
    fam=w.family; p=dict(w.payload)
    if fam=='hidden_choice': return s.selected==p['answer']
    if fam=='decode': return s.selected==p['answer']
    if fam=='hidden_decode': return s.selected==p['answer']
    if fam=='generate': return s.selected==p['answer']
    if fam=='relation': return s.selected==p['answer']
    if fam=='compose': return s.retained==(p['a'],p['b'])
    if fam=='nested': return s.retained==('nested',p['answer'],p['nest_depth'])
    if fam=='retain': return s.retained==p['answer']
    return False


def freeze(x):
    if isinstance(x, dict): return tuple(sorted((k,freeze(v)) for k,v in x.items()))
    if isinstance(x, (list,tuple)): return tuple(freeze(v) for v in x)
    if isinstance(x, set): return tuple(sorted(freeze(v) for v in x))
    return x

def canon(s):
    return (freeze(s.data),freeze(s.candidates),freeze(s.evidence),freeze(s.relations),freeze(s.constraints),freeze(s.classes),freeze(s.selected),freeze(s.composed),freeze(s.retained),s.depth)

def solve(w,allowed,max_depth=8, order_policy=None):
    s0=init_state(w)
    if goal(s0,w): return []
    q=[(s0,[])] ; seen={canon(s0)}
    while q:
        s,path=q.pop(0)
        if len(path)>=max_depth: continue
        ops=list(allowed)
        if order_policy: ops=order_policy(ops,path)
        for op in ops:
            ns=apply(op,s,w)
            if ns is None: continue
            c=canon(ns)
            if c in seen: continue
            np=path+[op]
            if goal(ns,w): return np
            seen.add(c); q.append((ns,np))
    return None


def make_worlds(seed=7,n_per=40):
    r=random.Random(seed); W=[]
    for _ in range(n_per):
        ans=r.randrange(2,18); parity=ans%2
        # one lower opposite-parity distractor plus higher same-parity distractors:
        # PROBE -> DISTINGUISH removes lower distractor, CONSTRAIN(threshold) removes higher ones.
        cands=[ans, ans+2, ans+4, ans-1]
        r.shuffle(cands)
        W.append(World('hidden_choice',tuple({'candidates':cands,'threshold':ans,'answer':ans}.items()),(('parity',parity),)))
        # decode
        ans=r.randrange(2,30); raw=format(ans,'x'); cands=list(range(max(0,ans-2),ans+3))
        W.append(World('decode',tuple({'raw':raw,'base':16,'candidates':cands,'answer':ans}.items())))
        # hidden decode
        ans=r.randrange(0,16); key=r.randrange(1,16); cipher=ans^key; cands=list(range(16))
        W.append(World('hidden_decode',tuple({'cipher':cipher,'candidates':cands,'answer':ans}.items()),(('key',key),)))
        # generate
        ans=r.randrange(5,25)
        W.append(World('generate',tuple({'target_hint':ans,'threshold':ans+2,'class_mod':ans%5,'mod':5,'answer':ans}.items())))
        # relation: choose answer as sole element participating in target gap after threshold
        anchor=r.randrange(10,20); gap=r.randrange(2,5); ans=anchor-gap
        c=[ans, anchor-gap-1, anchor+gap+1, anchor+gap+2]
        W.append(World('relation',tuple({'candidates':c,'gap':gap,'anchor':anchor,'answer':ans}.items())))
        # compose and retain
        a=r.randrange(1,9); b=r.randrange(10,19)
        W.append(World('compose',tuple({'a':a,'b':b}.items())))
        # retain simple
        ans=r.randrange(0,20)
        W.append(World('retain',tuple({'candidates':[ans],'answer':ans}.items())))
        # nested: needs recurse then select/composition/retain
        ans=r.randrange(0,20); dep=r.randrange(1,4)
        W.append(World('nested',tuple({'candidates':[ans],'answer':ans,'nest_depth':dep}.items())))
    return W

W=make_worlds()

def evalset(allowed):
    out=[]
    for w in W:
        p=solve(w,allowed)
        out.append(p)
    return out

base=evalset(OPS)
base_s=sum(x is not None for x in base)
print('worlds',len(W),'base',base_s)
# ablations
ab={}
for op in OPS:
    rs=evalset([x for x in OPS if x!=op]); ab[op]=sum(x is not None for x in rs)
print('ablations',ab)
# minimal subsets by max coverage and size
best=[]
for k in range(1,11):
    maxcov=-1; bestsubs=[]
    for sub in itertools.combinations(OPS,k):
        cov=sum(solve(w,sub) is not None for w in W)
        if cov>maxcov: maxcov=cov; bestsubs=[sub]
        elif cov==maxcov: bestsubs.append(sub)
    best.append((k,maxcov,bestsubs[:5]))
    if maxcov==base_s:
        print('minimal full-coverage size',k,'examples',bestsubs[:3]); break
# pairwise synergy: excess loss over individual losses
pair=[]
for a,b in itertools.combinations(OPS,2):
    cov=sum(solve(w,[x for x in OPS if x not in (a,b)]) is not None for w in W)
    loss=base_s-cov; expected=(base_s-ab[a])+(base_s-ab[b])
    pair.append((loss-expected,loss,a,b,cov))
pair.sort(reverse=True)
print('top pair interactions',pair[:10])
# trace motifs / order sensitivity
from collections import Counter
motifs=Counter(); order_shuf_success=0; order_trials=0
rng=random.Random(99)
for w,p in zip(W,base):
    if not p: continue
    for a,b in zip(p,p[1:]): motifs[(a,b)]+=1
    if len(p)>1:
        for _ in range(10):
            q=p[:] ; rng.shuffle(q); order_trials+=1
            s=init_state(w); ok=True
            for op in q:
                ns=apply(op,s,w)
                if ns is None: ok=False; break
                s=ns
            if ok and goal(s,w): order_shuf_success+=1
print('top motifs',motifs.most_common(15))
print('order_shuffle_success',order_shuf_success,'/',order_trials)
# blind omega* candidates on Omega9 for worlds full solves but 9 fails
fail9=[]
for w in W:
    if solve(w,OPS) is not None and solve(w,OMEGA9) is None: fail9.append(w)
print('omega9 gap worlds',len(fail9),Counter(w.family for w in fail9))
# generic epistemic candidate extensions; only reveal_one maps to hidden query, names opaque here
CANDS=['copy_observed','drop_candidate','invert_evidence','reveal_one','add_random_candidate']

def apply_meta(name,s,w):
    s=State(dict(s.data),list(s.candidates),dict(s.evidence),set(s.relations),list(s.constraints),dict(s.classes),s.selected,s.composed,s.retained,s.depth)
    if name=='reveal_one':
        for k,v in w.hidden:
            if k not in s.evidence: s.evidence[k]=v; return s
    elif name=='copy_observed':
        if s.evidence: s.data['copied']=next(iter(s.evidence.values())); return s
    elif name=='drop_candidate':
        if len(s.candidates)>1: s.candidates=s.candidates[:-1]; return s
    elif name=='invert_evidence':
        if s.evidence:
            k=next(iter(s.evidence)); v=s.evidence[k]
            if isinstance(v,int): s.evidence[k]=1-v if v in (0,1) else -v; return s
    elif name=='add_random_candidate':
        if s.candidates: s.candidates=s.candidates+[max(s.candidates)+7]; return s
    return None

def solve_ext(w,meta,max_depth=8):
    s0=init_state(w); q=[(s0,[])]; seen={canon(s0)}
    ops=OMEGA9+['META']
    while q:
        s,path=q.pop(0)
        if len(path)>=max_depth: continue
        for op in ops:
            ns=apply_meta(meta,s,w) if op=='META' else apply(op,s,w)
            if ns is None: continue
            c=canon(ns)
            if c in seen: continue
            np=path+[op if op!='META' else f'omega*:{meta}']
            if goal(ns,w): return np
            seen.add(c); q.append((ns,np))
    return None
meta_scores={m:sum(solve_ext(w,m) is not None for w in fail9) for m in CANDS}
print('meta_scores',meta_scores)
# label permutation null: permute operator implementations but keep displayed labels in original traces -> evaluate exact trace replay
# Effectively asks whether names are arbitrary: yes labels themselves should not matter. Semantic permutation of implementation-to-token should destroy programs.
perm_trials=200; perm_success=[]
for t in range(perm_trials):
    perm=OPS[:] ; rng.shuffle(perm); mapping=dict(zip(OPS,perm))
    good=0; total=0
    for w,p in zip(W,base):
        if not p: continue
        s=init_state(w); total+=1; ok=True
        for label in p:
            ns=apply(mapping[label],s,w)
            if ns is None: ok=False; break
            s=ns
        if ok and goal(s,w): good+=1
    perm_success.append(good/total if total else 0)
print('semantic_shuffle_mean',sum(perm_success)/len(perm_success),'max',max(perm_success))

result={
 'worlds':len(W),'base_solved':base_s,'ablation_solved':ab,
 'minimal_full_coverage_size': next((k for k,c,_ in best if c==base_s),None),
 'best_by_size':[(k,c,[list(x) for x in subs]) for k,c,subs in best],
 'top_pair_interactions':pair[:20],
 'top_motifs':[(list(k),v) for k,v in motifs.most_common(20)],
 'order_shuffle_success':order_shuf_success,'order_shuffle_trials':order_trials,
 'omega9_gap_count':len(fail9),'omega9_gap_families':dict(Counter(w.family for w in fail9)),
 'blind_meta_scores':meta_scores,
 'semantic_shuffle_mean':sum(perm_success)/len(perm_success),'semantic_shuffle_max':max(perm_success),
}
open('/tmp/alphabet_collider_result.json','w').write(json.dumps(result,indent=2))
# robustness sweep over independent generated worlds
sweep=[]
for seed in range(100,120):
    W0=W; W=make_worlds(seed=seed,n_per=20)
    b=sum(solve(w,OPS) is not None for w in W)
    abl={op:sum(solve(w,[x for x in OPS if x!=op]) is not None for w in W) for op in OPS}
    f9=[w for w in W if solve(w,OPS) is not None and solve(w,OMEGA9) is None]
    ms={m:sum(solve_ext(w,m) is not None for w in f9) for m in CANDS}
    sweep.append({'seed':seed,'n':len(W),'full':b,'ablation':abl,'gap9':len(f9),'meta':ms})
W=W0
print('sweep_full_all',all(x['full']==x['n'] for x in sweep))
print('sweep_all10_necessary',all(all(x['ablation'][op] < x['full'] for op in OPS) for x in sweep))
print('sweep_probe_recovery',[(x['gap9'],x['meta']['reveal_one'],max(v for k,v in x['meta'].items() if k!='reveal_one')) for x in sweep[:5]],'...')
result['robustness_sweep']=sweep
result['sweep_full_all']=all(x['full']==x['n'] for x in sweep)
result['sweep_all10_necessary']=all(all(x['ablation'][op] < x['full'] for op in OPS) for x in sweep)
result['sweep_reveal_one_closes_all']=all(x['meta']['reveal_one']==x['gap9'] for x in sweep)
result['sweep_reveal_one_strictly_best']=all(x['meta']['reveal_one']>max(v for k,v in x['meta'].items() if k!='reveal_one') for x in sweep)
open('/tmp/alphabet_collider_result.json','w').write(json.dumps(result,indent=2))
