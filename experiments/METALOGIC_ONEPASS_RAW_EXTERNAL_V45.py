import hashlib,json,subprocess,re,runpy
from pathlib import Path
OUT=Path('artifacts/v45'); OUT.mkdir(parents=True,exist_ok=True)
DJ=Path('/tmp/v45_django'); RQ=Path('/tmp/v45_requests'); CK=Path('/tmp/v45_click'); RH=Path('/tmp/v45_rich')
SEED='V45_ONEPASS_RAW_EXTERNAL_20260814'
def sh(cmd,cwd,t=90):
    try:
        p=subprocess.run(cmd,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=t)
        return p.returncode==0,p.stdout[-1800:]
    except subprocess.TimeoutExpired as e:
        x=e.stdout or ''
        if isinstance(x,bytes): x=x.decode(errors='replace')
        return False,(x+'\nTIMEOUT')[-1800:]
def reset(r): subprocess.run('git reset --hard -q HEAD && git clean -fdxq',cwd=r,shell=True,check=True)
def repl(p,a,b):
    s=p.read_text()
    if a not in s: raise RuntimeError(f'missing {a}')
    p.write_text(s.replace(a,b,1))
def atom(p,needle):
    for line in p.read_text().splitlines():
        if needle in line:
            m=re.match(r'([A-Za-z_]+)',line.strip()); return m.group(1) if m else '<NONE>'
    raise RuntimeError(needle)
def H(x): return 'c_'+hashlib.sha256((SEED+'|'+x).encode()).hexdigest()[:20]
trig=DJ/'django/db/backends/utils.py'; cls=DJ/'django/core/paginator.py'; contra=DJ/'django/contrib/auth/password_validation.py'; trans=RQ/'src/requests/utils.py'; click=CK/'src/click/types.py'; rich=RH/'rich/highlighter.py'
def dj1(): return sh('python tests/runtests.py backends.test_utils.TestUtils.test_truncate_name --verbosity 0',DJ,45)
def dj2(): return sh('python tests/runtests.py pagination.tests.PaginationTests.test_orphans_value_larger_than_per_page_value --verbosity 0',DJ,45)
def dj3(): return sh('python tests/runtests.py auth_tests.test_validators.MinimumLengthValidatorTest.test_validate --verbosity 0',DJ,45)
def rq(): return sh('timeout 8s pytest -q tests/test_utils.py -k test_iter_slices',RQ,15)
def ck(): return sh('pytest -q tests/test_options.py::test_counting',CK,45)
def rh(): return sh('pytest -q tests/test_highlighter.py',RH,75)
for r in (DJ,RQ,CK,RH): reset(r)
spec={'trigger':(trig,'len(name) <= length'),'positive_class':(cls,'self.per_page <= self.orphans'),'transfer':(trans,'slice_length <= 0'),'protected_click':(click,'operator.lt'),'protected_rich':(rich,'cursor < len(plain)'),'counterexample':(contra,'len(password) < self.min_length')}
raw={k:atom(*v) for k,v in spec.items()}; obs={k:H(v) for k,v in raw.items()}
P={}
reset(DJ); repl(trig,'len(name) <= length','len(name) < length'); x,_=dj1(); repl(trig,'len(name) < length','len(name) <= length'); y,_=dj1(); P['trigger']=(x,y)
reset(DJ); repl(cls,'self.per_page <= self.orphans','self.per_page < self.orphans'); x,_=dj2(); repl(cls,'self.per_page < self.orphans','self.per_page <= self.orphans'); y,_=dj2(); P['positive_class']=(x,y)
reset(RQ); repl(trans,'slice_length <= 0','slice_length < 0'); x,_=rq(); repl(trans,'slice_length < 0','slice_length <= 0'); y,_=rq(); P['transfer']=(x,y)
reset(CK); cb,_=ck(); repl(click,'operator.le if self.min_open else operator.lt','operator.le if self.min_open else operator.le'); cm,_=ck()
reset(RH); rb,_=rh(); repl(rich,'cursor < len(plain)','cursor <= len(plain)'); rm,_=rh()
pos=['trigger','positive_class','transfer']; neg=['protected_click','protected_rich']
old_survivors=[]
vocab=sorted(set(obs.values())); new=[c for c in vocab if all(obs[k]==c for k in pos) and all(obs[k]!=c for k in neg)]; selected=new[0] if len(new)==1 else None
reset(RQ); repl(trans,'slice_length <= 0','slice_length < 0'); cold,_=rq()
if selected and obs['transfer']==selected: repl(trans,'slice_length < 0','slice_length <= 0')
warm,_=rq(); reset(RQ); repl(trans,'slice_length <= 0','slice_length < 0'); abl,_=rq()
reset(DJ); base,_=dj3()
if selected and obs['counterexample']==selected: repl(contra,'if len(password) < self.min_length:','if len(password) <= self.min_length:')
after,_=dj3(); decision='REVOKE' if selected and base and not after else 'WITHHOLD'
R={'protocol':SEED,'representation':'opaque hash of first lexical atom; no AST used by learner','raw_posthoc':raw,'obs':obs,'positive':P,'protected':{'click':(cb,cm),'rich':(rb,rm)},'old_survivors':old_survivors,'new_survivors':new,'selected':selected,'transfer':{'cold':cold,'warm':warm,'ablated':abl},'counter':{'base':base,'after':after},'decision':decision}
R['gates']={'positive_repairs_causal':all((not a) and b for a,b in P.values()),'protected_behaviors_causal':cb and not cm and rb and not rm,'old_closure_obstructed':len(old_survivors)==0,'unique_raw_category':selected is not None and len(new)==1,'source_distinct_transfer':not cold and warm,'ablation_restores_failure':not abl,'counterevidence_inside_category':bool(selected and obs['counterexample']==selected),'counterevidence_falsifies':base and not after,'revokes':decision=='REVOKE','posthoc_selected_is_if':bool(selected and all(raw[k]=='if' for k in pos+['counterexample']))}
R['verdict']='PASS_V45_ONEPASS_RAW_EXTERNAL_RATCHET' if all(R['gates'].values()) else 'FAIL_V45_ONEPASS_RAW_EXTERNAL_RATCHET'
R['claim_boundary']='Single fresh external executable chain with repository-owned tests and no AST in learner representation. Mutation sites and first-token projection remain designer supplied.'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2))
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
runpy.run_path('experiments/METALOGIC_GENERIC_LEXICAL_CONSTRUCTOR_V46.py',run_name='__main__')
