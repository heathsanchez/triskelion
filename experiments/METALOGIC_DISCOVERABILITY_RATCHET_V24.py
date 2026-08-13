"""METALOGIC V24 — BOUNDED DISCOVERABILITY RATCHET

Question: can one verified generator causally enlarge what the *same frozen one-step
discovery procedure* can discover next?

The world has three typed interfaces:
    RAW --q1--> QUOTIENT --q2--> STAT --q3--> LABEL

Each operator is selected from a frozen rival family by an external exact verifier.
A discovery episode may promote at most ONE new generator. A later interface can be
searched only if its input type is currently reachable, unless an explicit oracle-input
control supplies values of that type.

This intentionally proves a bounded claim about Discoverable_1(A), not open-ended AGI.
"""
from __future__ import annotations
import json, random
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple, Any

OUT = Path("artifacts/discoverability_ratchet_v24")
OUT.mkdir(parents=True, exist_ok=True)

# ---------- deterministic graph world ----------
Raw = Tuple[int, Tuple[Tuple[int,int], ...], Tuple[int, ...]]  # n, edges, colors
Quot = Tuple[int, Tuple[Tuple[int,int], ...]]                  # k, quotient edges


def make_raw(seed: int, n_min=5, n_max=11) -> Raw:
    r = random.Random(seed)
    n = r.randint(n_min, n_max)
    k = r.randint(2, min(4, n))
    colors = tuple(r.randrange(k) for _ in range(n))
    # force all color classes to occur
    colors = list(colors)
    for i in range(k): colors[i] = i
    r.shuffle(colors)
    colors = tuple(colors)
    edges=[]
    for i in range(n):
        for j in range(i+1,n):
            if r.random() < 0.28 + 0.08*((i+j)%2): edges.append((i,j))
    # avoid empty graph
    if not edges: edges=[(0,1)]
    return (n, tuple(edges), colors)


def canon_edges(es):
    return tuple(sorted(set((min(a,b),max(a,b)) for a,b in es if a!=b)))


def q1_color(raw: Raw) -> Quot:
    n,edges,colors=raw
    vals=sorted(set(colors)); remap={c:i for i,c in enumerate(vals)}
    qe=[]
    for a,b in edges:
        x,y=remap[colors[a]],remap[colors[b]]
        if x!=y: qe.append((x,y))
    return (len(vals), canon_edges(qe))


def q1_parity(raw: Raw) -> Quot:
    n,edges,colors=raw
    qe=[]
    for a,b in edges:
        x,y=a%2,b%2
        if x!=y: qe.append((x,y))
    return (2, canon_edges(qe))


def q1_all(raw: Raw) -> Quot:
    return (1, tuple())


def q1_singletons(raw: Raw) -> Quot:
    n,edges,_=raw
    return (n, canon_edges(edges))

Q1: Dict[str,Callable[[Raw],Quot]]={
    "QUOTIENT_BY_COLOR":q1_color,
    "QUOTIENT_BY_NODE_PARITY":q1_parity,
    "QUOTIENT_ALL":q1_all,
    "QUOTIENT_SINGLETONS":q1_singletons,
}


def adj(q: Quot):
    k,edges=q
    A=[set() for _ in range(k)]
    for a,b in edges: A[a].add(b);A[b].add(a)
    return A


def q2_peel_rounds(q: Quot) -> int:
    # parallel leaf/isolated peeling rounds until empty; cycles require final bulk round
    k,_=q; A=adj(q); alive=set(range(k)); rounds=0
    while alive:
        low={v for v in alive if len(A[v]&alive)<=1}
        if not low:
            rounds += 1
            break
        alive-=low; rounds+=1
    return rounds


def q2_edge_count(q: Quot)->int:return len(q[1])
def q2_vertex_count(q: Quot)->int:return q[0]
def q2_max_degree(q: Quot)->int:return max((len(x) for x in adj(q)),default=0)
def q2_components(q: Quot)->int:
    k,_=q;A=adj(q);seen=set();c=0
    for s in range(k):
        if s in seen: continue
        c+=1;st=[s];seen.add(s)
        while st:
            v=st.pop()
            for w in A[v]:
                if w not in seen:seen.add(w);st.append(w)
    return c

