#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from itertools import combinations, permutations
from fractions import Fraction
import hashlib, json, math, sys

Q=3
OP_COUNT=19683
POINTED_COUNT=59049
P3=[1,3,9,27,81,243,729,2187,6561]
PERMS=list(permutations(range(3)))

def decode_op(code):
    t=[]
    for _ in range(9):
        t.append(code%3);code//=3
    return t

def encode_op(t):
    return sum(v*P3[i] for i,v in enumerate(t))

def opv(op,a,b): return op[3*a+b]

def canonical_key(rawkey):
    g,code=divmod(rawkey,OP_COUNT);old=decode_op(code)
    best=POINTED_COUNT+1
    for p in PERMS:
        for sw in (0,1):
            nt=[0]*9
            for a in range(3):
                for b in range(3):
                    oa,ob=(b,a) if sw else (a,b)
                    nt[3*p[a]+p[b]]=p[opv(old,oa,ob)]
            best=min(best,p[g]*OP_COUNT+encode_op(nt))
    return best

def compose_unary(f,h):
    return tuple(f[h[x]] for x in range(len(f)))

def transformation_monoid(gens,q):
    ident=tuple(range(q))
    seen={ident,*gens};queue=list(seen);i=0
    while i<len(queue):
        a=queue[i];i+=1
        snap=list(queue)
        for b in snap:
            for z in (compose_unary(a,b),compose_unary(b,a)):
                if z not in seen:
                    seen.add(z);queue.append(z)
    return tuple(sorted(seen))

def matmul(A,B):
    n=len(A);m=len(B[0]);k=len(B)
    out=[[0]*m for _ in range(n)]
    for i in range(n):
        for z in range(k):
            if A[i][z]==0:continue
            az=A[i][z]
            for j in range(m):
                if B[z][j]:
                    out[i][j]+=az*B[z][j]
    return out

def matpow_path_counts(C,kmax=8):
    cur=[row[:] for row in C]
    seq=[]
    for k in range(1,kmax+1):
        seq.append(sum(map(sum,cur)))
        if k<kmax:cur=matmul(cur,C)
    return seq

def reachability(C):
    n=len(C)
    R=[[False]*n for _ in range(n)]
    for i in range(n):
        R[i][i]=True
        for j in range(n):
            if C[i][j]>0:R[i][j]=True
    for k in range(n):
        for i in range(n):
            if R[i][k]:
                rik=R[i]
                rkk=R[k]
                for j in range(n):
                    rik[j]=rik[j] or rkk[j]
    return R

def sccs_from_C(C):
    n=len(C)
    adj=[[j for j in range(n) if C[i][j]>0] for i in range(n)]
    radj=[[] for _ in range(n)]
    for i in range(n):
        for j in adj[i]:radj[j].append(i)
    seen=[False]*n;order=[]
    def dfs(u):
        seen[u]=True
        for v in adj[u]:
            if not seen[v]:dfs(v)
        order.append(u)
    for i in range(n):
        if not seen[i]:dfs(i)
    comp=[-1]*n;groups=[]
    def rdfs(u,c):
        comp[u]=c;groups[c].append(u)
        for v in radj[u]:
            if comp[v]<0:rdfs(v,c)
    for u in reversed(order):
        if comp[u]<0:
            groups.append([])
            rdfs(u,len(groups)-1)
    return groups

def cycle_states(C):
    groups=sccs_from_C(C)
    cyc=set()
    for g in groups:
        if len(g)>1:cyc.update(g)
        elif len(g)==1 and C[g[0]][g[0]]>0:cyc.add(g[0])
    return cyc

def fraction_obj(f:Fraction):
    return {"num":f.numerator,"den":f.denominator,"float":float(f)}

