import hashlib, io, json, re, subprocess, tokenize
from pathlib import Path

OUT=Path('artifacts/v50'); OUT.mkdir(parents=True,exist_ok=True)
DJ=Path('/tmp/v50_django'); CK=Path('/tmp/v50_click'); RH=Path('/tmp/v50_rich')
SEED='V50_OUTCOME_LABELED_SEALED_20260814'

def sh(cmd,cwd,t=60):
    try:
        p=subprocess.run(cmd,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=t)
        return p.returncode==0
    except subprocess.TimeoutExpired:
        return False

def reset(r): subprocess.run('git reset --hard -q HEAD && git clean -fdxq',cwd=r,shell=True,check=True)
def H(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def th(x): return 't_'+hashlib.sha256((SEED+'|tok|'+x).encode()).hexdigest()[:16]
def lex(line): return re.findall(r'[A-Za-z_]+|\d+',line)

def token_sites(path, old):
    src=path.read_text(); ts=list(tokenize.generate_tokens(io.StringIO(src).readline)); out=[]
    if old.startswith('operator.'):
        want=old.split('.')[1]
        for i in range(len(ts)-2):
            a,b,c=ts[i:i+3]
            if a.type==tokenize.NAME and a.string=='operator' and b.type==tokenize.OP and b.string=='.' and c.type==tokenize.NAME and c.string==want:
                out.append((a.start[0],a.start[1],c.end[1],old))
    else:
        for t in ts:
            if t.type==tokenize.OP and t.string==old: out.append((t.start[0],t.start[1],t.end[1],old))
    return out

def mutate(path,site,new):
    row,c0,c1,_=site; lines=path.read_text().splitlines(True); original=lines[row-1]
    lines[row-1]=original[:c0]+new+original[c1:]; path.write_text(''.join(lines)); return original.strip()

def find_unique_causal(repo,path,old,new,test,timeout,key):
    reset(repo); base=sh(test,repo,timeout); sites=token_sites(path,old); causal=[]
    for i in sorted(range(len(sites)),key=lambda j:H(key+'|'+str(sites[j][:3]))):
        reset(repo); line=mutate(path,sites[i],new); after=sh(test,repo,timeout)
        if base != after: causal.append({'site':list(sites[i][:3]),'line':line,'before':base,'after':after})
    return causal

# No positive/negative labels are supplied. Each episode is simply a file, a test, and one proposed widening transform.
episodes=[
 {'id':'e1','repo':DJ,'path':DJ/'django/db/backends/utils.py','old':'<=','broken':'<','repair':'<=','test':'python tests/runtests.py backends.test_utils.TestUtils.test_truncate_name --verbosity 0','timeout':40},
 {'id':'e2','repo':DJ,'path':DJ/'django/core/paginator.py','old':'<=','broken':'<','repair':'<=','test':'python tests/runtests.py pagination.tests.PaginationTests.test_orphans_value_larger_than_per_page_value --verbosity 0','timeout':40},
 {'id':'e3','repo':CK,'path':CK/'src/click/types.py','old':'operator.lt','broken':'operator.lt','repair':'operator.le','test':'pytest -q tests/test_options.py::test_counting','timeout':40},
 {'id':'e4','repo':RH,'path':RH/'rich/highlighter.py','old':'<','broken':'<','repair':'<=','test':'pytest -q tests/test_highlighter.py::test_highlight_json_string_only tests/test_highlighter.py::test_highlight_json_empty_string_only','timeout':40},
]

obs=[]
for e in episodes:
    # Locate the unique test-sensitive source site without semantic needles.
    if e['old']=='<=':
        cs=find_unique_causal(e['repo'],e['path'],'<=','<',e['test'],e['timeout'],e['id'])
        if len(cs)!=1: obs.append({'id':e['id'],'error':'nonunique_site','causal_count':len(cs)}); continue
        site=tuple(cs[0]['site'])+('<=',); line=cs[0]['line']
        # Create broken state, measure, then apply the common widening repair.
        reset(e['repo']); mutate(e['path'],site,'<'); before=sh(e['test'],e['repo'],e['timeout'])
        broken_sites=token_sites(e['path'],'<'); matching=[s for s in broken_sites if s[0]==site[0] and s[1]==site[1]]
        if len(matching)!=1: obs.append({'id':e['id'],'error':'broken_site_lost'}); continue
        mutate(e['path'],matching[0],'<='); after=sh(e['test'],e['repo'],e['timeout'])
    elif e['old']=='operator.lt':
        cs=find_unique_causal(e['repo'],e['path'],'operator.lt','operator.le',e['test'],e['timeout'],e['id'])
        if len(cs)!=1: obs.append({'id':e['id'],'error':'nonunique_site','causal_count':len(cs)}); continue
        site=tuple(cs[0]['site'])+('operator.lt',); line=cs[0]['line']; reset(e['repo']); before=sh(e['test'],e['repo'],e['timeout']); mutate(e['path'],site,'operator.le'); after=sh(e['test'],e['repo'],e['timeout'])
    else:
        cs=find_unique_causal(e['repo'],e['path'],'<','<=',e['test'],e['timeout'],e['id'])
        if len(cs)!=1: obs.append({'id':e['id'],'error':'nonunique_site','causal_count':len(cs)}); continue
        site=tuple(cs[0]['site'])+('<',); line=cs[0]['line']; reset(e['repo']); before=sh(e['test'],e['repo'],e['timeout']); mutate(e['path'],site,'<='); after=sh(e['test'],e['repo'],e['timeout'])
    sign='HELP' if (not before and after) else 'HARM' if (before and not after) else 'NEUTRAL'
    fs={(i,th(t)) for i,t in enumerate(lex(line))}
    obs.append({'id':e['id'],'site':list(site[:3]),'line':line,'before':before,'after':after,'sign':sign,'features':[list(x) for x in sorted(fs)]})

valid=[o for o in obs if 'sign' in o]; helps=[o for o in valid if o['sign']=='HELP']; harms=[o for o in valid if o['sign']=='HARM']
feature_sets={o['id']:{tuple(x) for x in o['features']} for o in valid}; vocab=sorted(set().union(*feature_sets.values())) if valid else []
survivors=[f for f in vocab if helps and harms and all(f in feature_sets[o['id']] for o in helps) and all(f not in feature_sets[o['id']] for o in harms)]
selected=survivors[0] if len(survivors)==1 else None
decode={}
for o in valid:
    for i,t in enumerate(lex(o['line'])): decode[(i,th(t))]=(i,t)
commit={'protocol':SEED,'selected':list(selected) if selected else None,'selected_hash':H(repr(selected)) if selected else None,'labels_generated_by':'verifier transition sign HELP/HARM','requests_forbidden_in_phase_a':True}
R={'protocol':SEED,'phase':'A_OUTCOME_LABELED_CALIBRATION','episodes':obs,'help_count':len(helps),'harm_count':len(harms),'candidate_count':len(vocab),'survivor_count':len(survivors),'selected':list(selected) if selected else None,'posthoc_selected':list(decode[selected]) if selected else None,'commitment':commit}
R['gates']={'all_four_sites_resolved':len(valid)==4,'labels_not_supplied':True,'two_help_two_harm':len(helps)==2 and len(harms)==2,'unique_relation_from_verifier_signs':len(survivors)==1,'posthoc_relation_is_position0_if':bool(selected and decode[selected]==(0,'if')),'requests_unseen':True}
R['verdict']='PASS_V50_PHASE_A_OUTCOME_LABELED' if all(R['gates'].values()) else 'FAIL_V50_PHASE_A_OUTCOME_LABELED'
(OUT/'PHASE_A.json').write_text(json.dumps(R,indent=2)); (OUT/'COMMITMENT.json').write_text(json.dumps(commit,sort_keys=True,indent=2)); print(json.dumps(R,indent=2))
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
