import os,json,ast,subprocess,tempfile,sys,signal,itertools,collections
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

BASE='Qwen/Qwen3.5-9B'; SEED=20260903
CHECKPOINT='river://02f13904-fe14-4f1a-a30d-05c945b8b137/weights/v15_C_lineage_step4'
REPO='https://github.com/jkoppel/QuixBugs.git'; COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
PROGRAMS={
 'A':('find_first_in_sorted',['CMP']),
 'B':('bitcount',['BIN']),
 'AB_TEST':('find_in_sorted',['CMP','BIN']),
 'C':('bucketsort',['CONST']),
 'ABC_TEST':('get_factors',['CMP','BIN','CONST']),
}
HELD=list(range(100,108)); OUT=Path('artifacts/verified_composer_v16'); OUT.mkdir(parents=True,exist_ok=True)
root=Path(tempfile.mkdtemp())/'qb'; subprocess.run(['git','clone','-q',REPO,str(root)],check=True); subprocess.run(['git','checkout','-q',COMMIT],cwd=root,check=True); sys.path.insert(0,str(root))
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0); assert client.health_check(); tok=AutoTokenizer.from_pretrained(BASE)

class Timeout(Exception): pass
def alarm(*a): raise Timeout()
signal.signal(signal.SIGALRM,alarm)
CMP={ast.Lt:ast.LtE,ast.LtE:ast.Lt,ast.Gt:ast.GtE,ast.GtE:ast.Gt,ast.Eq:ast.NotEq,ast.NotEq:ast.Eq}
BIN={ast.Add:ast.Sub,ast.Sub:ast.Add,ast.BitAnd:ast.BitXor,ast.BitXor:ast.BitAnd}

def tests_for(name):
    rows=[]
    for line in (root/'json_testcases'/f'{name}.json').read_text().splitlines():
        if line.strip(): rows.append(json.loads(line))
    return rows

def rename_locals(src,name,suffix):
    tree=ast.parse(src); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    loc=set(a.arg for a in fn.args.args)
    for n in ast.walk(fn):
        if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store): loc.add(n.id)
    mp={x:f'{x}_{suffix}' for x in sorted(loc) if x!=name}
    class R(ast.NodeTransformer):
        def visit_arg(self,n):
            if n.arg in mp:n.arg=mp[n.arg]
            return n
        def visit_Name(self,n):
            if n.id in mp:n.id=mp[n.id]
            return n
    tree=R().visit(tree); ast.fix_missing_locations(tree); return ast.unparse(tree)+'\n'

def transform(src,name,kind,index=0,repair=False):
    tree=ast.parse(src); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name); seen=-1; done=False
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
                if seen==index:n.value += (-1 if repair else 1);done=True
            return n
    T().visit(fn); ast.fix_missing_locations(tree)
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
    name,ops=PROGRAMS[key]; src=(root/'correct_python_programs'/f'{name}.py').read_text(); src=rename_locals(src,name,k); mut=mutate(src,name,ops)
    tests=tests_for(name); ok,args,got,exp=run_source(name,mut,tests); assert not ok,(key,k)
    residual=f'input={args!r}; observed={got!r}; expected={exp!r}'
    return name,mut,residual

def prompt(key,k):
    name,src,res=variant(key,k)
    return f'''A Python function was freshly mutated after checkout. Repair it using only this DSL: CMP@i, BIN@i, CONST@i separated by semicolons. Indices are zero-based among eligible AST nodes of that kind. Return ONLY the repair plan.\nProgram: {name}\nVerified residual: {res}\n\n{src}'''

def parse_plan(text):
    t=text.strip().splitlines()[0].strip() if text.strip() else ''; out=[]
    for part in t.split(';'):
        part=part.strip()
        if not part:continue
        if '@' not in part:return None
        op,idx=part.split('@',1);op=op.strip()
        if op not in {'CMP','BIN','CONST'}:return None
        try:i=int(idx.strip())
        except:return None
        if i<0 or i>20:return None
        out.append((op,i))
    return out or None

def direct_eval(m,key):
    gs=m.sample(prompts=[prompt(key,k) for k in HELD],max_tokens=24,temperature=0.0)
    texts=[g[0].text for g in gs]; scores=[]
    for k,t in zip(HELD,texts):
        plan=parse_plan(t); name,mut,_=variant(key,k); tests=tests_for(name)
        try:fixed=repair(mut,name,plan) if plan else mut; ok=run_source(name,fixed,tests)[0]
        except:ok=False
        scores.append(ok)
    return sum(scores)/len(scores),[x.strip().splitlines()[0] if x.strip() else '' for x in texts]

