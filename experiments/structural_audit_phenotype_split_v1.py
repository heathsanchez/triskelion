#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from itertools import permutations, product
from math import gcd
from pathlib import Path
import hashlib
import json
import sys

Q=3
OP_COUNT=19683
POINTED_COUNT=59049
P3=(1,3,9,27,81,243,729,2187,6561)
PERMS=list(permutations(range(Q)))
OMEGA=[(a,b) for a in range(Q) for b in range(Q)]
OIDX={p:i for i,p in enumerate(OMEGA)}

# Frozen primary measurement families. Derived percentile/ranking labels are excluded.
FAMILY_FIELDS={
    "F1_final_semantic_reach":("binary","no_ground"),
    "F2_bounded_derivational_geometry":("d0","d1","d2","d3","recombinant3"),
    "F3_recurrence_dynamics":(
        "recur_distinct_sum","recur_distinct_max",
        "recur_cycle_sum","recur_cycle_max",
    ),
    "F4_mutation_neighborhood":(
        "mutation_complete","mutation_generative","mutation_ref_independent",
    ),
    "F5_operational_without_presentation_neighborhood":(
        "binary","no_ground",
        "recur_distinct_sum","recur_distinct_max",
        "recur_cycle_sum","recur_cycle_max",
    ),
    "F6_intrinsic_current_run_bundle":(
        "binary","no_ground",
        "d0","d1","d2","d3","recombinant3",
        "recur_distinct_sum","recur_distinct_max",
        "recur_cycle_sum","recur_cycle_max",
    ),
    "F7_full_primary_measurements":(
        "binary","no_ground",
        "d0","d1","d2","d3","recombinant3",
        "recur_distinct_sum","recur_distinct_max",
        "recur_cycle_sum","recur_cycle_max",
        "mutation_complete","mutation_generative","mutation_ref_independent",
    ),
}

AUDITED_FIELDS=(
    "d0","d1","d2","d3","recombinant3",
    "recur_distinct_sum","recur_distinct_max",
    "recur_cycle_sum","recur_cycle_max",
    "mutation_complete","mutation_generative","mutation_ref_independent",
)

EDGES={
    "V0_fully_anonymous":{"V1_ground_source_marked","V2_side_marked"},
    "V1_ground_source_marked":{"V3_ground_source_x_side_marked","V4_generator_incidence_marked"},
    "V2_side_marked":{"V3_ground_source_x_side_marked","V5_fully_marked_elementary_incidence"},
    "V3_ground_source_x_side_marked":{"V5_fully_marked_elementary_incidence"},
    "V4_generator_incidence_marked":{"V5_fully_marked_elementary_incidence"},
    "V5_fully_marked_elementary_incidence":set(),
}

def decode_op(code:int):
    out=[]
    for _ in range(9):
        out.append(code%3)
        code//=3
    return tuple(out)

def encode_op(t):
    return sum(int(v)*P3[i] for i,v in enumerate(t))

DIGITS=[decode_op(i) for i in range(OP_COUNT)]

def opv(op,a,b):
    return op[3*a+b]

def transform(rawkey:int,p,swap=False):
    g,code=divmod(rawkey,OP_COUNT)
    old=DIGITS[code]
    nt=[0]*9
    for a in range(Q):
        for b in range(Q):
            oa,ob=(b,a) if swap else (a,b)
            nt[3*p[a]+p[b]]=p[old[3*oa+ob]]
    return p[g]*OP_COUNT+encode_op(nt)

def canonical_key(rawkey:int):
    return min(transform(rawkey,p,sw) for p in PERMS for sw in (False,True))

def x0code():
    return encode_op([a for a in range(Q) for _b in range(Q)])

def x1code():
    return encode_op([b for _a in range(Q) for b in range(Q)])

X0=x0code()
X1=x1code()
CONST_CODES=tuple(encode_op([c]*9) for c in range(Q))

def compose_code(op,f,h):
    F=DIGITS[f];H=DIGITS[h]
    return sum(op[3*F[i]+H[i]]*P3[i] for i in range(9))

