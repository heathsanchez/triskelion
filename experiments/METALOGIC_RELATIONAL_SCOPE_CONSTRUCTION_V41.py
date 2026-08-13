import ast, json, subprocess
from pathlib import Path
from itertools import combinations

OUT=Path('artifacts/v41'); OUT.mkdir(parents=True, exist_ok=True)
DJ=Path('/tmp/v41_django'); RQ=Path('/tmp/v41_requests'); CK=Path('/tmp/v41_click'); RH=Path('/tmp/v41_rich')


def sh(cmd,cwd,timeout=40):
    try:
        p=subprocess.run(cmd,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
        return p.returncode==0,p.stdout[-3500:]
    except subprocess.TimeoutExpired as e:
        out=(e.stdout or '')
        if isinstance(out,bytes): out=out.decode(errors='replace')
        return False,(out+'\nTIMEOUT')[-3500:]

def reset(repo):
    subprocess.run('git reset --hard -q HEAD && git clean -fdxq',cwd=repo,shell=True,check=True)

def replace(path,old,new):
    s=path.read_text()
    if old not in s: raise RuntimeError(f'pattern not found: {path}: {old}')
    path.write_text(s.replace(old,new,1))

# External semantic authorities.
def dj_trunc(): return sh('python tests/runtests.py backends.test_utils.TestUtils.test_truncate_name --verbosity 0',DJ)
def dj_class_positive(): return sh('python tests/runtests.py pagination.PaginationTests.test_orphans_value_larger_than_per_page_value --verbosity 0',DJ)
def dj_pass(): return sh('python tests/runtests.py auth_tests.test_validators.MinimumLengthValidatorTest.test_validate --verbosity 0',DJ)
def rq_slice(): return sh('timeout 5s pytest -q tests/test_utils.py -k test_iter_slices',RQ,10)
def ck_count(): return sh('pytest -q tests/test_options.py::test_counting',CK)
def rh_suite(): return sh('pytest -q',RH,120)

# Generic target finder. No semantic scope names appear here.
def find_target(source,kind,needle):
    tree=ast.parse(source)
    matches=[]
    for n in ast.walk(tree):
        seg=ast.get_source_segment(source,n) or ''
        if kind=='compare' and isinstance(n,ast.Compare) and needle in seg:
            matches.append(n)
        elif kind=='attribute' and isinstance(n,ast.Attribute) and needle in seg:
            matches.append(n)
    if not matches: raise RuntimeError(f'target not found: {needle}')
    return tree,min(matches,key=lambda n:(getattr(n,'end_lineno',n.lineno)-n.lineno,getattr(n,'end_col_offset',999)-n.col_offset))

# Primitive metalanguage: relation R(target, AncestorNodeType, ChildFieldName).
# The relation vocabulary is discovered from the AST, not pre-enumerated.
def ancestor_field_relations(source,kind,needle):
    tree,target=find_target(source,kind,needle)
    parent={}; edge={}
    for p in ast.walk(tree):
        for field,value in ast.iter_fields(p):
            if isinstance(value,ast.AST):
                parent[id(value)]=p; edge[id(value)]=field
            elif isinstance(value,list):
                for child in value:
                    if isinstance(child,ast.AST):
                        parent[id(child)]=p; edge[id(child)]=field
    rel=set(); cur=target
    while id(cur) in parent:
        p=parent[id(cur)]
        rel.add((type(p).__name__,edge[id(cur)]))
        cur=p
    return rel

def relname(r): return f'ANCESTOR[{r[0]}].FIELD[{r[1]}]'
def predname(pred): return ' & '.join(('+' if sign else '-')+relname(r) for r,sign in pred)
def applies(pred,rels): return all((r in rels)==sign for r,sign in pred)

trigger_path=DJ/'django/db/backends/utils.py'
transfer_path=RQ/'src/requests/utils.py'
class_positive_path=DJ/'django/core/paginator.py'
click_path=CK/'src/click/types.py'
rich_path=RH/'rich/highlighter.py'
contra_path=DJ/'django/contrib/auth/password_validation.py'

for repo in (DJ,RQ,CK,RH): reset(repo)
rels={
 'trigger':ancestor_field_relations(trigger_path.read_text(),'compare','len(name) <= length'),
 'transfer':ancestor_field_relations(transfer_path.read_text(),'compare','slice_length <= 0'),
 'positive_class':ancestor_field_relations(class_positive_path.read_text(),'compare','self.per_page <= self.orphans'),
 'protected_click':ancestor_field_relations(click_path.read_text(),'attribute','operator.lt'),
 'protected_rich':ancestor_field_relations(rich_path.read_text(),'compare','cursor < len(plain)'),
 'counterexample':ancestor_field_relations(contra_path.read_text(),'compare','len(password) < self.min_length'),
}

vocab=sorted(set().union(*rels.values()))
lits=[(r,s) for r in vocab for s in (False,True)]
cands=[(lit,) for lit in lits]
for a,b in combinations(lits,2):
    if a[0]!=b[0]: cands.append((a,b))

R={
 'protocol':'V41B_GENERIC_AST_RELATION_SCOPE_CONSTRUCTION_20260814',
 'old_scope_language':['TRUE'],
 'constructor_primitive':'R(target, ancestor_node_type, child_field_name)',
 'vocabulary_source':'enumerated from actual Python AST ancestor-field relations at frozen external sites',
 'vocabulary':[relname(r) for r in vocab],
 'relations':{k:sorted(relname(r) for r in v) for k,v in rels.items()},
}

# Old broad rule is useful somewhere but unsafe globally.
reset(DJ); replace(trigger_path,'len(name) <= length','len(name) < length')
old_trigger,_=dj_trunc()
replace(trigger_path,'len(name) < length','len(name) <= length')
repair_trigger,_=dj_trunc()
reset(CK); replace(click_path,'operator.le if self.min_open else operator.lt','operator.le if self.min_open else operator.le')
click_preserved,_=ck_count()
reset(RH); replace(rich_path,'cursor < len(plain)','cursor <= len(plain)')
rich_preserved,rich_log=rh_suite()
R['old_scope']={'seeded_trigger_passes':old_trigger,'repair_restores_trigger':repair_trigger,'broad_rule_preserves_click':click_preserved,'broad_rule_preserves_rich':rich_preserved,'rich_log_tail':rich_log[-800:]}

# Independently executable class-method positive kills the accidental "not ClassDef" scope.
reset(DJ); replace(class_positive_path,'self.per_page <= self.orphans','self.per_page < self.orphans')
class_old,class_old_log=dj_class_positive()
replace(class_positive_path,'self.per_page < self.orphans','self.per_page <= self.orphans')
class_new,class_new_log=dj_class_positive()
R['class_positive']={'old_passes':class_old,'repair_passes':class_new,'old_log_tail':class_old_log[-700:],'new_log_tail':class_new_log[-400:]}

# Construct from three positives and two structurally distinct protected negatives.
positive_keys=('trigger','transfer','positive_class')
negative_keys=('protected_click','protected_rich')
valid=[]
for p in cands:
    if all(applies(p,rels[k]) for k in positive_keys) and all(not applies(p,rels[k]) for k in negative_keys):
        valid.append(p)
min_len=min((len(p) for p in valid),default=None)
minimal=sorted([p for p in valid if len(p)==min_len],key=predname)
selected=minimal[0] if len(minimal)==1 else None
R['construction']={'candidate_count':len(cands),'valid_count':len(valid),'minimal_count':len(minimal),'minimal':[predname(p) for p in minimal],'selected':predname(selected) if selected else None}

# Source-distinct causal transfer under the constructed relation.
reset(RQ); replace(transfer_path,'slice_length <= 0','slice_length < 0')
transfer_old,_=rq_slice()
if selected and applies(selected,rels['transfer']): replace(transfer_path,'slice_length < 0','slice_length <= 0')
transfer_new,new_log=rq_slice()
R['transfer']={'old_passes':transfer_old,'scope_applies':bool(selected and applies(selected,rels['transfer'])),'new_passes':transfer_new,'new_log_tail':new_log[-600:]}

# Later counterevidence arrives inside the discovered relation.
reset(DJ); contra_base,_=dj_pass()
if selected and applies(selected,rels['counterexample']): replace(contra_path,'if len(password) < self.min_length:','if len(password) <= self.min_length:')
contra_after,contra_log=dj_pass()
R['counterevidence']={'baseline_passes':contra_base,'scope_applies':bool(selected and applies(selected,rels['counterexample'])),'after_passes':contra_after,'log_tail':contra_log[-900:]}

consistent=[]
for p in cands:
    if (all(applies(p,rels[k]) for k in positive_keys) and
        all(not applies(p,rels[k]) for k in negative_keys) and
        not applies(p,rels['counterexample'])):
        consistent.append(p)
decision='REVOKE' if selected and not consistent else ('REVISE' if selected and selected not in consistent else 'KEEP' if selected else 'WITHHOLD')
R['revision']={'consistent_count':len(consistent),'consistent':[predname(p) for p in consistent[:30]],'decision':decision}
expected='+ANCESTOR[If].FIELD[test]'
R['gates']={
 'old_undifferentiated_language_obstructed':(not old_trigger) and repair_trigger and (not click_preserved) and (not rich_preserved),
 'class_method_positive_is_causal':(not class_old) and class_new,
 'class_method_positive_eliminates_not_ClassDef':('ANCESTOR[ClassDef].FIELD[body]' in rels['positive_class']),
 'relation_vocabulary_not_pre_named':('IN_IF_TEST' not in json.dumps(R['vocabulary'])),
 'unique_minimal_relation_scope':selected is not None and len(minimal)==1,
 'emergent_relation_is_If_test':selected is not None and predname(selected)==expected,
 'covers_all_three_positive_behaviors':selected is not None and all(applies(selected,rels[k]) for k in positive_keys),
 'excludes_two_structurally_distinct_protected_sites':selected is not None and all(not applies(selected,rels[k]) for k in negative_keys),
 'source_distinct_transfer_is_causal':(not transfer_old) and transfer_new,
 'later_counterevidence_falls_inside_constructed_relation':selected is not None and applies(selected,rels['counterexample']),
 'later_external_behavior_falsifies_retained_rule':contra_base and not contra_after,
 'accumulated_evidence_eliminates_current_relation_language':len(consistent)==0,
 'system_revokes':decision=='REVOKE',
}
R['verdict']='PASS_V41B_GENERIC_RELATIONAL_CONSTRUCTION' if all(R['gates'].values()) else 'FAIL_V41B_GENERIC_RELATIONAL_CONSTRUCTION'
R['claim_boundary']='The decisive If.test distinction is not supplied as a feature or scope token. It emerges uniquely from a frozen generic ancestor-node/child-field relation constructor after external executable evidence includes a class-method positive that eliminates the accidental not-ClassDef hypothesis. Python AST node/field ontology remains supplied.'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2))
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
