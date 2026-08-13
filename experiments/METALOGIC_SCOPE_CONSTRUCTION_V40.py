import ast, json, subprocess
from pathlib import Path

OUT=Path('artifacts/v40'); OUT.mkdir(parents=True, exist_ok=True)
DJ=Path('/tmp/v40_django'); RQ=Path('/tmp/v40_requests'); CK=Path('/tmp/v40_click')
FEATURES=('IN_IF_TEST','IN_IFEXP','IN_RETURN')


def sh(cmd,cwd,timeout=30):
    p=subprocess.run(cmd,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
    return p.returncode==0,p.stdout[-2500:]

def reset(repo):
    subprocess.run('git reset --hard -q HEAD && git clean -fdxq',cwd=repo,shell=True,check=True)

def replace(path,old,new):
    s=path.read_text()
    if old not in s: raise RuntimeError(f'pattern not found: {path}: {old}')
    path.write_text(s.replace(old,new,1))

def dj_trunc(): return sh('python tests/runtests.py backends.test_utils.TestUtils.test_truncate_name --verbosity 0',DJ)
def dj_pass(): return sh('python tests/runtests.py auth_tests.test_validators.MinimumLengthValidatorTest.test_validate --verbosity 0',DJ)
def rq_slice(): return sh('timeout 5s pytest -q tests/test_utils.py -k test_iter_slices',RQ,10)
def ck_count(): return sh('pytest -q tests/test_options.py::test_counting',CK)

# Generic structural feature extraction for a selected source span.
def compare_features(source,needle):
    tree=ast.parse(source)
    parents={}
    for p in ast.walk(tree):
        for c in ast.iter_child_nodes(p): parents[id(c)]=p
    target=None
    for n in ast.walk(tree):
        seg=ast.get_source_segment(source,n)
        if seg and needle in seg and isinstance(n,(ast.Compare,ast.Attribute)):
            target=n; break
    if target is None:
        # Click's comparator value is an Attribute inside an IfExp; find operator.lt.
        for n in ast.walk(tree):
            if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='operator' and n.attr=='lt':
                target=n; break
    if target is None: raise RuntimeError('target site not found')
    f={k:False for k in FEATURES}; cur=target
    while id(cur) in parents:
        p=parents[id(cur)]
        if isinstance(p,ast.If) and target in list(ast.walk(p.test)): f['IN_IF_TEST']=True
        if isinstance(p,ast.IfExp): f['IN_IFEXP']=True
        if isinstance(p,ast.Return): f['IN_RETURN']=True
        cur=p
    return f

def eval_pred(pred,feat):
    if pred=='TRUE': return True
    return all(feat[k]==v for k,v in pred)

def predicate_name(pred):
    if pred=='TRUE': return 'TRUE'
    return ' & '.join(f'{k}={int(v)}' for k,v in pred)

# Frozen generic constructor: all 1-literal structural predicates, then 2-literal conjunctions.
def construct_candidates():
    out=[]
    for k in FEATURES:
        for v in (False,True): out.append(((k,v),))
    for i,k1 in enumerate(FEATURES):
        for k2 in FEATURES[i+1:]:
            for v1 in (False,True):
                for v2 in (False,True): out.append(((k1,v1),(k2,v2)))
    return out

# Selected sites are fixed before outcomes.
trigger_path=DJ/'django/db/backends/utils.py'
transfer_path=RQ/'src/requests/utils.py'
protected_path=CK/'src/click/types.py'
contra_path=DJ/'django/contrib/auth/password_validation.py'

# Baseline feature vectors are derived from source structure, not named scopes.
reset(DJ); reset(RQ); reset(CK)
trigger_feat=compare_features(trigger_path.read_text(),'len(name) <= length')
transfer_feat=compare_features(transfer_path.read_text(),'slice_length <= 0')
protected_feat=compare_features(protected_path.read_text(),'operator.lt')
contra_feat=compare_features(contra_path.read_text(),'len(password) < self.min_length')

R={'protocol':'V40_GENERIC_STRUCTURAL_SCOPE_CONSTRUCTION_20260814','old_scope_language':['TRUE'],'feature_substrate':list(FEATURES),'features':{'trigger':trigger_feat,'transfer':transfer_feat,'protected':protected_feat,'counterexample':contra_feat}}

# Old scope TRUE repairs the trigger but damages protected external behavior.
reset(DJ); replace(trigger_path,'len(name) <= length','len(name) < length')
old_trigger,_=dj_trunc()
replace(trigger_path,'len(name) < length','len(name) <= length')
true_repairs,_=dj_trunc()
reset(CK); replace(protected_path,'operator.le if self.min_open else operator.lt','operator.le if self.min_open else operator.le')
true_protect,_=ck_count()
R['old_scope']={'seeded_trigger_passes':old_trigger,'TRUE_repairs_trigger':true_repairs,'TRUE_preserves_protected':true_protect}

# Construct a scope from generic structural features. It must cover trigger and exclude protected.
cands=construct_candidates()
valid=[p for p in cands if eval_pred(p,trigger_feat) and not eval_pred(p,protected_feat)]
min_len=min(map(len,valid)) if valid else None
minimal=[p for p in valid if len(p)==min_len]
# Deterministic tie-break by textual representation; uniqueness is not assumed unless evidence provides it.
minimal=sorted(minimal,key=predicate_name)
selected=minimal[0] if minimal else None
R['construction']={'candidate_count':len(cands),'valid_count':len(valid),'minimal_count':len(minimal),'minimal':[predicate_name(p) for p in minimal],'selected':predicate_name(selected) if selected else None}

# External transfer: candidate predicate decides whether the retained repair may apply.
reset(RQ); replace(transfer_path,'slice_length <= 0','slice_length < 0')
transfer_old,_=rq_slice()
if selected and eval_pred(selected,transfer_feat): replace(transfer_path,'slice_length < 0','slice_length <= 0')
transfer_new,_=rq_slice()
R['transfer']={'old_passes':transfer_old,'constructed_scope_applies':bool(selected and eval_pred(selected,transfer_feat)),'new_passes':transfer_new}

# Later counterevidence arrives.
reset(DJ); contra_base,_=dj_pass()
if selected and eval_pred(selected,contra_feat): replace(contra_path,'if len(password) < self.min_length:','if len(password) <= self.min_length:')
contra_after,contra_log=dj_pass()
R['counterevidence']={'baseline_passes':contra_base,'constructed_scope_applies':bool(selected and eval_pred(selected,contra_feat)),'after_passes':contra_after,'log_tail':contra_log[-700:]}

# Ask whether any predicate in the same frozen generic constructor can now cover both positives while excluding both negatives.
consistent=[]
for p in cands:
    if eval_pred(p,trigger_feat) and eval_pred(p,transfer_feat) and not eval_pred(p,protected_feat) and not eval_pred(p,contra_feat): consistent.append(p)
decision='REVOKE' if selected and not consistent else ('REVISE' if selected and consistent and selected not in consistent else 'KEEP' if selected else 'WITHHOLD')
R['revision']={'consistent_count':len(consistent),'consistent':[predicate_name(p) for p in consistent[:20]],'decision':decision}
R['gates']={
 'old_scope_insufficient':(not old_trigger) and true_repairs and (not true_protect),
 'new_scope_constructed_from_generic_features':selected is not None and predicate_name(selected)!='TRUE',
 'constructed_scope_excludes_protected_site':selected is not None and not eval_pred(selected,protected_feat),
 'constructed_scope_applies_to_source_distinct_transfer':selected is not None and eval_pred(selected,transfer_feat),
 'source_distinct_transfer_is_causal':(not transfer_old) and transfer_new,
 'later_counterevidence_is_in_scope':selected is not None and eval_pred(selected,contra_feat),
 'later_external_test_falsifies_constructed_scope':contra_base and not contra_after,
 'no_current_constructed_scope_fits_all_evidence':len(consistent)==0,
 'revision_policy_revokes':decision=='REVOKE'}
R['verdict']='PASS_V40_GENERIC_SCOPE_CONSTRUCTION' if all(R['gates'].values()) else 'FAIL_V40_GENERIC_SCOPE_CONSTRUCTION'
R['claim_boundary']='The named IF_TEST scope is not supplied. A new scope predicate is constructed from a frozen generic structural-feature substrate. This is construction within that meta-substrate, not proof of invention outside the substrate.'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2))
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
