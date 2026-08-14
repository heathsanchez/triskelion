import os,json,ast,subprocess,tempfile,sys,signal
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

BASE='Qwen/Qwen3.5-9B'; REPO='https://github.com/jkoppel/QuixBugs.git'; COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
TH=.75; LR=5e-5; STEPS=8; BATCH=16
TRAIN=list(range(16)); HELD=list(range(100,108))
C_TRAIN=['find_in_sorted','get_factors']; J_TRAIN=['gcd','is_valid_parenthesization']; HELD_PROGS=['possible_change','quicksort','sieve','subsequences']
C=[('CMP',0),('BIN',0)]; J=[('CMP',0),('CONST',0)]
OUT=Path('artifacts/ikkf_v2_capability_routing'); OUT.mkdir(parents=True,exist_ok=True)
root=Path(tempfile.mkdtemp())/'qb'; subprocess.run(['git','clone','-q',REPO,str(root)],check=True); subprocess.run(['git','checkout','-q',COMMIT],cwd=root,check=True)
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=240.0); assert client.health_check(); tok=AutoTokenizer.from_pretrained(BASE); EOS=tok.eos_token_id
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
   nonlocal seen,done
   self.generic_visit(n)
   if kind=='CMP' and len(n.ops)==1 and type(n.ops[0]) in CMP:
    seen+=1
    if seen==index: n.ops[0]=CMP[type(n.ops[0])](); done=True
   return n
  def visit_BinOp(self,n):
   nonlocal seen,done
   self.generic_visit(n)
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
 return mut,f'input={args!r}; observed={got!r}; expected={exp!r}'
def verify(names,suffixes,plan):
 rows=[]
 for name in names:
  for k in suffixes:
   try: mut,_=variant(name,k,plan); ok=run(name,apply(mut,name,plan,True))[0]
   except Exception as e: ok=False
   rows.append({'program':name,'suffix':k,'ok':ok})
 return all(r['ok'] for r in rows),rows
def ptxt(plan): return ';'.join(f'{a}@{i}' for a,i in plan)
def prompt(name,k,plan):
 src,res=variant(name,k,plan)
 return f'A Python function was freshly mutated after checkout. Repair it using only this DSL: CMP@i, BIN@i, CONST@i separated by semicolons. Indices are zero-based among eligible AST nodes of that kind. Return ONLY the repair plan.\nProgram: {name}\nVerified residual: {res}\n\n{src}'
def parse(text):
 line=text.strip().splitlines()[0].strip() if text.strip() else ''; out=[]
 for x in line.split(';'):
  if '@' not in x:return None
  a,b=x.strip().split('@',1)
  if a not in {'CMP','BIN','CONST'}:return None
  try:i=int(b)
  except:return None
  out.append((a,i))
 return out or None
def datum(name,k,mutation,target):
 q=tok(prompt(name,k,mutation),add_special_tokens=False)['input_ids']; a=tok(' '+ptxt(target),add_special_tokens=False)['input_ids']+[EOS]; ids=q+a
 return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(q)-1)+[1.0]*(len(a)+1)}
def eval_model(m):
 rows=[]; prompts=[]; meta=[]
 for name in HELD_PROGS:
  for k in HELD:
   for label,plan in [('C',C),('J',J)]: prompts.append(prompt(name,k,plan)); meta.append((name,k,label,plan))
 gs=m.sample(prompts=prompts,max_tokens=24,temperature=0.0)
 for (name,k,label,required),g in zip(meta,gs):
  text=g[0].text; pred=parse(text); mut,_=variant(name,k,required)
  try: ok=run(name,apply(mut,name,pred,True))[0] if pred else False
  except: ok=False
  rows.append({'program':name,'suffix':k,'required':label,'output':text.strip().splitlines()[0] if text.strip() else '', 'parsed':pred,'route_ok':pred==required,'repair_ok':ok})
 def score(label,key):
  z=[r for r in rows if r['required']==label]; return sum(r[key] for r in z)/len(z)
 c=score('C','repair_ok'); j=score('J','repair_ok'); route=sum(r['route_ok'] for r in rows)/len(rows)
 return {'C':c,'J':j,'joint':min(c,j),'route_accuracy':route,'rows':rows}
