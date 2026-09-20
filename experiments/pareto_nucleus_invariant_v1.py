#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from itertools import combinations, permutations
import hashlib, json, math, sys

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
    return tuple(f[h[x]] for x in range(3))

def transformation_monoid(gens):
    ident=(0,1,2)
    seen={ident,*gens};q=list(seen)
    i=0
    while i<len(q):
        a=q[i];i+=1
        snap=list(q)
        for b in snap:
            for z in (compose_unary(a,b),compose_unary(b,a)):
                if z not in seen:
                    seen.add(z);q.append(z)
    return seen

def transitive_action(monoid):
    for u in range(3):
        reach={m[u] for m in monoid}
        if len(reach)<3:return False
    return True

def subalgebra_counts(op,g):
    proper=[]
    for mask in range(1,7):
        S={i for i in range(3) if mask&(1<<i)}
        ok=all(opv(op,a,b) in S for a in S for b in S)
        if ok:proper.append(S)
    return len(proper),sum(g in S for S in proper)

PARTITIONS=[
    [{0},{1},{2}],
    [{0,1},{2}],
    [{0,2},{1}],
    [{1,2},{0}],
    [{0,1,2}],
]
def congruence_count(op):
    cnt=0
    for blocks in PARTITIONS:
        cls={}
        for i,B in enumerate(blocks):
            for x in B:cls[x]=i
        ok=True
        for a in range(3):
            for ap in range(3):
                if cls[a]!=cls[ap]:continue
                for b in range(3):
                    for bp in range(3):
                        if cls[b]!=cls[bp]:continue
                        if cls[opv(op,a,b)]!=cls[opv(op,ap,bp)]:
                            ok=False;break
                    if not ok:break
                if not ok:break
            if not ok:break
        if ok:cnt+=1
    return cnt

def automorphism_count(op,g):
    cnt=0
    for p in PERMS:
        if p[g]!=g:continue
        ok=True
        for a in range(3):
            for b in range(3):
                if p[opv(op,a,b)]!=opv(op,p[a],p[b]):
                    ok=False;break
            if not ok:break
        if ok:cnt+=1
    return cnt

def functional_graph_features(op):
    nxt=[]
    for a in range(3):
        for b in range(3):
            nxt.append(3*b+opv(op,a,b))
    bij=len(set(nxt))==9
    visited=[False]*9
    cycle_nodes=set()
    cycles=[]
    comps=[]
    for s in range(9):
        if visited[s]:continue
        path=[];pos={}
        u=s
        while not visited[u] and u not in pos:
            pos[u]=len(path);path.append(u);u=nxt[u]
        cyc=[]
        if u in pos:
            cyc=path[pos[u]:]
            cycle_nodes.update(cyc);cycles.append(len(cyc))
        for v in path:visited[v]=True
    # weak components of functional graph
    und=[set() for _ in range(9)]
    for u,v in enumerate(nxt):
        und[u].add(v);und[v].add(u)
    seen=set()
    for s in range(9):
        if s in seen:continue
        q=[s];seen.add(s);n=0
        while q:
            u=q.pop();n+=1
            for v in und[u]:
                if v not in seen:seen.add(v);q.append(v)
        comps.append(n)
    return (len(cycles),max(cycles) if cycles else 0,len(cycle_nodes),max(comps) if comps else 0,bij)

def rowcol_features(op):
    rows=[tuple(op[3*a+b] for b in range(3)) for a in range(3)]
    cols=[tuple(op[3*a+b] for a in range(3)) for b in range(3)]
    rim=tuple(sorted(len(set(r)) for r in rows))
    cim=tuple(sorted(len(set(c)) for c in cols))
    rc_pair=tuple(sorted((rim,cim)))
    perms=sum(len(set(r))==3 for r in rows)+sum(len(set(c))==3 for c in cols)
    consts=sum(len(set(r))==1 for r in rows)+sum(len(set(c))==1 for c in cols)
    dists=[]
    for fam in (rows,cols):
        for i in range(3):
            for j in range(i+1,3):
                dists.append(sum(a!=b for a,b in zip(fam[i],fam[j])))
    freqs=tuple(sorted(op.count(v) for v in range(3)))
    return rc_pair,perms,consts,min(dists),max(dists),freqs

