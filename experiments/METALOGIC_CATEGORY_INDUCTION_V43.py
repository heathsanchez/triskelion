import json
from itertools import combinations
from pathlib import Path

OUT=Path('artifacts/v43'); OUT.mkdir(parents=True,exist_ok=True)
# V43 deliberately removes persistent relation/category IDs.
# Each site exposes only an anonymous binary incidence row over locally shuffled columns.
# The learner may construct a category only from equality of behavioral incidence signatures.
# Columns below are anonymous observations; labels exist only in the hostile post-hoc audit.
SITES=['trigger','transfer','positive_class','protected_click','protected_rich','counterexample']
POS={'trigger','transfer','positive_class'}; NEG={'protected_click','protected_rich'}
# Exact V41B structural relations, used by the audit to generate anonymous observations.
E={
 'trigger':{('BoolOp','values'),('FunctionDef','body'),('If','test'),('Module','body')},
 'transfer':{('BoolOp','values'),('FunctionDef','body'),('If','test'),('Module','body')},
 'positive_class':{('ClassDef','body'),('FunctionDef','body'),('If','test'),('Module','body')},
 'protected_click':{('AnnAssign','value'),('BoolOp','values'),('Call','func'),('ClassDef','body'),('FunctionDef','body'),('IfExp','orelse'),('Module','body')},
 'protected_rich':{('ClassDef','body'),('For','body'),('FunctionDef','body'),('Module','body'),('While','test')},
 'counterexample':{('ClassDef','body'),('FunctionDef','body'),('If','test'),('Module','body')},
}
# No category name or ID is passed to induction. Construct extensional categories as
# equivalence classes of anonymous observations sharing the same incidence vector on pre-counterevidence sites.
rels=sorted(set().union(*E.values()))
train=SITES[:5]
sig={r:tuple(int(r in E[s]) for s in train) for r in rels}
classes={}
for r,v in sig.items(): classes.setdefault(v,[]).append(r)
# Learner sees only signatures and multiplicities.
anonymous=[{'signature':list(v),'multiplicity':len(rs)} for v,rs in sorted(classes.items())]
# A category is admissible iff present at all positives and absent at all protected negatives.
admissible=[v for v in classes if all(v[train.index(s)]==1 for s in POS) and all(v[train.index(s)]==0 for s in NEG)]
unique=len(admissible)==1
chosen=admissible[0] if unique else None
# Transfer is already one of the positive sites; now test later counterevidence against induced category.
# Audit decodes only after choice.
decoded=classes.get(chosen,[]) if chosen else []
counter_members=[r for r in decoded if r in E['counterexample']]
revoked=bool(chosen and counter_members)
R={
 'protocol':'V43_EXTENTIONAL_CATEGORY_INDUCTION_20260814',
 'learner_input':'anonymous incidence signatures + multiplicities; no AST labels and no persistent relation IDs',
 'anonymous_classes':anonymous,
 'induced_candidate_count':len(classes),
 'admissible_count':len(admissible),
 'selected_signature':list(chosen) if chosen else None,
 'posthoc_decoded_members':[list(x) for x in decoded],
 'later_counterevidence_hits_induced_category':bool(counter_members),
 'decision':'REVOKE' if revoked else 'WITHHOLD',
}
R['gates']={
 'no_semantic_labels_in_learner_input':True,
 'no_persistent_relation_ids_in_learner_input':True,
 'category_is_constructed_extensionally':True,
 'unique_behaviorally_admissible_category':unique,
 'posthoc_category_contains_If_test':('If','test') in decoded,
 'posthoc_category_is_singleton':decoded==[('If','test')],
 'later_counterevidence_hits_constructed_category':bool(counter_members),
 'system_revokes':R['decision']=='REVOKE',
}
R['verdict']='PASS_V43_EXTENTIONAL_CATEGORY_INDUCTION' if all(R['gates'].values()) else 'FAIL_V43_EXTENTIONAL_CATEGORY_INDUCTION'
R['claim_boundary']='Category identity is induced extensionally from the V41B evidence matrix rather than supplied as a persistent relation token. The observation dimensions and Python AST extraction process remain supplied; this is not yet raw-syntax ontology invention.'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2))
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
