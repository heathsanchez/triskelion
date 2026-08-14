import ast, json, subprocess, tempfile, signal, sys, hashlib, itertools, copy
from pathlib import Path
from collections import Counter

REPO='https://github.com/jkoppel/QuixBugs.git'
COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
MAX_TASKS=36
MAX_CLOSURE_DEPTH=2
TIMEOUT=1

root=Path(tempfile.mkdtemp())/'qb'
subprocess.run(['git','clone','-q',REPO,str(root)],check=True)
subprocess.run(['git','checkout','-q',COMMIT],cwd=root,check=True)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==COMMIT
sys.path[:0]=[str(root),str(root/'python_programs')]

class TO(Exception): pass
def alarm(*_): raise TO()
signal.signal(signal.SIGALRM,alarm)

def load_tests(name):
    p=root/'json_testcases'/f'{name}.json'
    if not p.exists(): return None
    rows=[]
    try:
        for line in p.read_text().splitlines():
            if line.strip(): rows.append(json.loads(line))
    except Exception:return None
    return rows or None

def verify(name,src,tests):
    ns={'__name__':'candidate'}
    try: exec(compile(src,'<candidate>','exec'),ns,ns); fn=ns[name]
    except Exception:return False
    try:
        for args,exp in tests:
            signal.alarm(TIMEOUT)
            got=fn(*args)
            signal.alarm(0)
            if got!=exp:return False
        return True
    except BaseException:
        signal.alarm(0); return False

CMP=[ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.Eq,ast.NotEq,ast.Is,ast.IsNot,ast.In,ast.NotIn]
BIN=[ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv,ast.Mod,ast.Pow,ast.BitAnd,ast.BitOr,ast.BitXor]
BOOL=[ast.And,ast.Or]
UNARY=[ast.Not,ast.USub,ast.UAdd,ast.Invert]

def schema_key(s):return '|'.join(map(str,s))
def dl(s):
    # one structural opcode + one payload/replacement; NEGATE_TEST has no payload.
    return 1 if s[0]=='NEGATE_TEST' else 2

def schemas_in(src):
    try:t=ast.parse(src)
    except Exception:return []
    out=set()
    for n in ast.walk(t):
        if isinstance(n,ast.Compare) and len(n.ops)==1:
            old=type(n.ops[0])
            for new in CMP:
                if new is not old: out.add(('CMP',old.__name__,new.__name__))
        elif isinstance(n,ast.BinOp):
            old=type(n.op)
            for new in BIN:
                if new is not old: out.add(('BIN',old.__name__,new.__name__))
        elif isinstance(n,ast.BoolOp):
            old=type(n.op)
            for new in BOOL:
                if new is not old: out.add(('BOOL',old.__name__,new.__name__))
        elif isinstance(n,ast.UnaryOp):
            old=type(n.op)
            for new in UNARY:
                if new is not old: out.add(('UNARY',old.__name__,new.__name__))
        elif isinstance(n,ast.Constant) and isinstance(n.value,int) and not isinstance(n.value,bool):
            out.add(('CONST_DELTA',1)); out.add(('CONST_DELTA',-1))
        elif isinstance(n,(ast.If,ast.While)):
            out.add(('NEGATE_TEST',type(n).__name__))
    return sorted(out,key=schema_key)

CLS={c.__name__:c for c in CMP+BIN+BOOL+UNARY}

def matching(n,s):
    k=s[0]
    if k=='CMP': return isinstance(n,ast.Compare) and len(n.ops)==1 and type(n.ops[0]).__name__==s[1]
    if k=='BIN': return isinstance(n,ast.BinOp) and type(n.op).__name__==s[1]
    if k=='BOOL': return isinstance(n,ast.BoolOp) and type(n.op).__name__==s[1]
    if k=='UNARY': return isinstance(n,ast.UnaryOp) and type(n.op).__name__==s[1]
    if k=='CONST_DELTA': return isinstance(n,ast.Constant) and isinstance(n.value,int) and not isinstance(n.value,bool)
    if k=='NEGATE_TEST': return isinstance(n,(ast.If,ast.While)) and type(n).__name__==s[1]
    return False