Q2: Dict[str,Callable[[Quot],int]]={
    "ITERATIVE_PEEL_DEPTH":q2_peel_rounds,
    "QUOTIENT_EDGE_COUNT":q2_edge_count,
    "QUOTIENT_VERTEX_COUNT":q2_vertex_count,
    "QUOTIENT_MAX_DEGREE":q2_max_degree,
    "QUOTIENT_COMPONENTS":q2_components,
}


def q3_ge2(x:int)->int:return int(x>=2)
def q3_even(x:int)->int:return int(x%2==0)
def q3_nonzero(x:int)->int:return int(x!=0)
def q3_mod3(x:int)->int:return int(x%3==0)
def q3_ge3(x:int)->int:return int(x>=3)
Q3: Dict[str,Callable[[int],int]]={
    "DEPTH_AT_LEAST_TWO":q3_ge2,
    "DEPTH_EVEN":q3_even,
    "DEPTH_NONZERO":q3_nonzero,
    "DEPTH_MOD3_ZERO":q3_mod3,
    "DEPTH_AT_LEAST_THREE":q3_ge3,
}

TRUE=("QUOTIENT_BY_COLOR","ITERATIVE_PEEL_DEPTH","DEPTH_AT_LEAST_TWO")

@dataclass
class Algebra:
    q1: str|None=None
    q2: str|None=None
    q3: str|None=None

    def reachable_types(self):
        t={"RAW"}
        if self.q1:t.add("QUOTIENT")
        if self.q1 and self.q2:t.add("STAT")
        if self.q1 and self.q2 and self.q3:t.add("LABEL")
        return t


def unique_survivor(cands: Dict[str,Callable], xs: List[Any], ys: List[Any]):
    surv=[]
    for name,f in cands.items():
        try: ok=all(f(x)==y for x,y in zip(xs,ys))
        except Exception: ok=False
        if ok:surv.append(name)
    return surv

# Frozen one-step discoverer. It can search only the first missing reachable interface.
def discover_one(A:Algebra, raw_cases:List[Raw], oracle_q:List[Quot]|None=None,
                 oracle_stat:List[int]|None=None):
    before=sorted(A.reachable_types())
    # q1 interface is reachable from RAW
    if A.q1 is None:
        ys=[q1_color(x) for x in raw_cases]
        s=unique_survivor(Q1,raw_cases,ys)
        return {"promoted":s[0] if len(s)==1 else None,"slot":"q1","survivors":s,
                "before":before,"after_type":"QUOTIENT" if len(s)==1 else None}
    # q2 interface requires quotient inputs, either generated by q1 or explicit oracle
    if A.q2 is None:
        qs=oracle_q if oracle_q is not None else [Q1[A.q1](x) for x in raw_cases]
        ys=[q2_peel_rounds(q) for q in qs]
        s=unique_survivor(Q2,qs,ys)
        return {"promoted":s[0] if len(s)==1 else None,"slot":"q2","survivors":s,
                "before":before,"after_type":"STAT" if len(s)==1 else None}
    # q3 interface requires stat inputs, either generated by q1/q2 or explicit oracle
    if A.q3 is None:
        if oracle_stat is not None: stats=oracle_stat
        else: stats=[Q2[A.q2](Q1[A.q1](x)) for x in raw_cases]
        ys=[q3_ge2(v) for v in stats]
        s=unique_survivor(Q3,stats,ys)
        return {"promoted":s[0] if len(s)==1 else None,"slot":"q3","survivors":s,
                "before":before,"after_type":"LABEL" if len(s)==1 else None}
    return {"promoted":None,"slot":None,"survivors":[],"before":before,"after_type":None}


def apply_promotion(A:Algebra,r):
    B=Algebra(A.q1,A.q2,A.q3)
    if r["promoted"]:
        setattr(B,r["slot"],r["promoted"])
    return B


def eval_pipeline(A:Algebra, raws:List[Raw]):
    if not (A.q1 and A.q2 and A.q3): return None
    return [Q3[A.q3](Q2[A.q2](Q1[A.q1](x))) for x in raws]

# Independent calibration streams for each generation + hostile holdout.
S1=[make_raw(1000+i) for i in range(40)]
S2=[make_raw(2000+i) for i in range(40)]
S3=[make_raw(3000+i) for i in range(40)]
H =[make_raw(9000+i) for i in range(2000)]

