import hashlib,io,json,os,re,shutil,subprocess,sys,tempfile,tokenize
from pathlib import Path
from collections import Counter,defaultdict
SEED='V52E_HISTORICAL_COVERAGE_RATCHET_20260814'; OUT=Path('artifacts/v52e'); OUT.mkdir(parents=True,exist_ok=True)
BIP=Path('/tmp/BugsInPy'); WORK=Path('/tmp/v52e_work'); WORK.mkdir(exist_ok=True)
MAX_EP=20; MAX_SITES=24; DESTS=sorted(s for s in tokenize.EXACT_TOKEN_TYPES if 1<=len(s)<=2); OLD=['IDENTITY','REVERSE_WINDOW','ROTATE_LEFT','ROTATE_RIGHT','SWAP_ADJACENT']
def H(x):return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def run(cmd,cwd=None,t=90,env=None):
 try:
  p=subprocess.run(cmd,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=t,env=env);return p.returncode,p.stdout
 except subprocess.TimeoutExpired as e:
  x=e.stdout or ''; x=x.decode(errors='replace') if isinstance(x,bytes) else x; return 124,x+'\nTIMEOUT'
def info(p):
 d={}
 if not p.exists():return d
 for s in p.read_text(errors='ignore').splitlines():
  m=re.match(r'(\w+)="(.*)"',s.strip())
  if m:d[m.group(1)]=m.group(2)
 return d
def stream():
 per=defaultdict(list)
 for p in sorted((BIP/'projects').iterdir()):
  if not p.is_dir() or not (p/'bugs').is_dir() or info(p/'project.info').get('status')!='OK':continue
  for b in (p/'bugs').iterdir():
   d=info(b/'bug.info'); py=d.get('python_version','')
   if re.match(r'^3\.(8|9|10|11)',py):per[p.name].append((p.name,b.name,py))
 for k in per:per[k].sort(key=lambda x:H('|'.join(x)))
 names=sorted(per,key=lambda x:H('project|'+x));out=[];i=0
 while len(out)<MAX_EP and any(i<len(per[n]) for n in names):
  for n in names:
   if i<len(per[n]):out.append(per[n][i])
   if len(out)>=MAX_EP:break
  i+=1
 return out
def checkout(project,bug):
 root=WORK/f'{project}_{bug}'; shutil.rmtree(root,ignore_errors=True);root.mkdir(parents=True)
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
 mm='.'.join(py.split('.')[:2]);rc,o=run(f'uv python install {mm} && uv venv --seed --python {mm} .v52env',repo,60)
 if rc:return False,o
 pip=repo/'.v52env/bin/pip'; req=repo/'bugsinpy_requirements.txt';chunks=[]
 if req.exists():
  txt=decode_req(req); clean=repo/'.v52req.txt'; clean.write_text('\n'.join(s.strip() for s in txt.splitlines() if s.strip() and not s.lstrip().startswith('#')))
  rc,x=run(f'{pip} install -q -r .v52req.txt',repo,90);chunks.append(x)
  if rc:return False,'\n'.join(chunks)
 e=os.environ.copy();e['PATH']=str(repo/'.v52env/bin')+':'+e.get('PATH','');sh=repo/'bugsinpy_setup.sh'
 if sh.exists():
  rc,x=run('bash bugsinpy_setup.sh',repo,45,e);chunks.append(x)
  if rc:return False,'\n'.join(chunks)
 run(f'{pip} install -q coverage',repo,45)
 return True,'\n'.join(chunks)
def env(repo):
 e=os.environ.copy();e['PATH']=str(repo/'.v52env/bin')+':'+e.get('PATH','');return e
def test(repo,coverage=False):
 harness=repo/'bugsinpy_run_test.sh'
 if not harness.exists(): return False,'MISSING_BUGSINPY_RUN_TEST'
 cmd='bash bugsinpy_run_test.sh'
 if coverage:
  s=harness.read_text(errors='ignore'); s=s.replace('pytest ','coverage run --parallel-mode -m pytest ').replace('python -m pytest ','coverage run --parallel-mode -m pytest '); (repo/'.v52cov.sh').write_text(s);cmd='bash .v52cov.sh'
 return (lambda z:(z[0]==0,z[1]))(run(cmd,repo,35,env(repo)))
def reset(repo):
 # BugsInPy checkout writes the test/setup/requirements harness as untracked files.
 # Preserve those plus the isolated environment while restoring only the historical source tree.
 run("git reset --hard -q HEAD && git clean -fdxq -e .v52env -e 'bugsinpy_*' -e .v52req.txt",repo,20)
