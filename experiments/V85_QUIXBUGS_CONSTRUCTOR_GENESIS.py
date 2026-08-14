import ast, copy, hashlib, io, itertools, json, os, pathlib, subprocess, sys, tokenize

QB=pathlib.Path(os.environ.get('QUIXBUGS_DIR','/tmp/QuixBugs')).resolve()
COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
TIMEOUT=8
N_TRAIN=12; N_TEST=12; SUPPORT=2; CAP=30
K0_PAIRS=[('<','<='),('<=','<'),('>','>='),('>=','>'),('==','!='),('!=','=='),('+','-'),('-','+'),('*','+'),('+','*'),('//','/'),('/','//'),('%','//'),('//','%'),('and','or'),('or','and'),('True','False'),('False','True'),('min','max'),('max','min'),('append','extend'),('extend','append'),('0','1'),('1','0'),('1','2'),('2','1')]
FAMILIES=['COMPARE_OP','BIN_OP','BOOL_OP','CONST_INT','NAME_LOAD','CALL_ARG_SWAP','BIN_SWAP','NEGATE_TEST','COMPARE_SWAP','CALL_ARG_REPLACE','RETURN_ATOM']

def h(s): return hashlib.sha256(s.encode()).hexdigest()
def ordered(xs,seed): return sorted(xs,key=lambda x:h(seed+'|'+x))

def task_names():
    out=[]
    for p in sorted((QB/'python_testcases').glob('test_*.py')):
        n=p.stem[len('test_'):]
        if (QB/'python_programs'/f'{n}.py').exists() and n not in {'knapsack','levenshtein','bitcount'}: out.append(n)
    return ordered(out,'V85-SPLIT')

cache={}
def verify(name,src):
    key=(name,h(src))
    if key in cache:return cache[key]
    path=QB/'python_programs'/f'{name}.py'; orig=path.read_text()
    try:
        path.write_text(src)
        pc=QB/'python_programs'/'__pycache__'
        if pc.exists():
            for pyc in pc.glob(f'{name}.*.pyc'): pyc.unlink(missing_ok=True)
        cp=subprocess.run([sys.executable,'-m','pytest','-q',f'python_testcases/test_{name}.py','--disable-warnings','--maxfail=1'],cwd=QB,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=TIMEOUT)
        ok=cp.returncode==0
    except subprocess.TimeoutExpired: ok=False
    finally: path.write_text(orig)
    cache[key]=ok; return ok

def token_mutations(src,schema):
    old,new=schema; toks=list(tokenize.generate_tokens(io.StringIO(src).readline)); out=[]
    for i,t in enumerate(toks):
        if t.string!=old or t.type not in (tokenize.OP,tokenize.NAME,tokenize.NUMBER): continue
        tt=toks.copy(); tt[i]=tt[i]._replace(string=new)
        try:s=tokenize.untokenize(tt); compile(s,'<mut>','exec')
        except Exception:continue
        out.append(s)
    return out

def k0_solves(name):
    src=(QB/'python_programs'/f'{name}.py').read_text()
    if verify(name,src): return True
    for s in K0_PAIRS:
        for m in token_mutations(src,s):
            if verify(name,m): return True
    return False

def atom_values(tree):
    names=sorted({n.id for n in ast.walk(tree) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load)})
    consts=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,bool,str,type(None))):
            if n.value not in consts: consts.append(n.value)
    return names,consts

def emit(tree):
    ast.fix_missing_locations(tree)
    try:
        s=ast.unparse(tree)+'\n'; compile(s,'<mut>','exec'); return s
    except Exception:return None

