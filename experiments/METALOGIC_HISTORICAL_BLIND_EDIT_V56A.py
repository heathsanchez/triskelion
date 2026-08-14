import hashlib,io,json,os,re,shutil,subprocess,sys,tokenize,keyword
from pathlib import Path
from collections import Counter
SEED='V56A_HISTORICAL_BLIND_EDIT_20260814';BIP=Path('/tmp/BugsInPy');WORK=Path('/tmp/v56a');OUT=Path('artifacts/v56a');OUT.mkdir(parents=True,exist_ok=True);WORK.mkdir(exist_ok=True)
CANDS=[('PySnooper','1','3.8.1'),('PySnooper','2','3.8.1'),('black','13','3.8.3'),('black','17','3.8.3'),('black','19','3.8.3'),('matplotlib','4','3.8.1'),('matplotlib','25','3.8.1'),('tqdm','1','3.6.9'),('httpie','5','3.6.9')]
MAX_READY=4;MAX_SITES=24;VOC=sorted(set([s for s in tokenize.EXACT_TOKEN_TYPES if 1<=len(s)<=2]+keyword.kwlist+['None','True','False']))[:40]
def H(x):return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def run(c,cwd=None,t=90,env=None):
 try:p=subprocess.run(c,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=t,env=env);return p.returncode,p.stdout
 except subprocess.TimeoutExpired as e:
  x=e.stdout or '';x=x.decode(errors='replace') if isinstance(x,bytes) else x;return 124,x+'\nTIMEOUT'
def info(p):
 d={}
 if p.exists():
  for s in p.read_text(errors='ignore').splitlines():
   m=re.match(r'(\w+)="(.*)"',s.strip());
   if m:d[m.group(1)]=m.group(2)
 return d
def checkout(pr,bg):
 root=WORK/f'{pr}_{bg}';shutil.rmtree(root,ignore_errors=True);root.mkdir(parents=True);rc,o=run(f'export BUGSINPY_HOME={BIP};export PATH={BIP}/framework/bin:$PATH;bugsinpy-checkout -p {pr} -i {bg} -v 0 -w {root}',t=90);return rc,o,root/pr
def dec(p):
 b=p.read_bytes();
 if b'\x00' in b:
  for e in ('utf-16','utf-16le','utf-16be'):
   try:return b.decode(e)
   except:pass
 return b.decode(errors='ignore')
def setup(repo,py):
 mm='.'.join(py.split('.')[:2]);rc,o=run(f'uv python install {mm} && uv venv --seed --python {mm} .venv',repo,70)
 if rc:return False,o
 pip=repo/'.venv/bin/pip';run(f'{pip} install -q "pip<24" "setuptools<69" "wheel<0.43"',repo,45);req=repo/'bugsinpy_requirements.txt'
 if req.exists():
  ls=[]
  for s in dec(req).splitlines():
   s=s.strip();lo=s.lower()
   if not s or s.startswith('#') or 'pywin32' in lo or 'requests-async' in lo:continue
   ls.append(s)
  (repo/'.req').write_text('\n'.join(ls));rc,o=run(f'{pip} install -q --use-deprecated=legacy-resolver -r .req',repo,120)
  if rc:return False,o
 e=os.environ.copy();e['PATH']=str(repo/'.venv/bin')+':'+e.get('PATH','');st=repo/'bugsinpy_setup.sh'
 if st.exists():
  rc,o=run('bash bugsinpy_setup.sh',repo,60,e)
  if rc:return False,o
 return True,''
def env(repo):e=os.environ.copy();e['PATH']=str(repo/'.venv/bin')+':'+e.get('PATH','');e['PYTHONDONTWRITEBYTECODE']='1';return e
def test(repo):
 p=repo/'bugsinpy_run_test.sh';return (False,'NO_TEST') if not p.exists() else (lambda z:(z[0]==0,z[1]))(run('bash bugsinpy_run_test.sh',repo,45,env(repo)))
def reset(repo):run('git reset --hard -q HEAD && git clean -fdxq -e .venv -e bugsinpy_run_test.sh -e bugsinpy_setup.sh -e bugsinpy_requirements.txt -e .req',repo,20)
def toks(p):
 try:return list(tokenize.generate_tokens(io.StringIO(p.read_text(errors='ignore')).readline))
 except:return []
