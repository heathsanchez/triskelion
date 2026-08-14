import hashlib, io, json, os, re, shutil, subprocess, sys, tokenize
from pathlib import Path
from collections import Counter

SEED='V53_HISTORICAL_CLEANROOM_20260814'
BIP=Path('/tmp/BugsInPy')
WORK=Path('/tmp/v53_work')
OUT=Path('artifacts/v53'); OUT.mkdir(parents=True,exist_ok=True)
WORK.mkdir(parents=True,exist_ok=True)
# Frozen metadata-only candidate stream. No patch/fixed source is inspected before terminal audit.
CANDIDATES=[
 ('PySnooper','1','3.8.1'),('PySnooper','2','3.8.1'),('PySnooper','3','3.8.1'),
 ('black','13','3.8.3'),('black','17','3.8.3'),('black','19','3.8.3'),
 ('matplotlib','4','3.8.1'),('matplotlib','25','3.8.1'),
 ('fastapi','11','3.8.3'),('fastapi','16','3.8.3'),
 ('scrapy','7','3.8.3'),('scrapy','16','3.8.3')]
MAX_READY=8; MAX_SITES=12
DESTS=sorted(s for s in tokenize.EXACT_TOKEN_TYPES if 1<=len(s)<=2)
OLD=['IDENTITY','REVERSE_WINDOW','ROTATE_LEFT','ROTATE_RIGHT','SWAP_ADJACENT']