def candidates(src,family,seed):
    try: base=ast.parse(src)
    except Exception:return []
    nodes=list(ast.walk(base)); names,consts=atom_values(base); outs=[]
    cmp_types=[ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.Eq,ast.NotEq]
    bin_types=[ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv,ast.Mod]
    for idx,node in enumerate(nodes):
        specs=[]
        if family=='COMPARE_OP' and isinstance(node,ast.Compare):
            for oi,op in enumerate(node.ops):
                for typ in cmp_types:
                    if isinstance(op,typ):continue
                    specs.append(('cmp',oi,typ))
        elif family=='BIN_OP' and isinstance(node,ast.BinOp):
            for typ in bin_types:
                if isinstance(node.op,typ):continue
                specs.append(('binop',typ))
        elif family=='BOOL_OP' and isinstance(node,ast.BoolOp):
            typ=ast.Or if isinstance(node.op,ast.And) else ast.And; specs.append(('bool',typ))
        elif family=='CONST_INT' and isinstance(node,ast.Constant) and isinstance(node.value,int) and not isinstance(node.value,bool):
            vals=sorted(set([-1,0,1,2]+[x for x in consts if isinstance(x,int) and not isinstance(x,bool)]))
            for v in vals:
                if v!=node.value: specs.append(('const',v))
        elif family=='NAME_LOAD' and isinstance(node,ast.Name) and isinstance(node.ctx,ast.Load):
            for nm in names:
                if nm!=node.id: specs.append(('name',nm))
        elif family=='CALL_ARG_SWAP' and isinstance(node,ast.Call) and len(node.args)>=2:
            for a in range(len(node.args)):
                for b in range(a+1,len(node.args)):specs.append(('argswap',a,b))
        elif family=='BIN_SWAP' and isinstance(node,ast.BinOp): specs.append(('binswap',))
        elif family=='NEGATE_TEST' and isinstance(node,(ast.If,ast.While)): specs.append(('negtest',))
        elif family=='COMPARE_SWAP' and isinstance(node,ast.Compare) and len(node.comparators)==1: specs.append(('cmpswap',))
        elif family=='CALL_ARG_REPLACE' and isinstance(node,ast.Call) and node.args:
            atoms=[('name',x) for x in names]+[('const',x) for x in consts[:8]]
            for ai in range(len(node.args)):
                for atom in atoms: specs.append(('argreplace',ai,atom))
        elif family=='RETURN_ATOM' and isinstance(node,ast.Return):
            for nm in names: specs.append(('retname',nm))
            for v in consts[:8]: specs.append(('retconst',v))
        for spec in specs:
            t=copy.deepcopy(base); ns=list(ast.walk(t)); n=ns[idx]
            try:
                tag=spec[0]
                if tag=='cmp': n.ops[spec[1]]=spec[2]()
                elif tag=='binop': n.op=spec[1]()
                elif tag=='bool': n.op=spec[1]()
                elif tag=='const': n.value=spec[1]
                elif tag=='name': n.id=spec[1]
                elif tag=='argswap': n.args[spec[1]],n.args[spec[2]]=n.args[spec[2]],n.args[spec[1]]
                elif tag=='binswap': n.left,n.right=n.right,n.left
                elif tag=='negtest': n.test=ast.UnaryOp(op=ast.Not(),operand=n.test)
                elif tag=='cmpswap': n.left,n.comparators[0]=n.comparators[0],n.left
                elif tag=='argreplace':
                    _,ai,atom=spec; kind,val=atom; n.args[ai]=ast.Name(id=val,ctx=ast.Load()) if kind=='name' else ast.Constant(value=val)
                elif tag=='retname': n.value=ast.Name(id=spec[1],ctx=ast.Load())
                elif tag=='retconst': n.value=ast.Constant(value=spec[1])
                s=emit(t)
                if s and s!=src: outs.append(s)
            except Exception: pass
    # Stable de-dup and bounded verifier budget per family/task.
    uniq={h(x):x for x in outs}; ordered_hash=sorted(uniq,key=lambda z:h(seed+'|'+z))[:CAP]
    return [uniq[z] for z in ordered_hash]

def family_solves(name,family):
    src=(QB/'python_programs'/f'{name}.py').read_text()
    for m in candidates(src,family,'V85|'+name+'|'+family):
        if verify(name,m): return True
    return False

names=task_names(); train=names[:N_TRAIN]; test=names[N_TRAIN:N_TRAIN+N_TEST]
# Baseline K0 measured on sealed test independently of family selection.
k0_test={n:k0_solves(n) for n in test}
train_matrix={f:{n:family_solves(n,f) for n in train} for f in FAMILIES}
support={f:sum(train_matrix[f].values()) for f in FAMILIES}
selected=sorted([f for f in FAMILIES if support[f]>=SUPPORT])
# Frozen selection rule: if no family has support >= SUPPORT, K1 is empty and experiment is negative.
test_matrix={f:{n:family_solves(n,f) for n in test} for f in FAMILIES}
def subset_solved(fs): return {n for n in test if any(test_matrix[f][n] for f in fs)}
k0_set={n for n,v in k0_test.items() if v}; k1_set=subset_solved(selected)
new_set=k1_set-k0_set
# Exhaustive matched-cardinality null over all family subsets, evaluated only after selection is frozen.
null=[]
if selected:
    for comb in itertools.combinations(FAMILIES,len(selected)):
        if set(comb)==set(selected): continue
        null.append(len(subset_solved(comb)-k0_set))
null_mean=sum(null)/len(null) if null else 0.0; null_max=max(null) if null else 0
# Family ablation signatures on held-out closure.
ablation={f:len(k1_set-subset_solved([x for x in selected if x!=f])) for f in selected}
res={
 'protocol':'V85_QUIXBUGS_CONSTRUCTOR_GENESIS','external_repo':'jkoppel/QuixBugs','external_commit':COMMIT,
 'correct_solutions_read':False,'train':train,'test':test,'family_count':len(FAMILIES),'candidate_cap_per_family_task':CAP,'support_threshold':SUPPORT,
 'train_support':support,'selected_K1_families':selected,'k0_test_solved':sorted(k0_set),'k1_test_solved':sorted(k1_set),'new_test_closure':sorted(new_set),
 'k0_count':len(k0_set),'k1_count':len(k1_set),'new_count':len(new_set),'matched_null_mean_new':null_mean,'matched_null_max_new':null_max,'ablation_loss':ablation,
 'gates':{
   'natural_preexisting_corpus':True,
   'no_correct_solutions_read':True,
   'constructor_family_induced_from_verifier_training_support':bool(selected),
   'heldout_closure_strictly_expands':len(new_set)>0,
   'selected_beats_matched_family_null_mean':len(new_set)>null_mean,
   'at_least_one_selected_family_is_causally_load_bearing':any(v>0 for v in ablation.values()),
 },
 'qualification':'Bounded constructor-genesis bridge. K1 is selected from a supplied generic AST mutation-family meta-substrate using executable training support only; this is not unrestricted invention of constructor families. Correct QuixBugs implementations are never read. Held-out test outcomes are used only after K1 selection is frozen.'
}
res['verdict']='PASS_NATURAL_CONSTRUCTOR_GENESIS_V85' if all(res['gates'].values()) else 'MIXED_NATURAL_CONSTRUCTOR_GENESIS_V85'
print(json.dumps(res,indent=2)); open(os.environ.get('V85_RESULT','/tmp/v85_result.json'),'w').write(json.dumps(res,indent=2))
