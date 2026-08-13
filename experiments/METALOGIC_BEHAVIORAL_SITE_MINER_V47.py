import hashlib,json,re,subprocess
from pathlib import Path
OUT=Path('artifacts/v47'); OUT.mkdir(parents=True,exist_ok=True)
DJ=Path('/tmp/v45_django'); RQ=Path('/tmp/v45_requests'); CK=Path('/tmp/v45_click'); RH=Path('/tmp/v45_rich')
SEED='V47_BEHAVIORAL_SITE_MINER_20260814'
def sh(cmd,cwd,t=90):
    try:
        p=subprocess.run(cmd,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=t)
        return p.returncode==0
    except subprocess.TimeoutExpired: return False
def reset(r): subprocess.run('git reset --hard -q HEAD && git clean -fdxq',cwd=r,shell=True,check=True)
def mutate_n(path,old,new,n):
    s=path.read_text(); starts=[m.start() for m in re.finditer(re.escape(old),s)]
    if n>=len(starts): return None
    i=starts[n]; path.write_text(s[:i]+new+s[i+len(old):])
    line=s.count('\n',0,i)+1
    text=s.splitlines()[line-1].strip()
    return line,text
def H(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
roles={
 'trigger':{'repo':DJ,'path':DJ/'django/db/backends/utils.py','old':'<=','new':'<','test':'python tests/runtests.py backends.test_utils.TestUtils.test_truncate_name --verbosity 0'},
 'positive_class':{'repo':DJ,'path':DJ/'django/core/paginator.py','old':'<=','new':'<','test':'python tests/runtests.py pagination.tests.PaginationTests.test_orphans_value_larger_than_per_page_value --verbosity 0'},
 'transfer':{'repo':RQ,'path':RQ/'src/requests/utils.py','old':'<=','new':'<','test':'timeout 8s pytest -q tests/test_utils.py -k test_iter_slices'},
 'protected_click':{'repo':CK,'path':CK/'src/click/types.py','old':'operator.lt','new':'operator.le','test':'pytest -q tests/test_options.py::test_counting'},
 'protected_rich':{'repo':RH,'path':RH/'rich/highlighter.py','old':'<','new':'<=','test':'pytest -q tests/test_highlighter.py'},
 'counterexample':{'repo':DJ,'path':DJ/'django/contrib/auth/password_validation.py','old':'<','new':'<=','test':'python tests/runtests.py auth_tests.test_validators.MinimumLengthValidatorTest.test_validate --verbosity 0'},
}
mined={}
for role,c in roles.items():
    reset(c['repo']); baseline=sh(c['test'],c['repo'])
    count=c['path'].read_text().count(c['old'])
    order=sorted(range(count),key=lambda i:H(role+'|'+str(i)))
    causal=[]
    attempts=[]
    for i in order:
        reset(c['repo']); hit=mutate_n(c['path'],c['old'],c['new'],i)
        if hit is None: continue
        ok=sh(c['test'],c['repo']); attempts.append({'index':i,'line':hit[0],'passes':ok})
        if baseline and not ok: causal.append({'index':i,'line':hit[0],'text':hit[1]})
    mined[role]={'baseline':baseline,'candidate_count':count,'attempts':attempts,'causal':causal}
# Require one causally identified site per externally defined role; no source needle is supplied.
unique=all(len(mined[k]['causal'])==1 for k in roles)
lines={k:mined[k]['causal'][0]['text'] for k in roles if len(mined[k]['causal'])==1}
def toks(line): return re.findall(r'[A-Za-z_]+|\d+|<=|>=|==|!=|:=|\S',line)
def th(x): return 't_'+hashlib.sha256((SEED+'|tok|'+x).encode()).hexdigest()[:16]
features={}; decode={}
for k,line in lines.items():
    fs=set()
    for i,t in enumerate(toks(line)):
        if t in {'<','<=','>','>=','lt','le','gt','ge'}: continue
        f=(i,th(t)); fs.add(f); decode[f]=(i,t)
    features[k]=fs
pos=['trigger','positive_class','transfer']; neg=['protected_click','protected_rich']
vocab=sorted(set().union(*features.values())) if features else []
survivors=[f for f in vocab if all(f in features[k] for k in pos) and all(f not in features[k] for k in neg)] if unique else []
selected=survivors[0] if len(survivors)==1 else None
counter_hit=bool(selected and selected in features.get('counterexample',set()))
R={'protocol':SEED,'site_selection':'all literal comparator occurrences in each frozen file, hash-ordered; repository test decides causal site','mined':mined,'unique_site_each_role':unique,'lexical_candidate_count':len(vocab),'lexical_survivors':[list(x) for x in survivors],'selected':list(selected) if selected else None,'posthoc_selected':list(decode[selected]) if selected else None,'counterexample_hits_selected':counter_hit,'decision':'REVOKE' if counter_hit else 'WITHHOLD'}
R['gates']={'all_role_baselines_pass':all(mined[k]['baseline'] for k in roles),'exactly_one_causal_site_per_role':unique,'no_preidentified_source_needles':True,'unique_lexical_relation_after_site_mining':len(survivors)==1,'posthoc_relation_is_position0_if':bool(selected and decode[selected]==(0,'if')),'source_distinct_transfer_role_in_relation':bool(selected and selected in features.get('transfer',set())),'two_protected_roles_outside_relation':bool(selected and all(selected not in features.get(k,set()) for k in neg)),'counterevidence_inside_relation':counter_hit,'system_revokes':R['decision']=='REVOKE'}
R['verdict']='PASS_V47_BEHAVIORAL_SITE_MINING' if all(R['gates'].values()) else 'FAIL_V47_BEHAVIORAL_SITE_MINING'
R['claim_boundary']='Mutation sites are no longer source-needeled: repository tests select among all comparator occurrences in frozen files. Files, tests, mutation family, regex tokenization, and role ordering remain supplied.'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2))
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