def retrieve_primitive(m,key):
    gs=m.sample(prompts=[prompt(key,k) for k in HELD],max_tokens=24,temperature=0.0)
    parsed=[parse_plan(g[0].text) for g in gs]
    canon=[tuple(p) for p in parsed if p]
    mode=collections.Counter(canon).most_common(1)[0][0] if canon else tuple()
    return list(mode),[list(x) if x else None for x in parsed]

def compose_target(key,primitive_plans,allowed_names=None):
    rows=[]; protected=[]
    names=list(primitive_plans) if allowed_names is None else [n for n in primitive_plans if n in allowed_names]
    for k in HELD:
        name,mut,_=variant(key,k); tests=tests_for(name); cut=max(1,len(tests)//2); select_tests=tests[:cut]; protect_tests=tests[cut:] or tests[:cut]
        candidates=[]
        for r in range(1,len(names)+1):
            for subset in itertools.combinations(names,r):
                plan=[]
                for n in subset: plan.extend(primitive_plans[n])
                # stable de-duplication
                plan=list(dict.fromkeys(plan))
                try: fixed=repair(mut,name,plan); sel=run_source(name,fixed,select_tests)[0]
                except: sel=False; fixed=None
                candidates.append({'subset':subset,'plan':plan,'select_pass':sel})
        passing=[c for c in candidates if c['select_pass']]
        chosen=min(passing,key=lambda c:(len(c['plan']),len(c['subset']),c['subset'])) if passing else None
        if chosen:
            try: fixed=repair(mut,name,chosen['plan']); prot=run_source(name,fixed,protect_tests)[0]
            except: prot=False
        else: prot=False
        rows.append({'variant':k,'chosen':chosen,'protected_pass':prot,'candidate_count':len(candidates)})
        protected.append(prot)
    return sum(protected)/len(protected),rows

R={'checkpoint':CHECKPOINT,'source':COMMIT,'protocol':'zero-gradient retrieve -> subset closure -> selection tests -> protected tests','direct':{},'retrieved':{},'composer':{},'ablations':{}}
with client.session(project='ml-v16-verified-composer') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=CHECKPOINT)
    for k in ['A','B','C']:
        plan,raw=retrieve_primitive(m,k);R['retrieved'][k]={'plan':plan,'raw':raw}
    for k in ['AB_TEST','ABC_TEST']:
        sc,samp=direct_eval(m,k);R['direct'][k]={'score':sc,'samples':samp}

plans={'A':R['retrieved']['A']['plan'],'B':R['retrieved']['B']['plan'],'C':R['retrieved']['C']['plan']}
for target in ['AB_TEST','ABC_TEST']:
    score,rows=compose_target(target,plans);R['composer'][target]={'score':score,'rows':rows}
    for missing in plans:
        allowed=[x for x in plans if x!=missing];sc,_=compose_target(target,plans,allowed);R['ablations'][f'{target}_minus_{missing}']=sc

# Fresh-session persistence: repeat retrieval + composition after a second independent load.
with client.session(project='ml-v16-reload-confirm') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=CHECKPOINT)
    fresh={}
    for k in ['A','B','C']: fresh[k]=retrieve_primitive(m,k)[0]
R['reload_retrieved']=fresh
for target in ['AB_TEST','ABC_TEST']:
    sc,_=compose_target(target,fresh);R.setdefault('reload_composer',{})[target]=sc

R['gates']={
 'primitives_retrieved':all(plans[k] for k in plans),
 'direct_AB_fails':R['direct']['AB_TEST']['score']<0.75,
 'direct_ABC_fails':R['direct']['ABC_TEST']['score']<0.75,
 'composer_AB_passes':R['composer']['AB_TEST']['score']>=0.75,
 'composer_ABC_passes':R['composer']['ABC_TEST']['score']>=0.75,
 'AB_requires_A':R['ablations']['AB_TEST_minus_A']<0.75,
 'AB_requires_B':R['ablations']['AB_TEST_minus_B']<0.75,
 'ABC_requires_A':R['ablations']['ABC_TEST_minus_A']<0.75,
 'ABC_requires_B':R['ablations']['ABC_TEST_minus_B']<0.75,
 'ABC_requires_C':R['ablations']['ABC_TEST_minus_C']<0.75,
 'reload_AB':R['reload_composer']['AB_TEST']>=0.75,
 'reload_ABC':R['reload_composer']['ABC_TEST']>=0.75,
}
R['verdict']='PASS_VERIFIED_COMPOSITION_LAYER' if all(R['gates'].values()) else 'MIXED_VERIFIED_COMPOSITION_LAYER'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2),flush=True)