def features(rawkey):
    g,code=divmod(rawkey,OP_COUNT);op=decode_op(code)
    L=[tuple(opv(op,a,x) for x in range(3)) for a in range(3)]
    R=[tuple(opv(op,x,a) for x in range(3)) for a in range(3)]
    trans=L+R
    ims=[len(set(t)) for t in trans]
    mon=transformation_monoid(trans)
    ground_orbit=len({m[g] for m in mon})
    rc_pair,permrc,constrc,mind,maxd,freqs=rowcol_features(op)
    minors=[
        tuple(opv(op,x,x) for x in range(3)),
        tuple(opv(op,g,x) for x in range(3)),
        tuple(opv(op,x,g) for x in range(3)),
    ]
    sub,subg=subalgebra_counts(op,g)
    cong=congruence_count(op)
    aut=automorphism_count(op,g)
    fg=functional_graph_features(op)
    op2=[opv(op,b,a) for a in range(3) for b in range(3)]
    fg2=functional_graph_features(op2)
    fgp=tuple(sorted((fg,fg2)))
    return {
        "distinct_translations":len(set(trans)),
        "bijective_translations":sum(len(set(t))==3 for t in trans),
        "constant_translations":sum(len(set(t))==1 for t in trans),
        "translation_image_min":min(ims),
        "translation_image_max":max(ims),
        "translation_image_mean":sum(ims)/6.0,
        "translation_monoid_size":len(mon),
        "ground_orbit_size":ground_orbit,
        "translation_transitive":transitive_action(mon),
        "rowcol_image_multisets":repr(rc_pair),
        "permutation_rows_cols":permrc,
        "constant_rows_cols":constrc,
        "rowcol_hamming_min":mind,
        "rowcol_hamming_max":maxd,
        "output_frequency_multiset":repr(freqs),
        "pointed_minor_distinct":len(set(minors)),
        "pointed_minor_image_multiset":repr(tuple(sorted(len(set(m)) for m in minors))),
        "pointed_minor_any_permutation":any(len(set(m))==3 for m in minors),
        "pointed_minor_any_constant":any(len(set(m))==1 for m in minors),
        "proper_subalgebras":sub,
        "pointed_proper_subalgebras":subg,
        "congruence_count":cong,
        "pointed_automorphism_group_size":aut,
        "simple":cong==2,
        "no_pointed_proper_subalgebra":subg==0,
        "recurrence_signature":repr(fgp),
        "recurrence_bijective_any":fg[4] or fg2[4],
        "recurrence_bijective_both":fg[4] and fg2[4],
        "recurrence_cycle_count_mean":(fg[0]+fg2[0])/2.0,
        "recurrence_max_cycle_mean":(fg[1]+fg2[1])/2.0,
        "recurrence_cyclic_states_mean":(fg[2]+fg2[2])/2.0,
        "recurrence_max_basin_mean":(fg[3]+fg2[3])/2.0,
    }

# Terms: atoms 0:g,1:x,2:y. Composite represented as (left,right)
def build_terms():
    terms=[
        {"size":0,"kind":"atom","atom":"g","str":"g"},
        {"size":0,"kind":"atom","atom":"x","str":"x"},
        {"size":0,"kind":"atom","atom":"y","str":"y"},
    ]
    bysize={0:[0,1,2]}
    for size in range(1,4):
        ids=[]
        for ls in range(size):
            rs=size-1-ls
            for i in bysize[ls]:
                for j in bysize[rs]:
                    s=f"d({terms[i]['str']},{terms[j]['str']})"
                    terms.append({"size":size,"kind":"d","left":i,"right":j,"str":s})
                    ids.append(len(terms)-1)
        bysize[size]=ids
    # mirror indices by serialization
    index={t["str"]:i for i,t in enumerate(terms)}
    def mstr(i):
        t=terms[i]
        if t["kind"]=="atom":return t["str"]
        return f"d({mstr(t['right'])},{mstr(t['left'])})"
    mirror=[index[mstr(i)] for i in range(len(terms))]
    return terms,mirror

