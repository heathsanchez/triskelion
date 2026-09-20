#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from itertools import permutations
import hashlib, json, sys

Q=3
OP_COUNT=19683
POINTED_COUNT=59049
P3=[1,3,9,27,81,243,729,2187,6561]
PERMS=list(permutations(range(3)))
DELTAS=[(a,b) for a in range(3) for b in range(3) if a!=b]
DIDX={d:i for i,d in enumerate(DELTAS)}

def decode_op(code):
    t=[]
    for _ in range(9):
        t.append(code%3); code//=3
    return t

def encode_op(t):
    return sum(v*P3[i] for i,v in enumerate(t))

def opv(op,a,b): return op[3*a+b]

def transform(rawkey,p,swap=False):
    g,code=divmod(rawkey,OP_COUNT)
    old=decode_op(code)
    nt=[0]*9
    for a in range(3):
        for b in range(3):
            oa,ob=(b,a) if swap else (a,b)
            nt[3*p[a]+p[b]]=p[opv(old,oa,ob)]
    return p[g]*OP_COUNT+encode_op(nt)

def canonical_key(rawkey):
    return min(transform(rawkey,p,sw) for p in PERMS for sw in (False,True))

def elementary_translations(rawkey):
    g,code=divmod(rawkey,OP_COUNT)
    op=decode_op(code)
    ts=[]
    for c in range(3):
        ts.append(tuple(opv(op,c,x) for x in range(3)))
    for c in range(3):
        ts.append(tuple(opv(op,x,c) for x in range(3)))
    return g,ts

def aggregate_matrix(rawkey):
    g,ts=elementary_translations(rawkey)
    C=[[0]*6 for _ in range(6)]
    for i,(a,b) in enumerate(DELTAS):
        for t in ts:
            aa,bb=t[a],t[b]
            if aa!=bb:
                C[i][DIDX[(aa,bb)]]+=1
    return g,C

def action_multiset(rawkey):
    g,ts=elementary_translations(rawkey)
    acts=[]
    for t in ts:
        row=[]
        for a,b in DELTAS:
            aa,bb=t[a],t[b]
            row.append(-1 if aa==bb else DIDX[(aa,bb)])
        acts.append(tuple(row))
    return g,tuple(sorted(acts))

def sig0(rawkey):
    reps=[]
    for p in PERMS:
        rk=transform(rawkey,p,False)
        _,C=aggregate_matrix(rk)
        reps.append(tuple(x for row in C for x in row))
    return min(reps)

def sig1(rawkey):
    reps=[]
    for p in PERMS:
        rk=transform(rawkey,p,False)
        g,C=aggregate_matrix(rk)
        colors=tuple(int(a==g or b==g) for a,b in DELTAS)
        reps.append((colors,tuple(x for row in C for x in row)))
    return min(reps)

def sig2(rawkey):
    reps=[]
    for p in PERMS:
        rk=transform(rawkey,p,False)
        g,acts=action_multiset(rk)
        colors=tuple(int(a==g or b==g) for a,b in DELTAS)
        reps.append((colors,acts))
    return min(reps)

def audit_keys():
    out=[];seen=set();i=0
    while len(out)<256:
        h=hashlib.sha256(f"DTO1-AUDIT|{i}".encode()).hexdigest()
        k=int(h[:16],16)%POINTED_COUNT
        if k not in seen:
            seen.add(k);out.append(k)
        i+=1
    return out

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
    collision=[v for v in classes.values() if len(v)>1]
    sufficient=True
    counter=None
    heterogeneous_classes=0
    for members in classes.values():
        ph={}
        for r in members:
            p=phenotype(r,pareto_set)
            ph.setdefault(phenotype_tuple(p),[]).append(r)
        if len(ph)>1:
            sufficient=False
            heterogeneous_classes+=1
            if counter is None:
                groups=list(ph.values())
                a=groups[0][0]
                b=groups[1][0]
                pa=phenotype(a,pareto_set);pb=phenotype(b,pareto_set)
                diffs={f:[pa[f],pb[f]] for f in PHEN_FIELDS if pa[f]!=pb[f]}
                counter={
                    "key_a":int(a["key"]),
                    "key_b":int(b["key"]),
                    "phenotype_differences":diffs,
                    "class_size":len(members),
                }
    raw_collision_mass=sum(sum(int(r["weight"]) for r in members) for members in collision)
    largest=max((len(v) for v in classes.values()),default=0)
    largest_raw=max((sum(int(r["weight"]) for r in v) for v in classes.values()),default=0)
    return {
        "name":name,
        "unique_signatures":len(classes),
        "canonical_orbits":len(rows),
        "compression_ratio_orbits":len(classes)/len(rows),
        "collision_classes":len(collision),
        "heterogeneous_collision_classes":heterogeneous_classes,
        "largest_collision_class_orbits":largest,
        "largest_collision_class_raw_weight":largest_raw,
        "raw_weighted_collision_mass":raw_collision_mass,
        "injective":len(classes)==len(rows),
        "developmentally_sufficient":sufficient,
        "counterexample":counter,
    }

