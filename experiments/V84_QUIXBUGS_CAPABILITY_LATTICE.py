import hashlib, io, itertools, json, os, pathlib, subprocess, sys, tokenize

QB = pathlib.Path(os.environ.get('QUIXBUGS_DIR','/tmp/QuixBugs')).resolve()
COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
TIMEOUT=8
# Same frozen one-token constructor family as V83.
PAIRS=[
('<','<='),('<=','<'),('>','>='),('>=','>'),('==','!='),('!=','=='),
('+','-'),('-','+'),('*','+'),('+','*'),('//','/'),('/','//'),('%','//'),('//','%'),
('and','or'),('or','and'),('True','False'),('False','True'),
('min','max'),('max','min'),('append','extend'),('extend','append'),
('0','1'),('1','0'),('1','2'),('2','1')
]

def h(s): return hashlib.sha256(s.encode()).hexdigest()
def dl(s): return len(s[0])+len(s[1])+2

def task_names():
    names=[]
    for p in sorted((QB/'python_testcases').glob('test_*.py')):
        n=p.stem[len('test_'):]
        if not (QB/'python_programs'/f'{n}.py').exists(): continue
        if n in {'knapsack','levenshtein','bitcount'}: continue
        names.append(n)
    return sorted(names,key=lambda n:h('V84-NATURAL-LATTICE|'+n))

def mutations(src, schema):
    old,new=schema
    toks=list(tokenize.generate_tokens(io.StringIO(src).readline))
    idx=[i for i,t in enumerate(toks) if t.string==old and t.type in (tokenize.OP,tokenize.NAME,tokenize.NUMBER)]
    out=[]
    for i in idx:
        tt=toks.copy(); tt[i]=tt[i]._replace(string=new)
        try:
            s=tokenize.untokenize(tt); compile(s,'<mut>','exec')
        except Exception:
            continue
        out.append(s)
    return out

cache={}
def verify(name, src):
    key=(name,hashlib.sha256(src.encode()).hexdigest())
    if key in cache:return cache[key]
    path=QB/'python_programs'/f'{name}.py'; orig=path.read_text()
    try:
        path.write_text(src)
        pc=QB/'python_programs'/'__pycache__'
        if pc.exists():
            for pyc in pc.glob(f'{name}.*.pyc'): pyc.unlink(missing_ok=True)
        cp=subprocess.run([sys.executable,'-m','pytest','-q',f'python_testcases/test_{name}.py','--disable-warnings','--maxfail=1'],cwd=QB,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=TIMEOUT)
        ok=cp.returncode==0
    except subprocess.TimeoutExpired:
        ok=False
    finally:
        path.write_text(orig)
    cache[key]=ok; return ok

def schema_solves(name,schema):
    src=(QB/'python_programs'/f'{name}.py').read_text()
    return any(verify(name,m) for m in mutations(src,schema))

names=task_names()
# Ignore tasks already passing unchanged when constructing repair capability sets.
baseline={n:verify(n,(QB/'python_programs'/f'{n}.py').read_text()) for n in names}
failed=[n for n in names if not baseline[n]]
solve_sets={}
for s in PAIRS:
    solve_sets[s]=frozenset(n for n in failed if schema_solves(n,s))

# Quotient by extensional action over this frozen observational universe.
classes={}
for s,ss in solve_sets.items(): classes.setdefault(tuple(sorted(ss)),[]).append(s)
q=[]
for obs,members in classes.items():
    if not obs: continue
    members=sorted(members)
    q.append({'members':[list(x) for x in members], 'solve_set':list(obs), 'size':len(obs), 'min_dl':min(dl(x) for x in members)})
q.sort(key=lambda x:(x['size'],x['solve_set'],x['members']))