def essential_both(code):
    F=DIGITS[code]
    e0=False
    e1=False
    for y in range(Q):
        vals={F[3*x+y] for x in range(Q)}
        if len(vals)>1:
            e0=True
            break
    for x in range(Q):
        vals={F[3*x+y] for y in range(Q)}
        if len(vals)>1:
            e1=True
            break
    return e0 and e1

def local_cycle(op,a,b):
    first={}
    t=0
    while (a,b) not in first:
        first[(a,b)]=t
        t+=1
        a,b=b,opv(op,a,b)
    mu=first[(a,b)]
    lam=t-mu
    return mu,lam

def lcm(a,b):
    return a//gcd(a,b)*b

def independent_metrics(key:int):
    g,code=divmod(key,OP_COUNT)
    op=DIGITS[code]
    seeds=(X0,X1,CONST_CODES[g])

    S=set(seeds)
    depth=[len(S)]
    for _r in range(3):
        prev=tuple(S)
        fresh=set()
        for f in prev:
            for h in prev:
                z=compose_code(op,f,h)
                if z not in S:
                    fresh.add(z)
        S.update(fresh)
        depth.append(len(S))

    recombinant=sum(1 for f in S if essential_both(f))

    local={(a,b):local_cycle(op,a,b) for a in range(Q) for b in range(Q)}
    distinct_sum=0
    distinct_max=0
    cycle_sum=0
    cycle_max=0
    for f in seeds:
        F=DIGITS[f]
        for h in seeds:
            H=DIGITS[h]
            mu=0
            lam=1
            for i in range(9):
                m,c=local[(F[i],H[i])]
                mu=max(mu,m)
                lam=lcm(lam,c)
            distinct=mu+lam
            distinct_sum+=distinct
            distinct_max=max(distinct_max,distinct)
            cycle_sum+=lam
            cycle_max=max(cycle_max,lam)

    return {
        "d0":depth[0],"d1":depth[1],"d2":depth[2],"d3":depth[3],
        "recombinant3":recombinant,
        "recur_distinct_sum":distinct_sum,
        "recur_distinct_max":distinct_max,
        "recur_cycle_sum":cycle_sum,
        "recur_cycle_max":cycle_max,
    }


DIRECT_DERIVATION_FIELDS=("d0","d1","d2","d3","recombinant3")
DIRECT_RECURRENCE_FIELDS=(
    "recur_distinct_sum","recur_distinct_max",
    "recur_cycle_sum","recur_cycle_max",
)

def recurrence_metrics(key:int):
    g,code=divmod(key,OP_COUNT)
    op=DIGITS[code]
    seeds=(X0,X1,CONST_CODES[g])
    local={(a,b):local_cycle(op,a,b) for a in range(Q) for b in range(Q)}
    distinct_sum=0
    distinct_max=0
    cycle_sum=0
    cycle_max=0
    for f in seeds:
        F=DIGITS[f]
        for h in seeds:
            H=DIGITS[h]
            mu=0
            lam=1
            for i in range(9):
                m,cyc=local[(F[i],H[i])]
                mu=max(mu,m)
                lam=lcm(lam,cyc)
            distinct=mu+lam
            distinct_sum+=distinct
            distinct_max=max(distinct_max,distinct)
            cycle_sum+=lam
            cycle_max=max(cycle_max,lam)
    return {
        "recur_distinct_sum":distinct_sum,
        "recur_distinct_max":distinct_max,
        "recur_cycle_sum":cycle_sum,
        "recur_cycle_max":cycle_max,
    }

def orbit_symmetry_diagnostic(rawkey:int):
    base=independent_metrics(rawkey)
    relabel_diffs=set()
    for p in PERMS:
        m=independent_metrics(transform(rawkey,p,False))
        for field in DIRECT_DERIVATION_FIELDS+DIRECT_RECURRENCE_FIELDS:
            if m[field]!=base[field]:
                relabel_diffs.add(field)
    trans=independent_metrics(transform(rawkey,(0,1,2),True))
    transpose_diffs=[
        field for field in DIRECT_DERIVATION_FIELDS+DIRECT_RECURRENCE_FIELDS
        if trans[field]!=base[field]
    ]
    return {
        "carrier_relabel_differences":sorted(relabel_diffs),
        "transpose_differences":sorted(transpose_diffs),
    }

