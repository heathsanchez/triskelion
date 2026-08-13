import ast,json,random,collections,itertools,math
from pathlib import Path

SEED=20261011
SHUFFLES=10000
SRC=Path('experiments/METALOGIC_ALPHABET_FALSIFICATION_V2.py')
OUT=Path('artifacts/multiscale_motif_discovery_v70');OUT.mkdir(parents=True,exist_ok=True)
random.seed(SEED)

# Frozen scale partition, declared before motif outcomes.
SCALE={
 'math':'task','coding':'task','science':'task','search':'task',
 'collider':'representation','representation':'representation','ecology':'control',
 'river':'architecture','memory':'architecture','development':'architecture','system':'architecture'
}

def load_events():
    tree=ast.parse(SRC.read_text())
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='E' for t in node.targets):
            return ast.literal_eval(node.value)
    raise RuntimeError('E not found')

E=load_events()
P=[tuple(x[3]) for x in E]
D=[x[0] for x in E]
L=[SCALE[x[0]] for x in E]
DOMAINS=sorted(set(D))

def contiguous(p,k): return {tuple(p[i:i+k]) for i in range(len(p)-k+1)}
def gapped(p,k): return {tuple(p[i] for i in idx) for idx in itertools.combinations(range(len(p)),k)}
def motifs(programs, maxk=5):
    out=collections.Counter()
    for p in programs:
        seen=set()
        for k in range(2,min(maxk,len(p))+1): seen |= {('C',)+m for m in contiguous(p,k)}
        for k in range(2,min(3,len(p))+1): seen |= {('G',)+m for m in gapped(p,k)}
        out.update(seen)
    return out

OBS=motifs(P)

def support_meta(m):
    hits=[i for i,p in enumerate(P) if m in ({('C',)+x for k in range(2,min(5,len(p))+1) for x in contiguous(p,k)} | {('G',)+x for k in range(2,min(3,len(p))+1) for x in gapped(p,k)})]
    return {'events':len(hits),'domains':len(set(D[i] for i in hits)),'scales':len(set(L[i] for i in hits)), 'domain_names':sorted(set(D[i] for i in hits)), 'scale_names':sorted(set(L[i] for i in hits))}

# Null preserves each event's exact multiset and length, destroying only order.
null={m:[] for m,c in OBS.items() if c>=2}
for _ in range(SHUFFLES):
    sp=[]
    for p in P:
        q=list(p); random.shuffle(q); sp.append(tuple(q))
    c=motifs(sp)
    for m in null: null[m].append(c.get(m,0))

rows=[]
for m,obs in OBS.items():
    if obs<2: continue
    vals=null[m]; mean=sum(vals)/len(vals); ge=sum(v>=obs for v in vals)
    meta=support_meta(m)
    rows.append({
      'kind':'contiguous' if m[0]=='C' else 'gapped', 'motif':list(m[1:]), 'support':obs,
      'domains':meta['domains'],'scales':meta['scales'],'domain_names':meta['domain_names'],'scale_names':meta['scale_names'],
      'null_mean':mean,'enrichment':obs/(mean+1e-9),'p_empirical':(ge+1)/(SHUFFLES+1)
    })
rows.sort(key=lambda r:(r['p_empirical'],-r['scales'],-r['domains'],-r['support']))

# Promotion criteria are frozen: cross-domain, cross-scale, enriched, significant.
def qualifies(r): return r['domains']>=3 and r['scales']>=2 and r['support']>=4 and r['enrichment']>=1.5 and r['p_empirical']<=0.01
promoted=[r for r in rows if qualifies(r)]

# Leave-one-domain-out stability: same motif must still meet support >=3, >=2 remaining domains, >=2 scales.
def motif_present(p,m):
    ops=tuple(m['motif']); k=len(ops)
    if m['kind']=='contiguous': return ops in contiguous(p,k)
    return ops in gapped(p,k)

