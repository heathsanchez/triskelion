import ast,json,subprocess,tempfile,signal,itertools
from pathlib import Path
REPO='https://github.com/jkoppel/QuixBugs.git';COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf';OUT=Path('artifacts/external_law_miner_v32');OUT.mkdir(parents=True,exist_ok=True)
root=Path(tempfile.mkdtemp())/'qb';subprocess.run(['git','clone','-q',REPO,str(root)],check=True);subprocess.run(['git','checkout','-q',COMMIT],cwd=root,check=True)
class Timeout(Exception):pass
def alarm(*a):raise Timeout()
signal.signal(signal.SIGALRM,alarm)
CMP={ast.Lt:ast.LtE,ast.LtE:ast.Lt,ast.Gt:ast.GtE,ast.GtE:ast.Gt,ast.Eq:ast.NotEq,ast.NotEq:ast.Eq};BIN={ast.Add:ast.Sub,ast.Sub:ast.Add,ast.BitAnd:ast.BitXor,ast.BitXor:ast.BitAnd}
def tests_for(name):
 p=root/'json_testcases'/f'{name}.json'
 if not p.exists():return []
 return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def change(src,name,kind,index=0,repair=False):
 tree=ast.parse(src);fns=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name]
 if not fns:raise RuntimeError('no fn')
 fn=fns[0];seen=-1;done=False
 class T(ast.NodeTransformer):
  def visit_Compare(self,n):
   nonlocal seen,done;self.generic_visit(n)
   if kind=='CMP' and len(n.ops)==1 and type(n.ops[0]) in CMP:
    seen+=1
    if seen==index:n.ops[0]=CMP[type(n.ops[0])]();done=True
   return n
  def visit_BinOp(self,n):
   nonlocal seen,done;self.generic_visit(n)
   if kind=='BIN' and type(n.op) in BIN:
    seen+=1
    if seen==index:n.op=BIN[type(n.op)]();done=True
   return n
  def visit_Constant(self,n):
   nonlocal seen,done
   if kind=='CONST' and isinstance(n.value,int) and not isinstance(n.value,bool):
    seen+=1
    if seen==index:n.value+=(-1 if repair else 1);done=True
   return n
 T().visit(fn);ast.fix_missing_locations(tree)
 if not done:raise RuntimeError('missing')
 return ast.unparse(tree)+'\n'
def apply(src,name,seq,repair=True):
 for k in seq:src=change(src,name,k,0,repair and k=='CONST')
 return src
def run_source(name,src,tests):
 ns={'__name__':'candidate'}
 try:exec(compile(src,'<c>','exec'),ns,ns);fn=ns[name]
 except:return False
 for args,exp in tests:
  try:signal.alarm(1);got=fn(*args);signal.alarm(0)
  except:signal.alarm(0);return False
  if got!=exp:return False
 return True
def eligible(src,name,k):
 try:change(src,name,k);return True
 except:return False
OPS=['CMP','BIN','CONST'];rows=[]
for p in sorted((root/'correct_python_programs').glob('*.py')):
 name=p.stem;tests=tests_for(name)
 if not tests:continue
 src=p.read_text();avail=[k for k in OPS if eligible(src,name,k)]
 if len(avail)<2:continue
 base_ok=run_source(name,src,tests)
 if not base_ok:continue
 rec={'name':name,'available':avail,'pairs':{},'triples':{}}
 for a,b in itertools.combinations(avail,2):
  try:
   mut=apply(src,name,[a,b],repair=False);ab=apply(mut,name,[a,b],repair=True);ba=apply(mut,name,[b,a],repair=True)
   rec['pairs'][a+'|'+b]={'commute_source':ab==ba,'ab_pass':run_source(name,ab,tests),'ba_pass':run_source(name,ba,tests)}
  except Exception as e:rec['pairs'][a+'|'+b]={'error':type(e).__name__}
 if len(avail)>=3:
  for perm in itertools.permutations(avail,3):
   try:
    mut=apply(src,name,avail,repair=False);fixed=apply(mut,name,perm,repair=True);rec['triples']['>'.join(perm)]={'pass':run_source(name,fixed,tests),'source':fixed}
   except Exception as e:rec['triples']['>'.join(perm)]={'pass':False,'error':type(e).__name__}
 rows.append(rec)
# unary algebra laws on source transformations: use correct source, apply repair-form operator twice.
unary=[]
for rec in rows:
 name=rec['name'];src=(root/'correct_python_programs'/f'{name}.py').read_text()
 for k in rec['available']:
  try:
   once=apply(src,name,[k],repair=True);twice=apply(once,name,[k],repair=True)
   unary.append({'name':name,'op':k,'idempotent':once==twice,'involution':src==twice})
  except:pass
pair_all={}
for a,b in itertools.combinations(OPS,2):
 xs=[r['pairs'].get(a+'|'+b) for r in rows if a+'|'+b in r['pairs']];xs=[x for x in xs if 'error' not in x]
 if xs:pair_all[a+'|'+b]={'support':len(xs),'commute_all':all(x['commute_source'] and x['ab_pass'] and x['ba_pass'] for x in xs)}
unary_laws={}
for k in OPS:
 xs=[x for x in unary if x['op']==k]
 unary_laws[k]={'support':len(xs),'idempotent_all':bool(xs) and all(x['idempotent'] for x in xs),'involution_all':bool(xs) and all(x['involution'] for x in xs)}
triple_rows=[r for r in rows if r['triples']]
triple_stats=[]
for r in triple_rows:
 vals=list(r['triples'].values());passing=[x for x in vals if x.get('pass')];classes=len(set(x.get('source') for x in passing))
 triple_stats.append({'name':r['name'],'permutations':len(vals),'passing':len(passing),'extensional_classes':classes})
R={'commit':COMMIT,'functions_with_multiop_support':len(rows),'rows':rows,'pair_laws':pair_all,'unary_laws':unary_laws,'triple_quotient':triple_stats}
R['summary']={'verified_commuting_pairs':[k for k,v in pair_all.items() if v['commute_all']],'verified_involutions':[k for k,v in unary_laws.items() if v['involution_all']],'verified_idempotents':[k for k,v in unary_laws.items() if v['idempotent_all']],'triple_functions':len(triple_stats),'mean_permutation_to_class_reduction':(sum(x['permutations']/max(1,x['extensional_classes']) for x in triple_stats)/len(triple_stats) if triple_stats else 0)}
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R['summary'],indent=2));print(json.dumps({'pair_laws':pair_all,'unary_laws':unary_laws,'triple_quotient':triple_stats},indent=2))