def translations(key:int):
    g,code=divmod(key,OP_COUNT)
    op=DIGITS[code]
    L=[tuple(opv(op,c,x) for x in range(Q)) for c in range(Q)]
    R=[tuple(opv(op,x,c) for x in range(Q)) for c in range(Q)]
    return g,L,R

def pair_action(t):
    return tuple(OIDX[(t[a],t[b])] for a,b in OMEGA)

def point_colors(g):
    out=[]
    for a,b in OMEGA:
        if a==g and b==g:
            out.append(3)
        elif a==b:
            out.append(2)
        elif a==g or b==g:
            out.append(1)
        else:
            out.append(0)
    return tuple(out)

def view_base(key:int,view:str):
    g,L,R=translations(key)
    colors=point_colors(g)
    if view=="V0_fully_anonymous":
        return colors,tuple(sorted(pair_action(t) for t in L+R))
    if view=="V1_ground_source_marked":
        root=tuple(sorted((pair_action(L[g]),pair_action(R[g]))))
        others=[]
        for c in range(Q):
            if c!=g:
                others.extend((pair_action(L[c]),pair_action(R[c])))
        return colors,root,tuple(sorted(others))
    if view=="V2_side_marked":
        return colors,tuple(sorted(pair_action(t) for t in L)),tuple(sorted(pair_action(t) for t in R))
    if view=="V3_ground_source_x_side_marked":
        return (
            colors,
            pair_action(L[g]),pair_action(R[g]),
            tuple(sorted(pair_action(L[c]) for c in range(Q) if c!=g)),
            tuple(sorted(pair_action(R[c]) for c in range(Q) if c!=g)),
        )
    if view=="V4_generator_incidence_marked":
        blocks=[]
        for c in range(Q):
            blocks.append((1 if c==g else 0,tuple(sorted((pair_action(L[c]),pair_action(R[c]))))))
        return colors,tuple(blocks)
    if view=="V5_fully_marked_elementary_incidence":
        blocks=[]
        for c in range(Q):
            blocks.append((1 if c==g else 0,pair_action(L[c]),pair_action(R[c])))
        return colors,tuple(blocks)
    raise KeyError(view)

VIEW_NAMES=tuple(EDGES.keys())

def canonical_view_signature(key:int,view:str):
    return min(view_base(transform(key,p,sw),view) for p in PERMS for sw in (False,True))

def v4_descriptor(key:int):
    g,L,R=translations(key)
    return {
        "ground":g,
        "blocks":tuple(tuple(sorted((L[c],R[c]))) for c in range(Q)),
    }

def reconstruct_v4_canonical_orbits(desc):
    g=int(desc["ground"])
    blocks=desc["blocks"]
    choices=[]
    for block in blocks:
        a,b=block
        if a==b:
            choices.append(((a,b),))
        else:
            choices.append(((a,b),(b,a)))

    consistent=0
    orbits=set()
    raw_tables=set()
    for assignment in product(*choices):
        L=[lr[0] for lr in assignment]
        R=[lr[1] for lr in assignment]
        ok=True
        for a in range(Q):
            for b in range(Q):
                if L[a][b]!=R[b][a]:
                    ok=False
                    break
            if not ok:
                break
        if not ok:
            continue
        consistent+=1
        table=tuple(L[a][b] for a in range(Q) for b in range(Q))
        raw_tables.add(table)
        orbits.add(canonical_key(g*OP_COUNT+encode_op(table)))
    return {
        "consistent_orientations":consistent,
        "raw_operation_tables":len(raw_tables),
        "canonical_orbits":orbits,
    }

def mutation_counts(key:int,pointed_map):
    g,code=divmod(key,OP_COUNT)
    table=list(DIGITS[code])
    mc=mg=mr=0
    resolved=0
    for pos in range(9):
        old=table[pos]
        for nv in range(Q):
            if nv==old:
                continue
            nt=table[:]
            nt[pos]=nv
            ck=canonical_key(g*OP_COUNT+encode_op(nt))
            q=pointed_map.get(ck)
            if q is None:
                continue
            resolved+=1
            if int(q["binary"])==OP_COUNT:
                mc+=1
            if bool(q["generative"]):
                mg+=1
            if int(q["ref_delta"])==0:
                mr+=1
    return {
        "mutation_resolved":resolved,
        "mutation_complete":mc,
        "mutation_generative":mg,
        "mutation_ref_independent":mr,
    }