def sites(repo,out):
 ranked=[];frames=[]
 for m in re.finditer(r'File "([^"]+\.py)", line (\d+)',out):
  p=Path(m.group(1));p=p if p.is_absolute() else repo/p
  try:rel=p.resolve().relative_to(repo.resolve())
  except:continue
  if p.exists() and 'test' not in rel.parts:frames.append((p,int(m.group(2))))
 for p,ln in frames:
  for t in toks(p):
   if t.type in (tokenize.OP,tokenize.NAME) and abs(t.start[0]-ln)<=3:ranked.append((p,t.start[0],t.start[1],t.end[1],t.string))
 # Blind fallback: hash-ranked package source operator/name sites, no fix information.
 if not ranked:
  for p in repo.rglob('*.py'):
   try:rel=p.relative_to(repo)
   except:continue
   if any(x in rel.parts for x in ('tests','test','.venv')):continue
   for t in toks(p):
    if t.type in (tokenize.OP,tokenize.NAME):ranked.append((p,t.start[0],t.start[1],t.end[1],t.string))
 return sorted(set(ranked),key=lambda s:H('|'.join(map(str,s))))[:MAX_SITES]
def edit(site,text):
 p,r,a,b,_=site;ls=p.read_text().splitlines(True);ls[r-1]=ls[r-1][:a]+text+ls[r-1][b:];p.write_text(''.join(ls))
def construct(repo,S):
 wins=[]
 for s in S:
  src=s[-1]
  # rewrite generic bounded vocabulary
  for d in VOC[:20]:
   if d==src:continue
   reset(repo);edit(s,d);ok,_=test(repo)
   if ok:wins.append(('REWRITE',src,d))
  reset(repo);edit(s,'');ok,_=test(repo)
  if ok:wins.append(('DELETE',src,''))
  # insert immediately before site, generic token
  for d in VOC[:12]:
   reset(repo);p,r,a,b,_=s;ls=p.read_text().splitlines(True);ls[r-1]=ls[r-1][:a]+d+' '+ls[r-1][a:];p.write_text(''.join(ls));ok,_=test(repo)
   if ok:wins.append(('INSERT','',d))
 reset(repo);return sorted(set(wins))
def reuse(repo,S,op):
 hits=[]
 for s in S:
  typ,src,dst=op
  if typ in {'REWRITE','DELETE'} and s[-1]!=src:continue
  reset(repo)
  if typ=='REWRITE':edit(s,dst)
  elif typ=='DELETE':edit(s,'')
  else:
   p,r,a,b,_=s;ls=p.read_text().splitlines(True);ls[r-1]=ls[r-1][:a]+dst+' '+ls[r-1][a:];p.write_text(''.join(ls))
  ok,_=test(repo)
  if ok:hits.append([str(s[0].relative_to(repo)),s[1],s[2]])
 reset(repo);return hits
order=sorted(CANDS,key=lambda x:H('|'.join(x)));pre={'seed':SEED,'order':order,'human_fix_forbidden':True,'max_sites':MAX_SITES,'constructor':['REWRITE','DELETE','INSERT']};print('PRECOMMIT',json.dumps(pre));ready=[];screen=[]
for pr,bg,py in order:
 ev={'project':pr,'bug':bg};rc,o,repo=checkout(pr,bg)
 if rc or not repo.exists():ev['status']='CHECKOUT';screen.append(ev);continue
 good,o=setup(repo,py)
 if not good:ev['status']='SETUP';screen.append(ev);continue
 base,out=test(repo);ev['baseline']=base
 if base:ev['status']='NONREPRO';screen.append(ev);continue
 S=sites(repo,out);ev['sites']=len(S)
 if not S:ev['status']='NO_SITES';screen.append(ev);continue
 ev['status']='READY';ready.append((pr,bg,py));screen.append(ev)
 if len(ready)>=MAX_READY:break
learn=None;origin=None;reused=None;events=[]
for i,(pr,bg,py) in enumerate(ready,1):
 rc,o,repo=checkout(pr,bg);good,o=setup(repo,py);base,out=test(repo);S=sites(repo,out);ev={'episode':i,'project':pr,'bug':bg,'baseline':base,'site_count':len(S)}
 if learn is None:
  w=construct(repo,S);ev['wins']=w
  if len(w)==1:learn=w[0];origin=pr;ev['status']='FORMED';ev['operator']=learn
  else:ev['status']='AMBIGUOUS'
 else:
  if pr==origin:ev['status']='SAME_PROJECT'
  else:
   h=reuse(repo,S,learn);ev['hits']=h
   if h:
    ab,_=test(repo);ev['ablation_pass']=ab;ev['status']='REUSE' if not ab else 'ABLATION_FAIL'
    if not ab:reused={'project':pr,'bug':bg,'hits':h};events.append(ev);break
   else:ev['status']='NO_REUSE'
 events.append(ev)
R={'protocol':SEED,'precommit':pre,'screen':screen,'ready':ready,'events':events,'operator':learn,'reuse':reused};R['gates']={'three_clean_worlds':len(ready)>=3,'operator_formed':learn is not None,'different_project_reuse':bool(reused and origin and reused['project']!=origin),'ablation_failure_restored':bool(reused),'fix_withheld':True};R['verdict']='PASS_V56A_HISTORICAL_BLIND_EDIT' if all(R['gates'].values()) else 'INCOMPLETE_V56A_HISTORICAL_BLIND_EDIT';(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))