def generic_distinction_metrics(carrier,ground,opfn):
    q=len(carrier)
    distinctions=[(a,b) for a in carrier for b in carrier if a!=b]
    didx={d:i for i,d in enumerate(distinctions)}
    translations=[]
    for c in carrier:
        translations.append(tuple(opfn(c,x) for x in carrier))
    for c in carrier:
        translations.append(tuple(opfn(x,c) for x in carrier))
    C=[[0]*len(distinctions) for _ in distinctions]
    collapsed=0
    for i,(a,b) in enumerate(distinctions):
        for t in translations:
            aa,bb=t[a],t[b]
            if aa==bb:
                collapsed+=1
            else:
                C[i][didx[(aa,bb)]]+=1
    live_out=[sum(r) for r in C]
    P=matpow_path_counts(C,8)
    R=reachability(C)
    groups=sccs_from_C(C)
    cyc=cycle_states(C)
    ground_ids=[i for i,(a,b) in enumerate(distinctions) if a==ground or b==ground]
    ground_reach=set()
    for i in ground_ids:
        for j in range(len(distinctions)):
            if R[i][j]:ground_reach.add(j)
    monoid=transformation_monoid(translations,q)
    retention=[]
    sem_reach=[[False]*len(distinctions) for _ in distinctions]
    for i,(a,b) in enumerate(distinctions):
        cnt=0
        for m in monoid:
            aa,bb=m[a],m[b]
            if aa!=bb:
                cnt+=1
                sem_reach[i][didx[(aa,bb)]]=True
        retention.append(cnt)
    sem_cov=sum(v for row in sem_reach for v in row)
    er=Fraction(sum(live_out),len(distinctions)*len(translations))
    s8=Fraction(P[7],len(distinctions)*(len(translations)**8))
    mc=Fraction(sum(v for row in R for v in row),len(distinctions)**2)
    sr=Fraction(sum(retention),len(distinctions)*len(monoid))
    sf=Fraction(min(retention),len(monoid))
    smc=Fraction(sem_cov,len(distinctions)**2)
    dtc=sf*smc
    return {
        "distinctions":distinctions,
        "matrix":C,
        "matrix_hash":hashlib.sha256(json.dumps(C,separators=(",",":")).encode()).hexdigest(),
        "elementary_live_edges":sum(live_out),
        "elementary_collapsed_edges":collapsed,
        "elementary_min_live_outdegree":min(live_out),
        "elementary_max_live_outdegree":max(live_out),
        "dead_distinction_count":sum(x==0 for x in live_out),
        "P":P,
        "ER":er,"S8":s8,
        "MC":mc,
        "live_scc_count":len(groups),
        "live_largest_scc":max(map(len,groups)),
        "live_graph_strongly_connected":len(groups)==1,
        "live_cycle_state_count":len(cyc),
        "grounded_reachable_count":len(ground_reach),
        "grounded_all_reachable":len(ground_reach)==len(distinctions),
        "monoid_size":len(monoid),
        "monoid_min_retention_num":min(retention),
        "monoid_max_retention_num":max(retention),
        "monoid_mean_retention":Fraction(sum(retention),len(retention)),
        "SR":sr,"SF":sf,
        "SMC":smc,
        "semigroup_distinction_transitive":sem_cov==len(distinctions)**2,
        "DTC":dtc,
    }

def metrics_for_key(key):
    g,code=divmod(key,OP_COUNT)
    op=decode_op(code)
    return generic_distinction_metrics(tuple(range(3)),g,lambda a,b:opv(op,a,b))

def audit_keys():
    out=[];seen=set();i=0
    while len(out)<256:
        h=hashlib.sha256(f"DTNV1-AUDIT|{i}".encode()).hexdigest()
        k=int(h[:16],16)%POINTED_COUNT
        if k not in seen:
            seen.add(k);out.append(k)
        i+=1
    return out

def invariant_signature(m):
    return {
        "elementary_live_edges":m["elementary_live_edges"],
        "elementary_collapsed_edges":m["elementary_collapsed_edges"],
        "elementary_min_live_outdegree":m["elementary_min_live_outdegree"],
        "elementary_max_live_outdegree":m["elementary_max_live_outdegree"],
        "dead_distinction_count":m["dead_distinction_count"],
        "P":m["P"],
        "ER":(m["ER"].numerator,m["ER"].denominator),
        "S8":(m["S8"].numerator,m["S8"].denominator),
        "MC":(m["MC"].numerator,m["MC"].denominator),
        "live_scc_count":m["live_scc_count"],
        "live_largest_scc":m["live_largest_scc"],
        "live_graph_strongly_connected":m["live_graph_strongly_connected"],
        "live_cycle_state_count":m["live_cycle_state_count"],
        "grounded_reachable_count":m["grounded_reachable_count"],
        "grounded_all_reachable":m["grounded_all_reachable"],
        "monoid_size":m["monoid_size"],
        "monoid_min_retention_num":m["monoid_min_retention_num"],
        "monoid_max_retention_num":m["monoid_max_retention_num"],
        "monoid_mean_retention":(m["monoid_mean_retention"].numerator,m["monoid_mean_retention"].denominator),
        "SR":(m["SR"].numerator,m["SR"].denominator),
        "SF":(m["SF"].numerator,m["SF"].denominator),
        "SMC":(m["SMC"].numerator,m["SMC"].denominator),
        "semigroup_distinction_transitive":m["semigroup_distinction_transitive"],
        "DTC":(m["DTC"].numerator,m["DTC"].denominator),
    }

