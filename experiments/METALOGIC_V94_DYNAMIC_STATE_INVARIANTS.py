#!/usr/bin/env python3
import ast, atexit, copy, hashlib, json, math, os, re, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(os.environ.get('QUIXBUGS_DIR','/tmp/QuixBugs'))
OUT=Path(os.environ.get('OUT_DIR','results/v94')); OUT.mkdir(parents=True,exist_ok=True)
SEED='V94_DYNAMIC_STATE_INVARIANTS_2026-08-14'
COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
TRAIN_N=8; TEST_N=8; CAND_CAP=45; VERIFY_BUDGET=10
DIMS=['events','calls','returns','exceptions','max_depth','unique_lines','revisits','coll_grow','coll_shrink','num_up','num_down','locals_grow','locals_shrink']

def h(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def vec(d): return [float(d.get(k,0)) for k in DIMS]
def delta(a,b): return [y-x for x,y in zip(vec(a),vec(b))]
def norm(v):
    z=math.sqrt(sum(x*x for x in v)); return [x/z for x in v] if z else [0.0]*len(v)
def sim(a,b): return sum(x*y for x,y in zip(norm(a),norm(b)))

def tracer_code():
    return r'''import atexit,json,os,sys
T=os.environ.get("V94_TARGET",""); O=os.environ.get("V94_TRACE_OUT","")
m={"events":0,"calls":0,"returns":0,"exceptions":0,"max_depth":0,"unique_lines":0,"revisits":0,"coll_grow":0,"coll_shrink":0,"num_up":0,"num_down":0,"locals_grow":0,"locals_shrink":0}
seen=set(); last={}; depth=0

def snap(fr):
    coll=0; num=0.0; lc=len(fr.f_locals)
    for v in fr.f_locals.values():
        try:
            if isinstance(v,(list,tuple,set,dict,str,bytes)): coll+=len(v)
            elif isinstance(v,(int,float)) and not isinstance(v,bool): num+=float(v)
        except Exception: pass
    return coll,num,lc

def tr(fr,ev,arg):
    global depth
    fn=fr.f_code.co_filename.replace('\\','/')
    if T and ('/python_programs/'+T+'.py') not in fn: return tr
    if ev=='call': m['calls']+=1; depth+=1; m['max_depth']=max(m['max_depth'],depth)
    elif ev=='return': m['returns']+=1; depth=max(0,depth-1)
    elif ev=='exception': m['exceptions']+=1
    if ev=='line':
        m['events']+=1; key=(fn,fr.f_lineno)
        if key in seen:m['revisits']+=1
        else:seen.add(key);m['unique_lines']+=1
        s=snap(fr); k=id(fr)
        if k in last:
            p=last[k]
            if s[0]>p[0]:m['coll_grow']+=1
            elif s[0]<p[0]:m['coll_shrink']+=1
            if s[1]>p[1]:m['num_up']+=1
            elif s[1]<p[1]:m['num_down']+=1
            if s[2]>p[2]:m['locals_grow']+=1
            elif s[2]<p[2]:m['locals_shrink']+=1
        last[k]=s
    return tr
sys.settrace(tr)
@atexit.register
def done():
    try:
        if O: open(O,'w').write(json.dumps(m))
    except Exception: pass
'''

def run(name,text):
    p=ROOT/'python_programs'/f'{name}.py'; old=p.read_text(); td=Path(tempfile.mkdtemp(prefix='v94_')); (td/'sitecustomize.py').write_text(tracer_code()); tf=td/'trace.json'
    env=os.environ.copy(); env['PYTHONPATH']=str(td)+os.pathsep+env.get('PYTHONPATH',''); env['V94_TARGET']=name; env['V94_TRACE_OUT']=str(tf)
    try:
        p.write_text(text)
        r=subprocess.run([sys.executable,'-m','pytest','-q',f'python_testcases/test_{name}.py','--timeout=4'],cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=25)
        passed=(r.returncode==0)
        tr=json.loads(tf.read_text()) if tf.exists() else {k:0 for k in DIMS}
        return passed,tr
    except Exception:
        return False,{k:0 for k in DIMS}
    finally:
        p.write_text(old)
        try:
            for q in td.iterdir():q.unlink()
            td.rmdir()
        except Exception:pass

MUT=(ast.Name,ast.Constant,ast.cmpop,ast.operator,ast.boolop,ast.unaryop)
OP={ast.Lt:[ast.LtE,ast.Gt,ast.Eq],ast.LtE:[ast.Lt,ast.GtE,ast.Eq],ast.Gt:[ast.GtE,ast.Lt,ast.Eq],ast.GtE:[ast.Gt,ast.LtE,ast.Eq],ast.Eq:[ast.NotEq,ast.Lt,ast.LtE],ast.NotEq:[ast.Eq],ast.Add:[ast.Sub,ast.Mult],ast.Sub:[ast.Add,ast.Mult],ast.Mult:[ast.Add,ast.Sub,ast.FloorDiv],ast.FloorDiv:[ast.Div,ast.Mult],ast.Mod:[ast.FloorDiv,ast.Mult],ast.And:[ast.Or],ast.Or:[ast.And]}
def candidates(src,cap):
    try:t=ast.parse(src)
    except:return []
    names=sorted({n.id for n in ast.walk(t) if isinstance(n,ast.Name)}); nodes=[n for n in ast.walk(t) if isinstance(n,MUT)]; out=[]
    def repl(idx,new):
        k=-1
        class X(ast.NodeTransformer):
            def generic_visit(self,node):
                nonlocal k
                if isinstance(node,MUT):
                    k+=1
                    if k==idx:return copy.deepcopy(new)
                return super().generic_visit(node)
        z=ast.fix_missing_locations(X().visit(copy.deepcopy(t))); return ast.unparse(z)
    for i,n in enumerate(nodes):
        rs=[]
        if isinstance(n,ast.Name):rs=[ast.Name(id=x,ctx=copy.deepcopy(n.ctx)) for x in names if x!=n.id][:5]
        elif isinstance(n,ast.Constant) and isinstance(n.value,(int,float,bool)):rs=[ast.Constant(x) for x in (-1,0,1,2) if x!=n.value]
        else:
            for typ,alts in OP.items():
                if isinstance(n,typ):rs=[a() for a in alts];break
        for r in rs:
            try:out.append(repl(i,r))
            except Exception:pass
            if len(out)>=cap:return out
    return out

def permute(v):
    order=sorted(range(len(DIMS)),key=lambda i:h('perm|'+DIMS[i])); return [v[i] for i in order]

def main():
    buggy=ROOT/'python_programs'; correct=ROOT/'correct_python_programs'; tests=ROOT/'python_testcases'
    names=[]
    for p in buggy.glob('*.py'):
        n=p.stem
        if not (tests/f'test_{n}.py').exists() or not (correct/f'{n}.py').exists():continue
        ok,_=run(n,p.read_text())
        if not ok:names.append(n)
    names=sorted(names,key=h); train=names[:TRAIN_N]; test=names[TRAIN_N:TRAIN_N+TEST_N]
    prototypes=[]; train_rows=[]
    for n in train:
        btxt=(buggy/f'{n}.py').read_text(); ctxt=(correct/f'{n}.py').read_text()
        bok,bt=run(n,btxt); cok,ct=run(n,ctxt)
        d=delta(bt,ct)
        if cok and any(abs(x)>0 for x in d):prototypes.append(d)
        train_rows.append({'task':n,'bug_pass':bok,'correct_pass':cok,'delta':d})
    null_protos=[permute(x) for x in prototypes]
    rows=[]; learned_solved=[]; null_solved=[]; unrestricted=[]
    for n in test:
        src=(buggy/f'{n}.py').read_text(); _,base=run(n,src); cs=[]
        for text in candidates(src,CAND_CAP):
            ok,tr=run(n,text); d=delta(base,tr)
            ls=max([sim(d,p) for p in prototypes],default=-1); ns=max([sim(d,p) for p in null_protos],default=-1)
            cs.append((text,ok,ls,ns,d))
        if any(x[1] for x in cs):unrestricted.append(n)
        lr=sorted(cs,key=lambda x:(-x[2],h(x[0])))[:VERIFY_BUDGET]
        nr=sorted(cs,key=lambda x:(-x[3],h(x[0])))[:VERIFY_BUDGET]
        l=any(x[1] for x in lr); q=any(x[1] for x in nr)
        if l:learned_solved.append(n)
        if q:null_solved.append(n)
        rows.append({'task':n,'candidate_count':len(cs),'any_success':any(x[1] for x in cs),'learned_budget_success':l,'null_budget_success':q,'best_learned_scores':[round(x[2],5) for x in lr[:5]],'best_null_scores':[round(x[3],5) for x in nr[:5]]})
    gates={'preexisting_external_corpus':True,'heldout_correct_never_read':True,'nonempty_dynamic_prototypes':bool(prototypes),'reachable_success_exists':bool(unrestricted),'learned_beats_null':len(learned_solved)>len(null_solved),'learned_recovers_success':bool(learned_solved)}
    verdict='PASS_DYNAMIC_STATE_INVARIANTS_V94' if all(gates.values()) else 'MIXED_DYNAMIC_STATE_INVARIANTS_V94'
    res={'protocol':'V94_DYNAMIC_STATE_INVARIANTS','external_commit':COMMIT,'seed':SEED,'dims':DIMS,'train':train,'test':test,'train_rows':train_rows,'prototype_count':len(prototypes),'learned_solved':learned_solved,'null_solved':null_solved,'unrestricted_reachable':unrestricted,'rows':rows,'gates':gates,'verdict':verdict,'qualification':'Supervised natural bridge: training-side independently authored correct implementations are used only to induce anonymous execution-state delta prototypes. Held-out correct implementations are never read. Candidate syntax is generic and identical across learned/null arms. A PASS would show transfer of dynamic state-transition geometry under a fixed verification budget, not autonomous invention of invariant vocabulary.'}
    (OUT/'RESULT.json').write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
if __name__=='__main__':main()
