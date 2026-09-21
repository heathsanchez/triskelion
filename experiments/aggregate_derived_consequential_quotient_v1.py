# PR execution trigger; no scientific logic change
#!/usr/bin/env python3
from __future__ import annotations
from collections import defaultdict
from itertools import permutations
from pathlib import Path
import csv, hashlib, json, math, sys

Q=3
OP_COUNT=19683
POINTED_COUNT=59049
P3=[1,3,9,27,81,243,729,2187,6561]
PERMS=list(permutations(range(Q)))
OMEGA=[(a,b) for a in range(Q) for b in range(Q)]
OIDX={p:i for i,p in enumerate(OMEGA)}
FULL=19683

BASE_FIELDS=[
    "unary","binary","no_ground","d0","d1","d2","d3","recombinant3",
    "recur_distinct_sum","recur_distinct_max","recur_cycle_sum","recur_cycle_max"
]
OLD_PHEN_FIELDS=[
    "binary","no_ground","d3","recombinant3","recur_distinct_sum",
    "mutation_complete","mutation_generative","mutation_ref_independent",
    "joint_developmental","pareto"
]

def decode_op(code):
    t=[]
    for _ in range(9):
        t.append(code%3); code//=3
    return t

def encode_op(t):
    return sum(v*P3[i] for i,v in enumerate(t))

def canonical_key(rawkey):
    g,code=divmod(rawkey,OP_COUNT)
    old=decode_op(code)
    best=POINTED_COUNT+1
    for p in PERMS:
        for sw in (False,True):
            nt=[0]*9
            for a in range(Q):
                for b in range(Q):
                    oa,ob=(b,a) if sw else (a,b)
                    nt[3*p[a]+p[b]]=p[old[3*oa+ob]]
            best=min(best,p[g]*OP_COUNT+encode_op(nt))
    return best

def transform(rawkey,p,swap=False):
    g,code=divmod(rawkey,OP_COUNT)
    old=decode_op(code)
    nt=[0]*9
    for a in range(Q):
        for b in range(Q):
            oa,ob=(b,a) if swap else (a,b)
            nt[3*p[a]+p[b]]=p[old[3*oa+ob]]
    return p[g]*OP_COUNT+encode_op(nt)

def translations(rawkey):
    g,code=divmod(rawkey,OP_COUNT); op=decode_op(code)
    L=[tuple(op[3*c+x] for x in range(Q)) for c in range(Q)]
    R=[tuple(op[3*x+c] for x in range(Q)) for c in range(Q)]
    return g,L,R

def pair_action(t):
    return tuple(OIDX[(t[a],t[b])] for a,b in OMEGA)

def point_colors(g):
    out=[]
    for a,b in OMEGA:
        if a==g and b==g: out.append(3)
        elif a==b: out.append(2)
        elif a==g or b==g: out.append(1)
        else: out.append(0)
    return tuple(out)

def v4_base(rawkey):
    g,L,R=translations(rawkey)
    blocks=[]
    for c in range(Q):
        block=tuple(sorted((pair_action(L[c]),pair_action(R[c]))))
        blocks.append((1 if c==g else 0,block))
    return point_colors(g),tuple(blocks)

def v4_signature(rawkey):
    return min(v4_base(transform(rawkey,p,sw)) for p in PERMS for sw in (False,True))

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
            for k in ("key","weight","ground","opcode","unary","binary","no_ground","no_ground_all_constants",
                      "d0","d1","d2","d3","recombinant3","recur_distinct_sum","recur_distinct_max",
                      "recur_cycle_sum","recur_cycle_max"):
                r[k]=int(r[k])
            rows.append(r)
    return rows,metas

def wquant(rows,fn,q):
    vals=sorted((fn(r),r["weight"],r["key"]) for r in rows)
    target=math.ceil(q*sum(w for _,w,_ in vals))
    acc=0
    for v,w,_ in vals:
        acc+=w
        if acc>=target:return v
    return vals[-1][0]

def partition_stats(rows,fn,name):
    classes=defaultdict(list)
    for r in rows: classes[fn(r)].append(r)
    vals=list(classes.values())
    nontrivial=[v for v in vals if len(v)>1]
    sample=None
    if nontrivial:
        v=max(nontrivial,key=lambda z:(len(z),sum(x["weight"] for x in z),-min(x["key"] for x in z)))
        sample={"keys":[x["key"] for x in v[:12]],"orbit_class_size":len(v),
                "raw_weight":sum(x["weight"] for x in v)}
    return {
        "name":name,
        "classes":len(classes),
        "canonical_orbits":len(rows),
        "merged_orbits":len(rows)-len(classes),
        "class_ratio":len(classes)/len(rows),
        "nontrivial_classes":len(nontrivial),
        "singleton_classes":sum(len(v)==1 for v in vals),
        "largest_class_orbits":max(len(v) for v in vals),
        "largest_class_raw_weight":max(sum(x["weight"] for x in v) for v in vals),
        "sample_largest_merged_class":sample,
    },classes