# Empirical implication preorder: class A >= B when A reaches every task B reaches.
# Hasse covers are strict inclusion with no intermediate observed class.
sets=[frozenset(x['solve_set']) for x in q]
covers=[]
for i,a in enumerate(sets):
    for j,b in enumerate(sets):
        if i==j or not (b < a): continue
        intermediate=any(b < c < a for k,c in enumerate(sets) if k not in (i,j))
        if not intermediate: covers.append([i,j])

reachable=set().union(*solve_sets.values()) if solve_sets else set()
# Candidate classes represented by their cheapest member. Find minimum-description set cover
# over all tasks reachable by at least one primitive schema. This is NOT compositional completeness.
reps=[]
for qi,x in enumerate(q):
    mem=[tuple(m) for m in x['members']]
    rep=min(mem,key=lambda s:(dl(s),s))
    reps.append((qi,rep,frozenset(x['solve_set']),dl(rep)))

best=None
# Search exact basis by cardinality, then DL. q is small on natural data; cap at 10 classes.
if reachable:
    for r in range(1,min(10,len(reps))+1):
        found=[]
        for comb in itertools.combinations(reps,r):
            u=set().union(*(x[2] for x in comb))
            if u>=reachable:
                found.append((sum(x[3] for x in comb),comb))
        if found:
            found.sort(key=lambda z:(z[0],[(x[0],x[1]) for x in z[1]]))
            cost,comb=found[0]
            best={'cardinality':r,'dl':cost,'classes':[x[0] for x in comb],'representatives':[list(x[1]) for x in comb]}
            break

# Unique causal contribution and developmental gain proxy.
primitive_stats=[]
all_union=set(reachable)
for s,ss in solve_sets.items():
    others=set().union(*(v for k,v in solve_sets.items() if k!=s))
    unique=set(ss)-others
    primitive_stats.append({'schema':list(s),'dl':dl(s),'solve_count':len(ss),'unique_count':len(unique),'unique_tasks':sorted(unique),'DG':(len(ss)/dl(s) if dl(s) else 0.0)})
primitive_stats.sort(key=lambda x:(-x['DG'],-x['unique_count'],-x['solve_count'],x['schema']))

# Recurrence-vs-value test: does appearing on multiple tasks imply unique closure value?
recurrent=[x for x in primitive_stats if x['solve_count']>=2]
recurrent_zero_unique=[x for x in recurrent if x['unique_count']==0]

res={
 'protocol':'V84_QUIXBUGS_CAPABILITY_LATTICE',
 'external_repo':'jkoppel/QuixBugs','external_commit':COMMIT,
 'correct_solutions_read':False,
 'task_count':len(names),'baseline_fail_count':len(failed),'reachable_by_constructor':len(reachable),
 'schema_count':len(PAIRS),'nonempty_extensional_classes':len(q),
 'quotient_classes':q,'hasse_covers':covers,'minimum_observational_basis':best,
 'primitive_stats':primitive_stats,
 'recurrent_schema_count':len(recurrent),'recurrent_but_zero_unique_count':len(recurrent_zero_unique),
 'recurrent_but_zero_unique':[x['schema'] for x in recurrent_zero_unique],
 'gates':{
   'natural_preexisting_corpus':True,
   'nontrivial_quotient':len(q)>=2,
   'at_least_one_strict_inclusion':bool(covers),
   'exact_minimum_observational_basis_found':best is not None,
   'recurrence_distinguished_from_unique_value':bool(recurrent_zero_unique),
 },
 'qualification':'Empirical Post/ETP-style observational lattice for the frozen V83 one-token constructor. Inclusion means verified task-reachability inclusion on this corpus, not formal functional derivability; the minimum basis is a minimum set cover of constructor-reachable tasks, not a proof of universal/compositional completeness.'
}
res['verdict']='PASS_NATURAL_CAPABILITY_LATTICE_V84' if all(res['gates'].values()) else 'MIXED_NATURAL_CAPABILITY_LATTICE_V84'
print(json.dumps(res,indent=2))
open(os.environ.get('V84_RESULT','/tmp/v84_result.json'),'w').write(json.dumps(res,indent=2))
