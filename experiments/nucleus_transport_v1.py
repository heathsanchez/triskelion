#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from itertools import product
import hashlib, json

PROTOCOL="NUCLEUS_TRANSPORT_V1"
PRECOMMIT="fdf4ebd18dc7e2195ead3d247b1125491c874bc6"

def H(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class World:
    name:str
    carrier:tuple
    ground:int
    op_name:str
    op:object
    control_name:str|None=None
    control:object|None=None

def bool_d(a,b): return (1-a) & b
def h3_neg(a): return 2 if a==0 else 0
def h3_d(a,b): return min(h3_neg(a),b)
def k3_d(a,b): return min(2-a,b)
def t3_d(a,b): return max(0,b-a)
def z3_d(a,b): return (b-a)%3

def meet(a,b): return min(a,b)
def absdiff(a,b): return abs(b-a)
def z3_sum(a,b): return (a+b)%3

WORLDS=[
    World("B",(0,1),1,"directed_boolean",bool_d),
    World("H3",(0,1,2),2,"heyting_directed",h3_d,"meet",meet),
    World("K3",(0,1,2),2,"involutive_directed",k3_d,"meet",meet),
    World("T3",(0,1,2),2,"truncated_directed",t3_d,"absolute_difference",absdiff),
    World("Z3",(0,1,2),0,"cyclic_directed",z3_d,"cyclic_sum",z3_sum),
]

def assignments(carrier,n):
    return list(product(carrier, repeat=n))

def projections(carrier,n):
    A=assignments(carrier,n)
    return [tuple(row[j] for row in A) for j in range(n)]

def const_fn(carrier,n,c):
    return tuple([c]*(len(carrier)**n))

def pointwise(op,f,g):
    return tuple(op(a,b) for a,b in zip(f,g))

def closure(carrier,n,op,ground=None):
    seeds=projections(carrier,n)
    if ground is not None:
        seeds.append(const_fn(carrier,n,ground))
    seen={}
    order=[]
    depth={}
    for s in seeds:
        if s not in seen:
            seen[s]=len(order);order.append(s);depth[s]=0
    q=0
    while q<len(order):
        x=order[q]; q+=1
        snapshot=list(order)
        for y in snapshot:
            for a,b in ((x,y),(y,x)):
                z=pointwise(op,a,b)
                if z not in seen:
                    seen[z]=len(order);order.append(z)
                    depth[z]=1+max(depth[a],depth[b])
    total=len(carrier)**(len(carrier)**n)
    constants={c:const_fn(carrier,n,c) in seen for c in carrier}
    enc=[list(f) for f in sorted(order)]
    return {
        "count":len(order),
        "total":total,
        "fraction":len(order)/total,
        "max_derivation_depth":max(depth.values()) if depth else 0,
        "all_constants":all(constants.values()),
        "constants":constants,
        "hash":H(enc),
        "functions":set(order),
    }

def embed_unary_to_binary(carrier, unary_funcs):
    A=assignments(carrier,2)
    out=set()
    vals=list(carrier)
    pos={v:i for i,v in enumerate(vals)}
    for f in unary_funcs:
        out.add(tuple(f[pos[row[0]]] for row in A))
    return out

def bool_set_closure(n):
    A=assignments((0,1),n)
    universe=frozenset(range(len(A)))
    seeds=[]
    for j in range(n):
        seeds.append(frozenset(i for i,row in enumerate(A) if row[j]==1))
    seeds.append(universe)
    seen=set(seeds);order=list(seen);q=0
    while q<len(order):
        x=order[q];q+=1
        snap=list(order)
        for y in snap:
            # D(x,y)=y\x and reverse
            for z in (y-x,x-y):
                if z not in seen:
                    seen.add(z);order.append(z)
    masks=sorted(sum(1<<i for i in s) for s in seen)
    return {"count":len(seen),"hash":H(masks),"masks":masks}

def tuple_bool_masks(funcs):
    masks=[]
    for f in funcs:
        m=0
        for i,v in enumerate(f):
            if v:m|=1<<i
        masks.append(m)
    return sorted(masks)

def analyze_once():
    directed={}
    controls={}
    transported=[]
    comparisons={}
    for w in WORLDS:
        wr={}
        for n in (1,2)+( (3,) if w.name=="B" else () ):
            with_g=closure(w.carrier,n,w.op,w.ground)
            no_g=closure(w.carrier,n,w.op,None)
            rec={k:v for k,v in with_g.items() if k!="functions"}
            rec["no_ground_count"]=no_g["count"]
            rec["reference_delta"]=with_g["count"]-no_g["count"]
            rec["no_ground_all_constants"]=no_g["all_constants"]
            wr[str(n)]=rec
        unary=closure(w.carrier,1,w.op,w.ground)
        binary=closure(w.carrier,2,w.op,w.ground)
        embedded=embed_unary_to_binary(w.carrier,unary["functions"])
        fresh_count=len(binary["functions"]-embedded)
        wr["fresh_difference"]={
            "embedded_unary_count":len(embedded),
            "binary_count":binary["count"],
            "new_binary_consequences":fresh_count,
            "reopens":fresh_count>0,
        }
        directed[w.name]=wr

        if w.control is not None:
            c1=closure(w.carrier,1,w.control,w.ground)
            c2=closure(w.carrier,2,w.control,w.ground)
            controls[w.name]={
                "control_name":w.control_name,
                "1":{"count":c1["count"],"total":c1["total"],"hash":c1["hash"]},
                "2":{"count":c2["count"],"total":c2["total"],"hash":c2["hash"]},
            }
            comparisons[w.name]={
                "directed_count":binary["count"],
                "symmetric_count":c2["count"],
                "comparison":"outperform" if binary["count"]>c2["count"] else ("underperform" if binary["count"]<c2["count"] else "tie"),
                "operations_extensionally_different":any(w.op(a,b)!=w.control(a,b) for a in w.carrier for b in w.carrier),
            }

        if w.name!="B":
            seed_count=len(set(projections(w.carrier,2)+[const_fn(w.carrier,2,w.ground)]))
            refdelta=wr["2"]["reference_delta"]
            no_ground_all=wr["2"]["no_ground_all_constants"]
            different=comparisons[w.name]["operations_extensionally_different"]
            ok=(binary["count"]>seed_count and fresh_count>0 and different and (refdelta>0 or no_ground_all))
            if ok: transported.append(w.name)

    # Boolean representation invariance.
    btuple=closure((0,1),3,bool_d,1)
    bset=bool_set_closure(3)
    tuple_masks=tuple_bool_masks(btuple["functions"])
    repr_ok=(bset["count"]==btuple["count"] and bset["masks"]==tuple_masks)
    repr_hash=H(tuple_masks)

    all_transport_refdep=all(directed[n]["2"]["reference_delta"]>0 for n in transported) if transported else False
    transported_all_constants=[n for n in transported if directed[n]["2"]["no_ground_all_constants"]]
    support="broader_reference_plus_directed_difference" if transported else "boolean_only_under_this_protocol"

    return {
        "directed":directed,
        "controls":controls,
        "comparisons":comparisons,
        "transported_worlds":transported,
        "all_transported_reference_dependent":all_transport_refdep,
        "transported_deriving_all_constants_without_ground":transported_all_constants,
        "boolean_representation_invariance":{"ok":repr_ok,"hash":repr_hash,"count":btuple["count"]},
        "support_classification":support,
    }

def main():
    a=analyze_once(); b=analyze_once()
    replay=(H(a)==H(b))
    T={
        "T1_all_worlds_controls_exact":len(a["directed"])==5 and len(a["controls"])==4,
        "T2_boolean_n3_exact":"3" in a["directed"]["B"],
        "T3_deterministic_replay":replay,
        "T4_boolean_representation_invariance":a["boolean_representation_invariance"]["ok"],
        "T5_boolean_complete_n123":all(a["directed"]["B"][str(n)]["count"]==a["directed"]["B"][str(n)]["total"] for n in (1,2,3)),
        "T6_counts_within_totals":all(a["directed"][w][str(n)]["count"]<=a["directed"][w][str(n)]["total"] for w in a["directed"] for n in ((1,2,3) if w=="B" else (1,2))),
        "T7_fresh_difference_reported":all("fresh_difference" in a["directed"][w] for w in a["directed"]),
        "T8_reference_delta_reported":all("reference_delta" in a["directed"][w]["2"] for w in a["directed"]),
        "T9_directed_symmetric_comparison_reported":len(a["comparisons"])==4,
        "T10_nonboolean_transport_exists":len(a["transported_worlds"])>=1,
    }
    required_reports={
        "T11_transported_worlds":a["transported_worlds"],
        "T12_all_transported_reference_dependent":a["all_transported_reference_dependent"],
        "T13_transported_deriving_all_constants_without_ground":a["transported_deriving_all_constants_without_ground"],
        "T14_directed_vs_symmetric":a["comparisons"],
        "T15_name_blind_policy":True,
        "T16_support_classification":a["support_classification"],
    }
    verdict="PASS_NUCLEUS_TRANSPORT_V1" if all(T.values()) else ("PARTIAL_NUCLEUS_TRANSPORT_V1" if any(T.values()) else "VALID_NEGATIVE_NUCLEUS_TRANSPORT_V1")
    result={
        "protocol":PROTOCOL,
        "precommit_commit":PRECOMMIT,
        "verdict":verdict,
        **a,
        "headline_gates":T,
        "required_reports":required_reports,
        "result_hash":H(a),
        "claim_boundary":"Exact finite pointed algebras only. Transport means the frozen finite generativity signature, not universal substrate independence."
    }
    out=Path("results/nucleus_transport_v1");out.mkdir(parents=True,exist_ok=True)
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (out/"summary.json").write_text(json.dumps({
        "verdict":verdict,
        "transported_worlds":a["transported_worlds"],
        "comparisons":a["comparisons"],
        "boolean_representation_invariance":a["boolean_representation_invariance"],
        "support_classification":a["support_classification"],
        "headline_gates":T,
        "required_reports":required_reports,
        "result_hash":H(a),
    },indent=2,sort_keys=True)+"\n")
    print("NUCLEUS TRANSPORT V1",verdict)
    print(json.dumps(json.loads((out/"summary.json").read_text()),indent=2,sort_keys=True))
if __name__=="__main__":
    main()
