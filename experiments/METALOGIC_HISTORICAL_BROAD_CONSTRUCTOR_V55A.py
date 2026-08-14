import hashlib, io, json, keyword, os, re, shutil, subprocess, sys, tokenize
from collections import Counter
from pathlib import Path

SEED='V55A_HISTORICAL_BROAD_CONSTRUCTOR_20260814'
BIP=Path('/tmp/BugsInPy'); WORK=Path('/tmp/v55a_work'); OUT=Path('artifacts/v55a')
WORK.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
CANDIDATES=[
 ('PySnooper','1','3.8.1'),('PySnooper','2','3.8.1'),('PySnooper','3','3.8.1'),
 ('black','13','3.8.3'),('black','17','3.8.3'),('black','19','3.8.3'),
 ('matplotlib','4','3.8.1'),('matplotlib','25','3.8.1'),
 ('fastapi','11','3.8.3'),('fastapi','16','3.8.3'),
 ('scrapy','7','3.8.3'),('scrapy','16','3.8.3'),
 ('sanic','2','3.8.3'),('sanic','4','3.8.3'),('luigi','2','3.8.3'),('luigi','14','3.8.3')]
MAX_READY=6; MAX_SITES=8; MAX_DESTS=12
OLD=['IDENTITY','REVERSE_WINDOW','ROTATE_LEFT','ROTATE_RIGHT','SWAP_ADJACENT']

def H(x):return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def run(cmd,cwd=None,t=90,env=None):
    try:
        p=subprocess.run(cmd,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=t,env=env);return p.returncode,p.stdout
    except subprocess.TimeoutExpired as e:
        x=e.stdout or ''
        if isinstance(x,bytes):x=x.decode(errors='replace')
        return 124,x+'\nTIMEOUT'
def info(path):
    d={}
    if not path.exists():return d
    for s in path.read_text(errors='ignore').splitlines():
        m=re.match(r'(\w+)="(.*)"',s.strip())
        if m:d[m.group(1)]=m.group(2)
    return d
def checkout(pr,bg):
    root=WORK/f'{pr}_{bg}';shutil.rmtree(root,ignore_errors=True);root.mkdir(parents=True)
    cmd=f'export BUGSINPY_HOME={BIP}; export PATH={BIP}/framework/bin:$PATH; bugsinpy-checkout -p {pr} -i {bg} -v 0 -w {root}'
    rc,o=run(cmd,t=90);return rc,o,root/pr
def decode_req(p):
    b=p.read_bytes()
    if b'\x00' in b:
        for enc in ('utf-16','utf-16le','utf-16be'):
            try:return b.decode(enc)
            except:pass
    return b.decode(errors='ignore')
def setup(repo,py):
    mm='.'.join(py.split('.')[:2]);rc,o=run(f'uv python install {mm} && uv venv --seed --python {mm} .v55env',repo,70)
    if rc:return False,o
    pip=repo/'.v55env/bin/pip';run(f'{pip} install -q "pip<24" "setuptools<69" "wheel<0.43"',repo,45)
    req=repo/'bugsinpy_requirements.txt';chunks=[]
    if req.exists():
        lines=[s.strip() for s in decode_req(req).splitlines() if s.strip() and not s.lstrip().startswith('#') and 'pywin32' not in s.lower()]
        (repo/'.v55req.txt').write_text('\n'.join(lines))
        if lines:
            rc,x=run(f'{pip} install -q -r .v55req.txt',repo,120);chunks.append(x)
            if rc:return False,'\n'.join(chunks)
    e=os.environ.copy();e['PATH']=str(repo/'.v55env/bin')+':'+e.get('PATH','')
    if (repo/'bugsinpy_setup.sh').exists():
        rc,x=run('bash bugsinpy_setup.sh',repo,60,e);chunks.append(x)
        if rc:return False,'\n'.join(chunks)
    return True,'\n'.join(chunks)
def env(repo):
    e=os.environ.copy();e['PATH']=str(repo/'.v55env/bin')+':'+e.get('PATH','');return e
def test(repo):
    if not (repo/'bugsinpy_run_test.sh').exists():return False,'NO_RUN_TEST'
    rc,o=run('bash bugsinpy_run_test.sh',repo,45,env(repo));return rc==0,o
def reset(repo):run('git reset --hard -q HEAD && git clean -fdxq -e .v55env -e bugsinpy_run_test.sh -e bugsinpy_setup.sh -e bugsinpy_requirements.txt -e .v55req.txt',repo,25)

def source_frames(repo,out):
    ans=[];seen=set()
    for m in reversed(list(re.finditer(r'File "([^"]+\.py)", line (\d+)',out))):
        p=Path(m.group(1));ln=int(m.group(2));p=p if p.is_absolute() else repo/p
        try:rel=p.resolve().relative_to(repo.resolve())
        except:continue
        if not p.exists() or 'test' in rel.parts or str(rel).startswith(('tests/','test/')):continue
        k=(str(p),ln)
        if k not in seen:seen.add(k);ans.append((p,ln))
    return ans

def candidate_sites(repo,out):
    ss=[]
    for p,ln in source_frames(repo,out):
        try:ts=list(tokenize.generate_tokens(io.StringIO(p.read_text(errors='ignore')).readline))
        except:continue
        for t in ts:
            if abs(t.start[0]-ln)<=2 and t.type in (tokenize.OP,tokenize.NAME,tokenize.STRING,tokenize.NUMBER):
                ss.append((p,t.start[0],t.start[1],t.end[1],t.type,t.string))
    return sorted(ss,key=lambda x:H('|'.join(map(str,x))))[:MAX_SITES]

