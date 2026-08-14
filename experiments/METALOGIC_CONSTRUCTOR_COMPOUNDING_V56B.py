import io,json,keyword,subprocess,tokenize,os
from pathlib import Path
OUT=Path('artifacts/v56b');OUT.mkdir(parents=True,exist_ok=True)
DJ=Path('/tmp/v56_django');RQ=Path('/tmp/v56_requests')
NAMES=sorted(set(keyword.kwlist+['None','True','False'])); OPS=sorted(s for s in tokenize.EXACT_TOKEN_TYPES if 1<=len(s)<=2)

def sh(cmd,cwd,t=45):
 e=os.environ.copy();e['PYTHONDONTWRITEBYTECODE']='1';subprocess.run("find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true",cwd=cwd,shell=True)
 try:
  p=subprocess.run(cmd,cwd=cwd,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=t,env=e);return p.returncode==0
 except subprocess.TimeoutExpired:return False
def reset(r):subprocess.run('git reset --hard -q HEAD && git clean -fdxq',cwd=r,shell=True,check=True)
def ts(p,row):return [t for t in tokenize.generate_tokens(io.StringIO(p.read_text()).readline) if t.start[0]==row and t.type in (tokenize.NAME,tokenize.OP,tokenize.NUMBER)]
def line(p,row):return p.read_text().splitlines(True)[row-1]
def setline(p,row,s):ls=p.read_text().splitlines(True);ls[row-1]=s; p.write_text(''.join(ls))
def test_dj():return sh('python tests/runtests.py backends.test_utils.TestUtils.test_truncate_name --verbosity 0',DJ)
def test_rq():return sh('timeout 8s pytest -q tests/test_utils.py -k test_iter_slices',RQ,15)
def findrow(p,needle):
 for i,s in enumerate(p.read_text().splitlines(),1):
  if needle in s:return i
 raise RuntimeError(needle)
def remove_token(p,row,val):
 xs=[t for t in ts(p,row) if t.string==val];assert xs
 t=xs[0];s=line(p,row);setline(p,row,s[:t.start[1]]+s[t.end[1]:]);return t.start[1]
def gaps(p,row):
 x=ts(p,row);return sorted(set([0,len(line(p,row).rstrip('\n'))]+[t.start[1] for t in x]+[t.end[1] for t in x]))
def insert(p,row,col,tok):
 s=line(p,row); left=' ' if col>0 and not s[col-1].isspace() else ''; right=' ' if col<len(s) and not s[col].isspace() else '';setline(p,row,s[:col]+left+tok+right+s[col:])
def search_insert(repo,p,row,test,vocab):
 base=p.read_text();wins=[]
 for c in gaps(p,row):
  for tok in vocab:
   p.write_text(base);insert(p,row,c,tok)
   if test():wins.append((c,tok))
 p.write_text(base);return wins
# G1: delete a NAME from valid Django, K0 rewrite-only cannot restore token count.
dj=DJ/'django/db/backends/utils.py';r1=findrow(dj,'if length is None or len(name) <= length:');reset(DJ);assert test_dj();remove_token(dj,r1,'or');broken1=test_dj();name1=search_insert(DJ,dj,r1,test_dj,NAMES);op1=search_insert(DJ,dj,r1,test_dj,OPS);families1=[k for k,v in [('NAME',name1),('OP',op1)] if v];K1='INSERT_NAME' if families1==['NAME'] else None
# G2: two omissions, one NAME and one OP.
rq=RQ/'src/requests/utils.py';r2=findrow(rq,'if slice_length is None or slice_length <= 0:')
def dbl():reset(RQ);remove_token(rq,r2,'or');remove_token(rq,r2,'<=')
def find_k1_application():
 if K1!='INSERT_NAME':return None
 dbl();base=rq.read_text();good=[]
 for c in gaps(rq,r2):
  for tok in NAMES:
   rq.write_text(base);insert(rq,r2,c,tok);mid=rq.read_text();ops=search_insert(RQ,rq,r2,test_rq,OPS);rq.write_text(mid)
   if ops:good.append((c,tok,ops))
 rq.write_text(base);return good
# cold one-family cannot solve both
dbl();coldN=search_insert(RQ,rq,r2,test_rq,NAMES);dbl();coldO=search_insert(RQ,rq,r2,test_rq,OPS)
good=find_k1_application() or [];k1_applied=False
if len(good)==1:
 dbl();c,tok,_=good[0];insert(rq,r2,c,tok);k1_applied=True
mid=test_rq();warmN=search_insert(RQ,rq,r2,test_rq,NAMES);warmO=search_insert(RQ,rq,r2,test_rq,OPS);families2=[k for k,v in [('NAME',warmN),('OP',warmO)] if v];K2='INSERT_OP' if families2==['OP'] else None
final=False
if K2 and len(warmO)==1:
 c,t=warmO[0];insert(rq,r2,c,t);final=test_rq()
# ablate K1; K2 family alone must not solve
dbl();ablwins=search_insert(RQ,rq,r2,test_rq,OPS);ablated=bool(ablwins)
R={'protocol':'V56B_CONSTRUCTOR_COMPOUNDING','generation1':{'broken_passes':broken1,'name_wins':name1,'op_wins':op1,'families':families1,'K1':K1},'generation2':{'cold_name':coldN,'cold_op':coldO,'K1_candidates':good,'K1_applied':k1_applied,'after_K1':mid,'warm_name':warmN,'warm_op':warmO,'families':families2,'K2':K2,'final':final,'ablated_K1_K2_wins':ablwins}}
R['gates']={'K0_obstructed':not broken1,'K1_constructed':K1 is not None,'K1_outside_K0':K1 is not None,'K2_cold_absent':not(coldN or coldO),'K1_exposes_K2':k1_applied and not mid,'K2_constructed':K2 is not None,'K1_K2_solve':final,'K1_ablation_kills':not ablated};R['verdict']='PASS_V56B_CONSTRUCTOR_COMPOUNDING' if all(R['gates'].values()) else 'FAIL_V56B_CONSTRUCTOR_COMPOUNDING';(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2));raise SystemExit(0 if R['verdict'].startswith('PASS') else 1)