"""METALOGIC V24b — DISCOVERABILITY RATCHET WITH SEPARATING SUPPORT

V24's q3 promotion was correctly blocked because two rival q3 laws were observationally
identical on the original generator support (peel depth only 1–2). V24b changes ONLY
the world support so depth 3/4 cases exist; target laws, rival families, typed lineage,
one-generator-per-episode discovery budget, and all causal gates remain unchanged.

This tests both:
  (a) prior verified generators expand the next discoverable interface; and
  (b) ambiguity triggers more discriminating evidence rather than unjustified invention.
"""
import json, random
from pathlib import Path

OUT=Path('artifacts/discoverability_ratchet_v24b');OUT.mkdir(parents=True,exist_ok=True)

def canon_edges(es): return tuple(sorted(set((min(a,b),max(a,b)) for a,b in es if a!=b)))

def make_raw(seed,n_min=7,n_max=14):
    r=random.Random(seed);n=r.randint(n_min,n_max);k=r.randint(2,min(6,n))
    colors=[r.randrange(k) for _ in range(n)]
    for i in range(k):colors[i]=i
    r.shuffle(colors);colors=tuple(colors);edges=[]
    for i in range(n):
        for j in range(i+1,n):
            if r.random()<0.16+0.05*((i+j)%2):edges.append((i,j))
    if not edges:edges=[(0,1)]
    return (n,tuple(edges),colors)

def q1_color(raw):
    n,edges,colors=raw;vals=sorted(set(colors));m={c:i for i,c in enumerate(vals)};qe=[]
    for a,b in edges:
        x,y=m[colors[a]],m[colors[b]]
        if x!=y:qe.append((x,y))
    return (len(vals),canon_edges(qe))
def q1_parity(raw):
    n,edges,_=raw;qe=[]
    for a,b in edges:
        x,y=a%2,b%2
        if x!=y:qe.append((x,y))
    return (2,canon_edges(qe))
def q1_all(raw):return (1,tuple())
def q1_singletons(raw):n,e,_=raw;return (n,canon_edges(e))
Q1={'QUOTIENT_BY_COLOR':q1_color,'QUOTIENT_BY_NODE_PARITY':q1_parity,'QUOTIENT_ALL':q1_all,'QUOTIENT_SINGLETONS':q1_singletons}

def adj(q):
    k,e=q;A=[set() for _ in range(k)]
    for a,b in e:A[a].add(b);A[b].add(a)
    return A

def q2_peel(q):
    k,_=q;A=adj(q);alive=set(range(k));rounds=0
    while alive:
        low={v for v in alive if len(A[v]&alive)<=1}
        if not low:rounds+=1;break
        alive-=low;rounds+=1
    return rounds
def q2_edges(q):return len(q[1])
def q2_vertices(q):return q[0]
def q2_maxdeg(q):return max((len(x) for x in adj(q)),default=0)
def q2_components(q):
    k,_=q;A=adj(q);seen=set();c=0
    for s in range(k):
        if s in seen:continue
        c+=1;seen.add(s);st=[s]
        while st:
            v=st.pop()
            for w in A[v]:
                if w not in seen:seen.add(w);st.append(w)
    return c
Q2={'ITERATIVE_PEEL_DEPTH':q2_peel,'QUOTIENT_EDGE_COUNT':q2_edges,'QUOTIENT_VERTEX_COUNT':q2_vertices,'QUOTIENT_MAX_DEGREE':q2_maxdeg,'QUOTIENT_COMPONENTS':q2_components}

def q3_ge2(x):return int(x>=2)
def q3_even(x):return int(x%2==0)
def q3_nonzero(x):return int(x!=0)
def q3_mod3(x):return int(x%3==0)
def q3_ge3(x):return int(x>=3)
Q3={'DEPTH_AT_LEAST_TWO':q3_ge2,'DEPTH_EVEN':q3_even,'DEPTH_NONZERO':q3_nonzero,'DEPTH_MOD3_ZERO':q3_mod3,'DEPTH_AT_LEAST_THREE':q3_ge3}
TRUE=('QUOTIENT_BY_COLOR','ITERATIVE_PEEL_DEPTH','DEPTH_AT_LEAST_TWO')

class Algebra:
    def __init__(self,q1=None,q2=None,q3=None):self.q1,self.q2,self.q3=q1,q2,q3
    def reachable_types(self):
        t={'RAW'}
        if self.q1:t.add('QUOTIENT')
        if self.q1 and self.q2:t.add('STAT')
        if self.q1 and self.q2 and self.q3:t.add('LABEL')
        return t
    def as_dict(self):return {'q1':self.q1,'q2':self.q2,'q3':self.q3}

def unique(cands,xs,ys):
    s=[]
    for n,f in cands.items():
        try:ok=all(f(x)==y for x,y in zip(xs,ys))
        except Exception:ok=False
        if ok:s.append(n)
    return s