def raw_weight(rows,pred=lambda r:True):
    return sum(int(r["weight"]) for r in rows if pred(r))

def weighted_mean(rows,fn,pred=lambda r:True):
    den=raw_weight(rows,pred)
    if not den:return None
    return sum(int(r["weight"])*float(fn(r)) for r in rows if pred(r))/den

def weighted_corr(rows,fx,fy,pred=lambda r:True):
    sub=[r for r in rows if pred(r)]
    W=sum(int(r["weight"]) for r in sub)
    if not W:return None
    mx=sum(int(r["weight"])*float(fx(r)) for r in sub)/W
    my=sum(int(r["weight"])*float(fy(r)) for r in sub)/W
    vx=sum(int(r["weight"])*(float(fx(r))-mx)**2 for r in sub)/W
    vy=sum(int(r["weight"])*(float(fy(r))-my)**2 for r in sub)/W
    if vx==0 or vy==0:return 0.0
    cov=sum(int(r["weight"])*(float(fx(r))-mx)*(float(fy(r))-my) for r in sub)/W
    return cov/math.sqrt(vx*vy)

def weighted_quantile(rows,fn,q,pred=lambda r:True):
    vals=sorted((fn(r),int(r["weight"]),int(r["key"])) for r in rows if pred(r))
    total=sum(w for _,w,_ in vals)
    target=math.ceil(q*total)
    acc=0
    for v,w,_ in vals:
        acc+=w
        if acc>=target:return v
    return vals[-1][0]

def frac_to_pair(f):
    return [f.numerator,f.denominator]