def loo_stable(r):
    for d in DOMAINS:
        ids=[i for i in range(len(P)) if D[i]!=d and motif_present(P[i],r)]
        if len(ids)<3 or len(set(D[i] for i in ids))<2 or len(set(L[i] for i in ids))<2: return False
    return True
for r in promoted: r['loo_stable']=loo_stable(r)
stable=[r for r in promoted if r['loo_stable']]

# Held-out compression. Learn stable contiguous motifs from all domains except d, then greedily replace longest motifs in held-out programs.
def dictionary(train_ids):
    cnt=motifs([P[i] for i in train_ids])
    cand=[]
    for m,c in cnt.items():
        if m[0]!='C' or c<3: continue
        ids=[i for i in train_ids if tuple(m[1:]) in contiguous(P[i],len(m)-1)]
        if len(set(D[i] for i in ids))>=2 and len(set(L[i] for i in ids))>=2: cand.append(tuple(m[1:]))
    return sorted(set(cand),key=lambda x:(-len(x),x))
def compressed_len(p,dic):
    seq=list(p); cost=0; i=0
    while i<len(seq):
        hit=None
        for m in dic:
            if tuple(seq[i:i+len(m)])==m: hit=m; break
        if hit: cost+=1;i+=len(hit)
        else: cost+=1;i+=1
    return cost
folds=[]; total_raw=total_comp=0
for d in DOMAINS:
    tr=[i for i in range(len(P)) if D[i]!=d]; te=[i for i in range(len(P)) if D[i]==d]
    dic=dictionary(tr)
    raw=sum(len(P[i]) for i in te); comp=sum(compressed_len(P[i],dic) for i in te)
    folds.append({'domain':d,'dictionary_size':len(dic),'raw':raw,'compressed':comp,'reduction':(raw-comp)/raw if raw else 0})
    total_raw+=raw;total_comp+=comp
compression=(total_raw-total_comp)/total_raw

# Matched shuffled control for held-out compression: learn on independently shuffled training traces.
ctrl=[]
for rep in range(1000):
    raw=comp=0
    for d in DOMAINS:
        tr=[]
        for i in range(len(P)):
            if D[i]!=d:
                q=list(P[i]);random.shuffle(q);tr.append((i,tuple(q)))
        # reuse labels/scales but dictionary from shuffled traces
        cnt=collections.Counter()
        for i,q in tr:
            seen=set()
            for k in range(2,min(5,len(q))+1): seen|=contiguous(q,k)
            cnt.update(seen)
        dic=sorted([m for m,c in cnt.items() if c>=3],key=lambda x:(-len(x),x))
        for i in range(len(P)):
            if D[i]==d: raw+=len(P[i]);comp+=compressed_len(P[i],dic)
    ctrl.append((raw-comp)/raw)
ctrl_mean=sum(ctrl)/len(ctrl); ctrl_ge=sum(x>=compression for x in ctrl)

R={
 'protocol':'V70 frozen motif mining from V2 corpus','seed':SEED,'shuffles':SHUFFLES,'n_events':len(E),'domains':DOMAINS,'scale_partition':SCALE,
 'top_motifs':rows[:30],'promoted':promoted,'stable_motifs':stable,
 'loo_compression_folds':folds,'heldout_compression':compression,'shuffled_control_mean':ctrl_mean,'shuffled_control_p':(ctrl_ge+1)/(len(ctrl)+1)
}
R['gates']={
 'at_least_three_stable_motifs':len(stable)>=3,
 'motifs_cross_three_scales':any(r['scales']>=3 for r in stable),
 'heldout_compression_positive':compression>=0.15,
 'compression_beats_shuffle':compression>=ctrl_mean+0.10 and R['shuffled_control_p']<=0.01
}
R['verdict']='PASS_MULTISCALE_MOTIF_DISCOVERY_V70' if all(R['gates'].values()) else 'MIXED_MULTISCALE_MOTIF_DISCOVERY_V70'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))