def discover_one(A,raws,oracle_q=None,oracle_stat=None):
    before=sorted(A.reachable_types())
    if A.q1 is None:
        ys=[q1_color(x) for x in raws];s=unique(Q1,raws,ys);slot='q1';typ='QUOTIENT'
    elif A.q2 is None:
        xs=oracle_q if oracle_q is not None else [Q1[A.q1](x) for x in raws]
        ys=[q2_peel(x) for x in xs];s=unique(Q2,xs,ys);slot='q2';typ='STAT'
    elif A.q3 is None:
        xs=oracle_stat if oracle_stat is not None else [Q2[A.q2](Q1[A.q1](x)) for x in raws]
        ys=[q3_ge2(x) for x in xs];s=unique(Q3,xs,ys);slot='q3';typ='LABEL'
    else:return {'promoted':None,'slot':None,'survivors':[],'before':before,'after_type':None}
    return {'promoted':s[0] if len(s)==1 else None,'slot':slot,'survivors':s,'before':before,'after_type':typ if len(s)==1 else None}

def promote(A,r):
    B=Algebra(A.q1,A.q2,A.q3)
    if r['promoted']:setattr(B,r['slot'],r['promoted'])
    return B

def pipeline(A,raws):
    if not(A.q1 and A.q2 and A.q3):return None
    return [Q3[A.q3](Q2[A.q2](Q1[A.q1](x))) for x in raws]

S1=[make_raw(1000+i) for i in range(80)];S2=[make_raw(2000+i) for i in range(80)];S3=[make_raw(3000+i) for i in range(80)]
H=[make_raw(9000+i) for i in range(5000)]
A0=Algebra();r1=discover_one(A0,S1);A1=promote(A0,r1);r2=discover_one(A1,S2);A2=promote(A1,r2);r3=discover_one(A2,S3);A3=promote(A2,r3)

cold2=discover_one(A0,S2);cold3_A0=discover_one(A0,S3);cold3_A1=discover_one(A1,S3)
OQ=[q1_color(x) for x in S2];oracle_q2=discover_one(Algebra(q1=TRUE[0]),S2,oracle_q=OQ)
OS=[q2_peel(q1_color(x)) for x in S3];oracle_q3=discover_one(Algebra(q1=TRUE[0],q2=TRUE[1]),S3,oracle_stat=OS)

gold=[q3_ge2(q2_peel(q1_color(x))) for x in H];held=(pipeline(A3,H)==gold)
abl={}
for slot in ('q1','q2','q3'):
    B=Algebra(A3.q1,A3.q2,A3.q3);setattr(B,slot,None)
    abl[slot]={'pipeline_executable':pipeline(B,H) is not None,'reachable_types':sorted(B.reachable_types())}

# Evidence-support audit: the widened world must actually contain a separator for the V24 ambiguity.
stats3=[q2_peel(q1_color(x)) for x in S3];support=sorted(set(stats3))
separates_ge2_even=any(q3_ge2(x)!=q3_even(x) for x in support)

R={'protocol':'V24b same typed one-new-generator-per-episode discovery; widened separating support only',
   'support_stats':support,'candidate_counts':{'q1':len(Q1),'q2':len(Q2),'q3':len(Q3)},
   'r1':r1,'A1':A1.as_dict(),'r2':r2,'A2':A2.as_dict(),'r3':r3,'A3':A3.as_dict(),
   'cold_stage2_A0':cold2,'cold_stage3_A0':cold3_A0,'cold_stage3_A1':cold3_A1,
   'oracle_q2':oracle_q2,'oracle_q3':oracle_q3,'heldout_n':len(H),'heldout_exact':held,'ablations':abl}
R['gates']={
 'separator_exists':separates_ge2_even,
 'q1_unique':r1['promoted']==TRUE[0] and len(r1['survivors'])==1,
 'q2_unique_after_q1':r2['promoted']==TRUE[1] and len(r2['survivors'])==1,
 'q3_unique_after_q2':r3['promoted']==TRUE[2] and len(r3['survivors'])==1,
 'cold_A0_frontier_is_q1':cold2['slot']=='q1' and cold3_A0['slot']=='q1',
 'A1_frontier_is_q2':cold3_A1['slot']=='q2' and cold3_A1['promoted']==TRUE[1],
 'oracle_q2_discoverable':oracle_q2['promoted']==TRUE[1] and len(oracle_q2['survivors'])==1,
 'oracle_q3_discoverable':oracle_q3['promoted']==TRUE[2] and len(oracle_q3['survivors'])==1,
 '5000_fresh_exact':held,
 'every_lineage_part_required':all(not x['pipeline_executable'] for x in abl.values())}
R['verdict']='PASS_BOUNDED_DISCOVERABILITY_RATCHET_V24B' if all(R['gates'].values()) else 'MIXED_BOUNDED_DISCOVERABILITY_RATCHET_V24B'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))
