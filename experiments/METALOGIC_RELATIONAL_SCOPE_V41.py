import ast, json
from pathlib import Path

ROOTS={
 'trigger':('/tmp/v41_django/django/db/backends/utils.py','len(name) <= length'),
 'transfer':('/tmp/v41_requests/src/requests/utils.py','slice_length <= 0'),
 'protected_click':('/tmp/v41_click/src/click/types.py','operator.lt'),
 'protected_rich':('/tmp/v41_rich/rich/highlighter.py','cursor < len(plain)'),
 'counterexample':('/tmp/v41_django/django/contrib/auth/password_validation.py','len(password) < self.min_length'),
}
BOUNDARY_TYPES={'If','While','IfExp','Assert'}

def locate(path,needle):
    src=Path(path).read_text(); t=ast.parse(src); target=None
    for n in ast.walk(t):
        seg=ast.get_source_segment(src,n) or ''
        if isinstance(n,ast.Compare) and needle in seg: target=n; break
    if target is None and needle=='operator.lt':
        for n in ast.walk(t):
            if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='operator' and n.attr=='lt': target=n; break
    if target is None: raise RuntimeError((path,needle))
    parents={}
    for p in ast.walk(t):
        for field,val in ast.iter_fields(p):
            kids=[]
            if isinstance(val,ast.AST): kids=[val]
            elif isinstance(val,list): kids=[x for x in val if isinstance(x,ast.AST)]
            for k in kids: parents[id(k)]=(p,field)
    rel=[]; cur=target
    while id(cur) in parents:
        p,field=parents[id(cur)]
        if type(p).__name__ in BOUNDARY_TYPES: rel.append((type(p).__name__,field))
        cur=p
    return sorted(set(rel))

E={k:locate(*v) for k,v in ROOTS.items()}
universe=sorted(set(x for rels in E.values() for x in rels))
valid=[r for r in universe if r in E['trigger'] and r in E['transfer'] and r not in E['protected_click'] and r not in E['protected_rich']]
selected=valid[0] if len(valid)==1 else None
post=[r for r in universe if r in E['trigger'] and r in E['transfer'] and r not in E['protected_click'] and r not in E['protected_rich'] and r not in E['counterexample']]
R={
 'protocol':'V41_GENERIC_AST_RELATIONAL_SCOPE_20260814',
 'primitive':'ANCESTOR_FIELD_RELATION(target, ancestor_ast_type, field_name)',
 'named_scope_features_supplied':False,
 'boundary_types':sorted(BOUNDARY_TYPES),
 'relations':{k:[list(x) for x in v] for k,v in E.items()},
 'candidate_relations':[list(x) for x in universe],
 'initial_valid':[list(x) for x in valid],
 'selected':list(selected) if selected else None,
 'post_counterevidence_consistent':[list(x) for x in post],
 'decision':'REVOKE' if selected and not post else 'OTHER',
}
R['gates']={
 'no_named_IF_TEST_feature':True,
 'unique_relational_scope_emerges':len(valid)==1,
 'emergent_relation_is_If_test':selected==('If','test'),
 'covers_source_distinct_transfer':selected is not None and selected in E['transfer'],
 'excludes_click_protected':selected is not None and selected not in E['protected_click'],
 'excludes_rich_protected':selected is not None and selected not in E['protected_rich'],
 'later_counterexample_falls_under_relation':selected is not None and selected in E['counterexample'],
 'no_relational_scope_survives_accumulated_evidence':not post,
 'revision_is_revoke':R['decision']=='REVOKE',
}
R['verdict']='PASS_V41_GENERIC_RELATIONAL_SCOPE' if all(R['gates'].values()) else 'FAIL_V41_GENERIC_RELATIONAL_SCOPE'
R['claim_boundary']='The IF_TEST feature is not supplied; (If,test) is generated from generic AST ancestor/field relations. AST node types and field structure remain the supplied meta-substrate.'
Path('artifacts/v41').mkdir(parents=True,exist_ok=True)
Path('artifacts/v41/RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2))
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