A0=Algebra()
r1=discover_one(A0,S1); A1=apply_promotion(A0,r1)
r2=discover_one(A1,S2); A2=apply_promotion(A1,r2)
r3=discover_one(A2,S3); A3=apply_promotion(A2,r3)

# Causal discoverability ablations under the SAME one-promotion budget.
# Cold stage-2 episode from A0 can only discover q1, not q2.
cold2=discover_one(A0,S2)
# Cold stage-3 from A0 likewise only reaches q1; from A1 only q2.
cold3_A0=discover_one(A0,S3)
cold3_A1=discover_one(A1,S3)

# Oracle-interface controls: later operator families are perfectly discoverable if their
# input representation is supplied externally, showing they are not arbitrarily hidden.
OQ=[q1_color(x) for x in S2]
# To isolate q2, provide the q1 slot only as an interface-enabler; q values themselves are oracle supplied.
A_q_interface=Algebra(q1="QUOTIENT_BY_COLOR")
oracle_q2=discover_one(A_q_interface,S2,oracle_q=OQ)
OS=[q2_peel_rounds(q1_color(x)) for x in S3]
A_stat_interface=Algebra(q1="QUOTIENT_BY_COLOR",q2="ITERATIVE_PEEL_DEPTH")
oracle_q3=discover_one(A_stat_interface,S3,oracle_stat=OS)

# Fresh held-out exact verification and operator ablations.
gold=[q3_ge2(q2_peel_rounds(q1_color(x))) for x in H]
pred=eval_pipeline(A3,H)
heldout_correct=(pred==gold)
abla={}
for slot in ("q1","q2","q3"):
    B=Algebra(A3.q1,A3.q2,A3.q3);setattr(B,slot,None)
    nabla[slot]={"pipeline_executable":eval_pipeline(B,H) is not None,
                 "reachable_types":sorted(B.reachable_types())}

# stronger developmental ablation: q1 absence removes q2 discovery interface under one-step budget;
# q2 absence removes q3 discovery interface. We report the actual promoted slot, not just task failure.
q1_removed_frontier=discover_one(Algebra(),S2)
q2_removed_frontier=discover_one(Algebra(q1=A1.q1),S3)

R={
 "protocol":"V24 frozen typed one-new-generator-per-episode discoverer",
 "candidate_counts":{"q1":len(Q1),"q2":len(Q2),"q3":len(Q3)},
 "true_lineage":TRUE,
 "r1":r1,"A1":A1.__dict__,
 "r2":r2,"A2":A2.__dict__,
 "r3":r3,"A3":A3.__dict__,
 "cold_stage2_from_A0":cold2,
 "cold_stage3_from_A0":cold3_A0,
 "cold_stage3_from_A1":cold3_A1,
 "oracle_q2":oracle_q2,"oracle_q3":oracle_q3,
 "heldout_n":len(H),"heldout_exact":heldout_correct,
 "ablations":nabla,
 "q1_removed_discovery_frontier":q1_removed_frontier,
 "q2_removed_discovery_frontier":q2_removed_frontier,
}
R["gates"]={
 "q1_unique_verified":r1["promoted"]==TRUE[0] and len(r1["survivors"])==1,
 "q2_requires_prior_frontier":r2["promoted"]==TRUE[1] and cold2["slot"]=="q1" and cold2["promoted"]==TRUE[0],
 "q3_requires_prior_frontier":r3["promoted"]==TRUE[2] and cold3_A0["slot"]=="q1" and cold3_A1["slot"]=="q2",
 "oracle_restores_q2":oracle_q2["promoted"]==TRUE[1] and len(oracle_q2["survivors"])==1,
 "oracle_restores_q3":oracle_q3["promoted"]==TRUE[2] and len(oracle_q3["survivors"])==1,
 "independent_holdout_exact":heldout_correct,
 "all_lineage_parts_causally_required":all(not v["pipeline_executable"] for v in nabla.values()),
 "q1_ablation_removes_q2_discovery":q1_removed_frontier["slot"]=="q1",
 "q2_ablation_removes_q3_discovery":q2_removed_frontier["slot"]=="q2",
}
R["verdict"]="PASS_BOUNDED_DISCOVERABILITY_RATCHET_V24" if all(R["gates"].values()) else "MIXED_BOUNDED_DISCOVERABILITY_RATCHET_V24"
(OUT/"RESULT.json").write_text(json.dumps(R,indent=2))
print(json.dumps(R,indent=2))
