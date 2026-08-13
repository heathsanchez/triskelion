"""V28 — verified chunking expands a bounded program language.

Frozen search budget: programs of at most 2 atomic instructions.
A verified composite may be promoted as a new cost-1 atom. The base constructor
inventory never changes. The causal question is whether compression of a verified
composite makes a successor target discoverable that was previously outside the same
fixed description-length budget.
"""
import json, random
from pathlib import Path
OUT=Path('artifacts/chunked_language_ratchet_v28'); OUT.mkdir(parents=True,exist_ok=True)
BUDGET=2

# ---------- deterministic world ----------
def make_raw(seed):
    r=random.Random(seed); n=r.randint(7,13); k=r.randint(2,min(5,n))
    colors=list(range(k))+[r.randrange(k) for _ in range(n-k)]; r.shuffle(colors)
    # deliberately use noncanonical color names so normalization matters
    palette=[11,23,37,41,59][:k]; colors=tuple(palette[c] for c in colors)
    edges=[]
    for i in range(n):
        for j in range(i+1,n):
            if r.random()<0.2+0.08*((i+2*j)%3): edges.append((i,j))
    if not edges: edges=[(0,1)]
    return {'n':n,'edges':tuple(edges),'colors':colors}

def canon(es):return tuple(sorted(set((min(a,b),max(a,b)) for a,b in es if a!=b)))
def adj(g):
    A=[set() for _ in range(g['n'])]
    for a,b in g['edges']:A[a].add(b);A[b].add(a)
    return A

# ---------- frozen base instruction set ----------
# Each atom = (src_type,dst_type,function). Learned chunks are added separately and cost 1.
def normalize_colors(x):
    vals=sorted(set(x['colors'])); mp={c:i for i,c in enumerate(vals)}
    return {'n':x['n'],'edges':x['edges'],'colors':tuple(mp[c] for c in x['colors'])}
def build_quotient(x):
    vals=sorted(set(x['colors'])); k=len(vals); es=[]
    for a,b in x['edges']:
        u,v=x['colors'][a],x['colors'][b]
        if u!=v:es.append((u,v))
    return {'n':k,'edges':canon(es)}
def parity_quotient(x):
    es=[]
    for a,b in x['edges']:
        u,v=a%2,b%2
        if u!=v:es.append((u,v))
    return {'n':2,'edges':canon(es)}
def raw_graph(x):return {'n':x['n'],'edges':canon(x['edges'])}
def edge_count(g):return len(g['edges'])
def vertex_count(g):return g['n']
def max_degree(g):return max((len(s) for s in adj(g)),default=0)
def peel_rounds(g):
    A=adj(g);alive=set(range(g['n']));z=0
    while alive:
        low={v for v in alive if len(A[v]&alive)<=1}
        if not low:z+=1;break
        alive-=low;z+=1
    return z
def ge1(x):return int(x>=1)
def ge2(x):return int(x>=2)
def ge3(x):return int(x>=3)
def even(x):return int(x%2==0)
def nonzero(x):return int(x!=0)
def raw_edge_count(x):return len(x['edges'])
def raw_nonempty(x):return int(bool(x['edges']))

BASE={
 'NORMALIZE_COLORS':('RAW','NORM',normalize_colors),
 'BUILD_QUOTIENT':('NORM','GRAPH',build_quotient),
 'PARITY_QUOTIENT':('RAW','GRAPH',parity_quotient),
 'RAW_GRAPH':('RAW','GRAPH',raw_graph),
 'EDGE_COUNT':('GRAPH','INT',edge_count),
 'VERTEX_COUNT':('GRAPH','INT',vertex_count),
 'MAX_DEGREE':('GRAPH','INT',max_degree),
 'PEEL_ROUNDS':('GRAPH','INT',peel_rounds),
 'GE1':('INT','BOOL',ge1),'GE2':('INT','BOOL',ge2),'GE3':('INT','BOOL',ge3),
 'EVEN':('INT','BOOL',even),'NONZERO':('INT','BOOL',nonzero),
 'RAW_EDGE_COUNT':('RAW','INT',raw_edge_count),
 'RAW_NONEMPTY':('RAW','BOOL',raw_nonempty),
}

def eval_program(program,x,atoms):
    cur=x
    for name in program:cur=atoms[name][2](cur)
    return cur

def enumerate_programs(src,dst,atoms,budget=BUDGET):
    out=[]
    def dfs(t,p):
        if p and t==dst:out.append(tuple(p))
        if len(p)>=budget:return
        for name,(a,b,f) in sorted(atoms.items()):
            if a==t:dfs(b,p+[name])
    dfs(src,[])
    return sorted(set(out),key=lambda p:(len(p),p))

def unique_survivor(src,dst,xs,ys,atoms):
    cand=enumerate_programs(src,dst,atoms); surv=[]
    for p in cand:
        try:ok=all(eval_program(p,x,atoms)==y for x,y in zip(xs,ys))
        except Exception:ok=False
        if ok:surv.append(p)
    # shortest verified survivor only, with uniqueness at minimum cost
    if not surv:return None,cand,[]
    m=min(map(len,surv)); short=[p for p in surv if len(p)==m]
    return (short[0] if len(short)==1 else None),cand,short

def chunk(name,src,dst,program,atoms):
    frozen=dict(atoms)
    def f(x,p=tuple(program),A=frozen):return eval_program(p,x,A)
    return (src,dst,f)