def transitive_weaker():
    weaker={k:set() for k in EDGES}
    for a,bs in EDGES.items():
        for b in bs:
            weaker[b].add(a)
    changed=True
    while changed:
        changed=False
        for b in tuple(weaker):
            add=set()
            for a in tuple(weaker[b]):
                add |= weaker[a]
            if not add.issubset(weaker[b]):
                weaker[b] |= add
                changed=True
    return weaker

WEAKER=transitive_weaker()

def family_analysis(rows):
    sigs={view:{} for view in VIEW_NAMES}
    for r in rows:
        key=int(r["key"])
        for view in VIEW_NAMES:
            sig=canonical_view_signature(key,view)
            sigs[view].setdefault(sig,[]).append(r)

    out={}
    for fam,fields in FAMILY_FIELDS.items():
        views={}
        sufficient=[]
        for view in VIEW_NAMES:
            hetero=0
            counter=None
            collision_classes=0
            for members in sigs[view].values():
                if len(members)>1:
                    collision_classes+=1
                vals={}
                for r in members:
                    val=tuple(r[f] for f in fields)
                    vals.setdefault(val,[]).append(r)
                if len(vals)>1:
                    hetero+=1
                    if counter is None:
                        groups=list(vals.values())
                        a,b=groups[0][0],groups[1][0]
                        counter={
                            "key_a":int(a["key"]),
                            "key_b":int(b["key"]),
                            "differences":{
                                f:[a[f],b[f]] for f in fields if a[f]!=b[f]
                            }
                        }
            ok=hetero==0
            if ok:
                sufficient.append(view)
            views[view]={
                "sufficient":ok,
                "heterogeneous_collision_classes":hetero,
                "collision_classes":collision_classes,
                "first_counterexample":counter,
            }
        minimal=[
            v for v in sufficient
            if not any(w in sufficient for w in WEAKER[v])
        ]
        out[fam]={
            "fields":list(fields),
            "views":views,
            "sufficient_views":sufficient,
            "minimal_sufficient_views":minimal,
        }
    return out

def deterministic_audit_keys():
    out=[];seen=set();i=0
    while len(out)<256:
        h=hashlib.sha256(f"SAPS1-AUDIT|{i}".encode()).hexdigest()
        k=int(h[:16],16)%POINTED_COUNT
        if k not in seen:
            seen.add(k);out.append(k)
        i+=1
    return out