def apply_at(src,s,idx):
    try:t=ast.parse(src)
    except Exception:return None
    class T(ast.NodeTransformer):
        def __init__(self):self.i=0;self.done=False
        def generic_visit(self,node):
            node=super().generic_visit(node)
            if not self.done and matching(node,s):
                if self.i==idx:
                    k=s[0]
                    if k=='CMP': node.ops[0]=CLS[s[2]]()
                    elif k=='BIN': node.op=CLS[s[2]]()
                    elif k=='BOOL': node.op=CLS[s[2]]()
                    elif k=='UNARY': node.op=CLS[s[2]]()
                    elif k=='CONST_DELTA': node.value += s[1]
                    elif k=='NEGATE_TEST': node.test=ast.UnaryOp(op=ast.Not(),operand=node.test)
                    self.done=True
                self.i+=1
            return node
    tr=T(); t=tr.visit(t); ast.fix_missing_locations(t)
    if not tr.done:return None
    try:return ast.unparse(t)+'\n'
    except Exception:return None

def variants(src,s):
    try:t=ast.parse(src); n=sum(1 for x in ast.walk(t) if matching(x,s))
    except Exception:return []
    out=[];seen=set()
    for i in range(n):
        z=apply_at(src,s,i)
        if z and z not in seen:seen.add(z);out.append(z)
    return out

def closure_states(src,schemas,depth):
    seen={src}; frontier=[src]
    for _ in range(depth):
        nxt=[]
        for cur in frontier:
            for s in schemas:
                for z in variants(cur,s):
                    if z not in seen:seen.add(z);nxt.append(z)
        frontier=nxt
        if not frontier:break
    return list(seen)

def closure_solve(task,schemas):
    for z in closure_states(task['src'],schemas,MAX_CLOSURE_DEPTH):
        if z!=task['src'] and verify(task['name'],z,task['tests']):return True
    return False

def discover(task,learned):
    # New schema may be applied after at most one already-known edit. This makes
    # descendant discoverability empirically dependent on prior algebra when a
    # natural bug genuinely needs a composition.
    bases=closure_states(task['src'],learned,1)
    wins={}
    for base in bases:
        for s in schemas_in(base):
            if s in learned:continue
            for z in variants(base,s):
                if verify(task['name'],z,task['tests']):
                    wins.setdefault(s,0);wins[s]+=1
                    break
    if not wins:return None
    best_dl=min(dl(s) for s in wins); cand=[s for s in wins if dl(s)==best_dl]
    best_support=max(wins[s] for s in cand); cand=[s for s in cand if wins[s]==best_support]
    chosen=sorted(cand,key=schema_key)[0]
    return {'schema':chosen,'dl':best_dl,'passing_sites':best_support,'min_dl_winners':[list(x) for x in cand]}

def probe_closure(tasks,learned):return {t['name'] for t in tasks if closure_solve(t,learned)}

# Build task pool from BUGGY source + public tests only. The correct source tree is
# intentionally not opened anywhere before genesis is complete.
tasks=[]
for p in sorted((root/'python_programs').glob('*.py')):
    tests=load_tests(p.stem)
    if not tests:continue
    src=p.read_text()
    if verify(p.stem,src,tests):continue
    tasks.append({'name':p.stem,'src':src,'tests':tests})

tasks=sorted(tasks,key=lambda t:hashlib.sha256(('V83-POOL|'+t['name']).encode()).hexdigest())[:MAX_TASKS]
# Frozen split from names only. H is never used for invention.
hold=[t for t in tasks if int(hashlib.sha256(('V83-H|'+t['name']).encode()).hexdigest(),16)%4==0]
stream=[t for t in tasks if t not in hold]
# two independently ordered developmental histories over disjoint halves
stream=sorted(stream,key=lambda t:hashlib.sha256(('V83-SPLIT|'+t['name']).encode()).hexdigest())
mid=(len(stream)+1)//2
S1=stream[:mid];S2=stream[mid:]

def genesis(S,salt,banned=None):
    banned=set(banned or [])
    order=sorted(S,key=lambda t:hashlib.sha256((salt+'|'+t['name']).encode()).hexdigest())
    learned=[]; events=[]; front=[len(probe_closure(hold,learned))]
    for task in order:
        if closure_solve(task,learned):
            events.append({'task':task['name'],'event':'CLOSURE_SOLVE','learned':[list(x) for x in learned]});continue
        d=discover(task,[s for s in learned if s not in banned])
        if d is None or d['schema'] in banned:
            events.append({'task':task['name'],'event':'OBSTRUCTION_UNCLOSED','learned':[list(x) for x in learned]});continue
        s=d['schema']; learned.append(s)
        events.append({'task':task['name'],'event':'EXTEND','extension':{'schema':list(s),'dl':d['dl'],'passing_sites':d['passing_sites'],'min_dl_winners':d['min_dl_winners']}})
        front.append(len(probe_closure(hold,learned)))
    return {'learned':learned,'events':events,'frontier':front,'order':[t['name'] for t in order]}

