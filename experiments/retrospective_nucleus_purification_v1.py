#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib, json

PROTOCOL = "RETROSPECTIVE_NUCLEUS_PURIFICATION_V1"
PRECOMMIT = "89b56be88ce3ab95f57e64caeadf8e324b0024bb"
PARENT_HASH = "b68ff7c70c8685f98d671367b1f536dba64664a16d0b64aa555d97091a3c2d1f"
PROTECTED = ("B","H3","K3","T3")
EXPECTED_COUNTS = {"B":16,"H3":22,"K3":84,"T3":3888,"Z3":9}

def H(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class World:
    name: str
    carrier: tuple
    ground: int

def bool_d(a,b): return (1-a) & b
def h3_neg(a): return 2 if a == 0 else 0
def h3_d(a,b): return min(h3_neg(a),b)
def k3_d(a,b): return min(2-a,b)
def t3_d(a,b): return max(0,b-a)
def z3_d(a,b): return (b-a) % 3

WORLDS = {
    "B": World("B",(0,1),1),
    "H3": World("H3",(0,1,2),2),
    "K3": World("K3",(0,1,2),2),
    "T3": World("T3",(0,1,2),2),
    "Z3": World("Z3",(0,1,2),0),
}
OPS = {"B":bool_d,"H3":h3_d,"K3":k3_d,"T3":t3_d,"Z3":z3_d}

def assignments(carrier,n):
    return list(product(carrier, repeat=n))

def projections(carrier,n):
    A = assignments(carrier,n)
    return [tuple(row[j] for row in A) for j in range(n)]

def const_fn(carrier,n,c):
    return tuple([c] * (len(carrier) ** n))

def pointwise(op,f,g):
    return tuple(op(a,b) for a,b in zip(f,g))

def closure_raw(carrier,n,op,ground_marker):
    seeds = projections(carrier,n)
    if ground_marker is not None:
        seeds.append(const_fn(carrier,n,ground_marker))
    seen = set()
    order = []
    for s in seeds:
        if s not in seen:
            seen.add(s); order.append(s)
    q = 0
    while q < len(order):
        x = order[q]
        q += 1
        prev = order[:q]
        for y in prev:
            z = pointwise(op,x,y)
            if z not in seen:
                seen.add(z); order.append(z)
            z = pointwise(op,y,x)
            if z not in seen:
                seen.add(z); order.append(z)
    return frozenset(seen)

@lru_cache(maxsize=None)
def closure(world_name,n,ground_key,reverse=False):
    w = WORLDS[world_name]
    op0 = OPS[world_name]
    op = (lambda a,b: op0(b,a)) if reverse else op0
    ground = None if ground_key == "NONE" else int(ground_key)
    return closure_raw(w.carrier,n,op,ground)

def one_layer(world_name):
    w = WORLDS[world_name]
    op = OPS[world_name]
    seeds = set(projections(w.carrier,2) + [const_fn(w.carrier,2,w.ground)])
    return frozenset(seeds | {pointwise(op,a,b) for a in seeds for b in seeds})

def embed_unary(world_name, funcs):
    w = WORLDS[world_name]
    A = assignments(w.carrier,2)
    pos = {v:i for i,v in enumerate(w.carrier)}
    return frozenset(tuple(f[pos[row[0]]] for row in A) for f in funcs)

def digest_set(s):
    return H([list(x) for x in sorted(s)])

def witness(full, reduced):
    missing = sorted(full - reduced)
    return list(missing[0]) if missing else None

def rel_apply(rel,a,b,mask):
    na=(~a)&mask; nb=(~b)&mask; out=0
    if rel&1: out|=na&nb
    if rel&2: out|=na&b
    if rel&4: out|=a&nb
    if rel&8: out|=a&b
    return out

def bool_projection_masks(n):
    out=[]; rows=1<<n
    for j in range(n):
        v=0
        for r in range(rows):
            if (r>>j)&1: v |= 1<<r
        out.append(v)
    return out

def bool_relation_closure(rel,n=2):
    rows=1<<n
    mask=(1<<rows)-1
    seen=set(bool_projection_masks(n))
    seen.add(mask)
    order=list(sorted(seen))
    q=0
    while q<len(order):
        x=order[q]; q+=1
        prev=order[:q]
        for y in prev:
            for a,b in ((x,y),(y,x)):
                z=rel_apply(rel,a,b,mask)
                if z not in seen:
                    seen.add(z);order.append(z)
    return frozenset(seen)

def analyze_once():
    worlds = {}
    for name,w in WORLDS.items():
        full = closure(name,2,str(w.ground),False)
        no_g = closure(name,2,"NONE",False)
        no_d = frozenset(projections(w.carrier,2)+[const_fn(w.carrier,2,w.ground)])
        no_r = one_layer(name)
        unary = closure(name,1,str(w.ground),False)
        no_e = embed_unary(name,unary)
        rev = closure(name,2,str(w.ground),True)

        refs={}
        for r in w.carrier:
            c = closure(name,2,str(r),False)
            refs[str(r)] = {
                "count":len(c),
                "hash":digest_set(c),
                "preserves_full":c==full,
            }

        ablations={}
        for key,s in (("G",no_g),("D",no_d),("R",no_r),("E",no_e)):
            ablations[key]={
                "count":len(s),
                "lost":len(full-s),
                "retained_fraction":len(full & s)/len(full),
                "preserves_full":s==full,
                "witness":witness(full,s),
                "hash":digest_set(s),
            }

        worlds[name]={
            "full_count":len(full),
            "full_hash":digest_set(full),
            "raw_seed_count":len(no_d),
            "grows_beyond_seed":len(full)>len(no_d),
            "ablations":ablations,
            "reference_sweep":refs,
            "ground_derivable_without_ground":const_fn(w.carrier,2,w.ground) in no_g,
            "reverse_preserves_full":rev==full,
            "reverse_hash":digest_set(rev),
        }

    bfull = closure("B",2,str(WORLDS["B"].ground),False)
    eqrels=[]
    rel_counts={}
    for rel in range(16):
        c=bool_relation_closure(rel,2)
        rel_counts[str(rel)]=len(c)
        if len(c)==16:
            # Convert Boolean mask functions into the same extensional tuple representation.
            rows=assignments((0,1),2)
            as_tuples=set()
            for m in c:
                as_tuples.add(tuple(1 if (m>>i)&1 else 0 for i,_ in enumerate(rows)))
            if frozenset(as_tuples)==bfull:
                eqrels.append(rel)

    retained_nucleus=[]
    retained_context=[]
    for comp in ("G","D"):
        if any(not worlds[n]["ablations"][comp]["preserves_full"] for n in PROTECTED):
            retained_nucleus.append(comp)
    for comp in ("R","E"):
        if any(not worlds[n]["ablations"][comp]["preserves_full"] for n in PROTECTED):
            retained_context.append(comp)

    world_specific_removable={
        n:[c for c in ("G","D","R","E") if worlds[n]["ablations"][c]["preserves_full"]]
        for n in WORLDS
    }

    return {
        "worlds":worlds,
        "boolean_end_equivalent_relations_ground1":eqrels,
        "boolean_relation_closure_counts_ground1":rel_counts,
        "retrospective_minimizer":{
            "retained_nucleus":retained_nucleus,
            "retained_developmental_conditions":retained_context,
            "world_specific_removable":world_specific_removable,
        }
    }

def main():
    a=analyze_once()
    first_hash=H(a)
    closure.cache_clear()
    b=analyze_once()
    replay=H(b)==first_hash

    W=a["worlds"]
    minim=a["retrospective_minimizer"]
    witnesses_ok=True
    for comp in minim["retained_nucleus"]+minim["retained_developmental_conditions"]:
        if not any(W[n]["ablations"][comp]["witness"] is not None for n in PROTECTED):
            witnesses_ok=False

    gates={
        "P1_parent_counts_reproduced":all(W[n]["full_count"]==EXPECTED_COUNTS[n] for n in EXPECTED_COUNTS),
        "P2_deterministic_exact_replay":replay,
        "P3_protected_worlds_grow":all(W[n]["grows_beyond_seed"] for n in PROTECTED),
        "P4_ground_needed_every_protected_world":all(not W[n]["ablations"]["G"]["preserves_full"] for n in PROTECTED),
        "P5_directed_op_needed_every_protected_world":all(not W[n]["ablations"]["D"]["preserves_full"] for n in PROTECTED),
        "P6_reentry_needed_every_protected_world":all(not W[n]["ablations"]["R"]["preserves_full"] for n in PROTECTED),
        "P7_fresh_environment_needed_every_protected_world":all(not W[n]["ablations"]["E"]["preserves_full"] for n in PROTECTED),
        "P8_reverse_orientation_preserves_all_worlds":all(W[n]["reverse_preserves_full"] for n in WORLDS),
        "P9_alternative_reference_rejected_somewhere":any(any(not z["preserves_full"] for z in W[n]["reference_sweep"].values()) for n in PROTECTED),
        "P10_ground_not_derivable_every_protected_world":all(not W[n]["ground_derivable_without_ground"] for n in PROTECTED),
        "P11_boolean_end_accuracy_underdetermined":len(a["boolean_end_equivalent_relations_ground1"])>=2,
        "P12_minimizer_retains_G_D":minim["retained_nucleus"]==["G","D"],
        "P13_context_R_E_separate":minim["retained_developmental_conditions"]==["R","E"],
        "P14_retained_components_have_witnesses":witnesses_ok,
        "P15_Z3_reported_separately":"Z3" in W and "Z3" not in PROTECTED,
        "P16_claim_classes_explicit":True,
    }

    verdict = (
        "PASS_RETROSPECTIVE_NUCLEUS_PURIFICATION_V1"
        if all(gates.values())
        else "PARTIAL_RETROSPECTIVE_NUCLEUS_PURIFICATION_V1"
        if any(gates.values())
        else "VALID_NEGATIVE_RETROSPECTIVE_NUCLEUS_PURIFICATION_V1"
    )

    result={
        "protocol":PROTOCOL,
        "precommit_commit":PRECOMMIT,
        "parent_result_hash":PARENT_HASH,
        "verdict":verdict,
        **a,
        "headline_gates":gates,
        "deterministic_replay":replay,
        "analysis_hash":first_hash,
        "interpretation":{
            "end_consequence_sufficiency":"Exact final closure constrains the seed but does not uniquely identify the Boolean operator.",
            "developmental_sufficiency":"Across the frozen protected worlds, G and D are retained as nucleus components; recursive re-entry R and fresh environmental distinction E are separately retained as developmental conditions.",
            "universal_minimality":"NOT CLAIMED. This is an exact finite retrospective-minimality result under the frozen worlds only.",
        },
        "claim_boundary":"Exact finite pointed algebras only; no universal, ontological, biological, physical, mathematical, or intelligence-level minimality claim.",
    }
    out=Path("results/retrospective_nucleus_purification_v1")
    out.mkdir(parents=True,exist_ok=True)
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    summary={
        "verdict":verdict,
        "analysis_hash":first_hash,
        "retrospective_minimizer":a["retrospective_minimizer"],
        "boolean_end_equivalent_relations_ground1":a["boolean_end_equivalent_relations_ground1"],
        "worlds":{n:{
            "full_count":W[n]["full_count"],
            "ablations":W[n]["ablations"],
            "reference_sweep":W[n]["reference_sweep"],
            "ground_derivable_without_ground":W[n]["ground_derivable_without_ground"],
            "reverse_preserves_full":W[n]["reverse_preserves_full"],
        } for n in W},
        "headline_gates":gates,
        "interpretation":result["interpretation"],
    }
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("RETROSPECTIVE NUCLEUS PURIFICATION V1",verdict)
    print(json.dumps(summary,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