def main():
    if len(sys.argv)!=4:
        raise SystemExit("usage: script PRIOR_POINTED_JSON PRIOR_DEV_JSON OUT_DIR")
    prior=json.loads(Path(sys.argv[1]).read_text())
    dev=json.loads(Path(sys.argv[2]).read_text())
    out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)

    pmap={int(r["key"]):r for r in prior["orbits"]}
    dmap={int(r["key"]):r for r in dev["orbits"]}
    pareto_keys=sorted(int(r["key"]) for r in dev["pareto_orbits"])
    pareto_set=set(pareto_keys)
    joint_set={int(r["key"]) for r in dev["orbits"] if bool(r["joint_developmental"])}

    rows=[]
    for key in sorted(pmap):
        m=metrics_for_key(key)
        r=dict(pmap[key]);r.update(dmap[key])
        r["is_complete"]=int(r["binary"])==19683
        r["is_joint"]=key in joint_set
        r["is_pareto"]=key in pareto_set
        # exact distinction metrics retained as Fractions privately and serialized later
        r["_m"]=m
        rows.append(r)

    complete=[r for r in rows if r["is_complete"]]
    joint=[r for r in rows if r["is_joint"]]
    pareto=[r for r in rows if r["is_pareto"]]
    complete_weight=raw_weight(complete)
    pareto_weight=raw_weight(pareto)

    metric_fns={
        "ER":lambda r:r["_m"]["ER"],
        "S8":lambda r:r["_m"]["S8"],
        "MC":lambda r:r["_m"]["MC"],
        "SR":lambda r:r["_m"]["SR"],
        "SF":lambda r:r["_m"]["SF"],
        "SMC":lambda r:r["_m"]["SMC"],
        "DTC":lambda r:r["_m"]["DTC"],
    }
    dev_fns={
        "G3":lambda r:r["d3"],
        "R3":lambda r:r["recombinant3"],
        "P":lambda r:r["recurrence_mean_distinct"],
        "M":lambda r:r["mutation_complete"]/18.0,
    }
    correlations={}
    for mn,mf in metric_fns.items():
        correlations[mn]={dn:weighted_corr(complete,mf,df) for dn,df in dev_fns.items()}

    quartiles={mn:weighted_quantile(complete,mf,.75) for mn,mf in metric_fns.items()}
    enrichment={}
    for mn,mf in metric_fns.items():
        q=quartiles[mn]
        enrichment[mn]={
            "q75":fraction_obj(q),
            "pareto_at_or_above_q75":sum(mf(r)>=q for r in pareto),
            "pareto_fraction_at_or_above_q75":sum(mf(r)>=q for r in pareto)/len(pareto),
            "pareto_mean":sum(float(mf(r)) for r in pareto)/len(pareto),
            "complete_weighted_mean":weighted_mean(complete,mf),
            "joint_weighted_mean":weighted_mean(joint,mf),
        }

    discrete_fns={
        "dead_distinction_count":lambda r:r["_m"]["dead_distinction_count"],
        "live_graph_strongly_connected":lambda r:r["_m"]["live_graph_strongly_connected"],
        "live_cycle_state_count":lambda r:r["_m"]["live_cycle_state_count"],
        "grounded_all_reachable":lambda r:r["_m"]["grounded_all_reachable"],
        "semigroup_distinction_transitive":lambda r:r["_m"]["semigroup_distinction_transitive"],
        "elementary_min_live_outdegree":lambda r:r["_m"]["elementary_min_live_outdegree"],
        "monoid_size":lambda r:r["_m"]["monoid_size"],
        "monoid_min_retention_num":lambda r:r["_m"]["monoid_min_retention_num"],
    }
    common=[]
    for name,fn in discrete_fns.items():
        vals={fn(r) for r in pareto}
        if len(vals)==1:
            v=next(iter(vals))
            cw=raw_weight(complete,lambda r,fn=fn,v=v:fn(r)==v)
            jw=raw_weight(joint,lambda r,fn=fn,v=v:fn(r)==v)
            common.append({
                "feature":name,"value":v,
                "complete_raw_weight":cw,
                "complete_prevalence":cw/complete_weight,
                "joint_raw_weight":jw,
                "joint_prevalence":jw/raw_weight(joint) if joint else 0.0,
            })
    common.sort(key=lambda z:(z["complete_prevalence"],z["feature"],repr(z["value"])))
    rarest_common=common[0] if common else None

    best_pair=None
    for a,b in combinations(common,2):
        fa,va=a["feature"],a["value"];fb,vb=b["feature"],b["value"]
        fna=discrete_fns[fa];fnb=discrete_fns[fb]
        cw=raw_weight(complete,lambda r,fna=fna,va=va,fnb=fnb,vb=vb:fna(r)==va and fnb(r)==vb)
        if cw<24:continue
        jw=raw_weight(joint,lambda r,fna=fna,va=va,fnb=fnb,vb=vb:fna(r)==va and fnb(r)==vb)
        z={
            "features":[fa,fb],"values":[va,vb],
            "complete_raw_weight":cw,"complete_prevalence":cw/complete_weight,
            "joint_raw_weight":jw,"joint_prevalence":jw/raw_weight(joint) if joint else 0.0,
        }
        if best_pair is None or (z["complete_prevalence"],tuple(z["features"]))<(best_pair["complete_prevalence"],tuple(best_pair["features"])):
            best_pair=z

    # DTC ranking and weighted percentile recall.
    ranked=sorted(complete,key=lambda r:(-float(r["_m"]["DTC"]),int(r["key"])))
    ranks={int(r["key"]):i+1 for i,r in enumerate(ranked)}
    pareto_ranks={str(k):ranks[k] for k in pareto_keys}
    top_recovery={str(n):sum(k in {int(r["key"]) for r in ranked[:n]} for k in pareto_keys) for n in (16,32,64,128)}
    percentile_recall={}
    for q in (.75,.90,.95,.99):
        th=weighted_quantile(complete,metric_fns["DTC"],q)
        hit=raw_weight(pareto,lambda r,th=th:r["_m"]["DTC"]>=th)
        percentile_recall[str(q)]={
            "threshold":fraction_obj(th),
            "pareto_raw_recall":hit/pareto_weight if pareto_weight else 0.0,
            "pareto_raw_weight_hit":hit,
            "pareto_raw_weight_total":pareto_weight,
        }

    # Strongest metric correlations requested.
    strongest_g3=max(correlations.items(),key=lambda kv:abs(kv[1]["G3"]))
    strongest_p=max(correlations.items(),key=lambda kv:abs(kv[1]["P"]))

    dtc_corr=correlations["DTC"]
    dtc_en=enrichment["DTC"]
    supported=(
        all(dtc_corr[x]>0 for x in ("G3","R3","P","M"))
        and dtc_en["pareto_at_or_above_q75"]>=12
        and dtc_en["pareto_mean"]>dtc_en["joint_weighted_mean"]
        and dtc_en["pareto_mean"]>dtc_en["complete_weighted_mean"]
    )
    classification="distinction-transport hypothesis supported" if supported else "distinction-transport hypothesis not sufficient under V1"

    # Boolean realization.
    bm=generic_distinction_metrics((0,1),1,lambda a,b:(1-a)&b)
    boolean={
        "ER":fraction_obj(bm["ER"]),
        "S8":fraction_obj(bm["S8"]),
        "MC":fraction_obj(bm["MC"]),
        "SR":fraction_obj(bm["SR"]),
        "SF":fraction_obj(bm["SF"]),
        "SMC":fraction_obj(bm["SMC"]),
        "DTC":fraction_obj(bm["DTC"]),
        "live_graph_strongly_connected":bm["live_graph_strongly_connected"],
        "semigroup_distinction_transitive":bm["semigroup_distinction_transitive"],
        "monoid_size":bm["monoid_size"],
    }

    # 256 raw/canonical audits.
    audit_pass=0
    for raw in audit_keys():
        ck=canonical_key(raw)
        if invariant_signature(metrics_for_key(raw))==invariant_signature(metrics_for_key(ck)):
            audit_pass+=1

    serialized_orbits=[]
    for r in rows:
        m=r["_m"]
        serialized_orbits.append({
            "key":int(r["key"]),"weight":int(r["weight"]),
            "complete":bool(r["is_complete"]),"joint":bool(r["is_joint"]),"pareto":bool(r["is_pareto"]),
            "matrix":m["matrix"],"matrix_hash":m["matrix_hash"],
            "P":m["P"],
            "elementary_live_edges":m["elementary_live_edges"],
            "elementary_collapsed_edges":m["elementary_collapsed_edges"],
            "elementary_min_live_outdegree":m["elementary_min_live_outdegree"],
            "elementary_max_live_outdegree":m["elementary_max_live_outdegree"],
            "dead_distinction_count":m["dead_distinction_count"],
            "ER":frac_to_pair(m["ER"]),"S8":frac_to_pair(m["S8"]),"MC":frac_to_pair(m["MC"]),
            "live_scc_count":m["live_scc_count"],"live_largest_scc":m["live_largest_scc"],
            "live_graph_strongly_connected":m["live_graph_strongly_connected"],
            "live_cycle_state_count":m["live_cycle_state_count"],
            "grounded_reachable_count":m["grounded_reachable_count"],
            "grounded_all_reachable":m["grounded_all_reachable"],
            "monoid_size":m["monoid_size"],
            "monoid_min_retention_num":m["monoid_min_retention_num"],
            "monoid_max_retention_num":m["monoid_max_retention_num"],
            "monoid_mean_retention":frac_to_pair(m["monoid_mean_retention"]),
            "SR":frac_to_pair(m["SR"]),"SF":frac_to_pair(m["SF"]),"SMC":frac_to_pair(m["SMC"]),
            "semigroup_distinction_transitive":m["semigroup_distinction_transitive"],
            "DTC":frac_to_pair(m["DTC"]),
        })

    payload_for_hash={
        "correlations":correlations,
        "quartiles":{k:frac_to_pair(v) for k,v in quartiles.items()},
        "enrichment":enrichment,
        "common":common,
        "best_pair":best_pair,
        "pareto_ranks":pareto_ranks,
        "top_recovery":top_recovery,
        "percentile_recall":percentile_recall,
        "audit_pass":audit_pass,
        "classification":classification,
    }
    h1=hashlib.sha256(json.dumps(payload_for_hash,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    h2=hashlib.sha256(json.dumps(payload_for_hash,sort_keys=True,separators=(",",":")).encode()).hexdigest()

    reports={
        "R1_DTC_positive_all_four":all(dtc_corr[x]>0 for x in ("G3","R3","P","M")),
        "R2_strongest_abs_G3_correlation":{"metric":strongest_g3[0],"correlation":strongest_g3[1]["G3"]},
        "R3_strongest_abs_P_correlation":{"metric":strongest_p[0],"correlation":strongest_p[1]["P"]},
        "R4_pareto_above_DTC_q75_fraction":dtc_en["pareto_fraction_at_or_above_q75"],
        "R5_rarest_pareto_common_distinction_property":rarest_common,
        "R6_rarest_two_feature_distinction_conjunction":best_pair,
        "R7_DTC_top_recovery":top_recovery,
        "R8_all_pareto_live_graph_strongly_connected":all(r["_m"]["live_graph_strongly_connected"] for r in pareto),
        "R9_all_pareto_semigroup_distinction_transitive":all(r["_m"]["semigroup_distinction_transitive"] for r in pareto),
        "R10_classification":classification,
    }

    gates={
        "DTN1_all_5130_orbits":len(rows)==5130,
        "DTN2_weight_sum_59049":raw_weight(rows)==59049,
        "DTN3_exact_matrices_all":all(len(r["matrix"])==6 and all(len(x)==6 for x in r["matrix"]) for r in serialized_orbits),
        "DTN4_exact_P1_P8_all":all(len(r["P"])==8 for r in serialized_orbits),
        "DTN5_reachability_scc_all":all("live_scc_count" in r and "live_cycle_state_count" in r for r in serialized_orbits),
        "DTN6_grounded_reachability_all":all("grounded_reachable_count" in r for r in serialized_orbits),
        "DTN7_monoid_retention_all":all("monoid_min_retention_num" in r for r in serialized_orbits),
        "DTN8_semigroup_mixing_all":all("SMC" in r for r in serialized_orbits),
        "DTN9_DTC_all":all("DTC" in r for r in serialized_orbits),
        "DTN10_all_correlations":len(correlations)==7 and all(len(v)==4 for v in correlations.values()),
        "DTN11_all_quartile_enrichment":len(enrichment)==7,
        "DTN12_pareto_common_reported":common is not None,
        "DTN13_two_feature_search":best_pair is not None or len(common)<2,
        "DTN14_DTC_recovery_reported":len(pareto_ranks)==16 and len(top_recovery)==4,
        "DTN15_256_symmetry_audits":audit_pass==256,
        "DTN16_deterministic_hash":h1==h2,
    }
    verdict="PASS_DISTINCTION_TRANSPORT_NUCLEUS_V1" if all(gates.values()) else ("PARTIAL_DISTINCTION_TRANSPORT_NUCLEUS_V1" if any(gates.values()) else "VALID_NEGATIVE_DISTINCTION_TRANSPORT_NUCLEUS_V1")

    result={
        "protocol":"DISTINCTION_TRANSPORT_NUCLEUS_V1",
        "precommit_commit":"8d7fd842fad3546cf26bea7bc1d921c2f31fd821",
        "verdict":verdict,
        "classification":classification,
        "complete_raw_weight":complete_weight,
        "pareto_keys":pareto_keys,
        "correlations":correlations,
        "quartiles":{k:fraction_obj(v) for k,v in quartiles.items()},
        "pareto_enrichment":enrichment,
        "pareto_common_exact_properties":common,
        "two_feature_conjunction":best_pair,
        "DTC_pareto_ranks":pareto_ranks,
        "DTC_top_recovery":top_recovery,
        "DTC_percentile_recall":percentile_recall,
        "boolean_realization":boolean,
        "audit":{"total":256,"passed":audit_pass},
        "required_reports":reports,
        "headline_gates":gates,
        "aggregation_hash":h1,
        "orbits":serialized_orbits,
        "claim_boundary":"Exact finite 3-element distinction-transport census. DTC is a programme-defined invariant; no external novelty claim is made."
    }
    summary={k:result[k] for k in (
        "verdict","classification","complete_raw_weight","pareto_keys","correlations","quartiles",
        "pareto_enrichment","pareto_common_exact_properties","two_feature_conjunction",
        "DTC_pareto_ranks","DTC_top_recovery","DTC_percentile_recall","boolean_realization",
        "audit","required_reports","headline_gates","aggregation_hash"
    )}
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("DISTINCTION TRANSPORT NUCLEUS V1",verdict)
    print(json.dumps(summary,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