def file_vocab(path,typ):
    try:ts=list(tokenize.generate_tokens(io.StringIO(path.read_text(errors='ignore')).readline))
    except:return []
    vals=sorted(set(t.string for t in ts if t.type==typ))
    if typ==tokenize.NAME:vals=sorted(set(vals+keyword.kwlist+['None','True','False']))
    if typ==tokenize.OP:vals=sorted(set(vals+[s for s in tokenize.EXACT_TOKEN_TYPES if len(s)<=2]))
    if typ==tokenize.NUMBER:vals=sorted(set(vals+['0','1']))
    return sorted(vals,key=lambda x:H('dst|'+x))[:MAX_DESTS]

def mutate(site,dst):
    p,row,c0,c1,typ,src=site;ls=p.read_text().splitlines(True);ls[row-1]=ls[row-1][:c0]+dst+ls[row-1][c1:];p.write_text(''.join(ls))

def construct(repo,sites):
    wins=[]
    for s in sites:
        for d in file_vocab(s[0],s[4]):
            if d==s[5]:continue
            reset(repo)
            try:mutate(s,d)
            except:continue
            ok,_=test(repo)
            if ok:wins.append({'src':s[5],'dst':d,'type':s[4],'path':str(s[0].relative_to(repo)),'row':s[1],'col':s[2]})
    reset(repo);pairs=sorted(set((w['type'],w['src'],w['dst']) for w in wins));return pairs,wins

def reuse(repo,sites,op):
    hits=[]
    for s in sites:
        if s[4]!=op['type'] or s[5]!=op['src']:continue
        reset(repo);mutate(s,op['dst']);ok,_=test(repo)
        if ok:hits.append({'path':str(s[0].relative_to(repo)),'row':s[1],'col':s[2]})
    reset(repo);return hits

order=sorted(CANDIDATES,key=lambda x:H('|'.join(x)));pre={'seed':SEED,'candidate_order':order,'max_ready':MAX_READY,'max_sites':MAX_SITES,'max_destinations_per_site':MAX_DESTS,'old_generators':OLD,'human_fix_forbidden':True}
(OUT/'PRECOMMIT.json').write_text(json.dumps(pre,indent=2));print('PRECOMMIT',json.dumps(pre,sort_keys=True))
ready=[];screen=[]
for pr,bg,py in order:
    ev={'project':pr,'bug':bg,'python':py};rc,o,repo=checkout(pr,bg)
    if rc or not repo.exists():ev['status']='CHECKOUT_FAIL';screen.append(ev);continue
    good,so=setup(repo,py)
    if not good:ev['status']='SETUP_FAIL';ev['tail']=so[-250:];screen.append(ev);continue
    base,bout=test(repo);ev['baseline_pass']=base
    if base:ev['status']='NONREPRODUCING';screen.append(ev);continue
    ss=candidate_sites(repo,bout);ev['site_count']=len(ss)
    if not ss:ev['status']='NO_LOCALIZED_TOKEN_SITE';screen.append(ev);continue
    ev['status']='READY';ready.append((pr,bg,py));screen.append(ev)
    if len(ready)>=MAX_READY:break

events=[];learned=None;origin=None;reused=None
for idx,(pr,bg,py) in enumerate(ready,1):
    ev={'episode':idx,'project':pr,'bug':bg,'python':py};rc,o,repo=checkout(pr,bg);good,so=setup(repo,py)
    if rc or not good:ev['status']='INFRA_FAIL';events.append(ev);continue
    base,bout=test(repo);ev['baseline_pass']=base;ss=candidate_sites(repo,bout);ev['site_count']=len(ss)
    if learned is None:
        pairs,wins=construct(repo,ss);ev['repair_pairs']=pairs;ev['win_count']=len(wins)
        if len(pairs)==1:
            typ,src,dst=pairs[0];ob=Counter([src])!=Counter([dst]);ev['old_closure_obstruction']=ob
            if ob:learned={'kind':'TOKEN_REWRITE','type':typ,'src':src,'dst':dst,'origin_project':pr,'origin_bug':bg};origin=pr;ev['status']='OPERATOR_FORMED';ev['operator']=learned
            else:ev['status']='NO_NOVELTY'
        else:ev['status']='AMBIGUOUS_OR_NO_REPAIR'
    else:
        if pr==origin:ev['status']='SAME_PROJECT_CONTROL'
        else:
            hits=reuse(repo,ss,learned);ev['reuse_hits']=hits
            if hits:
                reset(repo);ab,_=test(repo);ev['ablation_pass']=ab
                if not ab:ev['status']='CAUSAL_REUSE';reused={'project':pr,'bug':bg,'hits':hits};events.append(ev);break
                ev['status']='ABLATION_FAILED'
            else:ev['status']='NO_REUSE'
    events.append(ev)
R={'protocol':SEED,'precommit':pre,'screen':screen,'ready':ready,'events':events,'learned_operator':learned,'causal_reuse':reused}
R['gates']={'at_least_three_clean_worlds':len(ready)>=3,'historical_failures_reproduced':any(e.get('baseline_pass') is False for e in events),'operator_formed':learned is not None,'old_closure_obstruction':any(e.get('old_closure_obstruction') for e in events),'different_project_reuse':bool(reused and learned and reused['project']!=learned['origin_project']),'ablation_restores_failure':bool(reused),'human_fix_withheld':True}
R['verdict']='PASS_V55A_HISTORICAL_NATURAL_REPLICATION' if all(R['gates'].values()) else 'INCOMPLETE_V55A_HISTORICAL_NATURAL_REPLICATION'
R['claim_boundary']='Real historical BugsInPy failures, fixed patches withheld. Broader same-token-type rewrite constructor and traceback-localized sites are supplied. A pass requires different-project causal reuse.'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2));sys.exit(0)