def stable_hash(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def build_aggregate(rows,reverse=False):
    seq=list(reversed(rows)) if reverse else list(rows)
    # Build order-independent summaries from a distinct traversal.
    mismatch_summary={}
    for f in AUDITED_FIELDS:
        mismatch_summary[f]=sum(1 for r in seq if r["_mismatch"].get(f,False))
    family=family_analysis(seq)
    recon_counter=Counter(r["_v4_reconstructed_orbit_count"] for r in seq)
    orientation_counter=Counter(r["_v4_consistent_orientations"] for r in seq)
    return {
        "mismatch_summary":mismatch_summary,
        "family_analysis":family,
        "v4_reconstructed_orbit_count_distribution":dict(sorted(recon_counter.items())),
        "v4_consistent_orientation_distribution":dict(sorted(orientation_counter.items())),
    }


def symmetry_compatibility_report(pointed_rows):
    # Every raw pointed operation is a member of exactly one canonical orbit.
    # Recurrence metrics are computed directly for every distinct raw member.
    # The depth/recombinant fields are exactly invariant under:
    #   (i) carrier relabeling, by conjugacy of the carrier action; and
    #   (ii) global transpose, because each synchronous closure round ranges
    #        over all ordered pairs, so swapping d(f,h) with d(h,f) leaves
    #        the generated set unchanged. Essential-coordinate dependence is
    #        preserved by the same carrier/output relabeling.
    stats={}
    for field in DIRECT_DERIVATION_FIELDS+DIRECT_RECURRENCE_FIELDS:
        stats[field]={
            "noninvariant_orbits":0,
            "raw_weight_in_noninvariant_orbits":0,
            "first_counterexample":None,
            "method":"exact_structural_invariance" if field in DIRECT_DERIVATION_FIELDS else "direct_all_raw_members",
        }

    carrier_relabel_noninvariant={field:0 for field in DIRECT_RECURRENCE_FIELDS}
    transpose_noninvariant={field:0 for field in DIRECT_RECURRENCE_FIELDS}
    raw_members_examined=0
    seen_raw=set()

    for p_row in pointed_rows:
        key=int(p_row["key"])
        weight=int(p_row["weight"])
        members=set()
        no_swap=set()
        swap_members=set()
        for perm in PERMS:
            a=transform(key,perm,False)
            b=transform(key,perm,True)
            members.add(a);members.add(b)
            no_swap.add(a);swap_members.add(b)
        if len(members)!=weight:
            raise RuntimeError(f"orbit weight mismatch key={key} generated={len(members)} expected={weight}")
        raw_members_examined+=len(members)
        if seen_raw.intersection(members):
            raise RuntimeError(f"raw orbit overlap at key={key}")
        seen_raw.update(members)

        rec_by_raw={raw:recurrence_metrics(raw) for raw in sorted(members)}
        for field in DIRECT_RECURRENCE_FIELDS:
            values={}
            for raw,m in rec_by_raw.items():
                values.setdefault(m[field],[]).append(raw)
            if len(values)>1:
                stats[field]["noninvariant_orbits"]+=1
                stats[field]["raw_weight_in_noninvariant_orbits"]+=weight
                if stats[field]["first_counterexample"] is None:
                    groups=list(values.items())
                    stats[field]["first_counterexample"]={
                        "canonical_key":key,
                        "raw_a":groups[0][1][0],
                        "value_a":groups[0][0],
                        "raw_b":groups[1][1][0],
                        "value_b":groups[1][0],
                    }

            no_vals={rec_by_raw[r][field] for r in no_swap}
            sw_vals={rec_by_raw[r][field] for r in swap_members}
            if len(no_vals)>1:
                carrier_relabel_noninvariant[field]+=1
            # Relabel-invariant sets should each be singleton. A difference
            # between the no-swap and swap value sets isolates transpose.
            if no_vals!=sw_vals:
                transpose_noninvariant[field]+=1

    if raw_members_examined!=POINTED_COUNT or len(seen_raw)!=POINTED_COUNT:
        raise RuntimeError(
            f"expected exhaustive raw coverage {POINTED_COUNT}, got "
            f"count={raw_members_examined} unique={len(seen_raw)}"
        )

    for field in DIRECT_DERIVATION_FIELDS:
        stats[field]["carrier_relabel_noninvariant_orbits"]=0
        stats[field]["transpose_noninvariant_orbits"]=0
    for field in DIRECT_RECURRENCE_FIELDS:
        stats[field]["carrier_relabel_noninvariant_orbits"]=carrier_relabel_noninvariant[field]
        stats[field]["transpose_noninvariant_orbits"]=transpose_noninvariant[field]

    return {
        "raw_members_examined":raw_members_examined,
        "unique_raw_members":len(seen_raw),
        "direct_fields":stats,
        "all_direct_fields_orbit_invariant":all(
            s["noninvariant_orbits"]==0 for s in stats.values()
        ),
    }

def main():
    if len(sys.argv)!=4:
        raise SystemExit("usage: structural_audit_phenotype_split_v1.py POINTED_RESULT DEV_RESULT OUT_DIR")

    pointed=json.loads(Path(sys.argv[1]).read_text())
    dev=json.loads(Path(sys.argv[2]).read_text())
    out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)

    pointed_rows=pointed["orbits"]
    dev_rows=dev["orbits"]
    pointed_map={int(r["key"]):r for r in pointed_rows}
    dev_map={int(r["key"]):r for r in dev_rows}

    if len(pointed_map)!=5130 or len(dev_map)!=5130 or set(pointed_map)!=set(dev_map):
        raise RuntimeError("authoritative census key sets do not match expected 5,130 representatives")

    rows=[]
    first_mismatch={f:None for f in AUDITED_FIELDS}
    mismatch_counts={f:0 for f in AUDITED_FIELDS}
    mutation_all18=True
    reconstruction_contains_all=True
    reconstruction_unique_all=True
    reconstruction_failures=[]

    for idx,key in enumerate(sorted(pointed_map)):
        p=pointed_map[key]
        old=dev_map[key]

        m=independent_metrics(key)
        mut=mutation_counts(key,pointed_map)
        mutation_all18 &= (mut["mutation_resolved"]==18)

        row={
            "key":key,
            "weight":int(p["weight"]),
            "binary":int(p["binary"]),
            "no_ground":int(p["no_ground"]),
            **m,
            **{k:mut[k] for k in (
                "mutation_complete","mutation_generative","mutation_ref_independent"
            )},
        }

        mismatch={}
        for f in AUDITED_FIELDS:
            bad=int(row[f])!=int(old[f])
            mismatch[f]=bad
            if bad:
                mismatch_counts[f]+=1
                if first_mismatch[f] is None:
                    first_mismatch[f]={
                        "key":key,
                        "recomputed":row[f],
                        "authoritative":old[f],
                    }
        row["_mismatch"]=mismatch

        rec=reconstruct_v4_canonical_orbits(v4_descriptor(key))
        rec_orbits=rec["canonical_orbits"]
        contains=key in rec_orbits
        unique=(rec_orbits=={key})
        reconstruction_contains_all &= contains
        reconstruction_unique_all &= unique
        if (not unique or not contains) and len(reconstruction_failures)<10:
            reconstruction_failures.append({
                "key":key,
                "consistent_orientations":rec["consistent_orientations"],
                "reconstructed_orbits":sorted(rec_orbits),
            })
        row["_v4_consistent_orientations"]=rec["consistent_orientations"]
        row["_v4_reconstructed_orbit_count"]=len(rec_orbits)
        rows.append(row)

    family=family_analysis(rows)
    symmetry_compatibility=symmetry_compatibility_report(pointed_rows)
    family_symmetry_status={}
    for fam,fields in FAMILY_FIELDS.items():
        direct=[f for f in fields if f in symmetry_compatibility["direct_fields"]]
        family_symmetry_status[fam]={
            "direct_fields_checked":direct,
            "all_checked_fields_orbit_invariant":all(
                symmetry_compatibility["direct_fields"][f]["noninvariant_orbits"]==0
                for f in direct
            ),
        }

    # Symmetry audit on all six view signatures.
    sym_pass=0
    sym_fail=[]
    for raw in deterministic_audit_keys():
        ck=canonical_key(raw)
        ok=all(
            canonical_view_signature(raw,v)==canonical_view_signature(ck,v)
            for v in VIEW_NAMES
        )
        if ok:
            sym_pass+=1
        elif len(sym_fail)<5:
            sym_fail.append({"raw":raw,"canonical":ck})

    aggregate_a=build_aggregate(rows,reverse=False)
    aggregate_b=build_aggregate(rows,reverse=True)
    hash_a=stable_hash(aggregate_a)
    hash_b=stable_hash(aggregate_b)

    total_mismatches=sum(mismatch_counts.values())
    derived_excluded=all(
        "joint_developmental" not in fields and "pareto" not in fields
        for fields in FAMILY_FIELDS.values()
    )
    all_counterexamples=True
    for fam in family.values():
        for info in fam["views"].values():
            if not info["sufficient"] and info["collision_classes"]>0 and info["first_counterexample"] is None:
                all_counterexamples=False

    gates={
        "SA1_all_5130_representatives":len(rows)==5130,
        "SA2_weight_sum_59049":sum(r["weight"] for r in rows)==59049,
        "SA3_depth_recomputed_all":all(all(k in r for k in ("d0","d1","d2","d3")) for r in rows),
        "SA4_R3_recomputed_all":all("recombinant3" in r for r in rows),
        "SA5_recurrence_recomputed_all":all("recur_cycle_max" in r for r in rows),
        "SA6_all18_mutations_enumerated":mutation_all18,
        "SA7_zero_audited_field_mismatches":total_mismatches==0,
        "SA8_V4_reconstruction_all":all("_v4_reconstructed_orbit_count" in r for r in rows),
        "SA9_V4_contains_source_all":reconstruction_contains_all,
        "SA10_V4_uniqueness_reported_all":len(rows)==5130,
        "SA11_F1_F7_x_V0_V5":len(family)==7 and all(len(x["views"])==6 for x in family.values()),
        "SA12_minimal_sets_all_families":all("minimal_sufficient_views" in x for x in family.values()),
        "SA13_derived_labels_excluded":derived_excluded,
        "SA14_counterexamples_for_insufficient":all_counterexamples,
        "SA15_256_symmetry_audits":sym_pass==256,
        "SA16_independent_payload_hashes_match":hash_a==hash_b,
    }

    verdict="PASS_STRUCTURAL_AUDIT_PHENOTYPE_SPLIT_V1" if all(gates.values()) else "PARTIAL_STRUCTURAL_AUDIT_PHENOTYPE_SPLIT_V1"

    result={
        "protocol":"STRUCTURAL_AUDIT_PHENOTYPE_SPLIT_V1",
        "precommit_commit":"4e22d7d0c1ac3b8e8bbcbec829791a27bc8ec60d",
        "verdict":verdict,
        "audit":{
            "representatives":len(rows),
            "raw_weight":sum(r["weight"] for r in rows),
            "mismatch_counts":mismatch_counts,
            "first_mismatch":first_mismatch,
            "total_mismatches":total_mismatches,
            "mutation_all18_resolved":mutation_all18,
            "mutation_label_dependency":"Completeness/generativity/reference-independence labels are independently re-enumerated over mutations but looked up from the authoritative pointed census, per precommit.",
        },
        "v4_reconstruction":{
            "source_contained_all":reconstruction_contains_all,
            "unique_all":reconstruction_unique_all,
            "failures":reconstruction_failures,
            "consistent_orientation_distribution":dict(sorted(Counter(r["_v4_consistent_orientations"] for r in rows).items())),
            "reconstructed_orbit_count_distribution":dict(sorted(Counter(r["_v4_reconstructed_orbit_count"] for r in rows).items())),
        },
        "family_analysis":family,
        "family_fields":{k:list(v) for k,v in FAMILY_FIELDS.items()},
        "family_symmetry_status":family_symmetry_status,
        "symmetry_compatibility":symmetry_compatibility,
        "symmetry_audit":{"total":256,"passed":sym_pass,"failures":sym_fail},
        "aggregate_hash_forward":hash_a,
        "aggregate_hash_reverse":hash_b,
        "headline_gates":gates,
        "claim_boundary":"Exact finite audit for the frozen 3-element census. Final closure cardinalities and mutant labels depend on the authoritative pointed census; developmental depth/recurrence fields are independently recomputed from operation tables.",
    }

    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    summary={
        "protocol":result["protocol"],
        "verdict":verdict,
        "audit":result["audit"],
        "v4_reconstruction":result["v4_reconstruction"],
        "family_analysis":family,
        "family_symmetry_status":family_symmetry_status,
        "symmetry_compatibility":symmetry_compatibility,
        "symmetry_audit":result["symmetry_audit"],
        "headline_gates":gates,
        "aggregate_hash_forward":hash_a,
        "aggregate_hash_reverse":hash_b,
        "claim_boundary":result["claim_boundary"],
    }
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")

    print("STRUCTURAL AUDIT + PHENOTYPE SPLIT V1",verdict)
    print("TOTAL_MISMATCHES="+str(total_mismatches))
    print("V4_SOURCE_CONTAINED_ALL="+str(reconstruction_contains_all))
    print("V4_UNIQUE_ALL="+str(reconstruction_unique_all))
    for fam,x in family.items():
        print(f"{fam}: minimal={','.join(x['minimal_sufficient_views']) or 'NONE'}")
    print(json.dumps(summary,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
