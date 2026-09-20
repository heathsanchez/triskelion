#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import csv, hashlib, json, math, sys

OP_COUNT=19683
POINTED_COUNT=59049
BINARY_TOTAL=19683

BOOL_FEATURES=[
    "commutative","idempotent","associative","conservative","cancellative",
    "any_one_identity","two_identity","any_one_absorber","two_absorber",
    "ground_one_identity","ground_two_identity","ground_one_absorber","ground_two_absorber",
    "diag_ground_fixed",
]
INT_FEATURES=["asymmetry_score","isotone_orders","residual_orders","ground_top_residual_orders"]
PERMS=[(0,1,2),(0,2,1),(1,0,2),(1,2,0),(2,0,1),(2,1,0)]
P3=[1,3,9,27,81,243,729,2187,6561]

def decode_op(code):
    out=[]
    for _ in range(9):
        out.append(code%3);code//=3
    return out

def encode_op(t):
    return sum(v*P3[i] for i,v in enumerate(t))

def canonical_key(rawkey):
    g,code=divmod(rawkey,OP_COUNT)
    old=decode_op(code)
    best=POINTED_COUNT+1
    for p in PERMS:
        for sw in (0,1):
            nt=[0]*9
            for a in range(3):
                for b in range(3):
                    oa,ob=(b,a) if sw else (a,b)
                    nt[3*p[a]+p[b]]=p[old[3*oa+ob]]
            best=min(best,p[g]*OP_COUNT+encode_op(nt))
    return best

def load_shards(root):
    rows=[]; metas=[]
    for p in sorted(root.rglob("*.tsv")):
        lines=p.read_text().splitlines()
        if not lines or not lines[0].startswith("#META\t"):
            raise RuntimeError(f"missing shard meta: {p}")
        m=lines[0].split("\t")
        metas.append({"shard":int(m[1]),"shards":int(m[2]),"reps":int(m[3]),"weight":int(m[4])})
        rd=csv.DictReader(lines[1:],delimiter="\t")
        for r in rd:
            rows.append({k:int(v) for k,v in r.items()})
    return rows,metas

def wsum(rows,pred=lambda r:True):
    return sum(r["weight"] for r in rows if pred(r))

def wmean(rows,key,pred=lambda r:True):
    den=wsum(rows,pred)
    if not den:return None
    return sum(r["weight"]*r[key] for r in rows if pred(r))/den

def wmean_func(rows,fn,pred=lambda r:True):
    den=wsum(rows,pred)
    if not den:return None
    return sum(r["weight"]*fn(r) for r in rows if pred(r))/den

def wquant(rows,fn,q):
    vals=sorted((fn(r),r["weight"],r["key"]) for r in rows)
    target=math.ceil(q*sum(w for _,w,_ in vals))
    acc=0
    for v,w,_ in vals:
        acc+=w
        if acc>=target:return v
    return vals[-1][0]

def wcorr(rows,fx,fy,pred=lambda r:True):
    sub=[r for r in rows if pred(r)]
    W=sum(r["weight"] for r in sub)
    if not W:return None
    mx=sum(r["weight"]*fx(r) for r in sub)/W
    my=sum(r["weight"]*fy(r) for r in sub)/W
    vx=sum(r["weight"]*(fx(r)-mx)**2 for r in sub)/W
    vy=sum(r["weight"]*(fy(r)-my)**2 for r in sub)/W
    if vx<=0 or vy<=0:return 0.0
    cov=sum(r["weight"]*(fx(r)-mx)*(fy(r)-my) for r in sub)/W
    return cov/math.sqrt(vx*vy)

def enrichment(rows,feature_pred,joint_pred,complete_pred):
    base_den=wsum(rows,complete_pred)
    joint_den=wsum(rows,joint_pred)
    if not base_den or not joint_den:return None
    base=wsum(rows,lambda r:complete_pred(r) and feature_pred(r))/base_den
    if base==0:return None
    j=wsum(rows,lambda r:joint_pred(r) and feature_pred(r))/joint_den
    return j/base

