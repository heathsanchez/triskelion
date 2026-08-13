import ast,json,subprocess,tempfile,signal,sys
from pathlib import Path
REPO='https://github.com/jkoppel/QuixBugs.git'; COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
OUT=Path('artifacts/primitive_transfer_v15'); OUT.mkdir(parents=True,exist_ok=True)
root=Path(tempfile.mkdtemp())/'qb'; subprocess.run(['git','clone','-q',REPO,str(root)],check=True); subprocess.run(['git','checkout','-q',COMMIT],cwd=root,check=True); sys.path.insert(0,str(root))
class Timeout(Exception): pass
def alarm(*a): raise Timeout()
signal.signal(signal.SIGALRM,alarm)
CMP={ast.Lt:ast.LtE,ast.LtE:ast.Lt,ast.Gt:ast.GtE,ast.GtE:ast.Gt,ast.Eq:ast.NotEq,ast.NotEq:ast.Eq}
BIN={ast.Add:ast.Sub,ast.Sub:ast.Add,ast.BitAnd:ast.BitXor,ast.BitXor:ast.BitAnd}

def tests(name):
 p=root/'json_testcases'/f'{name}.json'; rows=[]
 if not p.exists(): return None
 try:
  for line in p.read_text().splitlines():
   if line.strip(): rows.append(json.loads(line))
 except: return None
 return rows or None

def run(name,src,ts):
 ns={'__name__':'candidate'}
 try: exec(compile(src,'<x>','exec'),ns,ns); fn=ns[name]
 except: return False
 try:
  for args,exp in ts:
   signal.alarm(1); got=fn(*args); signal.alarm(0)
   if got!=exp:return False
 except:
  signal.alarm(0); return False
 return True

def mutate(src,name,ops):
 tree=ast.parse(src); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
 for kind in ops:
  seen=-1; done=False
  class T(ast.NodeTransformer):
   def visit_Compare(self,n):
    nonlocal seen,done
    self.generic_visit(n)
    if kind=='CMP' and len(n.ops)==1 and type(n.ops[0]) in CMP:
     seen+=1
     if seen==0:n.ops[0]=CMP[type(n.ops[0])]();done=True
    return n
   def visit_BinOp(self,n):
    nonlocal seen,done
    self.generic_visit(n)
    if kind=='BIN' and type(n.op) in BIN:
     seen+=1
     if seen==0:n.op=BIN[type(n.op)]();done=True
    return n
   def visit_Constant(self,n):
    nonlocal seen,done
    if kind=='CONST' and isinstance(n.value,int) and not isinstance(n.value,bool):
     seen+=1
     if seen==0:n.value+=1;done=True
    return n
  T().visit(fn); ast.fix_missing_locations(tree)
  if not done:return None
  src=ast.unparse(tree)+'\n'; tree=ast.parse(src); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
 return src

rows=[]
for p in sorted((root/'correct_python_programs').glob('*.py')):
 name=p.stem; ts=tests(name)
 if not ts:continue
 src=p.read_text()
 if not run(name,src,ts):continue
 rec={'program':name}
 for ops in [('CMP',),('BIN',),('CONST',),('CMP','BIN'),('CMP','BIN','CONST')]:
  ms=mutate(src,name,ops); rec['+'.join(ops)]=None if ms is None else run(name,ms,ts)
 rows.append(rec)
sets={k:[r['program'] for r in rows if r.get(k) is False] for k in ['CMP','BIN','CONST','CMP+BIN','CMP+BIN+CONST']}
# choose fully source-distinct A-train, B-train, AB-eval, C-train, ABC-eval
quints=[]
for a in sets['CMP']:
 for b in sets['BIN']:
  for ab in sets['CMP+BIN']:
   for c in sets['CONST']:
    for abc in sets['CMP+BIN+CONST']:
     if len({a,b,ab,c,abc})==5: quints.append([a,b,ab,c,abc])
     if len(quints)>=100: break
    if len(quints)>=100: break
   if len(quints)>=100: break
  if len(quints)>=100: break
 if len(quints)>=100: break
R={'commit':COMMIT,'sets':sets,'first_quints':quints,'quint_count_at_least':len(quints),'rows':rows}
print(json.dumps({'sets':{k:v[:20] for k,v in sets.items()},'counts':{k:len(v) for k,v in sets.items()},'first_quints':quints[:20]},indent=2)); (OUT/'RESULT.json').write_text(json.dumps(R,indent=2))
