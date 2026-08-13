import ast, hashlib, json, subprocess
from pathlib import Path

ROOT=Path('/tmp/v40b_rich')
OUT=Path('artifacts/v40b'); OUT.mkdir(parents=True,exist_ok=True)
SEED='V40B_PROTECTED_MINER_20260814'


def run(cmd,timeout=90):
    try:
        p=subprocess.run(cmd,cwd=ROOT,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
        return p.returncode==0,p.stdout[-5000:]
    except subprocess.TimeoutExpired as e:
        out=e.stdout or ''
        if isinstance(out,bytes): out=out.decode(errors='replace')
        return False,('TIMEOUT\n'+out)[-5000:]

def reset():
    subprocess.run('git reset --hard -q HEAD && git clean -fdxq',cwd=ROOT,shell=True,check=True)

def context(tree,target):
    parents={}
    for p in ast.walk(tree):
        for c in ast.iter_child_nodes(p): parents[id(c)]=p
    out={'IN_IF_TEST':False,'IN_IFEXP':False,'IN_RETURN':False,'IN_ASSERT':False,'IN_WHILE_TEST':False}
    cur=target
    while id(cur) in parents:
        p=parents[id(cur)]
        if isinstance(p,ast.If) and target in list(ast.walk(p.test)): out['IN_IF_TEST']=True
        if isinstance(p,ast.IfExp): out['IN_IFEXP']=True
        if isinstance(p,ast.Return): out['IN_RETURN']=True
        if isinstance(p,ast.Assert): out['IN_ASSERT']=True
        if isinstance(p,ast.While) and target in list(ast.walk(p.test)): out['IN_WHILE_TEST']=True
        cur=p
    return out

cands=[]
for p in sorted((ROOT/'rich').rglob('*.py')):
    try:
        src=p.read_text(); tree=ast.parse(src)
    except Exception: continue
    for n in ast.walk(tree):
        if isinstance(n,ast.Compare) and len(n.ops)==1 and isinstance(n.ops[0],ast.Lt):
            ctx=context(tree,n)
            if ctx['IN_IF_TEST'] or ctx['IN_IFEXP']: continue
            seg=ast.get_source_segment(src,n) or ''
            sid=f'{p.relative_to(ROOT)}|{getattr(n,"lineno",0)}|{getattr(n,"col_offset",0)}|{seg}'
            cands.append({'path':str(p.relative_to(ROOT)),'line':n.lineno,'col':n.col_offset,'segment':seg,'context':ctx,'rank':hashlib.sha256((SEED+'|'+sid).encode()).hexdigest()})
cands=sorted(cands,key=lambda x:x['rank'])

baseline_ok,baseline_log=run('pytest -q',timeout=120)
R={'protocol':'V40B deterministic external protected semantic miner','seed':SEED,'repo':'Textualize/rich','commit':'9d8f9a372cc5916fd4781fec207ced7ddac2f08f','baseline_ok':baseline_ok,'candidate_count':len(cands),'ranked_candidates':cands[:20],'attempts':[],'selected':None}
if not baseline_ok:
    R['verdict']='INVALID_BASELINE'; (OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2)); raise SystemExit(1)

# Freeze a modest mutation budget before seeing outcomes.
for c in cands[:12]:
    reset(); p=ROOT/c['path']; src=p.read_text(); tree=ast.parse(src); target=(c['line'],c['col'])
    class T(ast.NodeTransformer):
        def visit_Compare(self,n):
            self.generic_visit(n)
            if (getattr(n,'lineno',0),getattr(n,'col_offset',0))==target and len(n.ops)==1 and isinstance(n.ops[0],ast.Lt): n.ops[0]=ast.LtE()
            return n
    T().visit(tree); ast.fix_missing_locations(tree); p.write_text(ast.unparse(tree)+'\n')
    ok,log=run('pytest -q',timeout=120)
    a={**c,'suite_passed':ok,'log_tail':log[-1200:]}; R['attempts'].append(a)
    if not ok:
        R['selected']=a; break

R['verdict']='FOUND_EXTERNAL_PROTECTED_BOUNDARY_V40B' if R['selected'] else 'NO_PROTECTED_BOUNDARY_WITHIN_BUDGET_V40B'
R['claim_boundary']='Hash-ranked production Lt sites outside If.test/IfExp; unchanged Rich full test suite is semantic authority. First failing mutation is selected without semantic skipping.'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2))