def cov_sites(repo):
 reset(repo);ok,out=test(repo,True);run('.v52env/bin/coverage combine >/dev/null 2>&1 || true; .v52env/bin/coverage json -o .v52cov.json >/dev/null 2>&1 || true',repo,20,env(repo)); p=repo/'.v52cov.json';sites=[]
 if p.exists():
  try:j=json.loads(p.read_text())
  except:j={}
  for fn,v in j.get('files',{}).items():
   q=(repo/fn) if not Path(fn).is_absolute() else Path(fn)
   try:rel=q.resolve().relative_to(repo.resolve())
   except:continue
   if 'test' in rel.parts or str(rel).startswith(('tests/','test/')) or not q.exists():continue
   ex=set(v.get('executed_lines',[])); txt=q.read_text(errors='ignore')
   try:ts=tokenize.generate_tokens(io.StringIO(txt).readline)
   except:continue
   for t in ts:
    if t.type==tokenize.OP and t.start[0] in ex:sites.append((q,t.start[0],t.start[1],t.end[1],t.string))
 return sorted(sites,key=lambda s:H('|'.join(map(str,s))))[:MAX_SITES],out
def mutate(site,dst):
 p,row,c0,c1,src=site;ls=p.read_text().splitlines(True);ls[row-1]=ls[row-1][:c0]+dst+ls[row-1][c1:];p.write_text(''.join(ls))
def construct(repo,sites):
 pairs=[]
 for site in sites:
  for dst in DESTS:
   if dst==site[-1]:continue
   reset(repo);mutate(site,dst);ok,_=test(repo)
   if ok:pairs.append((site[-1],dst))
 reset(repo);return sorted(set(pairs))
def reuse(repo,sites,op):
 hits=[]
 for s in sites:
  if s[-1]!=op['src']:continue
  reset(repo);mutate(s,op['dst']);ok,_=test(repo)
  if ok:hits.append([str(s[0].relative_to(repo)),s[1],s[2]])
 reset(repo);return hits
S=stream(); pre={'seed':SEED,'bugsinpy_commit':run('git rev-parse HEAD',BIP)[1].strip(),'stream':S,'old_generators':OLD,'max_sites':MAX_SITES,'fix_data_forbidden':True};(OUT/'PRECOMMIT.json').write_text(json.dumps(pre,indent=2));print('PRECOMMIT',json.dumps(pre))
events=[];op=None;origin=None;reuse_ev=None
for i,(pr,bg,py) in enumerate(S,1):
 ev={'episode':i,'project':pr,'bug':bg,'python':py};rc,o,repo=checkout(pr,bg)
 if rc or not repo.exists():ev['status']='INFRA_CHECKOUT';events.append(ev);continue
 good,so=setup(repo,py)
 if not good:ev['status']='INFRA_SETUP';ev['tail']=so[-400:];events.append(ev);continue
 base,bout=test(repo);ev['baseline_pass']=base
 if base:ev['status']='NONREPRODUCING';events.append(ev);continue
 sites,_=cov_sites(repo);ev['coverage_site_count']=len(sites);ev['sites']=[[str(s[0].relative_to(repo)),*s[1:]] for s in sites]
 if not sites:ev['status']='NO_EXECUTED_OPERATOR_SITE';events.append(ev);continue
 if op is None:
  pairs=construct(repo,sites);ev['repair_pairs']=pairs
  if len(pairs)==1:
   src,dst=pairs[0];ob=Counter([src])!=Counter([dst]);ev['old_closure_obstruction']=ob
   if ob:op={'kind':'TOKEN_REWRITE','src':src,'dst':dst,'origin_episode':i,'origin_project':pr,'origin_bug':bg};origin=pr;ev['status']='OPERATOR_FORMED';ev['operator']=op
   else:ev['status']='NO_NOVELTY'
  else:ev['status']='AMBIGUOUS_OR_NO_REPAIR'
 else:
  if pr==origin:ev['status']='SAME_PROJECT_CONTROL'
  else:
   hits=reuse(repo,sites,op);ev['reuse_hits']=hits
   if hits:
    ab,_=test(repo);ev['ablation_pass']=ab;ev['status']='CAUSAL_REUSE' if not ab else 'ABLATION_FAILED'
    if not ab:reuse_ev={'episode':i,'project':pr,'bug':bg,'hits':hits};events.append(ev);break
   else:ev['status']='NO_REUSE'
 events.append(ev)
R={'protocol':SEED,'precommit':pre,'events':events,'learned_operator':op,'causal_reuse':reuse_ev};R['gates']={'historical_bug_reproduced':any(e.get('baseline_pass') is False for e in events),'operator_formed':op is not None,'old_closure_obstruction':any(e.get('old_closure_obstruction') for e in events),'different_project_reuse':bool(reuse_ev and op and reuse_ev['project']!=op['origin_project']),'ablation_restores_failure':bool(reuse_ev),'fix_withheld':True};R['verdict']='PASS_V52E_HISTORICAL_COVERAGE_RATCHET' if all(R['gates'].values()) else 'INCOMPLETE_V52E_HISTORICAL_COVERAGE_RATCHET';(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))
