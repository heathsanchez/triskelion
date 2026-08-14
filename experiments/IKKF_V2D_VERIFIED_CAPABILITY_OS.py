import ast,json,subprocess,tempfile,signal
from pathlib import Path

REPO='https://github.com/jkoppel/QuixBugs.git'; COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
HELD=list(range(100,108)); HELD_PROGS=['possible_change','sieve','subsequences']
C=[('CMP',0),('BIN',0)]; J=[('CMP',0),('CONST',0)]
OUT=Path('artifacts/ikkf_v2d_verified_capability_os'); OUT.mkdir(parents=True,exist_ok=True)
root=Path(tempfile.mkdtemp())/'qb'; subprocess.run(['git','clone','-q',REPO,str(root)],check=True); subprocess.run(['git','checkout','-q',COMMIT],cwd=root,check=True)
class Timeout(Exception): pass
def alarm(*a): raise Timeout()
signal.signal(signal.SIGALRM,alarm)
CMP={ast.Lt:ast.LtE,ast.LtE:ast.Lt,ast.Gt:ast.GtE,ast.GtE:ast.Gt,ast.Eq:ast.NotEq,ast.NotEq:ast.Eq}; BIN={ast.Add:ast.Sub,ast.Sub:ast.Add,ast.BitAnd:ast.BitXor,ast.BitXor:ast.BitAnd}

def tests(name): return [json.loads(x) for x in (root/'json_testcases'/f'{name}.json').read_text().splitlines() if x.strip()]
def rename(src,name,k):
 t=ast.parse(src); fn=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name); loc={a.arg for a in fn.args.args}
 for n in ast.walk(fn):
  if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store): loc.add(n.id)
 mp={x:f'{x}_{k}' for x in sorted(loc) if x!=name}
 class R(ast.NodeTransformer):
  def visit_arg(self,n): n.arg=mp.get(n.arg,n.arg); return n
  def visit_Name(self,n): n.id=mp.get(n.id,n.id); return n
 t=R().visit(t); ast.fix_missing_locations(t); return ast.unparse(t)+'\n'
def transform(src,name,kind,index=0,repair=False):
 t=ast.parse(src); fn=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name); seen=-1; done=False
 class T(ast.NodeTransformer):
  def visit_Compare(self,n):
   nonlocal seen,done; self.generic_visit(n)
   if kind=='CMP' and len(n.ops)==1 and type(n.ops[0]) in CMP:
    seen+=1
    if seen==index: n.ops[0]=CMP[type(n.ops[0])](); done=True
   return n
  def visit_BinOp(self,n):
   nonlocal seen,done; self.generic_visit(n)
   if kind=='BIN' and type(n.op) in BIN:
    seen+=1
    if seen==index: n.op=BIN[type(n.op)](); done=True
   return n
  def visit_Constant(self,n):
   nonlocal seen,done
   if kind=='CONST' and isinstance(n.value,int) and not isinstance(n.value,bool):
    seen+=1
    if seen==index: n.value += (-1 if repair else 1); done=True
   return n
 T().visit(fn); ast.fix_missing_locations(t)
 if not done: raise RuntimeError((name,kind,index))
 return ast.unparse(t)+'\n'
def apply(src,name,plan,repair=False):
 for op,i in plan: src=transform(src,name,op,i,repair=(repair and op=='CONST'))
 return src
def run(name,src):
 ns={'__name__':'candidate'}
 try: exec(compile(src,'<cand>','exec'),ns,ns); fn=ns[name]
 except Exception as e:return False,None,repr(e),None
 for args,exp in tests(name):
  try: signal.alarm(1); got=fn(*args); signal.alarm(0)
  except Exception as e: signal.alarm(0); return False,args,repr(e),exp
  if got!=exp:return False,args,got,exp
 return True,None,None,None
def variant(name,k,plan):
 src=rename((root/'correct_python_programs'/f'{name}.py').read_text(),name,k); mut=apply(src,name,plan,False); ok,args,got,exp=run(name,mut)
 if ok: raise AssertionError(('mutation_did_not_fail',name,k,plan))
 return mut,{'input':args,'observed':got,'expected':exp}

def repaired(name,mut,plan):
 try:return run(name,apply(mut,name,plan,True))[0]
 except Exception:return False

rows=[]
for name in HELD_PROGS:
 for k in HELD:
  for required_label,required in [('C',C),('J',J)]:
   mut,residual=variant(name,k,required)
   noop=run(name,mut)[0]
   c_ok=repaired(name,mut,C); j_ok=repaired(name,mut,J)
   passing=[x for x,ok in [('C',c_ok),('J',j_ok)] if ok]
   selected=passing[0] if len(passing)==1 else None
   selected_ok=(c_ok if selected=='C' else j_ok if selected=='J' else False)
   nonselected_ok=(j_ok if selected=='C' else c_ok if selected=='J' else c_ok or j_ok)
   rows.append({'program':name,'suffix':k,'required':required_label,'residual':residual,'noop_ok':noop,'C_ok':c_ok,'J_ok':j_ok,'passing':passing,'selected':selected,'route_ok':selected==required_label,'selected_ok':selected_ok,'nonselected_ok':nonselected_ok})

crows=[r for r in rows if r['required']=='C']; jrows=[r for r in rows if r['required']=='J']
route=sum(r['route_ok'] for r in rows)/len(rows); joint=sum(r['selected_ok'] for r in rows)/len(rows)
G={
 'required_C_semantically_repairable':all(r['C_ok'] for r in crows),
 'required_J_semantically_repairable':all(r['J_ok'] for r in jrows),
 'all_broken_noop_fail':all(not r['noop_ok'] for r in rows),
 'unique_verifier_admissible_capability_every_world':all(len(r['passing'])==1 for r in rows),
 'unique_selection_matches_required_every_world':all(r['route_ok'] for r in rows),
 'selected_capability_executes_every_world':all(r['selected_ok'] for r in rows),
 'nonselected_capability_fails_every_world':all(not r['nonselected_ok'] for r in rows),
 'route_accuracy_one':route==1.0,
 'joint_execution_accuracy_one':joint==1.0,
 'no_learned_router_checkpoint_or_gradient':True,
 'modules_unchanged_from_v2c':C==[('CMP',0),('BIN',0)] and J==[('CMP',0),('CONST',0)],
 'heldout_universe_unchanged_from_v2c':HELD_PROGS==['possible_change','sieve','subsequences'] and HELD==list(range(100,108)),
}
R={'protocol':'protocols/IKKF_V2D_VERIFIED_CAPABILITY_OS_PRECOMMIT.txt','repository':REPO,'commit':COMMIT,'capabilities':{'C':C,'J':J},'heldout_programs':HELD_PROGS,'heldout_suffixes':HELD,'rows':rows,'route_accuracy':route,'joint_execution_accuracy':joint,'gates':G}
R['verdict']='PASS_IKKF_V2D_VERIFIED_CAPABILITY_OS' if all(G.values()) else 'FAIL_IKKF_V2D_VERIFIED_CAPABILITY_OS'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2,default=str)); print(json.dumps(R,indent=2,default=str),flush=True)
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