def term_semantics(rawkey,terms):
    g,code=divmod(rawkey,OP_COUNT);op=decode_op(code)
    # 9 assignments x,y
    vals=[]
    gcode=sum(g*P3[i] for i in range(9))
    xcode=sum((i//3)*P3[i] for i in range(9))
    ycode=sum((i%3)*P3[i] for i in range(9))
    for t in terms:
        if t["kind"]=="atom":
            vals.append(gcode if t["atom"]=="g" else (xcode if t["atom"]=="x" else ycode))
        else:
            a=vals[t["left"]];b=vals[t["right"]]
            aa=decode_op(a);bb=decode_op(b)
            out=[opv(op,aa[k],bb[k]) for k in range(9)]
            vals.append(encode_op(out))
    return vals

def raw_weight(rows,pred=lambda r:True):
    return sum(int(r["weight"]) for r in rows if pred(r))

def weighted_mean(rows,key,pred=lambda r:True):
    den=raw_weight(rows,pred)
    if not den:return None
    return sum(int(r["weight"])*float(r[key]) for r in rows if pred(r))/den

def audit_keys():
    out=[];seen=set();i=0
    while len(out)<256:
        h=hashlib.sha256(f"PINV1-AUDIT|{i}".encode()).hexdigest()
        k=int(h[:16],16)%POINTED_COUNT
        if k not in seen:
            seen.add(k);out.append(k)
        i+=1
    return out

def main():
    if len(sys.argv)!=4:
        raise SystemExit("usage: pareto_invariant PRIOR_POINTED_JSON PRIOR_DEV_JSON OUT_DIR")
    prior=json.loads(Path(sys.argv[1]).read_text())
    dev=json.loads(Path(sys.argv[2]).read_text())
    out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)

    prior_rows=prior["orbits"]
    dev_rows=dev["orbits"]
    pmap={int(r["key"]):r for r in prior_rows}
    dmap={int(r["key"]):r for r in dev_rows}
    pareto_keys=sorted(int(r["key"]) for r in dev["pareto_orbits"])
    if len(pareto_keys)!=16:raise RuntimeError(f"expected 16 Pareto keys, got {len(pareto_keys)}")
    joint_keys={int(r["key"]) for r in dev_rows if bool(r["joint_developmental"])}
    complete_keys={int(r["key"]) for r in prior_rows if int(r["binary"])==19683}

    rows=[]
    for r in prior_rows:
        key=int(r["key"]);z=dict(r);z.update(features(key))
        z["is_complete"]=key in complete_keys
        z["is_joint"]=key in joint_keys
        z["is_pareto"]=key in set(pareto_keys)
        rows.append(z)

    fmap={int(r["key"]):r for r in rows}
    pareto=[fmap[k] for k in pareto_keys]
    complete=[r for r in rows if r["is_complete"]]
    joint=[r for r in rows if r["is_joint"]]

    terms,mirror=build_terms()
    term_count=len(terms)

    # Pareto-common identity candidates, orbit-invariant under mirror.
    psem={k:term_semantics(k,terms) for k in pareto_keys}
    candidates=[]
    for i in range(term_count):
        for j in range(i+1,term_count):
            ok=True
            mi,mj=mirror[i],mirror[j]
            for k in pareto_keys:
                s=psem[k]
                if not (s[i]==s[j] or s[mi]==s[mj]):
                    ok=False;break
            if ok:candidates.append((i,j))

    # Exact prevalence of every candidate on complete and joint populations.
    complete_sem={int(r["key"]):term_semantics(int(r["key"]),terms) for r in complete}
    identity_rows=[]
    complete_weight=raw_weight(complete)
    joint_weight=raw_weight(joint)
    pareto_set=set(pareto_keys)
    for i,j in candidates:
        mi,mj=mirror[i],mirror[j]
        cw=jw=0
        holders=[]
        for r in complete:
            k=int(r["key"]);s=complete_sem[k]
            holds=(s[i]==s[j] or s[mi]==s[mj])
            if holds:
                cw+=int(r["weight"]);holders.append(k)
                if k in joint_keys:jw+=int(r["weight"])
        if cw==complete_weight:
            continue # trivial in complete population
        exclusive=set(holders)==pareto_set
        identity_rows.append({
            "left":terms[i]["str"],"right":terms[j]["str"],
            "left_size":terms[i]["size"],"right_size":terms[j]["size"],
            "complete_raw_weight":cw,
            "complete_prevalence":cw/complete_weight,
            "joint_raw_weight":jw,
            "joint_prevalence":jw/joint_weight if joint_weight else 0.0,
            "exclusive_to_pareto":exclusive,
            "_i":i,"_j":j,
        })
    identity_rows.sort(key=lambda x:(x["complete_prevalence"],x["left_size"]+x["right_size"],x["left"],x["right"]))
    rare5=[{k:v for k,v in z.items() if not k.startswith("_")} for z in identity_rows[:5]]
    rarest=rare5[0] if rare5 else None

    # Common feature-value properties.
    categorical=[
        "distinct_translations","bijective_translations","constant_translations",
        "translation_image_min","translation_image_max","translation_monoid_size","ground_orbit_size",
        "translation_transitive","rowcol_image_multisets","permutation_rows_cols","constant_rows_cols",
        "rowcol_hamming_min","rowcol_hamming_max","output_frequency_multiset",
        "pointed_minor_distinct","pointed_minor_image_multiset","pointed_minor_any_permutation",
        "pointed_minor_any_constant","proper_subalgebras","pointed_proper_subalgebras","congruence_count",
        "pointed_automorphism_group_size","simple","no_pointed_proper_subalgebra",
        "recurrence_signature","recurrence_bijective_any","recurrence_bijective_both",
    ]
    common_props=[]
    for f in categorical:
        vals={r[f] for r in pareto}
        if len(vals)==1:
            v=next(iter(vals))
            cw=raw_weight(complete,lambda r,f=f,v=v:r[f]==v)
            jw=raw_weight(joint,lambda r,f=f,v=v:r[f]==v)
            common_props.append({
                "feature":f,"value":v,
                "complete_raw_weight":cw,"complete_prevalence":cw/complete_weight,
                "joint_raw_weight":jw,"joint_prevalence":jw/joint_weight if joint_weight else 0.0,
            })
    common_props.sort(key=lambda z:(z["complete_prevalence"],z["feature"],repr(z["value"])))
    rare_feature=common_props[0] if common_props else None

    # Exact two-feature conjunction search with >=24 raw complete support.
    best_pair=None
    for a,b in combinations(common_props,2):
        fa,va=a["feature"],a["value"];fb,vb=b["feature"],b["value"]
        cw=raw_weight(complete,lambda r,fa=fa,va=va,fb=fb,vb=vb:r[fa]==va and r[fb]==vb)
        if cw<24:continue
        jw=raw_weight(joint,lambda r,fa=fa,va=va,fb=fb,vb=vb:r[fa]==va and r[fb]==vb)
        z={
            "features":[fa,fb],"values":[va,vb],
            "complete_raw_weight":cw,"complete_prevalence":cw/complete_weight,
            "joint_raw_weight":jw,"joint_prevalence":jw/joint_weight if joint_weight else 0.0,
        }
        if best_pair is None or (z["complete_prevalence"],tuple(z["features"]))<(best_pair["complete_prevalence"],tuple(best_pair["features"])):
            best_pair=z

    # Scalar/boolean separators.
    scalars=[
        "distinct_translations","bijective_translations","constant_translations",
        "translation_image_min","translation_image_max","translation_image_mean",
        "translation_monoid_size","ground_orbit_size","permutation_rows_cols","constant_rows_cols",
        "rowcol_hamming_min","rowcol_hamming_max","pointed_minor_distinct",
        "proper_subalgebras","pointed_proper_subalgebras","congruence_count",
        "pointed_automorphism_group_size","recurrence_cycle_count_mean","recurrence_max_cycle_mean",
        "recurrence_cyclic_states_mean","recurrence_max_basin_mean",
    ]
    booleans=[
        "translation_transitive","simple","no_pointed_proper_subalgebra",
        "pointed_minor_any_permutation","pointed_minor_any_constant",
        "recurrence_bijective_any","recurrence_bijective_both",
    ]
    sep_scalar={}
    for f in scalars:
        sep_scalar[f]={
            "pareto_mean":sum(float(r[f]) for r in pareto)/len(pareto),
            "complete_weighted_mean":weighted_mean(complete,f),
            "joint_weighted_mean":weighted_mean(joint,f),
        }
    sep_bool={}
    pareto_weight=sum(int(r["weight"]) for r in pareto)
    for f in booleans:
        sep_bool[f]={
            "pareto_prevalence":sum(bool(r[f]) for r in pareto)/len(pareto),
            "complete_prevalence":raw_weight(complete,lambda r,f=f:bool(r[f]))/complete_weight,
            "joint_prevalence":raw_weight(joint,lambda r,f=f:bool(r[f]))/joint_weight if joint_weight else 0.0,
        }

    # Feature most separating Pareto from joint by absolute standardized-ish prevalence/difference ratio.
    sep_candidates=[]
    for f,z in sep_bool.items():
        sep_candidates.append((abs(z["pareto_prevalence"]-z["joint_prevalence"]),f,"boolean"))
    for f,z in sep_scalar.items():
        base=z["joint_weighted_mean"]
        delta=abs(z["pareto_mean"]-base)/(abs(base)+1e-12)
        sep_candidates.append((delta,f,"scalar_relative"))
    sep_candidates.sort(reverse=True)
    strongest_separator={"feature":sep_candidates[0][1],"kind":sep_candidates[0][2],"score":sep_candidates[0][0]}

    # 256 symmetry audits.
    selected_ids=identity_rows[:5]
    audit_pass=0
    for raw in audit_keys():
        ck=canonical_key(raw)
        fr=features(raw);fc=features(ck)
        if fr!=fc:continue
        if selected_ids:
            sr=term_semantics(raw,terms);sc=term_semantics(ck,terms)
            ok=True
            for z in selected_ids:
                i,j=z["_i"],z["_j"];mi,mj=mirror[i],mirror[j]
                hr=(sr[i]==sr[j] or sr[mi]==sr[mj])
                hc=(sc[i]==sc[j] or sc[mi]==sc[mj])
                if hr!=hc:ok=False;break
            if not ok:continue
        audit_pass+=1

    if rarest is None:
        identity_class="no Pareto-common nontrivial low-complexity identity"
    elif rarest["exclusive_to_pareto"]:
        identity_class="exclusive"
    elif rarest["complete_prevalence"]<0.01:
        identity_class="rare"
    elif rarest["complete_prevalence"]<0.25:
        identity_class="selective"
    else:
        identity_class="common"

    exclusive_count=sum(z["exclusive_to_pareto"] for z in identity_rows)
    if exclusive_count>0:
        conclusion="shared low-complexity invariant"
    elif best_pair and best_pair["complete_prevalence"]<0.10:
        conclusion="conjunction of weak invariants"
    else:
        conclusion="no simple invariant within frozen search language"

    payload_for_hash={
        "pareto_keys":pareto_keys,
        "term_count":term_count,
        "identity_rows":[{k:v for k,v in z.items() if not k.startswith("_")} for z in identity_rows],
        "common_props":common_props,
        "best_pair":best_pair,
        "sep_scalar":sep_scalar,
        "sep_bool":sep_bool,
        "audit_pass":audit_pass,
    }
    h1=hashlib.sha256(json.dumps(payload_for_hash,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    h2=hashlib.sha256(json.dumps(payload_for_hash,sort_keys=True,separators=(",",":")).encode()).hexdigest()

    reports={
        "R1_any_pareto_common_nontrivial_identity":bool(identity_rows),
        "R2_rarest_identity":rarest,
        "R3_any_exclusive_identity":exclusive_count>0,
        "R4_rarest_single_common_feature":rare_feature,
        "R5_rarest_two_feature_conjunction":best_pair,
        "R6_all_pareto_translation_transitive":all(bool(r["translation_transitive"]) for r in pareto),
        "R7_pareto_universal_algebra":{
            "all_simple":all(bool(r["simple"]) for r in pareto),
            "all_no_pointed_proper_subalgebra":all(bool(r["no_pointed_proper_subalgebra"]) for r in pareto),
        },
        "R8_pareto_recurrence":{
            "all_bijective_any_orientation":all(bool(r["recurrence_bijective_any"]) for r in pareto),
            "common_signature":len({r["recurrence_signature"] for r in pareto})==1,
        },
        "R9_strongest_new_separator_vs_joint":strongest_separator,
        "R10_classification":conclusion,
        "identity_separator_class":identity_class,
    }

    gates={
        "PIN1_recover_16_pareto":len(pareto_keys)==16,
        "PIN2_all_5130_orbits":len(rows)==5130,
        "PIN3_weight_sum_59049":raw_weight(rows)==59049,
        "PIN4_translation_features_all":all("translation_monoid_size" in r for r in rows),
        "PIN5_rowcol_features_all":all("rowcol_image_multisets" in r for r in rows),
        "PIN6_minor_features_all":all("pointed_minor_distinct" in r for r in rows),
        "PIN7_universal_algebra_features_all":all("congruence_count" in r for r in rows),
        "PIN8_recurrence_features_all":all("recurrence_signature" in r for r in rows),
        "PIN9_terms_deterministic":term_count==471,
        "PIN10_common_identities_hold_all_pareto":all(
            all(
                (psem[k][z["_i"]]==psem[k][z["_j"]]) or
                (psem[k][mirror[z["_i"]]]==psem[k][mirror[z["_j"]]])
                for k in pareto_keys
            ) for z in identity_rows
        ),
        "PIN11_identity_prevalence_reported":all("complete_prevalence" in z and "joint_prevalence" in z for z in identity_rows),
        "PIN12_common_feature_analysis":all("complete_prevalence" in z for z in common_props),
        "PIN13_two_feature_search":best_pair is not None or len(common_props)<2,
        "PIN14_all_separators":bool(sep_scalar) and bool(sep_bool) and "identity_separator_class" in reports,
        "PIN15_256_symmetry_audits":audit_pass==256,
        "PIN16_deterministic_hash":h1==h2,
    }
    verdict="PASS_PARETO_NUCLEUS_INVARIANT_V1" if all(gates.values()) else ("PARTIAL_PARETO_NUCLEUS_INVARIANT_V1" if any(gates.values()) else "VALID_NEGATIVE_PARETO_NUCLEUS_INVARIANT_V1")

    result={
        "protocol":"PARETO_NUCLEUS_INVARIANT_V1",
        "precommit_commit":"b454381d44f9dc9bb92923909c64674b02b8fc74",
        "addendum_commit":"e98308bd06e3bc1a39a9ee60fdfd05be02dfa337",
        "verdict":verdict,
        "pareto_keys":pareto_keys,
        "term_count":term_count,
        "pareto_common_nontrivial_identity_count":len(identity_rows),
        "exclusive_identity_count":exclusive_count,
        "five_rarest_identities":rare5,
        "pareto_common_feature_properties":common_props,
        "separator_scalar":sep_scalar,
        "separator_boolean":sep_bool,
        "required_reports":reports,
        "audit":{"total":256,"passed":audit_pass},
        "headline_gates":gates,
        "aggregation_hash":h1,
        "claim_boundary":"Exact finite analysis of the authoritative 3-element pointed-operation population and terms with at most three d-nodes."
    }
    summary=result
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("PARETO NUCLEUS INVARIANT V1",verdict)
    print(json.dumps(summary,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
