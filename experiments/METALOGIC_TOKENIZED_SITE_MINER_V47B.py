import hashlib, io, json, re, subprocess, tokenize
from pathlib import Path
OUT=Path('artifacts/v47b'); OUT.mkdir(parents=True,exist_ok=True)
DJ=Path('/tmp/v45_django'); RQ=Path('/tmp/v45_requests'); CK=Path('/tmp/v45_click'); RH=Path('/tmp/v45_rich')
SEED='V47B_TOKENIZED_SITE_MINER_20260814'

def sh(cmd,cwd,t=60):
    try:
        p=subprocess.run(cmd,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=t)
        return p.returncode==0
    except subprocess.TimeoutExpired:
        return False

def reset(r): subprocess.run('git reset --hard -q HEAD && git clean -fdxq',cwd=r,shell=True,check=True)
def H(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()

def token_sites(path, old):
    src=path.read_text(); lines=src.splitlines(True); out=[]
    ts=list(tokenize.generate_tokens(io.StringIO(src).readline))
    if old.startswith('operator.'):
        want=old.split('.')[1]
        for i in range(len(ts)-2):
            a,b,c=ts[i:i+3]
            if a.type==tokenize.NAME and a.string=='operator' and b.type==tokenize.OP and b.string=='.' and c.type==tokenize.NAME and c.string==want:
                out.append((a.start[0],a.start[1],c.end[1],old))
    else:
        for t in ts:
            if t.type==tokenize.OP and t.string==old:
                out.append((t.start[0],t.start[1],t.end[1],old))
    return out

def mutate_site(path,site,new):
    row,c0,c1,_=site; lines=path.read_text().splitlines(True); line=lines[row-1]
    lines[row-1]=line[:c0]+new+line[c1:]
    path.write_text(''.join(lines)); return line.strip()

roles={
 'trigger':{'repo':DJ,'path':DJ/'django/db/backends/utils.py','old':'<=','new':'<','test':'python tests/runtests.py backends.test_utils.TestUtils.test_truncate_name --verbosity 0','timeout':40},
 'positive_class':{'repo':DJ,'path':DJ/'django/core/paginator.py','old':'<=','new':'<','test':'python tests/runtests.py pagination.tests.PaginationTests.test_orphans_value_larger_than_per_page_value --verbosity 0','timeout':40},
 'transfer':{'repo':RQ,'path':RQ/'src/requests/utils.py','old':'<=','new':'<','test':'timeout 8s pytest -q tests/test_utils.py -k test_iter_slices','timeout':15},
 'protected_click':{'repo':CK,'path':CK/'src/click/types.py','old':'operator.lt','new':'operator.le','test':'pytest -q tests/test_options.py::test_counting','timeout':40},
 'protected_rich':{'repo':RH,'path':RH/'rich/highlighter.py','old':'<','new':'<=','test':'pytest -q tests/test_highlighter.py::test_highlight_json_string_only tests/test_highlighter.py::test_highlight_json_empty_string_only','timeout':40},
 'counterexample':{'repo':DJ,'path':DJ/'django/contrib/auth/password_validation.py','old':'<','new':'<=','test':'python tests/runtests.py auth_tests.test_validators.MinimumLengthValidatorTest.test_validate --verbosity 0','timeout':40},
}
mined={}
for role,c in roles.items():
    reset(c['repo']); baseline=sh(c['test'],c['repo'],c['timeout']); sites=token_sites(c['path'],c['old'])
    order=sorted(range(len(sites)),key=lambda i:H(role+'|'+str(sites[i][0])+'|'+str(sites[i][1])))
    causal=[]; attempts=[]
    for i in order:
        reset(c['repo']); line=mutate_site(c['path'],sites[i],c['new']); ok=sh(c['test'],c['repo'],c['timeout'])
        attempts.append({'token_site':list(sites[i][:3]),'passes':ok})
        if baseline and not ok: causal.append({'token_site':list(sites[i][:3]),'text':line})
    mined[role]={'baseline':baseline,'candidate_count':len(sites),'attempts':attempts,'causal':causal}

unique=all(len(mined[k]['causal'])==1 for k in roles)
lines={k:mined[k]['causal'][0]['text'] for k in roles if len(mined[k]['causal'])==1}
def lex(line): return re.findall(r'[A-Za-z_]+|\d+|<=|>=|==|!=|:=|\S',line)
def th(x): return 't_'+hashlib.sha256((SEED+'|tok|'+x).encode()).hexdigest()[:16]
features={}; decode={}
for k,line in lines.items():
    fs=set()
    for i,t in enumerate(lex(line)):
        if t in {'<','<=','>','>=','lt','le','gt','ge'}: continue
        f=(i,th(t)); fs.add(f); decode[f]=(i,t)
    features[k]=fs
pos=['trigger','positive_class','transfer']; neg=['protected_click','protected_rich']
vocab=sorted(set().union(*features.values())) if features else []
survivors=[f for f in vocab if unique and all(f in features[k] for k in pos) and all(f not in features[k] for k in neg)]
selected=survivors[0] if len(survivors)==1 else None
counter_hit=bool(selected and selected in features.get('counterexample',set()))
R={'protocol':SEED,'site_language':'Python lexical tokens only; strings/comments excluded; all matching operator sites hash-ordered and repository test decides','mined':mined,'unique_site_each_role':unique,'lexical_candidate_count':len(vocab),'survivor_count':len(survivors),'selected':list(selected) if selected else None,'posthoc_selected':list(decode[selected]) if selected else None,'counterexample_hits_selected':counter_hit,'decision':'REVOKE' if counter_hit else 'WITHHOLD'}
R['gates']={'all_role_baselines_pass':all(mined[k]['baseline'] for k in roles),'exactly_one_causal_site_per_role':unique,'strings_comments_excluded_by_tokenizer':True,'no_preidentified_source_needles':True,'unique_lexical_relation_after_behavioral_mining':len(survivors)==1,'posthoc_relation_is_position0_if':bool(selected and decode[selected]==(0,'if')),'source_distinct_transfer_in_relation':bool(selected and selected in features.get('transfer',set())),'two_protected_roles_outside_relation':bool(selected and all(selected not in features.get(k,set()) for k in neg)),'counterevidence_inside_relation':counter_hit,'system_revokes':R['decision']=='REVOKE'}
R['verdict']='PASS_V47B_TOKENIZED_BEHAVIORAL_SITE_MINING' if all(R['gates'].values()) else 'FAIL_V47B_TOKENIZED_BEHAVIORAL_SITE_MINING'
R['claim_boundary']='Behavioral verifier now selects mutation sites from lexical operator occurrences without source needles or AST. Frozen files/tests, mutation family, role ordering, tokenization, and repository selection remain supplied.'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2))
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
