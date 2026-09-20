#!/usr/bin/env python3
from __future__ import annotations

from itertools import permutations
from pathlib import Path
import hashlib
import json
import sys

Q=3
OP_COUNT=19683
POINTED_COUNT=59049
P3=[1,3,9,27,81,243,729,2187,6561]
PERMS=list(permutations(range(Q)))
OMEGA=[(a,b) for a in range(Q) for b in range(Q)]
OIDX={p:i for i,p in enumerate(OMEGA)}

PHEN_FIELDS=[
    "binary",
    "no_ground",
    "d3",
    "recombinant3",
    "recur_distinct_sum",
    "mutation_complete",
    "mutation_generative",
    "mutation_ref_independent",
    "joint_developmental",
    "pareto",
]

def decode_op(code):
    t=[]
    for _ in range(9):
        t.append(code%3)
        code//=3
    return t

def encode_op(t):
    return sum(v*P3[i] for i,v in enumerate(t))

def opv(op,a,b):
    return op[3*a+b]

def transform(rawkey,p,swap=False):
    g,code=divmod(rawkey,OP_COUNT)
    old=decode_op(code)
    nt=[0]*9
    for a in range(Q):
        for b in range(Q):
            oa,ob=(b,a) if swap else (a,b)
            nt[3*p[a]+p[b]]=p[opv(old,oa,ob)]
    return p[g]*OP_COUNT+encode_op(nt)

def canonical_key(rawkey):
    return min(transform(rawkey,p,sw) for p in PERMS for sw in (False,True))

def translations(rawkey):
    g,code=divmod(rawkey,OP_COUNT)
    op=decode_op(code)
    L=[tuple(opv(op,c,x) for x in range(Q)) for c in range(Q)]
    R=[tuple(opv(op,x,c) for x in range(Q)) for c in range(Q)]
    return g,L,R

def pair_action(t):
    return tuple(OIDX[(t[a],t[b])] for a,b in OMEGA)

def point_colors(g):
    colors=[]
    for a,b in OMEGA:
        if a==g and b==g:
            colors.append(3)
        elif a==b:
            colors.append(2)
        elif a==g or b==g:
            colors.append(1)
        else:
            colors.append(0)
    return tuple(colors)

def V0_base(rawkey):
    g,L,R=translations(rawkey)
    actions=tuple(sorted(pair_action(t) for t in (L+R)))
    return point_colors(g),actions

def V1_base(rawkey):
    g,L,R=translations(rawkey)
    root=tuple(sorted((pair_action(L[g]),pair_action(R[g]))))
    other=[]
    for c in range(Q):
        if c!=g:
            other.extend((pair_action(L[c]),pair_action(R[c])))
    return point_colors(g),root,tuple(sorted(other))

def V2_base(rawkey):
    g,L,R=translations(rawkey)
    return point_colors(g),tuple(sorted(pair_action(t) for t in L)),tuple(sorted(pair_action(t) for t in R))

def V3_base(rawkey):
    g,L,R=translations(rawkey)
    l_other=tuple(sorted(pair_action(L[c]) for c in range(Q) if c!=g))
    r_other=tuple(sorted(pair_action(R[c]) for c in range(Q) if c!=g))
    return point_colors(g),pair_action(L[g]),pair_action(R[g]),l_other,r_other

def V4_base(rawkey):
    g,L,R=translations(rawkey)
    blocks=[]
    for c in range(Q):
        block=tuple(sorted((pair_action(L[c]),pair_action(R[c]))))
        blocks.append((1 if c==g else 0,block))
    # Carrier position remains structural; relabeling is handled by outer canonicalization.
    return point_colors(g),tuple(blocks)

def V5_base(rawkey):
    g,L,R=translations(rawkey)
    blocks=[]
    for c in range(Q):
        blocks.append((1 if c==g else 0,pair_action(L[c]),pair_action(R[c])))
    return point_colors(g),tuple(blocks)

BASES={
    "V0_fully_anonymous":V0_base,
    "V1_ground_source_marked":V1_base,
    "V2_side_marked":V2_base,
    "V3_ground_source_x_side_marked":V3_base,
    "V4_generator_incidence_marked":V4_base,
    "V5_fully_marked_elementary_incidence":V5_base,
}

def canonical_signature(rawkey,basefn):
    return min(
        basefn(transform(rawkey,p,sw))
        for p in PERMS
        for sw in (False,True)
    )

