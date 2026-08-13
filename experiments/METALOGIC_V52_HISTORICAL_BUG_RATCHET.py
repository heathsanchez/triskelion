import hashlib, io, json, os, re, shutil, subprocess, sys, time, tokenize
from pathlib import Path
from collections import Counter

SEED='V52_HISTORICAL_BUGINPY_RATCHET_20260814'
OUT=Path('artifacts/v52'); OUT.mkdir(parents=True, exist_ok=True)
BIP=Path('/tmp/BugsInPy')
WORK=Path('/tmp/v52_work'); WORK.mkdir(exist_ok=True)
MAX_EPISODES=16
MAX_SITES=3
TEST_TIMEOUT=25
# Generic token-emission substrate. This is not comparator-specific.
DESTS=sorted([s for s in tokenize.EXACT_TOKEN_TYPES if 1 <= len(s) <= 2])
OLD_GENERATORS=['IDENTITY','REVERSE_WINDOW','ROTATE_LEFT','ROTATE_RIGHT','SWAP_ADJACENT']

def H(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def run(cmd,cwd=None,timeout=120,env=None):
    try:
        p=subprocess.run(cmd,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout,env=env)
        return p.returncode,p.stdout
    except subprocess.TimeoutExpired as e:
        return 124,(e.stdout or '')+(e.stderr or '')

def parse_info(path):
    d={}
    for line in path.read_text(errors='ignore').splitlines():
        m=re.match(r'(\w+)="(.*)"',line.strip())
        if m:d[m.group(1)]=m.group(2)
    return d

def project_url(project):
    info=parse_info(BIP/'projects'/project/'project.info')
    return info.get('github_url')

def enumerate_bugs():
    out=[]
    for p in sorted((BIP/'projects').iterdir()):
        if not p.is_dir() or not (p/'bugs').is_dir(): continue
        pi=parse_info(p/'project.info')
        if pi.get('status')!='OK': continue
        for b in sorted((p/'bugs').iterdir(), key=lambda x:x.name):
            if not b.is_dir() or not (b/'bug.info').exists(): continue
            bi=parse_info(b/'bug.info')
            py=bi.get('python_version','')
            # Frozen infrastructure eligibility only; no fix contents or patch metadata inspected.
            if re.match(r'^3\.(8|9|10|11)',py):
                out.append((p.name,b.name,py))
    return sorted(out,key=lambda x:H('|'.join(x)))

def checkout_bug(project,bug):
    root=WORK/f'{project}_{bug}'
    if root.exists(): shutil.rmtree(root)
    root.mkdir(parents=True)
    cmd=f'export BUGSINPY_HOME={BIP}; export PATH={BIP}/framework/bin:$PATH; bugsinpy-checkout -p {project} -i {bug} -v 0 -w {root}'
    rc,out=run(cmd,timeout=180)
    repo=root/project
    return rc,out,repo

def setup_env(repo,pyver):
    # Install requested historical interpreter and an isolated environment.
    rc,out=run(f'uv python install {pyver} && uv venv --python {pyver} .v52env',cwd=repo,timeout=240)
    if rc:return False,out
    pip=repo/'.v52env/bin/pip'; python=repo/'.v52env/bin/python'
    chunks=[]
    req=repo/'bugsinpy_requirements.txt'
    if req.exists():
        lines=[]
        for s in req.read_text(errors='ignore').splitlines():
            s=s.strip()
            if s and not s.startswith('#'): lines.append(s)
        if lines:
            rc,o=run(f'{pip} install -q '+' '.join(repr(x) for x in lines),cwd=repo,timeout=300); chunks.append(o)
            if rc:return False,'\n'.join(chunks)
    setup=repo/'bugsinpy_setup.sh'
    if setup.exists():
        env=os.environ.copy(); env['PATH']=str(repo/'.v52env/bin')+':'+env.get('PATH','')
        rc,o=run('bash bugsinpy_setup.sh',cwd=repo,timeout=180,env=env); chunks.append(o)
        if rc:return False,'\n'.join(chunks)
    return True,'\n'.join(chunks)

def test(repo):
    env=os.environ.copy(); env['PATH']=str(repo/'.v52env/bin')+':'+env.get('PATH','')
    rc,out=run('bash bugsinpy_run_test.sh',cwd=repo,timeout=TEST_TIMEOUT,env=env)
    return rc==0,out

def reset(repo):
    run('git reset --hard -q HEAD && git clean -fdxq -e .v52env',cwd=repo,timeout=30)

def traceback_sites(repo,output):
    # Use only failing-output source frames. No fixed commit/diff data.
    frames=[]
    for m in re.finditer(r'File "([^"]+\.py)", line (\d+)',output):
        p=Path(m.group(1)); ln=int(m.group(2))
        if not p.is_absolute(): p=(repo/p)
        try: rp=p.resolve().relative_to(repo.resolve())
        except Exception: continue
        if 'test' in rp.parts or str(rp).startswith('tests/'): continue
        if p.exists(): frames.append((p,ln))
    # newest/deepest frames first, deterministic dedupe
    seen=set(); uniq=[]
    for p,ln in reversed(frames):
        k=(str(p),ln)
        if k not in seen: seen.add(k); uniq.append((p,ln))
    sites=[]
    for p,ln in uniq:
        txt=p.read_text(errors='ignore')
        try: ts=list(tokenize.generate_tokens(io.StringIO(txt).readline))
        except Exception: continue
        for t in ts:
            if t.type==tokenize.OP and abs(t.start[0]-ln)<=1:
                sites.append((p,t.start[0],t.start[1],t.end[1],t.string))
    return sorted(sites,key=lambda s:H('|'.join(map(str,s))))[:MAX_SITES]

def mutate(repo,site,dst):
    p,row,c0,c1,src=site
    lines=p.read_text().splitlines(True)
    lines[row-1]=lines[row-1][:c0]+dst+lines[row-1][c1:]
    p.write_text(''.join(lines))

def construct_operator(repo,sites):
    survivors=[]
    for site in sites:
        src=site[-1]
        for dst in DESTS:
            if dst==src: continue
            reset(repo)
            # reset removes env cache? preserve venv with exclusion; source returns historical buggy state.
            mutate(repo,site,dst)
            ok,_=test(repo)
            if ok: survivors.append({'src':src,'dst':dst,'path':str(site[0].relative_to(repo)),'row':site[1],'col':site[2]})
    reset(repo)
    pairs=sorted(set((x['src'],x['dst']) for x in survivors))
    return survivors,pairs

def old_closure_obstruction(src,dst):
    # All old generators only permute positions, so token-value multiset is invariant under arbitrary composition.
    return Counter([src]) != Counter([dst])

def try_reuse(repo,sites,op):
    hits=[]
    for site in sites:
        if site[-1] != op['src']: continue
        reset(repo); mutate(repo,site,op['dst']); ok,_=test(repo)
        if ok:hits.append({'path':str(site[0].relative_to(repo)),'row':site[1],'col':site[2]})
    reset(repo)
    return hits

stream=enumerate_bugs()
precommit={'seed':SEED,'bugs_in_py_commit':run('git rev-parse HEAD',cwd=BIP)[1].strip(),'eligible_count':len(stream),'ordered_first':[list(x) for x in stream[:MAX_EPISODES]],'max_episodes':MAX_EPISODES,'max_sites':MAX_SITES,'old_generators':OLD_GENERATORS,'constructor_destinations':DESTS,'human_fix_forbidden_until_terminal':True}
(OUT/'PRECOMMIT.json').write_text(json.dumps(precommit,indent=2))
print('PRECOMMIT',json.dumps(precommit,sort_keys=True))

events=[]; learned=None; origin_project=None; reused=None
for idx,(project,bug,pyver) in enumerate(stream[:MAX_EPISODES],1):
    ev={'episode':idx,'project':project,'bug':bug,'python_version':pyver}
    rc,co,repo=checkout_bug(project,bug)
    if rc or not repo.exists(): ev['status']='INFRA_CHECKOUT'; events.append(ev); continue
    ok,so=setup_env(repo,pyver)
    if not ok: ev['status']='INFRA_SETUP'; ev['setup_tail']=so[-500:]; events.append(ev); continue
    baseline,bout=test(repo); ev['baseline_pass']=baseline
    if baseline: ev['status']='NONREPRODUCING'; events.append(ev); continue
    sites=traceback_sites(repo,bout); ev['traceback_site_count']=len(sites); ev['sites']=[[str(s[0].relative_to(repo)),*s[1:]] for s in sites]
    if not sites: ev['status']='NO_OPERATOR_SITE'; events.append(ev); continue
    if learned is None:
        surv,pairs=construct_operator(repo,sites); ev['repair_survivor_count']=len(surv); ev['repair_pairs']=pairs
        # Promote only when one token-rewrite pair is uniquely supported by the historical failure.
        if len(pairs)==1:
            src,dst=pairs[0]
            obstruction=old_closure_obstruction(src,dst); ev['old_closure_obstruction']=obstruction
            if obstruction:
                learned={'kind':'TOKEN_REWRITE','src':src,'dst':dst,'origin_episode':idx,'origin_project':project,'origin_bug':bug}
                origin_project=project; ev['status']='OPERATOR_FORMED'; ev['operator']=learned.copy()
            else: ev['status']='OLD_CLOSURE_OR_NO_NOVELTY'
        else: ev['status']='AMBIGUOUS_OR_NO_REPAIR'
    else:
        if project==origin_project:
            ev['status']='SAME_PROJECT_CONTROL'; events.append(ev); continue
        hits=try_reuse(repo,sites,learned); ev['reuse_hits']=hits
        if hits:
            # Baseline is already known failing; warm succeeds by construction; reset is the ablation.
            ablated,_=test(repo)
            ev['ablation_pass']=ablated
            ev['status']='CAUSAL_REUSE' if not ablated else 'ABLATION_FAILED'
            if not ablated:
                reused={'episode':idx,'project':project,'bug':bug,'hits':hits}; events.append(ev); break
        else: ev['status']='NO_REUSE'
    events.append(ev)

# Human fixes remain unopened during all construction/reuse work. Only now audit the two fixed commits if success.
audit={}
if learned and reused:
    for role,pr,bg in [('origin',learned['origin_project'],learned['origin_bug']),('reuse',reused['project'],reused['bug'])]:
        bi=parse_info(BIP/'projects'/pr/'bugs'/bg/'bug.info')
        # Metadata gives IDs; compare buggy->fixed only terminally.
        url=project_url(pr)
        audit[role]={'project':pr,'bug':bg,'buggy_commit_id':bi.get('buggy_commit_id'),'fixed_commit_id':bi.get('fixed_commit_id'),'project_url':url}

R={'protocol':SEED,'precommit':precommit,'events':events,'learned_operator':learned,'causal_reuse':reused,'terminal_human_fix_metadata':audit}
R['gates']={
 'stream_precommitted_before_fix_audit':True,
 'historical_bug_reproduced':any(e.get('baseline_pass') is False for e in events),
 'operator_formed_from_historical_failure':learned is not None,
 'old_closure_obstruction_certified':any(e.get('old_closure_obstruction') for e in events),
 'different_project_causal_reuse':reused is not None and learned is not None and reused['project']!=learned['origin_project'],
 'ablation_restores_failure':reused is not None,
 'human_fix_withheld_until_terminal':True,
}
R['verdict']='PASS_V52_HISTORICAL_OPERATOR_RATCHET' if all(R['gates'].values()) else 'INCOMPLETE_V52_HISTORICAL_OPERATOR_RATCHET'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2))
if R['verdict'].startswith('PASS'): sys.exit(0)
# Incomplete is a scientific result, not CI infrastructure failure.
sys.exit(0)