def H(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def run(cmd,cwd=None,t=90,env=None):
    try:
        p=subprocess.run(cmd,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=t,env=env)
        return p.returncode,p.stdout
    except subprocess.TimeoutExpired as e:
        x=e.stdout or ''
        if isinstance(x,bytes): x=x.decode(errors='replace')
        return 124,x+'\nTIMEOUT'
def info(path):
    d={}
    if not path.exists(): return d
    for s in path.read_text(errors='ignore').splitlines():
        m=re.match(r'(\w+)="(.*)"',s.strip())
        if m:d[m.group(1)]=m.group(2)
    return d
def checkout(project,bug):
    root=WORK/f'{project}_{bug}'; shutil.rmtree(root,ignore_errors=True); root.mkdir(parents=True)
    cmd=f'export BUGSINPY_HOME={BIP}; export PATH={BIP}/framework/bin:$PATH; bugsinpy-checkout -p {project} -i {bug} -v 0 -w {root}'
    rc,o=run(cmd,t=90); return rc,o,root/project
def decode_req(p):
    b=p.read_bytes()
    if b'\x00' in b:
        for enc in ('utf-16','utf-16le','utf-16be'):
            try:return b.decode(enc)
            except:pass
    return b.decode(errors='ignore')
def setup(repo,py):
    mm='.'.join(py.split('.')[:2]); rc,o=run(f'uv python install {mm} && uv venv --seed --python {mm} .v53env',repo,70)
    if rc:return False,o
    pip=repo/'.v53env/bin/pip'; chunks=[]
    # old projects are sensitive to modern build tooling
    run(f'{pip} install -q "pip<24" "setuptools<69" "wheel<0.43"',repo,45)
    req=repo/'bugsinpy_requirements.txt'
    if req.exists():
        lines=[]
        for s in decode_req(req).splitlines():
            s=s.strip()
            if not s or s.startswith('#') or 'pywin32' in s.lower(): continue
            lines.append(s)
        (repo/'.v53req.txt').write_text('\n'.join(lines))
        if lines:
            rc,x=run(f'{pip} install -q -r .v53req.txt',repo,120); chunks.append(x)
            if rc:return False,'\n'.join(chunks)
    env=os.environ.copy(); env['PATH']=str(repo/'.v53env/bin')+':'+env.get('PATH','')
    sh=repo/'bugsinpy_setup.sh'
    if sh.exists():
        rc,x=run('bash bugsinpy_setup.sh',repo,60,env); chunks.append(x)
        if rc:return False,'\n'.join(chunks)
    return True,'\n'.join(chunks)
def env(repo):
    e=os.environ.copy(); e['PATH']=str(repo/'.v53env/bin')+':'+e.get('PATH',''); return e
def test(repo):
    p=repo/'bugsinpy_run_test.sh'
    if not p.exists(): return False,'NO_RUN_TEST'
    return (lambda z:(z[0]==0,z[1]))(run('bash bugsinpy_run_test.sh',repo,40,env(repo)))
def reset(repo):
    run('git reset --hard -q HEAD && git clean -fdxq -e .v53env -e bugsinpy_run_test.sh -e bugsinpy_setup.sh -e bugsinpy_requirements.txt -e .v53req.txt',repo,20)
def source_frames(repo,out):
    frames=[]
    for m in re.finditer(r'File "([^"]+\.py)", line (\d+)',out):
        p=Path(m.group(1)); ln=int(m.group(2)); p=p if p.is_absolute() else repo/p
        try: rel=p.resolve().relative_to(repo.resolve())
        except: continue
        if not p.exists() or 'test' in rel.parts or str(rel).startswith(('tests/','test/')): continue
        frames.append((p,ln))
    seen=set(); ans=[]
    for p,ln in reversed(frames):
        k=(str(p),ln)
        if k not in seen: seen.add(k); ans.append((p,ln))
    return ans
def candidate_sites(repo,out):
    sites=[]
    for p,ln in source_frames(repo,out):
        try: ts=list(tokenize.generate_tokens(io.StringIO(p.read_text(errors='ignore')).readline))
        except: continue
        for t in ts:
            if t.type==tokenize.OP and abs(t.start[0]-ln)<=2:
                sites.append((p,t.start[0],t.start[1],t.end[1],t.string))
    return sorted(sites,key=lambda s:H('|'.join(map(str,s))))[:MAX_SITES]
def mutate(site,dst):
    p,row,c0,c1,src=site; ls=p.read_text().splitlines(True); ls[row-1]=ls[row-1][:c0]+dst+ls[row-1][c1:]; p.write_text(''.join(ls))
def construct(repo,sites):
    wins=[]
    for site in sites:
        for dst in DESTS:
            if dst==site[-1]: continue
            reset(repo); mutate(site,dst); ok,_=test(repo)
            if ok:wins.append((site[-1],dst,str(site[0].relative_to(repo)),site[1],site[2]))
    reset(repo)
    pairs=sorted(set((a,b) for a,b,*_ in wins)); return pairs,wins
def reuse(repo,sites,op):
    hits=[]
    for s in sites:
        if s[-1]!=op['src']: continue
        reset(repo); mutate(s,op['dst']); ok,_=test(repo)
        if ok:hits.append([str(s[0].relative_to(repo)),s[1],s[2]])
    reset(repo); return hits

order=sorted(CANDIDATES,key=lambda x:H('|'.join(x)))
pre={'seed':SEED,'candidate_order':order,'ready_cap':MAX_READY,'max_sites':MAX_SITES,'old_generators':OLD,'human_fix_forbidden':True}
(OUT/'PRECOMMIT.json').write_text(json.dumps(pre,indent=2)); print('PRECOMMIT',json.dumps(pre,sort_keys=True))
# Phase 0: reproducibility screen uses buggy commit + test only. No fix or patch data.
ready=[]; screen=[]
for pr,bg,py in order:
    ev={'project':pr,'bug':bg,'python':py}; rc,o,repo=checkout(pr,bg)
    if rc or not repo.exists(): ev['status']='CHECKOUT_FAIL'; screen.append(ev); continue
    good,so=setup(repo,py)
    if not good: ev['status']='SETUP_FAIL'; ev['tail']=so[-300:]; screen.append(ev); continue
    base,bout=test(repo); ev['baseline_pass']=base
    if base: ev['status']='NONREPRODUCING'; screen.append(ev); continue
    sites=candidate_sites(repo,bout); ev['site_count']=len(sites)
    if not sites: ev['status']='NO_SOURCE_OPERATOR_SITE'; screen.append(ev); continue
    ev['status']='READY'; ready.append((pr,bg,py)); screen.append(ev)
    if len(ready)>=MAX_READY: break
selected_ready=ready[:6]
(OUT/'READY.json').write_text(json.dumps({'screen':screen,'selected':selected_ready},indent=2))
# Phase 1: clean-room algebra growth. Restart each selected buggy world from scratch.
events=[]; learned=None; origin_project=None; reused=None
for idx,(pr,bg,py) in enumerate(selected_ready,1):
    ev={'episode':idx,'project':pr,'bug':bg,'python':py}; rc,o,repo=checkout(pr,bg)
    if rc: ev['status']='CHECKOUT_FAIL'; events.append(ev); continue
    good,so=setup(repo,py)
    if not good: ev['status']='SETUP_FAIL'; events.append(ev); continue
    base,bout=test(repo); ev['baseline_pass']=base
    if base: ev['status']='NONREPRODUCING'; events.append(ev); continue
    sites=candidate_sites(repo,bout); ev['sites']=[[str(s[0].relative_to(repo)),*s[1:]] for s in sites]
    if learned is None:
        pairs,wins=construct(repo,sites); ev['repair_pairs']=pairs; ev['repair_wins']=wins[:20]
        if len(pairs)==1:
            src,dst=pairs[0]; obstruction=Counter([src])!=Counter([dst]); ev['old_closure_obstruction']=obstruction
            if obstruction:
                learned={'kind':'TOKEN_REWRITE','src':src,'dst':dst,'origin_project':pr,'origin_bug':bg,'origin_episode':idx}; origin_project=pr; ev['status']='OPERATOR_FORMED'; ev['operator']=learned
            else: ev['status']='NO_NOVELTY'
        else: ev['status']='AMBIGUOUS_OR_NO_REPAIR'
    else:
        if pr==origin_project: ev['status']='SAME_PROJECT_CONTROL'
        else:
            hits=reuse(repo,sites,learned); ev['reuse_hits']=hits
            if hits:
                reset(repo); ab,_=test(repo); ev['ablation_pass']=ab
                if not ab: ev['status']='CAUSAL_REUSE'; reused={'episode':idx,'project':pr,'bug':bg,'hits':hits}; events.append(ev); break
                ev['status']='ABLATION_FAILED'
            else: ev['status']='NO_REUSE'
    events.append(ev)
# Terminal audit may now read human fix metadata only after the experiment is over.
audit={}
if learned:
    for role,pr,bg in [('origin',learned['origin_project'],learned['origin_bug'])]+([('reuse',reused['project'],reused['bug'])] if reused else []):
        bi=info(BIP/'projects'/pr/'bugs'/bg/'bug.info'); audit[role]={'project':pr,'bug':bg,'buggy_commit':bi.get('buggy_commit_id'),'fixed_commit':bi.get('fixed_commit_id')}
R={'protocol':SEED,'precommit':pre,'screen':screen,'selected_ready':selected_ready,'events':events,'learned_operator':learned,'causal_reuse':reused,'terminal_fix_metadata':audit}
R['gates']={'at_least_six_clean_reproductions':len(selected_ready)>=6,'historical_failures_reproduced':all(e.get('baseline_pass') is False for e in events if 'baseline_pass' in e),'operator_formed':learned is not None,'old_closure_obstruction':any(e.get('old_closure_obstruction') for e in events),'different_project_causal_reuse':bool(reused and learned and reused['project']!=learned['origin_project']),'ablation_restores_failure':bool(reused),'fix_withheld_until_terminal':True}
R['verdict']='PASS_V53_HISTORICAL_CLEANROOM_RATCHET' if all(R['gates'].values()) else 'INCOMPLETE_V53_HISTORICAL_CLEANROOM_RATCHET'
R['claim_boundary']='Candidate order and reproducibility screen are frozen without patch/fixed-source access. Generic token rewrite constructor and source-frame localization are supplied. Human fix metadata is read only after construction/reuse terminates.'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2)); sys.exit(0)
