import ast, json, signal, subprocess, sys, tempfile
from pathlib import Path

REPO='https://github.com/jkoppel/QuixBugs.git'
COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
BASE='Qwen/Qwen3.5-9B'
CHECKPOINT='river://02f13904-fe14-4f1a-a30d-05c945b8b137/weights/v15_C_lineage_step4'
SEED=20260903
TRAIN=list(range(16))
HELD=list(range(100,108))
TH=.75
LR=5e-5
MAX_STEPS=10
BATCH=16
PROGRAMS={
 'A':('find_first_in_sorted',['CMP']),
 'B':('bitcount',['BIN']),
 'AB_TEST':('find_in_sorted',['CMP','BIN']),
 'C':('bucketsort',['CONST']),
}
PRIMITIVES={'A':[('CMP',0)],'B':[('BIN',0)],'C':[('CONST',0)]}
CMP={ast.Lt:ast.LtE,ast.LtE:ast.Lt,ast.Gt:ast.GtE,ast.GtE:ast.Gt,ast.Eq:ast.NotEq,ast.NotEq:ast.Eq}
BIN={ast.Add:ast.Sub,ast.Sub:ast.Add,ast.BitAnd:ast.BitXor,ast.BitXor:ast.BitAnd}
ROOT=None

class Timeout(Exception): pass
def _alarm(*a): raise Timeout()
signal.signal(signal.SIGALRM,_alarm)

def prepare():
    global ROOT
    if ROOT is not None:return ROOT
    ROOT=Path(tempfile.mkdtemp())/'qb'
    subprocess.run(['git','clone','-q',REPO,str(ROOT)],check=True)
    subprocess.run(['git','checkout','-q',COMMIT],cwd=ROOT,check=True)
    sys.path.insert(0,str(ROOT));return ROOT

def tests_for(name):
    prepare(); rows=[]
    for line in (ROOT/'json_testcases'/f'{name}.json').read_text().splitlines():
        if line.strip():rows.append(json.loads(line))
    return rows

def rename_locals(src,name,suffix):
    tree=ast.parse(src);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    loc=set(a.arg for a in fn.args.args)
    for n in ast.walk(fn):
        if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store):loc.add(n.id)
    mp={x:f'{x}_{suffix}' for x in sorted(loc) if x!=name}
    class R(ast.NodeTransformer):
        def visit_arg(self,n):
            if n.arg in mp:n.arg=mp[n.arg]
            return n
        def visit_Name(self,n):
            if n.id in mp:n.id=mp[n.id]
            return n
    tree=R().visit(tree);ast.fix_missing_locations(tree);return ast.unparse(tree)+'\n'

def transform(src,name,kind,index=0,repair=False):
    tree=ast.parse(src);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name);seen=-1;done=False
    class T(ast.NodeTransformer):
        def visit_Compare(self,n):
            nonlocal seen,done
            self.generic_visit(n)
            if kind=='CMP' and len(n.ops)==1 and type(n.ops[0]) in CMP:
                seen+=1
                if seen==index:n.ops[0]=CMP[type(n.ops[0])]();done=True
            return n
        def visit_BinOp(self,n):
            nonlocal seen,done
            self.generic_visit(n)
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
    if not done:raise RuntimeError((name,kind,index))
    return ast.unparse(tree)+'\n'

def mutate(src,name,ops):
    for op in ops:src=transform(src,name,op,0,False)
    return src

def repair(src,name,plan):
    for op,idx in plan:src=transform(src,name,op,idx,op=='CONST')
    return src

def run_source(name,src,tests):
    ns={'__name__':'candidate'}
    try:exec(compile(src,'<cand>','exec'),ns,ns);fn=ns[name]
    except Exception:return False,None,None,None
    for args,exp in tests:
        try:signal.alarm(1);got=fn(*args);signal.alarm(0)
        except Exception as e:signal.alarm(0);return False,args,repr(e),exp
        if got!=exp:return False,args,got,exp
    return True,None,None,None

def variant(key,k):
    prepare();name,ops=PROGRAMS[key];src=(ROOT/'correct_python_programs'/f'{name}.py').read_text();src=rename_locals(src,name,k);mut=mutate(src,name,ops)
    tests=tests_for(name);ok,args,got,exp=run_source(name,mut,tests);assert not ok,(key,k)
    return name,mut,f'input={args!r}; observed={got!r}; expected={exp!r}'

def verified(key,k,plan):
    name,mut,_=variant(key,k)
    try:fixed=repair(mut,name,plan)
    except Exception:return False
    return run_source(name,fixed,tests_for(name))[0]

def prompt(key,k):
    name,src,res=variant(key,k)
    return f'''A Python function was freshly mutated after checkout. Repair it using only this DSL: CMP@i, BIN@i, CONST@i separated by semicolons. Indices are zero-based among eligible AST nodes of that kind. Return ONLY the repair plan.\nProgram: {name}\nVerified residual: {res}\n\n{src}'''

def parse_plan(text):
    t=text.strip().splitlines()[0].strip() if text.strip() else '';out=[]
    for part in t.split(';'):
        part=part.strip()
        if not part:continue
        if '@' not in part:return None
        op,idx=part.split('@',1);op=op.strip()
        if op not in {'CMP','BIN','CONST'}:return None
        try:i=int(idx.strip())
        except Exception:return None
        if i<0 or i>20:return None
        out.append((op,i))
    return out or None

def plan_text(plan):return ';'.join(f'{a}@{b}' for a,b in plan)
