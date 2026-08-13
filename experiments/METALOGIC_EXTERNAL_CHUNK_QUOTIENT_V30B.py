"""V30b — quotient external repair compositions by verified extensional equivalence.

Builds on V30's fixed QuixBugs substrate. Syntactically different plans are placed in the
same equivalence class only when an independent law-check stream shows that they produce
identical repaired source and both pass the repository tests. The quotient class, not an
arbitrary ordering, is then retained as a new atomic chunk.
"""
import importlib.util, sys, json
from pathlib import Path

spec=importlib.util.spec_from_file_location('v30base','experiments/METALOGIC_EXTERNAL_CHUNK_RATCHET_V30.py')
v=importlib.util.module_from_spec(spec);sys.modules['v30base']=v;spec.loader.exec_module(v)
OUT=Path('artifacts/external_chunk_quotient_v30b');OUT.mkdir(parents=True,exist_ok=True)
CAL=list(range(32)); LAW=list(range(200,264)); HOLD=list(range(400,464))

def passing(name,kinds,variants,library):
    rows=[]
    for symbolic,low in v.plans(library):
        ok=True
        for k in variants:
            try: fixed=v.repair(v.variant(name,k,kinds),name,low)
            except Exception: ok=False;break
            if not v.run_source(name,fixed,v.tests_for(name)):ok=False;break
        if ok: rows.append({'symbolic':tuple(symbolic),'expanded':tuple(low)})
    if not rows:return []
    m=min(len(r['symbolic']) for r in rows);return [r for r in rows if len(r['symbolic'])==m]

def law_signature(name,kinds,row,variants):
    sig=[]
    for k in variants:
        mut=v.variant(name,k,kinds)
        try: fixed=v.repair(mut,name,row['expanded'])
        except Exception:return None
        if not v.run_source(name,fixed,v.tests_for(name)):return None
        sig.append(fixed)
    return tuple(sig)

def quotient_classes(name,kinds,rows,law_variants):
    groups={}
    for r in rows:
        s=law_signature(name,kinds,r,law_variants)
        if s is None:continue
        # stable but nonsemantic class key
        key=hash(s)
        groups.setdefault(key,[]).append(r)
    return list(groups.values())

def canonical_expanded(cls):
    # Representative is chosen only after equivalence was externally established.
    return min((tuple(r['expanded']) for r in cls),key=repr)

L0=dict(v.ATOMS)
# Generation 1: same external function/task as V30.
rows1=passing('get_factors',['CMP','BIN'],CAL,L0); classes1=quotient_classes('get_factors',['CMP','BIN'],rows1,LAW)
D=canonical_expanded(classes1[0]) if len(classes1)==1 else None
L1=dict(L0)
if D:L1['D_AB']=D

# Explicitly record the discovered law rather than silently canonicalizing.
commutation_verified=False
if len(classes1)==1:
    syms={tuple(r['symbolic']) for r in classes1[0]}
    commutation_verified={('CMP','BIN'),('BIN','CMP')}.issubset(syms)

# Generation 2: different QuixBugs function, fixed budget inherited from V30.
cold_rows=passing('quicksort',['CMP','BIN','CONST'],CAL,L0); cold_classes=quotient_classes('quicksort',['CMP','BIN','CONST'],cold_rows,LAW)
warm_rows=passing('quicksort',['CMP','BIN','CONST'],CAL,L1); warm_classes=quotient_classes('quicksort',['CMP','BIN','CONST'],warm_rows,LAW)
abl_rows=passing('quicksort',['CMP','BIN','CONST'],CAL,{k:x for k,x in L1.items() if k!='D_AB'});abl_classes=quotient_classes('quicksort',['CMP','BIN','CONST'],abl_rows,LAW)
chosen=canonical_expanded(warm_classes[0]) if len(warm_classes)==1 else None

# Independent heldout verification of the learned equivalence class and successor class.
def exact_all(name,kinds,plan,variants):
    if plan is None:return False
    for k in variants:
        try:fixed=v.repair(v.variant(name,k,kinds),name,plan)
        except Exception:return False
        if not v.run_source(name,fixed,v.tests_for(name)):return False
    return True
hold_D=exact_all('get_factors',['CMP','BIN'],D,HOLD)
hold_successor=exact_all('quicksort',['CMP','BIN','CONST'],chosen,HOLD)

R={
 'protocol':'V30b external QuixBugs chunk ratchet modulo independently verified composition equivalence',
 'commit':v.COMMIT,'budget':v.BUDGET,
 'generation1_syntactic_survivors':rows1,
 'generation1_equivalence_classes':[[{'symbolic':r['symbolic'],'expanded':r['expanded']} for r in c] for c in classes1],
 'commutation_law_CMP_BIN_verified':commutation_verified,
 'D_representative_after_quotient':D,
 'successor_cold_syntactic_survivors':cold_rows,'successor_cold_classes':len(cold_classes),
 'successor_warm_syntactic_survivors':warm_rows,
 'successor_warm_classes':[[{'symbolic':r['symbolic'],'expanded':r['expanded']} for r in c] for c in warm_classes],
 'ablation_classes':len(abl_classes),'heldout_variants':len(HOLD),
 'heldout_D_exact':hold_D,'heldout_successor_exact':hold_successor,
}
R['gates']={
 'one_verified_q1_equivalence_class':len(classes1)==1,
 'commutation_law_discovered':commutation_verified,
 'cold_successor_outside_budget':len(cold_classes)==0,
 'one_warm_successor_equivalence_class':len(warm_classes)==1 and any('D_AB' in r['symbolic'] for r in warm_classes[0]),
 'ablation_removes_successor':len(abl_classes)==0,
 'heldout_D_exact':hold_D,'heldout_successor_exact':hold_successor,
}
R['verdict']='PASS_EXTERNAL_QUOTIENT_CHUNK_RATCHET_V30B' if all(R['gates'].values()) else 'MIXED_EXTERNAL_QUOTIENT_CHUNK_RATCHET_V30B'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2,default=list));print(json.dumps(R,indent=2,default=list))