R1=genesis(S1,'V83-CURRICULUM-A');R2=genesis(S2,'V83-CURRICULUM-B')

def ext(R):return [tuple(e['extension']['schema']) for e in R['events'] if e['event']=='EXTEND']
E1=ext(R1);E2=ext(R2)

def signature(schema):
    # extensional signature over held-out source: which heldout programs become
    # solvable by this schema alone from A0.
    return tuple(sorted(probe_closure(hold,[schema])))
Q1=[{'schema':list(s),'signature':list(signature(s)),'dl':dl(s)} for s in E1]
Q2=[{'schema':list(s),'signature':list(signature(s)),'dl':dl(s)} for s in E2]
# quotient convergence ignores names/order and compares nonempty action signatures.
QS1=sorted((q['dl'],tuple(q['signature'])) for q in Q1 if q['signature'])
QS2=sorted((q['dl'],tuple(q['signature'])) for q in Q2 if q['signature'])

# Developmental counterfactual: if first learned schema exists, rerun same stream
# with it unavailable to both closure and invention. We do not assume it will have descendants.
def counterfactual(S,salt,R):
    es=ext(R)
    if not es:return None
    ban=es[0]
    rr=genesis(S,salt,banned={ban})
    return {'banned':list(ban),'original_later':[list(x) for x in es[1:]],'counterfactual_extensions':[list(x) for x in ext(rr)]}
CF1=counterfactual(S1,'V83-CURRICULUM-A',R1);CF2=counterfactual(S2,'V83-CURRICULUM-B',R2)

# Only now, after genesis state and hashes are frozen, read correct sources for audit.
preaudit_hash=hashlib.sha256(json.dumps({'R1':R1,'R2':R2},sort_keys=True,default=list).encode()).hexdigest()
audit=[]
for t in tasks:
    cp=root/'correct_python_programs'/f"{t['name']}.py"
    if cp.exists():
        audit.append({'program':t['name'],'bug_sha':hashlib.sha256(t['src'].encode()).hexdigest(),'correct_sha':hashlib.sha256(cp.read_bytes()).hexdigest()})

strict1=all(b>a for a,b in zip(R1['frontier'],R1['frontier'][1:])) if len(R1['frontier'])>1 else False
strict2=all(b>a for a,b in zip(R2['frontier'],R2['frontier'][1:])) if len(R2['frontier'])>1 else False
result={
 'protocol':'V83_QUIXBUGS_NATURAL_ALGEBRA_GENESIS_PILOT',
 'repo':REPO,'commit':COMMIT,
 'boundary':'pre-existing external buggy programs and public tests; generic AST mutation substrate is authored; correct sources sealed until after genesis; pilot does not require a three-generation lineage',
 'pool_size':len(tasks),'stream1_size':len(S1),'stream2_size':len(S2),'heldout_size':len(hold),
 'stream1':{'order_sha256':hashlib.sha256('\n'.join(R1['order']).encode()).hexdigest(),'extensions':[list(x) for x in E1],'heldout_closure_frontier':R1['frontier'],'events':R1['events'],'quotient':Q1},
 'stream2':{'order_sha256':hashlib.sha256('\n'.join(R2['order']).encode()).hexdigest(),'extensions':[list(x) for x in E2],'heldout_closure_frontier':R2['frontier'],'events':R2['events'],'quotient':Q2},
 'counterfactuals':{'stream1':CF1,'stream2':CF2},
 'independent_nonempty_quotient_signatures_equal':QS1==QS2 and bool(QS1),
 'strict_every_extension_stream1':strict1,'strict_every_extension_stream2':strict2,
 'preaudit_state_sha256':preaudit_hash,
 'correct_sources_read_only_after_genesis':True,
 'audit_hashes':audit,
}
# This is intentionally a diagnostic pilot. PASS means the natural corpus produced
# at least one verified reusable extension and a heldout closure expansion; it is
# not the IVAG crown jewel.
any_growth=(max(R1['frontier'] or [0])>0 or max(R2['frontier'] or [0])>0)
any_ext=bool(E1 or E2)
result['verdict']='PASS_NATURAL_GENESIS_PILOT_V83' if any_growth and any_ext else 'NEGATIVE_NATURAL_GENESIS_PILOT_V83'
print(json.dumps(result,indent=2,default=list))
Path('/tmp/v83_result.json').write_text(json.dumps(result,indent=2,default=list))
