import itertools, json
from pathlib import Path

FEATURES = ('IN_IF_TEST','IN_IFEXP','IN_RETURN')
E = {
 'trigger': {'IN_IF_TEST':True,'IN_IFEXP':False,'IN_RETURN':False},
 'transfer': {'IN_IF_TEST':True,'IN_IFEXP':False,'IN_RETURN':False},
 'protected_click': {'IN_IF_TEST':False,'IN_IFEXP':True,'IN_RETURN':False},
 'protected_rich': {'IN_IF_TEST':False,'IN_IFEXP':False,'IN_RETURN':False},
 'counterexample': {'IN_IF_TEST':True,'IN_IFEXP':False,'IN_RETURN':False},
}

def holds(p,f): return all(f[k] == v for k,v in p)
def name(p): return ' & '.join(f'{k}={int(v)}' for k,v in p)

candidates=[]
for k in FEATURES:
    for v in (False,True): candidates.append(((k,v),))
for a,b in itertools.combinations(FEATURES,2):
    for va in (False,True):
        for vb in (False,True): candidates.append(((a,va),(b,vb)))

initial=[p for p in candidates if holds(p,E['trigger']) and not holds(p,E['protected_click']) and not holds(p,E['protected_rich'])]
min_len=min(map(len,initial)) if initial else None
minimal=sorted([p for p in initial if len(p)==min_len],key=name)
selected=minimal[0] if len(minimal)==1 else None
post=[p for p in candidates if holds(p,E['trigger']) and holds(p,E['transfer']) and not holds(p,E['protected_click']) and not holds(p,E['protected_rich']) and not holds(p,E['counterexample'])]

R={
 'protocol':'V40C_VERIFIED_EVIDENCE_SCOPE_UNIQUENESS_20260814',
 'evidence_provenance':{
   'trigger_transfer_click_counterexample':'V40/V39 repository-test-backed evidence',
   'protected_rich':'V40b run 31739336144; first hash-ranked eligible mutation; Rich full suite 2 failed, 954 passed, 25 skipped'
 },
 'feature_substrate':FEATURES,
 'evidence':E,
 'candidate_count':len(candidates),
 'initial_valid_count':len(initial),
 'minimal_count':len(minimal),
 'minimal':[name(p) for p in minimal],
 'selected':name(selected) if selected else None,
 'post_counterevidence_consistent_count':len(post),
 'decision':'REVOKE' if selected and not post else 'OTHER',
}
R['gates']={
 'unique_minimal_scope':len(minimal)==1,
 'unique_scope_is_IN_IF_TEST':selected is not None and name(selected)=='IN_IF_TEST=1',
 'covers_source_distinct_transfer':selected is not None and holds(selected,E['transfer']),
 'excludes_click_protected':selected is not None and not holds(selected,E['protected_click']),
 'excludes_rich_protected':selected is not None and not holds(selected,E['protected_rich']),
 'later_counterexample_is_in_scope':selected is not None and holds(selected,E['counterexample']),
 'no_current_scope_fits_all_accumulated_evidence':len(post)==0,
 'revision_is_revoke':R['decision']=='REVOKE',
}
R['verdict']='PASS_V40C_UNIQUE_SCOPE_IDENTIFICATION' if all(R['gates'].values()) else 'FAIL_V40C_UNIQUE_SCOPE_IDENTIFICATION'
R['claim_boundary']='Pure synthesis over externally verified evidence from prior frozen runs. Establishes uniqueness in the supplied structural predicate substrate; it is not a new behavioral run.'
Path('artifacts/v40c').mkdir(parents=True,exist_ok=True)
Path('artifacts/v40c/RESULT.json').write_text(json.dumps(R,indent=2))
print(json.dumps(R,indent=2))
