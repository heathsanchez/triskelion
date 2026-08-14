#!/usr/bin/env python3
import ast, copy, hashlib, json, math, os, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT=Path(os.environ.get('QUIXBUGS_DIR','/tmp/QuixBugs'))
OUT=Path(os.environ.get('OUT_DIR','results/v93')); OUT.mkdir(parents=True,exist_ok=True)
SEED='V93_WHOLE_PROGRAM_SIGNATURE_2026-08-14'
COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
BUDGET=120

def h(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()
def run_test(name,text):
    p=ROOT/'python_programs'/f'{name}.py'; old=p.read_text()
    try:
        p.write_text(text)
        r=subprocess.run([sys.executable,'-m','pytest','-q',f'python_testcases/test_{name}.py','--timeout=4'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20)
        return r.returncode==0
    except Exception:return False
    finally:p.write_text(old)

def sig(src):
    try:t=ast.parse(src)
    except:return Counter()
    c=Counter()
    for n in ast.walk(t):
        c['N:'+type(n).__name__]+=1
        for f in getattr(n,'_fields',()):
            v=getattr(n,f)
            if isinstance(v,ast.AST): c[f'E:{type(n).__name__}:{f}:{type(v).__name__}']+=1
            elif isinstance(v,list):
                for x in v:
                    if isinstance(x,ast.AST): c[f'E:{type(n).__name__}:{f}:{type(x).__name__}']+=1
    return c

def delta(a,b):
    sa,sb=sig(a),sig(b); keys=set(sa)|set(sb)
    return Counter({k:sb[k]-sa[k] for k in keys if sb[k]!=sa[k]})

def cosine(a,b):
    keys=set(a)|set(b); dot=sum(a[k]*b[k] for k in keys); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb) if na and nb else 0.0

OP_REPL={ast.Lt:[ast.LtE,ast.Gt,ast.Eq],ast.LtE:[ast.Lt,ast.GtE,ast.Eq],ast.Gt:[ast.GtE,ast.Lt,ast.Eq],ast.GtE:[ast.Gt,ast.LtE,ast.Eq],ast.Eq:[ast.NotEq,ast.Lt,ast.LtE],ast.NotEq:[ast.Eq],ast.Add:[ast.Sub,ast.Mult],ast.Sub:[ast.Add,ast.Mult],ast.Mult:[ast.Add,ast.Sub],ast.And:[ast.Or],ast.Or:[ast.And]}
MUT=(ast.Name,ast.Constant,ast.cmpop,ast.operator,ast.boolop)

def candidates(src,cap=500):
    try:t=ast.parse(src)
    except:return []
    names=sorted({n.id for n in ast.walk(t) if isinstance(n,ast.Name)})
    nodes=[n for n in ast.walk(t) if isinstance(n,MUT)]
    out=[]
    for idx,node in enumerate(nodes):
        reps=[]
        if isinstance(node,ast.Name): reps=[ast.Name(id=x,ctx=copy.deepcopy(node.ctx)) for x in names if x!=node.id][:5]
        elif isinstance(node,ast.Constant) and isinstance(node.value,(int,float,bool)): reps=[ast.Constant(v) for v in (-1,0,1,2) if v!=node.value]
        else:
            for typ,alts in OP_REPL.items():
                if isinstance(node,typ): reps=[a() for a in alts]; break
        for rep in reps:
            k=-1
            class X(ast.NodeTransformer):
                def generic_visit(self,n):
                    nonlocal k
                    if isinstance(n,MUT):
                        k+=1
                        if k==idx:return copy.deepcopy(rep)
                    return super().generic_visit(n)
            try: out.append(ast.unparse(ast.fix_missing_locations(X().visit(copy.deepcopy(t)))))
            except: pass
            if len(out)>=cap:return out
    return out

def main():
    names=[p.stem for p in (ROOT/'python_programs').glob('*.py') if (ROOT/'python_testcases'/f'test_{p.stem}.py').exists() and not run_test(p.stem,p.read_text())]
    names=sorted(names,key=h); cut=max(10,len(names)//2); train,test=names[:cut],names[cut:]
    prototypes=[]
    for n in train:
        bug=(ROOT/'python_programs'/f'{n}.py').read_text(); cor=(ROOT/'correct_python_programs'/f'{n}.py').read_text(); prototypes.append(delta(bug,cor))
    rotated=prototypes[1:]+prototypes[:1]
    rows=[]; learned=[]; null=[]; unrestricted=[]
    for n in test:
        bug=(ROOT/'python_programs'/f'{n}.py').read_text(); cands=candidates(bug)
        scored=sorted(((max((cosine(delta(bug,c),p) for p in prototypes),default=0),c) for c in cands),key=lambda x:-x[0])
        scored_null=sorted(((max((cosine(delta(bug,c),p) for p in rotated),default=0),c) for c in cands),key=lambda x:-x[0])
        ls=ns=us=False
        for _,c in scored[:BUDGET]:
            if run_test(n,c): ls=True; break
        for _,c in scored_null[:BUDGET]:
            if run_test(n,c): ns=True; break
        for c in cands[:BUDGET]:
            if run_test(n,c): us=True; break
        if ls:learned.append(n)
        if ns:null.append(n)
        if us:unrestricted.append(n)
        rows.append({'task':n,'learned':ls,'null':ns,'unrestricted':us})
    new=sorted(set(learned)-set(null))
    gates={'preexisting_external_corpus':True,'heldout_correct_files_read':False,'nonempty_training_signatures':bool(prototypes),'learned_beats_null':len(learned)>len(null),'unique_learned_gain':bool(new)}
    res={'protocol':'V93_WHOLE_PROGRAM_SIGNATURE','external_commit':COMMIT,'train':train,'test':test,'learned_solved':learned,'null_solved':null,'unrestricted_solved':unrestricted,'unique_learned_gain':new,'rows':rows,'gates':gates,'verdict':'PASS_WHOLE_PROGRAM_SIGNATURE_V93' if all(gates.values()) else 'MIXED_WHOLE_PROGRAM_SIGNATURE_V93','qualification':'Supervised bridge. Whole-program AST graph-delta signatures are induced from training-side human fixes; held-out correct implementations remain sealed. No semantic operator/role labels are supplied. A PASS would show transfer of global change-shape priors, not autonomous ontology invention.'}
    (OUT/'RESULT.json').write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
if __name__=='__main__':main()