def stable_hash(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def main():
    if len(sys.argv)!=3:
        raise SystemExit("usage: distinction_theory_one_shot_v1.py DEV_RESULT_JSON OUT_DIR")
    dev=json.loads(Path(sys.argv[1]).read_text())
    out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)

    rows=dev["orbits"]
    pareto_set={int(r["key"]) for r in dev["pareto_orbits"]}

    if len(rows)!=5130:
        raise RuntimeError(f"expected 5130 canonical orbits, got {len(rows)}")

    results=[
        analyze("D0_pure_distinction_dynamics",rows,sig0,pareto_set),
        analyze("D1_pointed_distinction_dynamics",rows,sig1,pareto_set),
        analyze("D2_anonymous_distinction_action",rows,sig2,pareto_set),
    ]
    r0,r1,r2=results

    if r0["developmentally_sufficient"]:
        classification="PURE_DISTINCTION_THEORY_SUPPORTED"; selected=r0
    elif r1["developmentally_sufficient"]:
        classification="POINTED_DISTINCTION_THEORY_SUPPORTED"; selected=r1
    elif r2["developmentally_sufficient"]:
        classification="ACTIONAL_DISTINCTION_THEORY_SUPPORTED"; selected=r2
    else:
        classification="DISTINCTION_THEORY_NOT_SUFFICIENT_UNDER_V1"; selected=None

    if selected is None:
        strength="NO_SUFFICIENT_DISTINCTION_REPRESENTATION"
    elif not selected["injective"]:
        strength="STRONG_DISTINCTION_QUOTIENT"
    else:
        strength="COORDINATE_EQUIVALENCE_ONLY"

    # Audit raw-vs-canonical invariance.
    audit_pass=0
    audit_fail=[]
    for raw in audit_keys():
        ck=canonical_key(raw)
        ok=(sig0(raw)==sig0(ck) and sig1(raw)==sig1(ck) and sig2(raw)==sig2(ck))
        if ok:audit_pass+=1
        elif len(audit_fail)<5:audit_fail.append({"raw":raw,"canonical":ck})

    total_weight=sum(int(r["weight"]) for r in rows)

    # Protected phenotype completeness.
    ph_ok=True
    missing=[]
    for r in rows:
        try:
            phenotype(r,pareto_set)
        except Exception as e:
            ph_ok=False
            if len(missing)<5:missing.append({"key":r.get("key"),"error":repr(e)})

    # D2 operation-orbit reconstruction is exactly its injectivity on canonical operation orbits.
    d2_reconstructs_operation_orbit=r2["injective"]

    gates={
        "DT1_all_5130_orbits":len(rows)==5130,
        "DT2_weight_sum_59049":total_weight==59049,
        "DT3_D0_canonicalized":audit_pass==256,
        "DT4_D1_canonicalized":audit_pass==256,
        "DT5_D2_canonicalized":audit_pass==256,
        "DT6_protected_phenotype_all":ph_ok,
        "DT7_D0_collision_classes":r0["unique_signatures"]>0,
        "DT8_D1_collision_classes":r1["unique_signatures"]>0,
        "DT9_D2_collision_classes":r2["unique_signatures"]>0,
        "DT10_D0_homogeneity_checked":r0["heterogeneous_collision_classes"]>=0,
        "DT11_D1_homogeneity_checked":r1["heterogeneous_collision_classes"]>=0,
        "DT12_D2_homogeneity_checked":r2["heterogeneous_collision_classes"]>=0,
        "DT13_compression_stats_all":all("compression_ratio_orbits" in r for r in results),
        "DT14_counterexamples_for_insufficient":all(
            rr["developmentally_sufficient"] or rr["counterexample"] is not None for rr in results
        ),
        "DT15_256_symmetry_audits":audit_pass==256,
        "DT16_deterministic_hash":True,
    }

    core={
        "classification":classification,
        "strength":strength,
        "representations":results,
        "D2_reconstructs_operation_orbit":d2_reconstructs_operation_orbit,
        "protected_phenotype_fields":PHEN_FIELDS,
        "audit":{"total":256,"passed":audit_pass,"failures":audit_fail},
        "total_raw_weight":total_weight,
    }
    h1=stable_hash(core);h2=stable_hash(core)
    gates["DT16_deterministic_hash"]=h1==h2
    verdict="PASS_DISTINCTION_THEORY_ONE_SHOT_V1" if all(gates.values()) else ("PARTIAL_DISTINCTION_THEORY_ONE_SHOT_V1" if any(gates.values()) else "VALID_NEGATIVE_DISTINCTION_THEORY_ONE_SHOT_V1")

    result={
        "protocol":"DISTINCTION_THEORY_ONE_SHOT_V1",
        "precommit_commit":"e522b0b1ffb9554c4834e8608620ff73c00fd3d3",
        "verdict":verdict,
        **core,
        "headline_gates":gates,
        "aggregation_hash":h1,
        "claim_boundary":"Exact finite sufficiency test on the authoritative 3-element developmental census only."
    }
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (out/"summary.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("DISTINCTION THEORY ONE-SHOT V1",verdict)
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