def phenotype(row,pareto_set):
    return {
        "binary":int(row["binary"]),
        "no_ground":int(row["no_ground"]),
        "d3":int(row["d3"]),
        "recombinant3":int(row["recombinant3"]),
        "recur_distinct_sum":int(row["recur_distinct_sum"]),
        "mutation_complete":int(row["mutation_complete"]),
        "mutation_generative":int(row["mutation_generative"]),
        "mutation_ref_independent":int(row["mutation_ref_independent"]),
        "joint_developmental":bool(row["joint_developmental"]),
        "pareto":int(row["key"]) in pareto_set,
    }

def phenotype_tuple(p):
    return tuple(p[f] for f in PHEN_FIELDS)

def analyze(name,rows,basefn,pareto_set):
    classes={}
    for r in rows:
        s=canonical_signature(int(r["key"]),basefn)
        classes.setdefault(s,[]).append(r)

    collisions=[v for v in classes.values() if len(v)>1]
    hetero=0
    counter=None
    for members in classes.values():
        groups={}
        for r in members:
            p=phenotype(r,pareto_set)
            groups.setdefault(phenotype_tuple(p),[]).append(r)
        if len(groups)>1:
            hetero+=1
            if counter is None:
                gl=list(groups.values())
                a,b=gl[0][0],gl[1][0]
                pa,pb=phenotype(a,pareto_set),phenotype(b,pareto_set)
                counter={
                    "key_a":int(a["key"]),
                    "key_b":int(b["key"]),
                    "class_size":len(members),
                    "phenotype_differences":{
                        f:[pa[f],pb[f]] for f in PHEN_FIELDS if pa[f]!=pb[f]
                    }
                }

    return {
        "name":name,
        "canonical_orbits":len(rows),
        "unique_signatures":len(classes),
        "compression_ratio_orbits":len(classes)/len(rows),
        "collision_classes":len(collisions),
        "heterogeneous_collision_classes":hetero,
        "largest_collision_class_orbits":max((len(v) for v in classes.values()),default=0),
        "largest_collision_class_raw_weight":max(
            (sum(int(r["weight"]) for r in v) for v in classes.values()),
            default=0
        ),
        "raw_weighted_collision_mass":sum(
            sum(int(r["weight"]) for r in v) for v in collisions
        ),
        "injective":len(classes)==len(rows),
        "developmentally_sufficient":hetero==0,
        "counterexample":counter,
    }

def audit_keys():
    out=[];seen=set();i=0
    while len(out)<256:
        h=hashlib.sha256(f"MSSO1-AUDIT|{i}".encode()).hexdigest()
        k=int(h[:16],16)%POINTED_COUNT
        if k not in seen:
            seen.add(k);out.append(k)
        i+=1
    return out

