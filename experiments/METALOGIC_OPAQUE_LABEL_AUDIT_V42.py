import hashlib,json
from itertools import combinations
from pathlib import Path

OUT=Path('artifacts/v42'); OUT.mkdir(parents=True,exist_ok=True)
SEED='V42_OPAQUE_LABEL_AUDIT_20260814'
# Exact relation incidence recovered by V41B before construction.
E={
 'trigger':{('BoolOp','values'),('FunctionDef','body'),('If','test'),('Module','body')},
 'transfer':{('BoolOp','values'),('FunctionDef','body'),('If','test'),('Module','body')},
 'positive_class':{('ClassDef','body'),('FunctionDef','body'),('If','test'),('Module','body')},
 'protected_click':{('AnnAssign','value'),('BoolOp','values'),('Call','func'),('ClassDef','body'),('FunctionDef','body'),('IfExp','orelse'),('Module','body')},
 'protected_rich':{('ClassDef','body'),('For','body'),('FunctionDef','body'),('Module','body'),('While','test')},
 'counterexample':{('ClassDef','body'),('FunctionDef','body'),('If','test'),('Module','body')},
}
def h(r): return 'r_'+hashlib.sha256((SEED+'|'+r[0]+'|'+r[1]).encode()).hexdigest()[:20]
O={k:{h(r) for r in rs} for k,rs in E.items()}; vocab=sorted(set().union(*O.values()))
lits=[(r,s) for r in vocab for s in (False,True)]
cands=[(x,) for x in lits]+[(a,b) for a,b in combinations(lits,2) if a[0]!=b[0]]
def ok(p,rs): return all((r in rs)==s for r,s in p)
pos=('trigger','transfer','positive_class'); neg=('protected_click','protected_rich')
valid=[p for p in cands if all(ok(p,O[k]) for k in pos) and all(not ok(p,O[k]) for k in neg)]
m=min(map(len,valid)); mins=[p for p in valid if len(p)==m]; selected=mins[0] if len(mins)==1 else None
consistent=[p for p in cands if all(ok(p,O[k]) for k in pos) and all(not ok(p,O[k]) for k in neg) and not ok(p,O['counterexample'])]
inv={h(r):r for rs in E.values() for r in rs}; decoded=[(inv[r],s) for r,s in selected] if selected else []
R={'protocol':'V42_OPAQUE_LABEL_INVARIANCE_20260814','evidence_provenance':'V41B run 31741219608 executable relation incidence','learner_vocabulary':vocab,'candidate_count':len(cands),'minimal_count':len(mins),'selected':[(r,s) for r,s in selected] if selected else None,'posthoc_decoded':decoded,'post_counterevidence_consistent_count':len(consistent),'decision':'REVOKE' if selected and not consistent else 'WITHHOLD'}
R['gates']={'no_semantic_labels_visible':all(x.startswith('r_') for x in vocab),'unique_opaque_scope':len(mins)==1,'posthoc_scope_is_If_test':decoded==[(('If','test'),True)],'later_counterevidence_eliminates_all':len(consistent)==0,'decision_revokes':R['decision']=='REVOKE'}
R['verdict']='PASS_V42_OPAQUE_LABEL_INVARIANCE' if all(R['gates'].values()) else 'FAIL_V42_OPAQUE_LABEL_INVARIANCE'
R['claim_boundary']='Pure invariance audit over V41B externally verified relation incidence. It removes semantic label meaning, not category identity or the underlying Python AST ontology.'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
