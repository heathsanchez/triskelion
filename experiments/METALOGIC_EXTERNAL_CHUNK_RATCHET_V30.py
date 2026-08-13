"""V30 — verified chunking expands bounded repair search on independently authored QuixBugs code.

External substrate is a fixed QuixBugs commit. We mutate independently authored functions
with the same low-level repair atoms used in V14. Search budget is frozen at 2 atomic
repair capabilities. First discover and verify the 2-atom AB repair, retain it as one
atomic chunk D, then test whether the 3-atom ABC repair becomes discoverable only after D.
"""
import ast, json, subprocess, tempfile, signal, itertools
from pathlib import Path

REPO='https://github.com/jkoppel/QuixBugs.git'
COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
BUDGET=2
OUT=Path('artifacts/external_chunk_ratchet_v30'); OUT.mkdir(parents=True,exist_ok=True)
root=Path(tempfile.mkdtemp())/'qb'; subprocess.run(['git','clone','-q',REPO,str(root)],check=True); subprocess.run(['git','checkout','-q',COMMIT],cwd=root,check=True)

class Timeout(Exception):pass
def alarm(*a):raise Timeout()
signal.signal(signal.SIGALRM,alarm)

def tests_for(name):
    rows=[]
    for line in (root/'json_testcases'/f'{name}.json').read_text().splitlines():
        if line.strip():rows.append(json.loads(line))
    return rows

def rename_locals(src,name,suffix):
    tree=ast.parse(src); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
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

def change(src,name,kind,index=0,inverse=False):
    tree=ast.parse(src);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name);seen=-1;done=False
    cmpf={ast.Lt:ast.LtE,ast.LtE:ast.Lt,ast.Gt:ast.GtE,ast.GtE:ast.Gt,ast.Eq:ast.NotEq,ast.NotEq:ast.Eq}
    binf={ast.Add:ast.Sub,ast.Sub:ast.Add,ast.BitAnd:ast.BitXor,ast.BitXor:ast.BitAnd}
    class T(ast.NodeTransformer):
        def visit_Compare(self,n):
            nonlocal seen,done
            self.generic_visit(n)
            if kind=='CMP' and len(n.ops)==1 and type(n.ops[0]) in cmpf:
                seen+=1
                if seen==index:n.ops[0]=cmpf[type(n.ops[0])]();done=True
            return n
        def visit_BinOp(self,n):
            nonlocal seen,done
            self.generic_visit(n)
            if kind=='BIN' and type(n.op) in binf:
                seen+=1
                if seen==index:n.op=binf[type(n.op)]();done=True
            return n
        def visit_Constant(self,n):
            nonlocal seen,done
            if kind=='CONST' and isinstance(n.value,int) and not isinstance(n.value,bool):
                seen+=1
                if seen==index:n.value=n.value-1 if inverse else n.value+1;done=True
            return n
    T().visit(fn);ast.fix_missing_locations(tree)
    if not done:raise RuntimeError((name,kind,index))
    return ast.unparse(tree)+'\n'

def mutate(src,name,kinds):
    for k in kinds:src=change(src,name,k,0,False)
    return src

def repair(src,name,plan):
    for kind,idx in plan:src=change(src,name,kind,idx,kind=='CONST')
    return src

def run_source(name,src,tests):
    ns={'__name__':'candidate'}
    try:exec(compile(src,'<candidate>','exec'),ns,ns);fn=ns[name]
    except Exception:return False
    for args,exp in tests:
        try:signal.alarm(1);got=fn(*args);signal.alarm(0)
        except Exception:signal.alarm(0);return False
        if got!=exp:return False
    return True

def variant(name,k,kinds):
    src=(root/'correct_python_programs'/f'{name}.py').read_text();src=rename_locals(src,name,k);mut=mutate(src,name,kinds);assert not run_source(name,mut,tests_for(name));return mut

ATOMS={'CMP':(('CMP',0),),'BIN':(('BIN',0),),'CONST':(('CONST',0),)}
def expanded(atom,library):return library[atom]
def plans(library,budget=BUDGET):
    names=sorted(library);out=[]
    for n in range(1,budget+1):
        for seq in itertools.product(names,repeat=n):
            p=[]
            for a in seq:p.extend(expanded(a,library))
            # no duplicate low-level operation; canonical order to avoid gratuitous aliases
            kinds=[x[0] for x in p]
            if len(kinds)!=len(set(kinds)):continue
            out.append((seq,tuple(p)))
    return out

def survivor_plans(name,kinds,variants,library):
    surv=[]
    for symbolic,low in plans(library):
        ok=True
        for k in variants:
            try:fixed=repair(variant(name,k,kinds),name,low)
            except Exception:ok=False;break
            if not run_source(name,fixed,tests_for(name)):ok=False;break
        if ok:surv.append({'symbolic':symbolic,'expanded':low})
    # minimum symbolic length then unique expanded behavior
    if not surv:return []
    m=min(len(x['symbolic']) for x in surv);return [x for x in surv if len(x['symbolic'])==m]

TRAIN=list(range(32));HOLD=list(range(100,164))
# Generation 1 on external get_factors: repair requires CMP+BIN, within B=2.
L0=dict(ATOMS)
s1=survivor_plans('get_factors',['CMP','BIN'],TRAIN,L0)
D=tuple(s1[0]['expanded']) if len(s1)==1 else None
L1=dict(L0)
if D:L1['D_AB']=D
# Generation 2 on different external function quicksort: requires CMP+BIN+CONST.
cold=survivor_plans('quicksort',['CMP','BIN','CONST'],TRAIN,L0)
warm=survivor_plans('quicksort',['CMP','BIN','CONST'],TRAIN,L1)
# causal ablation and heldout verification
abl=survivor_plans('quicksort',['CMP','BIN','CONST'],TRAIN,{k:v for k,v in L1.items() if k!='D_AB'})
hold_ab=all(run_source('get_factors',repair(variant('get_factors',k,['CMP','BIN']),'get_factors',D),tests_for('get_factors')) for k in HOLD) if D else False
chosen=warm[0]['expanded'] if len(warm)==1 else None
hold_abc=all(run_source('quicksort',repair(variant('quicksort',k,['CMP','BIN','CONST']),'quicksort',chosen),tests_for('quicksort')) for k in HOLD) if chosen else False
R={'protocol':'V30 fixed QuixBugs commit, repair atom budget 2','commit':COMMIT,'budget':BUDGET,
   'generation1_survivors':s1,'D':D,'generation2_cold':cold,'generation2_warm':warm,'generation2_ablation':abl,
   'heldout_variants':len(HOLD),'heldout_D_exact':hold_ab,'heldout_successor_exact':hold_abc}
R['gates']={
 'external_D_unique':len(s1)==1 and set(x[0] for x in D)=={'CMP','BIN'},
 'successor_outside_cold_budget':len(cold)==0,
 'successor_unique_after_chunk':len(warm)==1 and 'D_AB' in warm[0]['symbolic'] and set(x[0] for x in warm[0]['expanded'])=={'CMP','BIN','CONST'},
 'ablation_removes_successor':len(abl)==0,
 'heldout_D_exact':hold_ab,'heldout_successor_exact':hold_abc}
R['verdict']='PASS_EXTERNAL_CHUNK_RATCHET_V30' if all(R['gates'].values()) else 'MIXED_EXTERNAL_CHUNK_RATCHET_V30'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2,default=list));print(json.dumps(R,indent=2,default=list))
