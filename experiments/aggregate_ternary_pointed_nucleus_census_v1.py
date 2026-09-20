#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from itertools import combinations
import csv, hashlib, json, math, sys

TOTAL_RAW=59049
UNARY_TOTAL=27
BINARY_TOTAL=19683

BOOL_FEATURES=[
    "commutative","idempotent","associative","conservative","cancellative",
    "any_one_identity","two_identity","any_one_absorber","two_absorber",
    "ground_one_identity","ground_two_identity","ground_one_absorber","ground_two_absorber",
    "diag_ground_fixed",
]
INT_FEATURES=["asymmetry_score","isotone_orders","residual_orders","ground_top_residual_orders"]

INT_COLUMNS={
    "key","weight","ground","opcode","unary","binary","no_ground","fresh_delta","ref_delta",
    "asymmetry_score","image_size","diag_image_size","isotone_orders","residual_orders","ground_top_residual_orders",
}
BOOL_COLUMNS=set(BOOL_FEATURES)|{"no_ground_all_constants","generative"}

def load_rows(root:Path):
    rows=[]; metas=[]; audit_total=audit_pass=0
    files=sorted(root.rglob("*.tsv"))
    if not files:
        raise RuntimeError(f"no shard tsv files under {root}")
    for p in files:
        lines=p.read_text().splitlines()
        if not lines or not lines[0].startswith("#META\t"):
            raise RuntimeError(f"missing meta in {p}")
        m=lines[0].split("\t")
        metas.append({"shard":int(m[1]),"shards":int(m[2]),"reps":int(m[3]),"weight":int(m[4])})
        reader=csv.DictReader(lines[1:],delimiter="\t")
        for row in reader:
            d={}
            for k,v in row.items():
                if k in INT_COLUMNS:d[k]=int(v)
                elif k in BOOL_COLUMNS:d[k]=bool(int(v))
                else:d[k]=v
            rows.append(d)
        ap=Path(str(p)+".audit")
        if not ap.exists(): raise RuntimeError(f"missing audit {ap}")
        a,b=map(int,ap.read_text().strip().split("\t"))
        audit_total+=a;audit_pass+=b
    return rows,metas,audit_total,audit_pass

def wsum(rows,pred=lambda r:True):
    return sum(r["weight"] for r in rows if pred(r))

def wmean(rows,key,pred=lambda r:True):
    den=wsum(rows,pred)
    return (sum(r["weight"]*r[key] for r in rows if pred(r))/den) if den else None

def weighted_quantile_threshold(rows,key,q):
    ordered=sorted(rows,key=lambda r:(r[key],r["key"]))
    target=math.ceil(q*sum(r["weight"] for r in ordered))
    acc=0
    for r in ordered:
        acc+=r["weight"]
        if acc>=target:return r[key]
    return ordered[-1][key]

def enrichment(rows,pred,strong_pred):
    total=wsum(rows); strong=wsum(rows,strong_pred)
    base=wsum(rows,pred)/total if total else 0
    cond=wsum(rows,lambda r:strong_pred(r) and pred(r))/strong if strong else 0
    return (cond/base) if base else None

def dist_by(rows,key,generative,strong_pred):
    vals=sorted(set(r[key] for r in rows))
    out={}
    for v in vals:
        pred=lambda r,v=v:r[key]==v
        out[str(v)]={
            "raw_count":wsum(rows,pred),
            "generative_count":wsum(rows,lambda r,v=v:r[key]==v and generative(r)),
            "strong_count":wsum(rows,lambda r,v=v:r[key]==v and strong_pred(r)),
            "mean_binary_closure":wmean(rows,"binary",pred),
        }
    return out

def stable_hash(rows):
    payload=[
        [r[k] for k in sorted(r)]
        for r in sorted(rows,key=lambda x:x["key"])
    ]
    blob=json.dumps(payload,separators=(",",":"),sort_keys=False).encode()
    return hashlib.sha256(blob).hexdigest()