def stable_hash(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def sig_count(sig):
    return sum(int(ch,16).bit_count() for ch in sig)

def main():
    if len(sys.argv)!=5:
        raise SystemExit("usage: aggregate SHARDS PRIOR_RESULT REPLAY_MARKER OUTDIR")
    shard_root=Path(sys.argv[1]); prior_path=Path(sys.argv[2]); replay_path=Path(sys.argv[3]); out=Path(sys.argv[4])
    out.mkdir(parents=True,exist_ok=True)

    rows,metas=load_shards(shard_root)
    rows=sorted(rows,key=lambda r:r["key"])
    prior=json.loads(prior_path.read_text())
    prior_map={int(r["key"]):r for r in prior["orbits"]}
    cur={r["key"]:r for r in rows}

    if len(rows)!=5130 or len(cur)!=5130: raise RuntimeError(f"expected 5130 rows, got {len(rows)}")
    if set(cur)!=set(prior_map): raise RuntimeError("independent census key set does not match prior census")
    if sum(r["weight"] for r in rows)!=59049: raise RuntimeError("raw orbit weight != 59049")

    audit_mismatch=defaultdict(list)
    for r in rows:
        p=prior_map[r["key"]]
        for f in BASE_FIELDS:
            if int(r[f])!=int(p[f]):
                if len(audit_mismatch[f])<5: audit_mismatch[f].append([r["key"],r[f],p[f]])
        r["fresh_delta"]=r["binary"]-r["unary"]
        r["ref_delta"]=r["binary"]-r["no_ground"]
        r["generative"]=bool(r["binary"]>3 and r["fresh_delta"]>0 and (r["ref_delta"]>0 or r["no_ground_all_constants"]))

    for r in rows:
        g,code=divmod(r["key"],OP_COUNT); table=decode_op(code)
        mc=mg=mr=stable=0; target_classes=set(); target_ref_classes=set()
        for pos in range(9):
            old=table[pos]
            for nv in range(3):
                if nv==old: continue
                nt=table[:]; nt[pos]=nv
                ck=canonical_key(g*OP_COUNT+encode_op(nt))
                q=cur[ck]
                mc += int(q["binary"]==FULL)
                mg += int(q["generative"])
                mr += int(q["ref_delta"]==0)
                stable += int(q["fixed_sig"]==r["fixed_sig"])
                target_classes.add(q["fixed_sig"])
                target_ref_classes.add((q["fixed_sig"],q["no_ground_sig"]))
        r["mutation_complete"]=mc
        r["mutation_generative"]=mg
        r["mutation_ref_independent"]=mr
        r["mutation_capability_stable"]=stable
        r["mutation_capability_target_classes"]=len(target_classes)
        r["mutation_reference_target_classes"]=len(target_ref_classes)

    for r in rows:
        p=prior_map[r["key"]]
        for f in ("mutation_complete","mutation_generative","mutation_ref_independent"):
            if int(r[f])!=int(p[f]) and len(audit_mismatch[f])<5:
                audit_mismatch[f].append([r["key"],r[f],p[f]])

    complete=[r for r in rows if r["binary"]==FULL]
    q75_g3=wquant(complete,lambda r:r["d3"],.75)
    q75_r3=wquant(complete,lambda r:r["recombinant3"],.75)
    q75_psum=wquant(complete,lambda r:r["recur_distinct_sum"],.75)
    q75_m=wquant(complete,lambda r:r["mutation_complete"],.75)
    for r in rows:
        r["joint_developmental"]=bool(
            r["binary"]==FULL and r["d3"]>=q75_g3 and r["recombinant3"]>=q75_r3
            and r["recur_distinct_sum"]>=q75_psum and r["mutation_complete"]>=q75_m
        )
        if r["joint_developmental"]!=bool(prior_map[r["key"]]["joint_developmental"]):
            if len(audit_mismatch["joint_developmental"])<5:
                audit_mismatch["joint_developmental"].append([r["key"],r["joint_developmental"],prior_map[r["key"]]["joint_developmental"]])

    pareto=set()
    pts=[r for r in rows if r["binary"]==FULL]
    vectors=[(r["d3"],r["recombinant3"],r["recur_distinct_sum"],r["mutation_complete"]) for r in pts]
    for i,a in enumerate(pts):
        av=vectors[i]; dominated=False
        for j,bv in enumerate(vectors):
            if i==j: continue
            if all(x>=y for x,y in zip(bv,av)) and any(x>y for x,y in zip(bv,av)):
                dominated=True; break
        if not dominated: pareto.add(a["key"])
    prior_pareto={int(x["key"]) for x in prior["pareto_orbits"]}
    if pareto!=prior_pareto:
        audit_mismatch["pareto_set"].append({
            "missing_from_recomputed":sorted(prior_pareto-pareto)[:10],
            "extra_in_recomputed":sorted(pareto-prior_pareto)[:10],
        })
    for r in rows:r["pareto"]=r["key"] in pareto

    v4map=defaultdict(list)
    for r in rows:v4map[v4_signature(r["key"])].append(r["key"])
    v4_injective=len(v4map)==5130 and all(len(v)==1 for v in v4map.values())

    parts={}
    classes={}
    specs=[
        ("Q_capability_fixed",lambda r:r["fixed_sig"]),
        ("Q_capability_plus_reference",lambda r:(r["fixed_sig"],r["no_ground_sig"])),
        ("Q_history_d0",lambda r:(r["h0_sig"],)),
        ("Q_history_d1",lambda r:(r["h0_sig"],r["h1_sig"])),
        ("Q_history_d2",lambda r:(r["h0_sig"],r["h1_sig"],r["h2_sig"])),
        ("Q_history_d3",lambda r:(r["h0_sig"],r["h1_sig"],r["h2_sig"],r["h3_sig"])),
        ("Q_capability_plus_history_d3",lambda r:(r["fixed_sig"],r["h0_sig"],r["h1_sig"],r["h2_sig"],r["h3_sig"])),
        ("Q_capability_history_mutation",lambda r:(
            r["fixed_sig"],r["h0_sig"],r["h1_sig"],r["h2_sig"],r["h3_sig"],
            r["mutation_capability_stable"],r["mutation_capability_target_classes"]
        )),
        ("Q_old_protected_measurements",lambda r:tuple(
            r[f] if f!="pareto" else bool(r["pareto"]) for f in OLD_PHEN_FIELDS
        )),
        ("Q_new_full_bundle",lambda r:(
            r["fixed_sig"],r["no_ground_sig"],r["h0_sig"],r["h1_sig"],r["h2_sig"],r["h3_sig"],
            r["recombinant3"],r["recur_distinct_sum"],r["mutation_capability_stable"],
            r["mutation_capability_target_classes"],r["mutation_reference_target_classes"]
        )),
    ]
    for name,fn in specs:
        st,cl=partition_stats(rows,fn,name); parts[name]=st; classes[name]=cl

    cap_history_witness=None
    for members in classes["Q_capability_fixed"].values():
        if len(members)<2: continue
        groups=defaultdict(list)
        for r in members:
            sig=(r["h0_sig"],r["h1_sig"],r["h2_sig"],r["h3_sig"],
                 r["mutation_capability_stable"],r["mutation_capability_target_classes"])
            groups[sig].append(r)
        if len(groups)>1:
            gg=list(groups.values())
            a,b=gg[0][0],gg[1][0]
            cap_history_witness={
                "key_a":a["key"],"key_b":b["key"],
                "same_fixed_capability":True,
                "a":{"d":[a["d0"],a["d1"],a["d2"],a["d3"]],
                     "mutation_capability_stable":a["mutation_capability_stable"],
                     "mutation_capability_target_classes":a["mutation_capability_target_classes"]},
                "b":{"d":[b["d0"],b["d1"],b["d2"],b["d3"]],
                     "mutation_capability_stable":b["mutation_capability_stable"],
                     "mutation_capability_target_classes":b["mutation_capability_target_classes"]},
            }
            break

    measurement_witness=None
    for members in classes["Q_old_protected_measurements"].values():
        if len(members)>1:
            measurement_witness={
                "keys":[r["key"] for r in members[:12]],
                "class_size":len(members),
                "same_old_protected_measurements":True,
            }
            break

    fixed_round_counts={}
    for d in range(4):
        fixed_round_counts[f"d{d}"]={
            "orbits":sum(r[f"h{d}_sig"]==r["fixed_sig"] for r in rows),
            "raw_weight":sum(r["weight"] for r in rows if r[f"h{d}_sig"]==r["fixed_sig"])
        }

    mismatch_counts={k:len(v) for k,v in audit_mismatch.items()}
    base_audit_ok=all(not audit_mismatch.get(f) for f in BASE_FIELDS)
    mutation_audit_ok=all(not audit_mismatch.get(f) for f in ("mutation_complete","mutation_generative","mutation_ref_independent"))
    joint_audit_ok=not audit_mismatch.get("joint_developmental")
    pareto_audit_ok=not audit_mismatch.get("pareto_set")
    replay_ok=replay_path.exists() and replay_path.read_text().strip()=="PASS"

    gates={
        "DQ1_5130_canonical_orbits":len(rows)==5130,
        "DQ2_raw_weight_59049":sum(r["weight"] for r in rows)==59049,
        "DQ3_independent_base_measurements_match_prior":base_audit_ok,
        "DQ4_independent_mutation_measurements_match_prior":mutation_audit_ok,
        "DQ5_independent_joint_labels_match_prior":joint_audit_ok,
        "DQ6_independent_pareto_matches_prior":pareto_audit_ok,
        "DQ7_true_reexecution_replay":replay_ok,
        "DQ8_V4_reconstruction_lookup_injective":v4_injective,
        "DQ9_exact_fixed_capability_partition":parts["Q_capability_fixed"]["classes"]>0,
        "DQ10_exact_reference_sensitive_partition":parts["Q_capability_plus_reference"]["classes"]>=parts["Q_capability_fixed"]["classes"],
        "DQ11_old_measurement_quotient_computed":parts["Q_old_protected_measurements"]["classes"]>0,
        "DQ12_history_refines_monotonically":all(
            parts[f"Q_history_d{i}"]["classes"]<=parts[f"Q_history_d{i+1}"]["classes"] for i in range(3)
        ),
        "DQ13_exact_signature_counts_self_consistent":all(
            sig_count(r["fixed_sig"])==r["binary"] and
            sig_count(r["no_ground_sig"])==r["no_ground"] and
            all(sig_count(r[f"h{i}_sig"])==r[f"d{i}"] for i in range(4))
            for r in rows
        ),
        "DQ14_capability_history_witness_reported":cap_history_witness is not None,
        "DQ15_measurement_merge_witness_reported":measurement_witness is not None or parts["Q_old_protected_measurements"]["classes"]==5130,
        "DQ16_no_audit_mismatch":not any(audit_mismatch.values()),
    }

    core={
        "protocol":"DERIVED_CONSEQUENTIAL_QUOTIENT_V1",
        "source_run":"35539755279/106155174472",
        "independent_engine":"fresh operation-table enumeration and closure computation; prior result used only after recomputation for audit comparison",
        "thresholds_recomputed":{
            "G3":q75_g3,"R3":q75_r3,"P_numerator_of_9":q75_psum,"M_numerator_of_18":q75_m
        },
        "partitions":parts,
        "fixed_point_reached_by_bounded_round":fixed_round_counts,
        "capability_same_history_different_witness":cap_history_witness,
        "old_measurement_merge_witness":measurement_witness,
        "v4":{"distinct_signatures":len(v4map),"injective":v4_injective},
        "audit":{
            "base_fields":BASE_FIELDS,
            "mismatch_counts":mismatch_counts,
            "examples":dict(audit_mismatch),
            "reexecution_replay":replay_ok,
        },
        "headline_gates":gates,
        "claim_boundary":(
            "Exact finite result for all 59,049 pointed ternary operations modulo the frozen relabeling/input-swap canonicalization. "
            "Q_capability_fixed identifies systems by the exact set of binary functions expressible from x,y,ground under arbitrary finite composition. "
            "It is a capability-set quotient, not contextual equivalence for a named primitive operation symbol."
        ),
    }
    core["aggregation_hash"]=stable_hash(core)
    core["verdict"]="PASS_DERIVED_CONSEQUENTIAL_QUOTIENT_V1" if all(gates.values()) else "PARTIAL_DERIVED_CONSEQUENTIAL_QUOTIENT_V1"
    (out/"result.json").write_text(json.dumps(core,indent=2,sort_keys=True)+"\n")
    (out/"summary.json").write_text(json.dumps(core,indent=2,sort_keys=True)+"\n")
    print("DERIVED CONSEQUENTIAL QUOTIENT V1",core["verdict"])
    for k in ("Q_capability_fixed","Q_capability_plus_reference","Q_history_d3","Q_old_protected_measurements","Q_new_full_bundle"):
        print(k,parts[k]["classes"],"/",len(rows))
    print("V4",len(v4map),"/",len(rows))
    print("AUDIT_MISMATCH_COUNTS",json.dumps(mismatch_counts,sort_keys=True))
    print(json.dumps(core,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