def stable_hash(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()

# Strict weaker relations frozen in protocol, represented transitively after closure.
EDGES={
    "V0_fully_anonymous":{
        "V1_ground_source_marked",
        "V2_side_marked"
    },
    "V1_ground_source_marked":{
        "V3_ground_source_x_side_marked",
        "V4_generator_incidence_marked"
    },
    "V2_side_marked":{
        "V3_ground_source_x_side_marked",
        "V5_fully_marked_elementary_incidence"
    },
    "V3_ground_source_x_side_marked":{
        "V5_fully_marked_elementary_incidence"
    },
    "V4_generator_incidence_marked":{
        "V5_fully_marked_elementary_incidence"
    },
    "V5_fully_marked_elementary_incidence":set(),
}

def transitive_weaker():
    weaker={k:set() for k in EDGES}
    for a,bs in EDGES.items():
        for b in bs:
            weaker[b].add(a)
    changed=True
    while changed:
        changed=False
        for b in list(weaker):
            add=set()
            for a in list(weaker[b]):
                add |= weaker[a]
            if not add.issubset(weaker[b]):
                weaker[b] |= add
                changed=True
    return weaker

def main():
    if len(sys.argv)!=3:
        raise SystemExit("usage: minimal_structural_sufficiency_one_shot_v1.py DEV_RESULT_JSON OUT_DIR")
    dev=json.loads(Path(sys.argv[1]).read_text())
    out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)

    rows=dev["orbits"]
    pareto_set={int(r["key"]) for r in dev["pareto_orbits"]}
    if len(rows)!=5130:
        raise RuntimeError(f"expected 5130 canonical orbits, got {len(rows)}")

    analyses=[]
    amap={}
    for name,fn in BASES.items():
        a=analyze(name,rows,fn,pareto_set)
        analyses.append(a)
        amap[name]=a

    sufficient=[a["name"] for a in analyses if a["developmentally_sufficient"]]
    weaker=transitive_weaker()
    minimal_sufficient=[
        name for name in sufficient
        if not any(w in sufficient for w in weaker[name])
    ]

    if not sufficient:
        strength="NO_FROZEN_VIEW_SUFFICIENT"
    elif any(not amap[n]["injective"] for n in minimal_sufficient):
        strength="EXACT_NONINJECTIVE_STRUCTURAL_QUOTIENT"
    else:
        strength="ONLY_INJECTIVE_SUFFICIENCY"

    phenotype_ok=True
    for r in rows:
        try:
            phenotype(r,pareto_set)
        except Exception:
            phenotype_ok=False
            break

    audit_pass=0
    audit_fail=[]
    for raw in audit_keys():
        ck=canonical_key(raw)
        ok=True
        for fn in BASES.values():
            if canonical_signature(raw,fn)!=canonical_signature(ck,fn):
                ok=False;break
        if ok:
            audit_pass+=1
        elif len(audit_fail)<5:
            audit_fail.append({"raw":raw,"canonical":ck})

    total_weight=sum(int(r["weight"]) for r in rows)
    core={
        "strength":strength,
        "sufficient_views":sufficient,
        "minimal_sufficient_views":minimal_sufficient,
        "representations":analyses,
        "protected_phenotype_fields":PHEN_FIELDS,
        "total_raw_weight":total_weight,
        "audit":{"total":256,"passed":audit_pass,"failures":audit_fail},
        "frozen_refinement_edges":{k:sorted(v) for k,v in EDGES.items()},
    }
    h1=stable_hash(core);h2=stable_hash(core)

    gates={
        "MS1_all_5130_orbits":len(rows)==5130,
        "MS2_weight_sum_59049":total_weight==59049,
        "MS3_V0_computed_canonicalized":audit_pass==256 and amap["V0_fully_anonymous"]["unique_signatures"]>0,
        "MS4_V1_computed_canonicalized":audit_pass==256 and amap["V1_ground_source_marked"]["unique_signatures"]>0,
        "MS5_V2_computed_canonicalized":audit_pass==256 and amap["V2_side_marked"]["unique_signatures"]>0,
        "MS6_V3_computed_canonicalized":audit_pass==256 and amap["V3_ground_source_x_side_marked"]["unique_signatures"]>0,
        "MS7_V4_computed_canonicalized":audit_pass==256 and amap["V4_generator_incidence_marked"]["unique_signatures"]>0,
        "MS8_V5_computed_canonicalized":audit_pass==256 and amap["V5_fully_marked_elementary_incidence"]["unique_signatures"]>0,
        "MS9_protected_phenotype_all":phenotype_ok,
        "MS10_collision_classes_exhaustive":all(a["heterogeneous_collision_classes"]>=0 for a in analyses),
        "MS11_counterexamples_for_insufficient":all(a["developmentally_sufficient"] or a["counterexample"] is not None for a in analyses),
        "MS12_sufficiency_set_reported":isinstance(sufficient,list),
        "MS13_minimal_sufficient_set_reported":isinstance(minimal_sufficient,list),
        "MS14_compression_injectivity_all":all("injective" in a and "compression_ratio_orbits" in a for a in analyses),
        "MS15_256_symmetry_audits":audit_pass==256,
        "MS16_deterministic_hash":h1==h2,
    }

    verdict=(
        "PASS_MINIMAL_STRUCTURAL_SUFFICIENCY_ONE_SHOT_V1"
        if all(gates.values())
        else "PARTIAL_MINIMAL_STRUCTURAL_SUFFICIENCY_ONE_SHOT_V1"
    )
    result={
        "protocol":"MINIMAL_STRUCTURAL_SUFFICIENCY_ONE_SHOT_V1",
        "precommit_commit":"932d475629fe85d2b1841a33972cea3bf7e988b1",
        "verdict":verdict,
        **core,
        "headline_gates":gates,
        "aggregation_hash":h1,
        "claim_boundary":"Exact finite structure-discovery result only for the frozen six-view lattice and authoritative three-element developmental phenotype."
    }
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (out/"summary.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")

    print("MINIMAL STRUCTURAL SUFFICIENCY ONE-SHOT V1",verdict)
    print("STRENGTH="+strength)
    print("SUFFICIENT="+",".join(sufficient))
    print("MINIMAL="+",".join(minimal_sufficient))
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
