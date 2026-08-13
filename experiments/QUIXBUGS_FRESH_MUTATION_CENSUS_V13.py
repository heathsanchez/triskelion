import ast,json,subprocess,tempfile,signal,sys
from pathlib import Path

REPO='https://github.com/jkoppel/QuixBugs.git'; COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
OUT=Path('artifacts/fresh_mutation_v13'); OUT.mkdir(parents=True,exist_ok=True)
root=Path(tempfile.mkdtemp())/'qb'; subprocess.run(['git','clone','-q',REPO,str(root)],check=True); subprocess.run(['git','checkout','-q',COMMIT],cwd=root,check=True)
sys.path.insert(0,str(root))

class Timeout(Exception): pass
def alarm(*a): raise Timeout()
signal.signal(signal.SIGALRM,alarm)

def mutate(src, which):
    tree=ast.parse(src)
    class T(ast.NodeTransformer):
        def __init__(self): self.done=False
        def visit_Compare(self,node):
            self.generic_visit(node)
            if which=='CMP' and not self.done and len(node.ops)==1:
                mp={ast.Lt:ast.LtE,ast.LtE:ast.Lt,ast.Gt:ast.GtE,ast.GtE:ast.Gt,ast.Eq:ast.NotEq,ast.NotEq:ast.Eq}
                typ=type(node.ops[0])
                if typ in mp: node.ops[0]=mp[typ](); self.done=True
            return node
        def visit_BinOp(self,node):
            self.generic_visit(node)
            if which=='BIN' and not self.done:
                mp={ast.Add:ast.Sub,ast.Sub:ast.Add,ast.Mult:ast.Add,ast.BitAnd:ast.BitXor,ast.BitXor:ast.BitAnd}
                typ=type(node.op)
                if typ in mp: node.op=mp[typ](); self.done=True
            return node
        def visit_Constant(self,node):
            if which=='CONST' and not self.done and isinstance(node.value,int) and not isinstance(node.value,bool):
                node.value=node.value+1; self.done=True
            return node
    t=T(); tree=t.visit(tree); ast.fix_missing_locations(tree)
    return (ast.unparse(tree)+'\n',t.done)

def apply_ops(src,ops):
    for op in ops:
        src,ok=mutate(src,op)
        if not ok: return None
    return src

def load_tests(p):
    rows=[]
    try:
        for line in p.read_text().splitlines():
            if line.strip(): rows.append(json.loads(line))
    except Exception: return None
    return rows

def run_source(name,src,tests):
    ns={'__name__':'candidate'}
    try: exec(compile(src,'<cand>','exec'),ns,ns); fn=ns[name]
    except Exception: return False
    try:
        for args,exp in tests:
            signal.alarm(1)
            got=fn(*args)
            signal.alarm(0)
            if got!=exp: return False
        return True
    except Exception:
        signal.alarm(0); return False

rows=[]
for p in sorted((root/'correct_python_programs').glob('*.py')):
    name=p.stem; jp=root/'json_testcases'/f'{name}.json'
    if not jp.exists(): continue
    tests=load_tests(jp)
    if not tests: continue
    src=p.read_text()
    if not run_source(name,src,tests): continue
    rec={'program':name,'base_pass':True,'chains':{}}
    for ops in [('CMP',),('CMP','BIN'),('CMP','BIN','CONST')]:
        ms=apply_ops(src,ops)
        rec['chains']['+'.join(ops)]=None if ms is None else run_source(name,ms,tests)
    rows.append(rec)

A=[r['program'] for r in rows if r['chains'].get('CMP') is False]
AB=[r['program'] for r in rows if r['chains'].get('CMP+BIN') is False and r['chains'].get('CMP') is False]
ABC=[r['program'] for r in rows if r['chains'].get('CMP+BIN+CONST') is False and r['chains'].get('CMP+BIN') is False and r['chains'].get('CMP') is False]
triples=[(a,b,c) for a in A for b in AB for c in ABC if len({a,b,c})==3]
R={'commit':COMMIT,'rows':rows,'eligible_A':A,'eligible_AB':AB,'eligible_ABC':ABC,'triple_count':len(triples),'first_triples':triples[:50]}
print(json.dumps(R,indent=2)); (OUT/'RESULT.json').write_text(json.dumps(R,indent=2))