def fresh(project,seed):
 with client.session(project=project) as s:
  m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=seed)); return eval_model(m)
def compile_arm(project,seed,shuffle=False):
 ex=[]
 for name in C_TRAIN:
  for k in TRAIN: ex.append(datum(name,k,C,J if shuffle else C))
 for name in J_TRAIN:
  for k in TRAIN: ex.append(datum(name,k,J,C if shuffle else J))
 curve=[]
 with client.session(project=project) as s:
  m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=seed))
  for st in range(STEPS):
   # deterministic balanced 8 C + 8 J every step
   batch=[]
   for i in range(8): batch.append(ex[(st*8+i)%32]); batch.append(ex[32+((st*8+i)%32)])
   fb=m.forward_backward(batch,loss_fn='cross_entropy'); m.optim_step(lr=LR,grad_clip_norm=1.0); curve.append(float(fb.metrics['loss'])); print(json.dumps({'arm':project,'step':st+1,'loss':curve[-1]}),flush=True)
  ev=eval_model(m); ck=m.save_weights(project+'-final',mode='training').path
 return {'eval':ev,'curve':curve,'checkpoint':ck}
def reload(ck):
 with client.session(project='ikkf-v2-reload') as s:
  m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=20260912),checkpoint=ck); return eval_model(m)

R={'protocol':'protocols/IKKF_V2_CAPABILITY_ROUTING_PRECOMMIT.txt','arms':{},'verification':{}}
okC,rC=verify(C_TRAIN,TRAIN,C); okJ,rJ=verify(J_TRAIN,TRAIN,J); R['verification']['practice_C']={'ok':okC}; R['verification']['practice_J']={'ok':okJ}
# held-out semantics are verified before neural evaluation only as a validity gate; no neural outputs are inspected during selection because targets were precommitted.
okHC,rHC=verify(HELD_PROGS,HELD,C); okHJ,rHJ=verify(HELD_PROGS,HELD,J); R['verification']['heldout_C']={'ok':okHC}; R['verification']['heldout_J']={'ok':okHJ}
if not all([okC,okJ,okHC,okHJ]):
 R['verdict']='FAIL_SEMANTIC_PRECONDITION'; R['verification']['rows']={'C':rHC,'J':rHJ}; (OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2)); raise SystemExit
B=fresh('ikkf-v2-B0',20260910); CJ=compile_arm('ikkf-v2-CJ',20260911,False); S=compile_arm('ikkf-v2-SHUFFLE',20260913,True); RR=reload(CJ['checkpoint'])
R['arms']={'B0':B,'CJ':CJ,'SHUFFLE':S,'R':RR}
R['gates']={
 'practice_C_verified':okC,'practice_J_verified':okJ,'heldout_C_semantically_verified':okHC,'heldout_J_semantically_verified':okHJ,
 'cold_joint_fails':B['joint']<TH,
 'CJ_C_passes':CJ['eval']['C']>=TH,'CJ_J_passes':CJ['eval']['J']>=TH,'CJ_routes':CJ['eval']['route_accuracy']>=TH,
 'shuffled_control_fails':S['eval']['joint']<TH or S['eval']['route_accuracy']<TH,
 'reload_preserves_routing':RR['C']>=TH and RR['J']>=TH and RR['route_accuracy']>=TH,
 'heldout_never_trained':set(HELD_PROGS).isdisjoint(C_TRAIN+J_TRAIN) and set(HELD).isdisjoint(TRAIN),
 'no_inherited_checkpoint':True}
R['verdict']='PASS_IKKF_V2_CAPABILITY_ROUTING' if all(R['gates'].values()) else 'FAIL_IKKF_V2_CAPABILITY_ROUTING'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2),flush=True)