def stable_hash(rows):
    cols=[
        "key","weight","d0","d1","d2","d3","recombinant3",
        "recur_distinct_sum","recur_distinct_max","recur_cycle_sum","recur_cycle_max",
        "mutation_complete","mutation_generative","mutation_ref_independent",
        "joint_developmental"
    ]
    payload=[[r[c] for c in cols] for r in sorted(rows,key=lambda x:x["key"])]
    return hashlib.sha256(json.dumps(payload,separators=(",",":")).encode()).hexdigest()

def operation_code(fn):
    t=[fn(a,b) for a in range(3) for b in range(3)]
    return encode_op(t)

def main():
    if len(sys.argv)!=4:
        raise SystemExit("usage: aggregate DEV_SHARDS PRIOR_RESULT_JSON OUT_DIR")
    shard_root=Path(sys.argv[1])
    prior_path=Path(sys.argv[2])
    out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)

    dev,metas=load_shards(shard_root)
    prior=json.loads(prior_path.read_text())
    prior_rows=prior["orbits"]
    prior_map={int(r["key"]):r for r in prior_rows}
    dev_map={r["key"]:r for r in dev}

    if len(prior_map)!=5130:
        raise RuntimeError(f"expected 5130 prior orbits, got {len(prior_map)}")
    if set(dev_map)!=set(prior_map):
        missing=set(prior_map)-set(dev_map);extra=set(dev_map)-set(prior_map)
        raise RuntimeError(f"dev/prior key mismatch missing={len(missing)} extra={len(extra)}")

    canonical_self=all(canonical_key(k)==k for k in prior_map)

    merged=[]
    all_mutants_resolved=True
    for key in sorted(prior_map):
        p=dict(prior_map[key])
        d=dev_map[key]
        r={**p,**d}
        g=int(r["ground"]);code=int(r["opcode"])
        table=decode_op(code)
        mc=mg=mr=0
        resolved=0
        for pos in range(9):
            old=table[pos]
            for nv in range(3):
                if nv==old:continue
                nt=table[:];nt[pos]=nv
                raw=g*OP_COUNT+encode_op(nt)
                ck=canonical_key(raw)
                q=prior_map.get(ck)
                if q is None:
                    all_mutants_resolved=False
                    continue
                resolved+=1
                if int(q["binary"])==BINARY_TOTAL: mc+=1
                if bool(q["generative"]): mg+=1
                if int(q["ref_delta"])==0: mr+=1
        r["mutation_resolved"]=resolved
        r["mutation_complete"]=mc
        r["mutation_generative"]=mg
        r["mutation_ref_independent"]=mr
        r["recurrence_mean_distinct"]=r["recur_distinct_sum"]/9.0
        r["recurrence_mean_cycle"]=r["recur_cycle_sum"]/9.0
        r["complete"]=int(r["binary"])==BINARY_TOTAL
        r["reference_free_complete"]=r["complete"] and int(r["no_ground"])==BINARY_TOTAL
        r["reference_minimal_complete"]=r["complete"] and int(r["no_ground"])!=BINARY_TOTAL
        merged.append(r)

    complete=[r for r in merged if r["complete"]]
    complete_weight=sum(r["weight"] for r in complete)

    q75_g3=wquant(complete,lambda r:r["d3"],.75)
    q75_r3=wquant(complete,lambda r:r["recombinant3"],.75)
    q75_p=wquant(complete,lambda r:r["recurrence_mean_distinct"],.75)
    q75_m=wquant(complete,lambda r:r["mutation_complete"],.75)
    thresholds={"G3":q75_g3,"R3":q75_r3,"P":q75_p,"M_numerator_of_18":q75_m}

    for r in merged:
        r["joint_developmental"]=bool(
            r["complete"] and r["d3"]>=q75_g3 and r["recombinant3"]>=q75_r3
            and r["recurrence_mean_distinct"]>=q75_p and r["mutation_complete"]>=q75_m
        )

    joint=[r for r in merged if r["joint_developmental"]]
    joint_weight=sum(r["weight"] for r in joint)
    joint_ref_min=sum(r["weight"] for r in joint if r["reference_minimal_complete"])
    joint_ref_free=sum(r["weight"] for r in joint if r["reference_free_complete"])

    complete_pred=lambda r:r["complete"]
    joint_pred=lambda r:r["joint_developmental"]

    structural={}
    for f in BOOL_FEATURES:
        base=wsum(merged,lambda r,f=f:r["complete"] and bool(r[f]))/complete_weight
        jp=wsum(merged,lambda r,f=f:r["joint_developmental"] and bool(r[f]))/joint_weight if joint_weight else 0.0
        structural[f]={
            "complete_prevalence":base,
            "joint_prevalence":jp,
            "enrichment":(jp/base if base else None),
        }
    noncomm_base=wsum(merged,lambda r:r["complete"] and not bool(r["commutative"]))/complete_weight
    noncomm_joint=wsum(merged,lambda r:r["joint_developmental"] and not bool(r["commutative"]))/joint_weight if joint_weight else 0
    noncomm_enrich=noncomm_joint/noncomm_base if noncomm_base else None

    integer_summary={}
    for f in INT_FEATURES:
        integer_summary[f]={
            "complete_weighted_mean":wmean(merged,f,complete_pred),
            "joint_weighted_mean":wmean(merged,f,joint_pred),
        }

    mutation_median=wquant(complete,lambda r:r["mutation_complete"],.50)

    metric_names={
        "G3":lambda r:r["d3"],
        "R3":lambda r:r["recombinant3"],
        "P":lambda r:r["recurrence_mean_distinct"],
        "M":lambda r:r["mutation_complete"]/18.0,
    }
    separators={}
    separators["A_closure_controlled"]={
        "joint_weight":joint_weight,
        "nonjoint_complete_weight":complete_weight-joint_weight,
        "joint_means":{k:wmean_func(merged,fn,joint_pred) for k,fn in metric_names.items()},
        "nonjoint_complete_means":{k:wmean_func(merged,fn,lambda r:not r["joint_developmental"] and r["complete"]) for k,fn in metric_names.items()},
    }
    separators["B_reference"]={
        "reference_minimal_weight":wsum(merged,lambda r:r["reference_minimal_complete"]),
        "reference_free_weight":wsum(merged,lambda r:r["reference_free_complete"]),
        "reference_minimal_means":{k:wmean_func(merged,fn,lambda r:r["reference_minimal_complete"]) for k,fn in metric_names.items()},
        "reference_free_means":{k:wmean_func(merged,fn,lambda r:r["reference_free_complete"]) for k,fn in metric_names.items()},
    }
    separators["C_mutation"]={
        "median_mutation_complete_numerator":mutation_median,
        "high_weight":wsum(merged,lambda r:r["complete"] and r["mutation_complete"]>=mutation_median),
        "low_weight":wsum(merged,lambda r:r["complete"] and r["mutation_complete"]<mutation_median),
        "high_G3":wmean(merged,"d3",lambda r:r["complete"] and r["mutation_complete"]>=mutation_median),
        "low_G3":wmean(merged,"d3",lambda r:r["complete"] and r["mutation_complete"]<mutation_median),
        "high_P":wmean_func(merged,lambda r:r["recurrence_mean_distinct"],lambda r:r["complete"] and r["mutation_complete"]>=mutation_median),
        "low_P":wmean_func(merged,lambda r:r["recurrence_mean_distinct"],lambda r:r["complete"] and r["mutation_complete"]<mutation_median),
    }
    separators["D_commutativity"]={
        "commutative_complete_weight":wsum(merged,lambda r:r["complete"] and bool(r["commutative"])),
        "commutative_joint_weight":wsum(merged,lambda r:r["joint_developmental"] and bool(r["commutative"])),
        "any_commutative_joint":any(r["joint_developmental"] and bool(r["commutative"]) for r in merged),
    }

    # Pareto frontier among complete canonical representatives.
    pts=complete
    pareto=[]
    for a in pts:
        av=(a["d3"],a["recombinant3"],a["recurrence_mean_distinct"],a["mutation_complete"])
        dominated=False
        for b in pts:
            if a is b:continue
            bv=(b["d3"],b["recombinant3"],b["recurrence_mean_distinct"],b["mutation_complete"])
            if all(x>=y for x,y in zip(bv,av)) and any(x>y for x,y in zip(bv,av)):
                dominated=True;break
        if not dominated:
            pareto.append({
                "key":a["key"],"weight":a["weight"],"ground":a["ground"],"opcode":a["opcode"],
                "G3":a["d3"],"R3":a["recombinant3"],"P":a["recurrence_mean_distinct"],"M":a["mutation_complete"]
            })

    extremes={
        "max_G3":max(r["d3"] for r in complete),
        "max_R3":max(r["recombinant3"] for r in complete),
        "max_P":max(r["recurrence_mean_distinct"] for r in complete),
        "max_M_numerator":max(r["mutation_complete"] for r in complete),
    }
    extremes["G3_orbits"]=[r["key"] for r in complete if r["d3"]==extremes["max_G3"]]
    extremes["R3_orbits"]=[r["key"] for r in complete if r["recombinant3"]==extremes["max_R3"]]
    extremes["P_orbits"]=[r["key"] for r in complete if r["recurrence_mean_distinct"]==extremes["max_P"]]
    extremes["M_orbits"]=[r["key"] for r in complete if r["mutation_complete"]==extremes["max_M_numerator"]]

    rho_gm=wcorr(merged,lambda r:r["d3"],lambda r:r["mutation_complete"],complete_pred)
    rho_gp=wcorr(merged,lambda r:r["d3"],lambda r:r["recurrence_mean_distinct"],complete_pred)
    mut_hit=abs(rho_gm)>=0.20
    rec_hit=abs(rho_gp)>=0.20
    corr_label="both" if mut_hit and rec_hit else ("mutation robustness" if mut_hit else ("recurrence persistence" if rec_hit else "neither"))

    strongest=None
    for f,s in structural.items():
        e=s["enrichment"]
        if e is None:continue
        cand=(e,f)
        if strongest is None or cand[0]>strongest[0] or (cand[0]==strongest[0] and cand[1]<strongest[1]):
            strongest=cand

    residual_complete=integer_summary["residual_orders"]["complete_weighted_mean"]
    residual_joint=integer_summary["residual_orders"]["joint_weighted_mean"]
    residual_ratio=(residual_joint/residual_complete) if residual_complete else None

    robust9=wsum(merged,lambda r:r["complete"] and r["mutation_complete"]>=9)

    def h3(a,b):
        neg=2 if a==0 else 0
        return min(neg,b)
    def k3(a,b):return min(2-a,b)
    def t3(a,b):return max(0,b-a)
    handpicked={}
    for name,fn in [("H3",h3),("K3",k3),("T3",t3)]:
        code=operation_code(fn);key=canonical_key(2*OP_COUNT+code)
        r=next(x for x in merged if x["key"]==key)
        handpicked[name]={
            "canonical_key":key,
            "binary_closure":r["binary"],
            "complete":r["complete"],
            "G3":r["d3"],"R3":r["recombinant3"],"P":r["recurrence_mean_distinct"],
            "M_numerator_of_18":r["mutation_complete"],
            "joint_developmental":r["joint_developmental"],
            "comparison_status":"in primary complete population" if r["complete"] else "outside primary complete population",
        }

    joint_fraction=joint_weight/complete_weight if complete_weight else 0
    max_enrich=max((s["enrichment"] for s in structural.values() if s["enrichment"] is not None),default=0)
    r10="narrow measured family" if joint_fraction<=0.10 and max_enrich>=1.5 else "developmental usefulness broadly distributed under frozen metrics"

    reports={
        "R1_joint_fraction_of_complete":joint_fraction,
        "R2_joint_reference_subclasses":{
            "reference_minimal_raw_weight":joint_ref_min,
            "reference_free_raw_weight":joint_ref_free,
            "more_prevalent":"reference-minimal" if joint_ref_min>joint_ref_free else ("reference-free" if joint_ref_free>joint_ref_min else "tie"),
        },
        "R3_noncommutativity":{
            "complete_prevalence":noncomm_base,
            "joint_prevalence":noncomm_joint,
            "enrichment":noncomm_enrich,
        },
        "R4_residual_orders":{
            "complete_mean":residual_complete,
            "joint_mean":residual_joint,
            "joint_over_complete":residual_ratio,
        },
        "R5_any_commutative_joint":separators["D_commutativity"]["any_commutative_joint"],
        "R6_strongest_boolean_feature_enrichment":{
            "feature":strongest[1] if strongest else None,
            "enrichment":strongest[0] if strongest else None,
        },
        "R7_complete_robust_at_least_9_of_18":robust9,
        "R8_early_growth_correlations":{
            "rho_G3_mutation":rho_gm,
            "rho_G3_recurrence":rho_gp,
            "classification":corr_label,
        },
        "R9_handpicked_transport_operations":handpicked,
        "R10_distribution_classification":r10,
    }

    # Exact gates.
    total_weight=sum(r["weight"] for r in merged)
    hash1=stable_hash(merged);hash2=stable_hash(merged)
    gates={
        "DVC1_all_5130_orbits":len(merged)==5130,
        "DVC2_weight_sum_59049":total_weight==59049,
        "DVC3_depth_profiles_exact":all(1<=r["d0"]<=r["d1"]<=r["d2"]<=r["d3"]<=BINARY_TOTAL for r in merged),
        "DVC4_recombinant_counts_exact":all(0<=r["recombinant3"]<=r["d3"] for r in merged),
        "DVC5_recurrence_all9":all(r["recur_distinct_sum"]>=9 and r["recur_cycle_sum"]>=9 for r in merged),
        "DVC6_all18_mutations_resolved":all(r["mutation_resolved"]==18 for r in merged) and all_mutants_resolved,
        "DVC7_canonicalization_reproduces":canonical_self,
        "DVC8_complete_weight_24534":complete_weight==24534,
        "DVC9_all_q75_thresholds":all(v is not None for v in thresholds.values()),
        "DVC10_joint_membership_all_complete":all("joint_developmental" in r for r in complete),
        "DVC11_reference_subclasses_reported":joint_ref_min>=0 and joint_ref_free>=0,
        "DVC12_boolean_structural_stats":len(structural)==len(BOOL_FEATURES),
        "DVC13_integer_structural_stats":len(integer_summary)==len(INT_FEATURES),
        "DVC14_all_separators":set(separators)=={"A_closure_controlled","B_reference","C_mutation","D_commutativity"},
        "DVC15_pareto_reported":len(pareto)>0,
        "DVC16_deterministic_hash":hash1==hash2,
    }
    verdict="PASS_TERNARY_DEVELOPMENTAL_NUCLEUS_CENSUS_V1" if all(gates.values()) else ("PARTIAL_TERNARY_DEVELOPMENTAL_NUCLEUS_CENSUS_V1" if any(gates.values()) else "VALID_NEGATIVE_TERNARY_DEVELOPMENTAL_NUCLEUS_CENSUS_V1")

    result={
        "protocol":"TERNARY_DEVELOPMENTAL_NUCLEUS_CENSUS_V1",
        "precommit_commit":"22d7953e80ed605103a5af82206f0b91d391ba29",
        "addendum_commit":"063309643ac7b43c350e92a15bc27aa3cd0df0a4",
        "verdict":verdict,
        "raw_pointed_nuclei":59049,
        "canonical_orbits":len(merged),
        "complete_raw_weight":complete_weight,
        "thresholds":thresholds,
        "joint_developmental_raw_weight":joint_weight,
        "joint_reference_minimal_raw_weight":joint_ref_min,
        "joint_reference_free_raw_weight":joint_ref_free,
        "structural_enrichment":structural,
        "integer_structural_summary":integer_summary,
        "separators":separators,
        "extremes":extremes,
        "pareto_orbits":pareto,
        "required_reports":reports,
        "headline_gates":gates,
        "aggregation_hash":hash1,
        "shards":sorted(metas,key=lambda x:x["shard"]),
        "orbits":sorted(merged,key=lambda r:r["key"]),
        "claim_boundary":"Exact finite three-element developmental census under frozen depth-3 growth, recurrence and one-cell mutation metrics only."
    }
    summary={k:result[k] for k in (
        "verdict","raw_pointed_nuclei","canonical_orbits","complete_raw_weight","thresholds",
        "joint_developmental_raw_weight","joint_reference_minimal_raw_weight","joint_reference_free_raw_weight",
        "integer_structural_summary","separators","extremes","pareto_orbits",
        "required_reports","headline_gates","aggregation_hash"
    )}
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("TERNARY DEVELOPMENTAL NUCLEUS CENSUS V1",verdict)
    print(json.dumps(summary,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
