import hashlib, io, json, re, subprocess, tokenize
from pathlib import Path
OUT=Path('artifacts/v50'); OUT.mkdir(parents=True,exist_ok=True)
DJ=Path('/tmp/v45_django'); CK=Path('/tmp/v45_click'); RH=Path('/tmp/v45_rich')
SEED='V50_OUTCOME_LABELED_SEALED_20260814'
def sh(cmd,cwd,t=60):
    try:
        p=subprocess.run(cmd,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=t); return p.returncode==0
    except subprocess.TimeoutExpired: return False
def reset(r): subprocess.run('git reset --hard -q HEAD && git clean -fdxq',cwd=r,shell=True,check=True)
def H(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def th(x): return 't_'+hashlib.sha256((SEED+'|tok|'+x).encode()).hexdigest()[:16]
def lex(line): return re.findall(r'[A-Za-z_]+|\d+',line)
def token_sites(path,old):
    src=path.read_text(); ts=list(tokenize.generate_tokens(io.StringIO(src).readline)); out=[]
    if old.startswith('operator.'):
        want=old.split('.')[1]
        for i in range(len(ts)-2):
            a,b,c=ts[i:i+3]
            if a.type==tokenize.NAME and a.string=='operator' and b.type==tokenize.OP and b.string=='.' and c.type==tokenize.NAME and c.string==want: out.append((a.start[0],a.start[1],c.end[1],old))
    else:
        for t in ts:
            if t.type==tokenize.OP and t.string==old: out.append((t.start[0],t.start[1],t.end[1],old))
    return out
def mutate(path,site,new):
    row,c0,c1,_=site; lines=path.read_text().splitlines(True); original=lines[row-1]; lines[row-1]=original[:c0]+new+original[c1:]; path.write_text(''.join(lines)); return original.strip()
def sensitive(repo,path,old,new,test,timeout,key):
    reset(repo); base=sh(test,repo,timeout); sites=token_sites(path,old); causal=[]
    for i in sorted(range(len(sites)),key=lambda j:H(key+'|'+str(sites[j][:3]))):
        reset(repo); line=mutate(path,sites[i],new); after=sh(test,repo,timeout)
        if base!=after: causal.append({'site':list(sites[i][:3]),'line':line,'before':base,'after':after})
    return causal
episodes=[
 ('e1',DJ,DJ/'django/db/backends/utils.py','<=','<','python tests/runtests.py backends.test_utils.TestUtils.test_truncate_name --verbosity 0',40),
 ('e2',DJ,DJ/'django/core/paginator.py','<=','<','python tests/runtests.py pagination.tests.PaginationTests.test_orphans_value_larger_than_per_page_value --verbosity 0',40),
 ('e3',CK,CK/'src/click/types.py','operator.lt','operator.le','pytest -q tests/test_options.py::test_counting',40),
 ('e4',RH,RH/'rich/highlighter.py','<','<=','pytest -q tests/test_highlighter.py::test_highlight_json_string_only tests/test_highlighter.py::test_highlight_json_empty_string_only',40)]
obs=[]
for eid,repo,path,old,new,test,t in episodes:
    cs=sensitive(repo,path,old,new,test,t,eid)
    if len(cs)!=1: obs.append({'id':eid,'error':'nonunique','count':len(cs)}); continue
    c=cs[0]; line=c['line']
    if old=='<=':
        site=tuple(c['site'])+('<=',); reset(repo); mutate(path,site,'<'); before=sh(test,repo,t); bs=[s for s in token_sites(path,'<') if s[0]==site[0] and s[1]==site[1]]
        if len(bs)!=1: obs.append({'id':eid,'error':'lost'}); continue
        mutate(path,bs[0],'<='); after=sh(test,repo,t)
    else:
        site=tuple(c['site'])+(old,); reset(repo); before=sh(test,repo,t); mutate(path,site,new); after=sh(test,repo,t)
    sign='HELP' if (not before and after) else 'HARM' if (before and not after) else 'NEUTRAL'; fs={(i,th(tok)) for i,tok in enumerate(lex(line))}; obs.append({'id':eid,'line':line,'before':before,'after':after,'sign':sign,'features':[list(x) for x in sorted(fs)]})
valid=[o for o in obs if 'sign' in o]; helps=[o for o in valid if o['sign']=='HELP']; harms=[o for o in valid if o['sign']=='HARM']; F={o['id']:{tuple(x) for x in o['features']} for o in valid}; vocab=sorted(set().union(*F.values())) if F else []
surv=[f for f in vocab if helps and harms and all(f in F[o['id']] for o in helps) and all(f not in F[o['id']] for o in harms)]; sel=surv[0] if len(surv)==1 else None; decode={}
for o in valid:
    for i,t in enumerate(lex(o['line'])): decode[(i,th(t))]=(i,t)
commit={'protocol':SEED,'selected':list(sel) if sel else None,'selected_hash':H(repr(sel)) if sel else None,'labels_generated_by':'verifier HELP/HARM transition','requests_unseen':True}
R={'protocol':SEED,'phase':'A_OUTCOME_LABELED','episodes':obs,'help_count':len(helps),'harm_count':len(harms),'candidate_count':len(vocab),'survivor_count':len(surv),'selected':list(sel) if sel else None,'posthoc_selected':list(decode[sel]) if sel else None,'commitment':commit}; R['gates']={'four_resolved':len(valid)==4,'labels_not_supplied':True,'two_help_two_harm':len(helps)==2 and len(harms)==2,'unique_relation':len(surv)==1,'posthoc_if':bool(sel and decode[sel]==(0,'if')),'requests_unseen':True}; R['verdict']='PASS_V50_PHASE_A_OUTCOME_LABELED' if all(R['gates'].values()) else 'FAIL_V50_PHASE_A_OUTCOME_LABELED'; (OUT/'PHASE_A.json').write_text(json.dumps(R,indent=2)); (OUT/'COMMITMENT.json').write_text(json.dumps(commit,sort_keys=True,indent=2)); print(json.dumps(R,indent=2));
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