# gold lineage as behavior, not supplied candidate labels
Q1_PROGRAM=('NORMALIZE_COLORS','BUILD_QUOTIENT')
def gold_q1(x):return eval_program(Q1_PROGRAM,x,BASE)
def gold_q2(x):return peel_rounds(gold_q1(x))
def gold_q3(x):return ge2(gold_q2(x))

S1=[make_raw(1000+i) for i in range(100)]
S2=[make_raw(2000+i) for i in range(100)]
S3=[make_raw(3000+i) for i in range(100)]
H=[make_raw(90000+i) for i in range(10000)]

# Generation 1: discover q1 within base budget 2.
A0=dict(BASE)
p1,c1,s1=unique_survivor('RAW','GRAPH',S1,[gold_q1(x) for x in S1],A0)
A1=dict(A0)
if p1:A1['Q1_CHUNK']=chunk('Q1_CHUNK','RAW','GRAPH',p1,A0)

# q2 before/after q1 chunk, same target and same budget.
y2=[gold_q2(x) for x in S2]
p2_cold,c2_cold,s2_cold=unique_survivor('RAW','INT',S2,y2,A0)
p2,c2,s2=unique_survivor('RAW','INT',S2,y2,A1)
A2=dict(A1)
if p2:A2['Q2_CHUNK']=chunk('Q2_CHUNK','RAW','INT',p2,A1)

# q3 before/after q2 chunk under same budget.
y3=[gold_q3(x) for x in S3]
p3_from_A1,c3_cold,s3_cold=unique_survivor('RAW','BOOL',S3,y3,A1)
p3,c3,s3=unique_survivor('RAW','BOOL',S3,y3,A2)
A3=dict(A2)
if p3:A3['Q3_CHUNK']=chunk('Q3_CHUNK','RAW','BOOL',p3,A2)

# oracle chunk controls: inject exact prior verified chunk, without lineage history.
O1=dict(A0);O1['Q1_CHUNK']=chunk('Q1_CHUNK','RAW','GRAPH',Q1_PROGRAM,A0)
op2,_,os2=unique_survivor('RAW','INT',S2,y2,O1)
O2=dict(O1)
if op2:O2['Q2_CHUNK']=chunk('Q2_CHUNK','RAW','INT',op2,O1)
op3,_,os3=unique_survivor('RAW','BOOL',S3,y3,O2)

# description-length accounting in unchunked base grammar
base_q2_program=Q1_PROGRAM+('PEEL_ROUNDS',)
base_q3_program=base_q2_program+('GE2',)

# heldout exact from learned top chunk and full explicit lineage
pred_top=[A3['Q3_CHUNK'][2](x) for x in H] if 'Q3_CHUNK' in A3 else []
gold=[gold_q3(x) for x in H]

# causal chunk ablations: remove each learned atomic abbreviation while preserving BASE.
def target_discoverable(atoms,dst,goldfn,stream):
    p,_,s=unique_survivor('RAW',dst,stream,[goldfn(x) for x in stream],atoms);return p,s
ab1_atoms=dict(A1);ab1_atoms.pop('Q1_CHUNK',None)
ab1_q2,_=target_discoverable(ab1_atoms,'INT',gold_q2,S2)
ab2_atoms=dict(A2);ab2_atoms.pop('Q2_CHUNK',None)
ab2_q3,_=target_discoverable(ab2_atoms,'BOOL',gold_q3,S3)

R={
 'protocol':'V28 fixed base grammar + cost-1 verified chunks; max program length 2',
 'budget':BUDGET,'base_atom_count':len(BASE),
 'q1':{'program':p1,'candidate_count':len(c1),'min_survivors':s1},
 'q2_cold':{'program':p2_cold,'candidate_count':len(c2_cold),'min_survivors':s2_cold,'true_unchunked_cost':len(base_q2_program)},
 'q2_warm':{'program':p2,'candidate_count':len(c2),'min_survivors':s2},
 'q3_before_q2_chunk':{'program':p3_from_A1,'candidate_count':len(c3_cold),'min_survivors':s3_cold,'true_unchunked_cost':len(base_q3_program)},
 'q3_warm':{'program':p3,'candidate_count':len(c3),'min_survivors':s3},
 'oracle_q2':op2,'oracle_q3':op3,
 'ablate_q1_then_q2_discoverable':ab1_q2,
 'ablate_q2_then_q3_discoverable':ab2_q3,
 'heldout_n':len(H),'heldout_exact':pred_top==gold,
}
R['gates']={
 'q1_verified_two_step_chunk':p1==Q1_PROGRAM and len(s1)==1,
 'q2_outside_cold_budget':p2_cold is None and len(base_q2_program)>BUDGET,
 'q2_becomes_discoverable_after_q1_chunk':p2==('Q1_CHUNK','PEEL_ROUNDS') and len(s2)==1,
 'q3_outside_pre_q2_budget':p3_from_A1 is None and len(base_q3_program)>BUDGET,
 'q3_becomes_discoverable_after_q2_chunk':p3==('Q2_CHUNK','GE2') and len(s3)==1,
 'oracle_chunks_restore_successors':op2==('Q1_CHUNK','PEEL_ROUNDS') and op3==('Q2_CHUNK','GE2'),
 'chunk_ablations_remove_successor_discoverability':ab1_q2 is None and ab2_q3 is None,
 'heldout_exact':pred_top==gold,
}
R['verdict']='PASS_CHUNKED_LANGUAGE_RATCHET_V28' if all(R['gates'].values()) else 'MIXED_CHUNKED_LANGUAGE_RATCHET_V28'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2,default=list));print(json.dumps(R,indent=2,default=list))
