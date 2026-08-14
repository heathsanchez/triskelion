import hashlib, json, os, pathlib, subprocess, sys, tokenize, io, time

QB = pathlib.Path(os.environ.get('QUIXBUGS_DIR','/tmp/QuixBugs')).resolve()
COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
SEED_A='V83-IVAG-A'
SEED_B='V83-IVAG-B'
STREAM_N=12
PROBE_N=10
TIMEOUT=8

# Frozen generic one-token edit substrate. No correct_python_programs access.
PAIRS=[
('<','<='),('<=','<'),('>','>='),('>=','>'),('==','!='),('!=','=='),
('+','-'),('-','+'),('*','+'),('+','*'),('//','/'),('/','//'),('%','//'),('//','%'),
('and','or'),('or','and'),('True','False'),('False','True'),
('min','max'),('max','min'),('append','extend'),('extend','append'),
('0','1'),('1','0'),('1','2'),('2','1')
]

def h(s): return hashlib.sha256(s.encode()).hexdigest()
def dl(schema): return len(schema[0])+len(schema[1])+2

def task_names():
    names=[]
    for p in sorted((QB/'python_testcases').glob('test_*.py')):
        n=p.stem[len('test_'):]
        if not (QB/'python_programs'/f'{n}.py').exists(): continue
        if n in {'knapsack','levenshtein','bitcount'}: continue
        names.append(n)
    return names

def ordered(names,seed): return sorted(names,key=lambda n:h(seed+'|'+n))

def mutations(src, schema):
    old,new=schema
    toks=list(tokenize.generate_tokens(io.StringIO(src).readline))
    idx=[i for i,t in enumerate(toks) if t.string==old and t.type in (tokenize.OP,tokenize.NAME,tokenize.NUMBER)]
    out=[]
    for i in idx:
        tt=toks.copy(); tt[i]=tt[i]._replace(string=new)
        try: s=tokenize.untokenize(tt); compile(s,'<mut>','exec')
        except Exception: continue
        out.append((i,s))
    return out

cache={}
def verify(name, src):
    key=(name,hashlib.sha256(src.encode()).hexdigest())
    if key in cache:return cache[key]
    path=QB/'python_programs'/f'{name}.py'; orig=path.read_text()
    try:
        path.write_text(src)
        # remove bytecode to force source reload
        for pyc in (QB/'python_programs'/'__pycache__').glob(f'{name}.*.pyc') if (QB/'python_programs'/'__pycache__').exists() else []: pyc.unlink(missing_ok=True)
        cp=subprocess.run([sys.executable,'-m','pytest','-q',f'python_testcases/test_{name}.py','--disable-warnings','--maxfail=1'],cwd=QB,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=TIMEOUT)
        ok=(cp.returncode==0)
    except subprocess.TimeoutExpired: ok=False
    finally: path.write_text(orig)
    cache[key]=ok; return ok

def schema_solves(name,schema):
    src=(QB/'python_programs'/f'{name}.py').read_text()
    return any(verify(name,m) for _,m in mutations(src,schema))

def closure_solved(name, retained):
    src=(QB/'python_programs'/f'{name}.py').read_text()
    if verify(name,src): return ('BASE',None)
    for s in retained:
        if schema_solves(name,s): return ('RETAINED',s)
    return (None,None)

def discover(name,retained):
    passes=[]
    for s in PAIRS:
        if s in retained: continue
        if schema_solves(name,s): passes.append(s)
    if not passes:return None,[]
    md=min(dl(s) for s in passes)
    mins=sorted([s for s in passes if dl(s)==md])
    return mins[0], mins

def frontier(probes, retained):
    return sorted([n for n in probes if closure_solved(n,retained)[0] is not None])

def run_stream(stream,probes):
    retained=[]; events=[]; fronts=[frontier(probes,retained)]
    for name in stream:
        mode,s=closure_solved(name,retained)
        if mode:
            events.append({'task':name,'event':'closure','via':list(s) if s else None}); continue
        ext,mins=discover(name,retained)
        if ext is None:
            events.append({'task':name,'event':'obstruction_unclosed'}); continue
        retained.append(ext)
        fr=frontier(probes,retained)
        events.append({'task':name,'event':'extend','extension':list(ext),'dl':dl(ext),'minimal_ties':[list(x) for x in mins],'frontier_gain':len(set(fr)-set(fronts[-1]))})
        fronts.append(fr)
    return {'retained':[list(x) for x in retained],'events':events,'frontiers':fronts}

names=task_names(); master=ordered(names,'V83-MASTER')
stream_pool=master[:STREAM_N]; probes=master[STREAM_N:STREAM_N+PROBE_N]
A=run_stream(ordered(stream_pool,SEED_A),probes)
B=run_stream(ordered(stream_pool,SEED_B),probes)

# extensional convergence: same set of retained token-rewrite schemas, independent order.
setA={tuple(x) for x in A['retained']}; setB={tuple(x) for x in B['retained']}
strictA=all(len(A['frontiers'][i])<len(A['frontiers'][i+1]) for i in range(len(A['frontiers'])-1)) if len(A['frontiers'])>1 else False
strictB=all(len(B['frontiers'][i])<len(B['frontiers'][i+1]) for i in range(len(B['frontiers'])-1)) if len(B['frontiers'])>1 else False
# Developmental lineage requires later newly acquired extensions to be unavailable/discoverability-dependent on ancestors.
# Under this generic one-edit constructor, every PAIR is always candidate-discoverable, so do NOT manufacture this gate.
lineage=False

res={
'protocol':'V83_QUIXBUGS_NATURAL_IVAG_CENSUS',
'external_repo':'jkoppel/QuixBugs','external_commit':COMMIT,
'correct_solutions_read_during_discovery':False,
'generic_schema_count':len(PAIRS),'stream_pool':stream_pool,'probe_set':probes,
'curriculum_A':ordered(stream_pool,SEED_A),'curriculum_B':ordered(stream_pool,SEED_B),
'A':A,'B':B,
'gates':{
  'natural_preexisting_corpus':True,
  'at_least_one_minimal_extension_each':bool(A['retained']) and bool(B['retained']),
  'strict_probe_closure_growth_A':strictA,
  'strict_probe_closure_growth_B':strictB,
  'independent_extension_set_convergence':setA==setB and bool(setA),
  'three_generation_developmental_causality':lineage,
 },
'qualification':'Natural pre-existing repair census under a frozen generic one-token constructor. Generic constructor exposes all token-pair schemas from the start, so descendant discoverability causality cannot pass by design and is reported false rather than inferred.'
}
g=res['gates']
if all(g.values()): verdict='PASS_NATURAL_IVAG_V83'
elif g['natural_preexisting_corpus'] and g['at_least_one_minimal_extension_each']: verdict='MIXED_NATURAL_IVAG_V83'
else: verdict='NEGATIVE_NATURAL_IVAG_V83'
res['verdict']=verdict
print(json.dumps(res,indent=2))
path=os.environ.get('V83_RESULT','/tmp/v83_result.json'); open(path,'w').write(json.dumps(res,indent=2))