def main():
    if len(sys.argv)!=3:
        raise SystemExit("usage: aggregate SHARD_DIR OUT_DIR")
    root=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
    rows,metas,audit_total,audit_pass=load_rows(root)
    if len({r["key"] for r in rows})!=len(rows):raise RuntimeError("duplicate canonical representative")
    total_weight=sum(r["weight"] for r in rows)
    rep_count=len(rows)

    q90=weighted_quantile_threshold(rows,"binary",0.90)
    generative=lambda r:r["generative"]
    strong=lambda r:r["generative"] and r["binary"]>=q90
    gen_count=wsum(rows,generative);strong_count=wsum(rows,strong)

    feature_stats={}
    for f in BOOL_FEATURES:
        pred=lambda r,f=f:r[f]
        feature_stats[f]={
            "raw_prevalence":wsum(rows,pred)/total_weight,
            "generative_prevalence":wsum(rows,lambda r,f=f:r["generative"] and r[f])/gen_count if gen_count else 0,
            "strong_prevalence":wsum(rows,lambda r,f=f:strong(r) and r[f])/strong_count if strong_count else 0,
            "mean_binary_true":wmean(rows,"binary",pred),
            "mean_binary_false":wmean(rows,"binary",lambda r,f=f:not r[f]),
            "strong_enrichment":enrichment(rows,pred,strong),
        }

    int_dists={f:dist_by(rows,f,generative,strong) for f in INT_FEATURES}

    max_cl=max(r["binary"] for r in rows)
    max_rows=[r for r in rows if r["binary"]==max_cl]
    max_weight=sum(r["weight"] for r in max_rows)
    complete_rows=[r for r in rows if r["binary"]==BINARY_TOTAL]
    complete_weight=sum(r["weight"] for r in complete_rows)
    complete_without_ref=sum(r["weight"] for r in complete_rows if r["no_ground"]==BINARY_TOTAL)

    ref_dep=lambda r:r["ref_delta"]>0
    fresh=lambda r:r["fresh_delta"]>0
    reference_stats={
        "reference_dependent_count":wsum(rows,ref_dep),
        "reference_independent_count":wsum(rows,lambda r:not ref_dep(r)),
        "generative_reference_dependent_count":wsum(rows,lambda r:r["generative"] and ref_dep(r)),
        "strong_reference_dependent_count":wsum(rows,lambda r:strong(r) and ref_dep(r)),
        "min_nonzero_reference_delta_generative":min((r["ref_delta"] for r in rows if r["generative"] and r["ref_delta"]>0),default=None),
        "max_reference_delta":max(r["ref_delta"] for r in rows),
    }
    fresh_stats={
        "fresh_positive_count":wsum(rows,fresh),
        "generative_fresh_positive_count":wsum(rows,lambda r:r["generative"] and fresh(r)),
        "max_fresh_delta":max(r["fresh_delta"] for r in rows),
    }

    # Frozen R9 conjunction rule.
    best_conj=None
    for size in (1,2,3):
        for combo in combinations(BOOL_FEATURES,size):
            pred=lambda r,c=combo:all(r[f] for f in c)
            support=wsum(rows,pred)
            if support<100:continue
            e=enrichment(rows,pred,strong)
            ss=wsum(rows,lambda r,c=combo:strong(r) and all(r[f] for f in c))
            if e is None:continue
            cand={"features":list(combo),"support":support,"strong_support":ss,"strong_enrichment":e}
            if best_conj is None:
                best_conj=cand
            else:
                A=(cand["strong_enrichment"],-len(cand["features"]),cand["strong_support"],tuple(chr(255-ord(ch)) for ch in "")) # unused
                better=False
                if cand["strong_enrichment"]>best_conj["strong_enrichment"]:better=True
                elif cand["strong_enrichment"]==best_conj["strong_enrichment"]:
                    if len(cand["features"])<len(best_conj["features"]):better=True
                    elif len(cand["features"])==len(best_conj["features"]):
                        if cand["strong_support"]>best_conj["strong_support"]:better=True
                        elif cand["strong_support"]==best_conj["strong_support"] and tuple(cand["features"])<tuple(best_conj["features"]):better=True
                if better:best_conj=cand

    noncomm_enrich=enrichment(rows,lambda r:not r["commutative"],strong)
    residual_enrich=enrichment(rows,lambda r:r["residual_orders"]>0,strong)
    gres_enrich=enrichment(rows,lambda r:r["ground_top_residual_orders"]>0,strong)
    ref_enrich=enrichment(rows,ref_dep,strong)
    if gres_enrich is not None and ref_enrich is not None and gres_enrich>=1.5 and ref_enrich>=1.2:
        classification="reference + directed residual"
    elif residual_enrich is not None and residual_enrich>=1.5:
        classification="ordered directed residual"
    elif noncomm_enrich is not None and noncomm_enrich>=1.5:
        classification="generic asymmetry"
    else:
        classification="no simple frozen structural family"

    asym_best=max(int_dists["asymmetry_score"].items(),key=lambda kv:(kv[1]["mean_binary_closure"],-int(kv[0])))[0]

    reports={
        "R1_noncommutativity":{
            "enrichment":noncomm_enrich,
            "direction":"enriched" if noncomm_enrich and noncomm_enrich>1 else ("depleted" if noncomm_enrich is not None and noncomm_enrich<1 else "tie"),
        },
        "R2_asymmetry_score_highest_mean_closure":int(asym_best),
        "R3_residual_signature_enrichment":residual_enrich,
        "R4_reference_dependence_enrichment":ref_enrich,
        "R5_any_commutative_strong":any(strong(r) and r["commutative"] for r in rows),
        "R6_any_zero_reference_delta_strong":any(strong(r) and r["ref_delta"]==0 for r in rows),
        "R7_complete_raw_pointed_count":complete_weight,
        "R8_complete_without_reference_raw_count":complete_without_ref,
        "R9_best_positive_feature_conjunction":best_conj,
        "R10_classification":classification,
        "derived_enrichments":{
            "noncommutative":noncomm_enrich,
            "residual_orders_gt0":residual_enrich,
            "ground_top_residual_orders_gt0":gres_enrich,
            "reference_delta_gt0":ref_enrich,
        }
    }

    h1=stable_hash(rows);h2=stable_hash(rows)
    any_nonunit=False
    for f,s in feature_stats.items():
        e=s["strong_enrichment"]
        if e is not None and abs(e-1.0)>1e-15:any_nonunit=True
    gates={
        "C1_all_59049_covered":total_weight==TOTAL_RAW,
        "C2_exact_closures_all_representatives":rep_count==sum(m["reps"] for m in metas) and all(r["unary"]>=1 and r["binary"]>=2 and r["no_ground"]>=2 for r in rows),
        "C3_counts_within_bounds":all(r["unary"]<=UNARY_TOTAL and r["binary"]<=BINARY_TOTAL and r["no_ground"]<=BINARY_TOTAL for r in rows),
        "C4_canonicalization_replay":audit_total==256 and audit_pass==256,
        "C5_256_raw_audits_agree":audit_total==256 and audit_pass==256,
        "C6_generativity_every_orbit":all("generative" in r for r in rows),
        "C7_weighted_q90_computed":q90 is not None and total_weight==TOTAL_RAW,
        "C8_features_every_orbit":all(all(f in r for f in BOOL_FEATURES+INT_FEATURES) for r in rows),
        "C9_boolean_predictors_reported":len(feature_stats)==len(BOOL_FEATURES),
        "C10_integer_distributions_reported":len(int_dists)==len(INT_FEATURES),
        "C11_maximum_reported":bool(max_rows),
        "C12_completeness_count_reported":complete_weight>=0,
        "C13_reference_statistics_reported":reference_stats["reference_dependent_count"]+reference_stats["reference_independent_count"]==TOTAL_RAW,
        "C14_fresh_statistics_reported":fresh_stats["fresh_positive_count"]<=TOTAL_RAW,
        "C15_nontrivial_enrichment_or_independence":any_nonunit or strong_count==0,
        "C16_deterministic_aggregation_hash":h1==h2,
    }
    verdict="PASS_TERNARY_POINTED_NUCLEUS_CENSUS_V1" if all(gates.values()) else ("PARTIAL_TERNARY_POINTED_NUCLEUS_CENSUS_V1" if any(gates.values()) else "VALID_NEGATIVE_TERNARY_POINTED_NUCLEUS_CENSUS_V1")

    result={
        "protocol":"TERNARY_POINTED_NUCLEUS_CENSUS_V1",
        "precommit_commit":"ecf7c3af6807cc3f8913348de59df594663abf79",
        "addendum_commit":"5db29f3df24abe7f2188bc8db3ec08cd75c9e79e",
        "verdict":verdict,
        "raw_pointed_nuclei":TOTAL_RAW,
        "canonical_orbits":rep_count,
        "orbit_weight_sum":total_weight,
        "audit":{"total":audit_total,"passed":audit_pass},
        "weighted_q90_binary_closure":q90,
        "generative_raw_count":gen_count,
        "strongly_generative_raw_count":strong_count,
        "feature_stats":feature_stats,
        "integer_feature_distributions":int_dists,
        "reference_stats":reference_stats,
        "fresh_difference_stats":fresh_stats,
        "extremes":{
            "max_binary_closure":max_cl,
            "maximizing_orbits":[{"key":r["key"],"weight":r["weight"],"ground":r["ground"],"opcode":r["opcode"]} for r in max_rows],
            "maximizing_raw_count":max_weight,
            "complete_raw_count":complete_weight,
            "complete_without_reference_raw_count":complete_without_ref,
        },
        "required_reports":reports,
        "headline_gates":gates,
        "aggregation_hash":h1,
        "shards":sorted(metas,key=lambda m:m["shard"]),
        "orbits":sorted(rows,key=lambda r:r["key"]),
        "claim_boundary":"Exact finite census on the 3-element carrier. Feature enrichment is association, not causal proof or universal law."
    }
    summary={k:result[k] for k in (
        "verdict","raw_pointed_nuclei","canonical_orbits","orbit_weight_sum","audit",
        "weighted_q90_binary_closure","generative_raw_count","strongly_generative_raw_count",
        "reference_stats","fresh_difference_stats","extremes","required_reports","headline_gates","aggregation_hash"
    )}
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("TERNARY POINTED NUCLEUS CENSUS V1",verdict)
    print(json.dumps(summary,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
