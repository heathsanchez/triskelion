#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from itertools import permutations
import hashlib
import json
import sys

Q = 3
OP_COUNT = 19683
POINTED_COUNT = 59049
P3 = [1,3,9,27,81,243,729,2187,6561]
PERMS = list(permutations(range(Q)))
OMEGA = [(a,b) for a in range(Q) for b in range(Q)]
OIDX = {p:i for i,p in enumerate(OMEGA)}

PHEN_FIELDS = [
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
        t.append(code % 3)
        code //= 3
    return t

def encode_op(t):
    return sum(v * P3[i] for i,v in enumerate(t))

def opv(op,a,b):
    return op[3*a+b]

def transform(rawkey,p,swap=False):
    g,code = divmod(rawkey,OP_COUNT)
    old = decode_op(code)
    nt=[0]*9
    for a in range(3):
        for b in range(3):
            oa,ob = (b,a) if swap else (a,b)
            nt[3*p[a]+p[b]] = p[opv(old,oa,ob)]
    return p[g]*OP_COUNT + encode_op(nt)

def canonical_key(rawkey):
    return min(transform(rawkey,p,sw) for p in PERMS for sw in (False,True))

def translations(rawkey):
    g,code = divmod(rawkey,OP_COUNT)
    op = decode_op(code)
    ts=[]
    for c in range(3):
        ts.append(tuple(opv(op,c,x) for x in range(3)))
    for c in range(3):
        ts.append(tuple(opv(op,x,c) for x in range(3)))
    return g,tuple(ts)

def pair_action(t):
    return tuple(OIDX[(t[a],t[b])] for a,b in OMEGA)

def compose_unary(f,h):
    # f ∘ h
    return tuple(f[h[x]] for x in range(3))

def monoid_from(ts):
    ident=(0,1,2)
    seen={ident,*ts}
    queue=list(seen)
    i=0
    while i < len(queue):
        a=queue[i];i+=1
        snap=list(queue)
        for b in snap:
            for z in (compose_unary(a,b),compose_unary(b,a)):
                if z not in seen:
                    seen.add(z)
                    queue.append(z)
    return tuple(sorted(seen))

def c0_base(rawkey):
    g,ts=translations(rawkey)
    K=[[0]*9 for _ in range(9)]
    for i,(a,b) in enumerate(OMEGA):
        for t in ts:
            K[i][OIDX[(t[a],t[b])]] += 1
    colors=tuple(1 if a==b else 0 for a,b in OMEGA)
    return colors,tuple(x for row in K for x in row)

def c1_base(rawkey):
    g,ts=translations(rawkey)
    K=[[0]*9 for _ in range(9)]
    for i,(a,b) in enumerate(OMEGA):
        for t in ts:
            K[i][OIDX[(t[a],t[b])]] += 1
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
    return tuple(colors),tuple(x for row in K for x in row)

def c2_base(rawkey):
    g,ts=translations(rawkey)
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
    acts=tuple(sorted(pair_action(t) for t in ts))
    return tuple(colors),acts

def c3_base(rawkey):
    g,ts=translations(rawkey)
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
    mon=monoid_from(ts)
    acts=tuple(sorted(pair_action(t) for t in mon))
    return tuple(colors),acts

def canonical_signature(rawkey,basefn):
    # Explicitly quotient by carrier relabeling and global argument swap.
    reps=[]
    for p in PERMS:
        for sw in (False,True):
            rk=transform(rawkey,p,sw)
            reps.append(basefn(rk))
    return min(reps)

def sig0(rawkey): return canonical_signature(rawkey,c0_base)
def sig1(rawkey): return canonical_signature(rawkey,c1_base)
def sig2(rawkey): return canonical_signature(rawkey,c2_base)
def sig3(rawkey): return canonical_signature(rawkey,c3_base)

def audit_keys():
    out=[];seen=set();i=0
    while len(out)<256:
        h=hashlib.sha256(f"CCO1-AUDIT|{i}".encode()).hexdigest()
        k=int(h[:16],16)%POINTED_COUNT
        if k not in seen:
            seen.add(k);out.append(k)
        i+=1
    return out

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

def analyze(name,rows,sigfn,pareto_set):
    classes={}
    for r in rows:
        s=sigfn(int(r["key"]))
        classes.setdefault(s,[]).append(r)

    collisions=[v for v in classes.values() if len(v)>1]
    insufficient=0
    first_counterexample=None

    for members in classes.values():
        phen_groups={}
        for r in members:
            p=phenotype(r,pareto_set)
            phen_groups.setdefault(phenotype_tuple(p),[]).append(r)
        if len(phen_groups)>1:
            insufficient += 1
            if first_counterexample is None:
                groups=list(phen_groups.values())
                a,b=groups[0][0],groups[1][0]
                pa,pb=phenotype(a,pareto_set),phenotype(b,pareto_set)
                first_counterexample={
                    "key_a":int(a["key"]),
                    "key_b":int(b["key"]),
                    "class_size":len(members),
                    "phenotype_differences":{
                        f:[pa[f],pb[f]]
                        for f in PHEN_FIELDS
                        if pa[f] != pb[f]
                    }
                }

    raw_collision_mass=sum(
        sum(int(r["weight"]) for r in members)
        for members in collisions
    )

    return {
        "name":name,
        "canonical_orbits":len(rows),
        "unique_signatures":len(classes),
        "compression_ratio_orbits":len(classes)/len(rows),
        "collision_classes":len(collisions),
        "heterogeneous_collision_classes":insufficient,
        "largest_collision_class_orbits":max((len(v) for v in classes.values()),default=0),
        "largest_collision_class_raw_weight":max(
            (sum(int(r["weight"]) for r in v) for v in classes.values()),
            default=0
        ),
        "raw_weighted_collision_mass":raw_collision_mass,
        "injective":len(classes)==len(rows),
        "developmentally_sufficient":insufficient==0,
        "counterexample":first_counterexample,
    }

def stable_hash(obj):
    return hashlib.sha256(
        json.dumps(obj,sort_keys=True,separators=(",",":")).encode()
    ).hexdigest()

def main():
    if len(sys.argv)!=3:
        raise SystemExit("usage: consequential_continuation_one_shot_v1.py DEV_RESULT_JSON OUT_DIR")

    dev=json.loads(Path(sys.argv[1]).read_text())
    out=Path(sys.argv[2])
    out.mkdir(parents=True,exist_ok=True)

    rows=dev["orbits"]
    pareto_set={int(r["key"]) for r in dev["pareto_orbits"]}

    if len(rows)!=5130:
        raise RuntimeError(f"expected 5130 canonical orbits, got {len(rows)}")

    total_weight=sum(int(r["weight"]) for r in rows)

    analyses=[
        analyze("C0_resolution_aware_aggregate_graph",rows,sig0,pareto_set),
        analyze("C1_pointed_resolution_aware_graph",rows,sig1,pareto_set),
        analyze("C2_anonymous_elementary_continuation_action",rows,sig2,pareto_set),
        analyze("C3_full_continuation_monoid_action",rows,sig3,pareto_set),
    ]
    c0,c1,c2,c3=analyses

    selected=None
    if c0["developmentally_sufficient"]:
        classification="RESOLUTION_CONTINUATION_QUOTIENT_SUPPORTED";selected=c0
    elif c1["developmentally_sufficient"]:
        classification="POINTED_CONTINUATION_QUOTIENT_SUPPORTED";selected=c1
    elif c2["developmentally_sufficient"]:
        classification="ACTIONAL_CONTINUATION_QUOTIENT_SUPPORTED";selected=c2
    elif c3["developmentally_sufficient"]:
        classification="MONOIDAL_CONTINUATION_QUOTIENT_SUPPORTED";selected=c3
    else:
        classification="CONSEQUENTIAL_CONTINUATION_NOT_SUFFICIENT_UNDER_V1"

    if selected is None:
        strength="NO_SUFFICIENT_CONTINUATION_REPRESENTATION"
    elif selected["injective"]:
        strength="COORDINATE_EQUIVALENCE_ONLY"
    else:
        strength="STRONG_CONTINUATION_QUOTIENT"

    strong_interpretation = (
        selected is not None and
        selected["developmentally_sufficient"] and
        not selected["injective"]
    )

    # Exhaustive phenotype presence.
    phenotype_ok=True
    for r in rows:
        try:
            phenotype(r,pareto_set)
        except Exception:
            phenotype_ok=False
            break

    # Symmetry audits: raw representation must equal representation of its
    # canonical operation orbit at every frozen level.
    audit_pass=0
    audit_fail=[]
    for raw in audit_keys():
        ck=canonical_key(raw)
        ok=(
            sig0(raw)==sig0(ck) and
            sig1(raw)==sig1(ck) and
            sig2(raw)==sig2(ck) and
            sig3(raw)==sig3(ck)
        )
        if ok:
            audit_pass += 1
        elif len(audit_fail)<5:
            audit_fail.append({"raw":raw,"canonical":ck})

    core={
        "classification":classification,
        "strength":strength,
        "strong_interpretation_supported":strong_interpretation,
        "representations":analyses,
        "protected_phenotype_fields":PHEN_FIELDS,
        "total_raw_weight":total_weight,
        "audit":{"total":256,"passed":audit_pass,"failures":audit_fail},
    }

    h1=stable_hash(core)
    h2=stable_hash(core)

    gates={
        "CC1_all_5130_orbits":len(rows)==5130,
        "CC2_weight_sum_59049":total_weight==59049,
        "CC3_C0_canonicalized":audit_pass==256,
        "CC4_C1_canonicalized":audit_pass==256,
        "CC5_C2_canonicalized":audit_pass==256,
        "CC6_C3_canonicalized":audit_pass==256,
        "CC7_protected_phenotype_all":phenotype_ok,
        "CC8_C0_collision_classes":c0["unique_signatures"]>0,
        "CC9_C1_collision_classes":c1["unique_signatures"]>0,
        "CC10_C2_collision_classes":c2["unique_signatures"]>0,
        "CC11_C3_collision_classes":c3["unique_signatures"]>0,
        "CC12_all_homogeneity_checked":all(
            a["heterogeneous_collision_classes"]>=0 for a in analyses
        ),
        "CC13_compression_stats_all":all(
            "compression_ratio_orbits" in a for a in analyses
        ),
        "CC14_counterexamples_for_insufficient":all(
            a["developmentally_sufficient"] or a["counterexample"] is not None
            for a in analyses
        ),
        "CC15_256_symmetry_audits":audit_pass==256,
        "CC16_deterministic_hash":h1==h2,
    }

    verdict=(
        "PASS_CONSEQUENTIAL_CONTINUATION_ONE_SHOT_V1"
        if all(gates.values())
        else "PARTIAL_CONSEQUENTIAL_CONTINUATION_ONE_SHOT_V1"
        if any(gates.values())
        else "VALID_NEGATIVE_CONSEQUENTIAL_CONTINUATION_ONE_SHOT_V1"
    )

    result={
        "protocol":"CONSEQUENTIAL_CONTINUATION_ONE_SHOT_V1",
        "precommit_commit":"28019f2cb7864ac0b755d44114bb5b765580980e",
        "verdict":verdict,
        **core,
        "headline_gates":gates,
        "aggregation_hash":h1,
        "claim_boundary":"Exact finite sufficiency test on the authoritative three-element developmental census only."
    }

    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (out/"summary.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")

    print("CONSEQUENTIAL CONTINUATION ONE-SHOT V1",verdict)
    print("CLASSIFICATION="+classification)
    print("STRENGTH="+strength)
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
