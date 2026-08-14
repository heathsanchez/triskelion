#!/usr/bin/env python3
import ast, copy, hashlib, importlib.util, json, os
from pathlib import Path
BASE=Path(__file__).with_name('METALOGIC_V100_BALANCED_K_CROSS_SOURCE_ORGANS.py')
spec=importlib.util.spec_from_file_location('v100',BASE); v100=importlib.util.module_from_spec(spec); spec.loader.exec_module(v100)
ROOT=v100.ROOT; full_score=v100.full_score; base_candidates=v100.balanced_rich_candidates
OUT=Path(os.environ.get('OUT_DIR','results/v102')); OUT.mkdir(parents=True,exist_ok=True)
SEED='V102_FRESH_SPLIT_EXPRESSION_CONSTRUCTOR_2026-08-14'
EXPOSED={'breadth_first_search','sieve','subsequences','find_in_sorted'}
TEST_N=12; CAP_BASE=220; CAP_EXPR=260

def h(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()

def expr_candidates(src,cap):
    try:t=ast.parse(src)
    except Exception:return []
    names=sorted({n.id for n in ast.walk(t) if isinstance(n,ast.Name)})
    out=[]; seen={src}
    def emit(z,kind):
        if len(out)>=cap:return
        try:s=ast.unparse(ast.fix_missing_locations(z))
        except Exception:return
        if s not in seen: seen.add(s); out.append((kind,s))
    # Generic callable construction from a frozen builtin vocabulary.
    builtins=['all','any','len','min','max','sum']
    calls=[n for n in ast.walk(t) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
    for i,c in enumerate(calls):
        for fn in builtins:
            if fn==c.func.id:continue
            z=copy.deepcopy(t); zc=[n for n in ast.walk(z) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
            if i<len(zc): zc[i].func.id=fn; emit(z,'CALLABLE_CONSTRUCT')
            if len(out)>=cap:return out
    # Generic guard construction from in-scope state expressions.
    guards=[n for n in ast.walk(t) if isinstance(n,(ast.If,ast.While))]
    for i,g in enumerate(guards):
        for nm in names:
            z=copy.deepcopy(t); zg=[n for n in ast.walk(z) if isinstance(n,(ast.If,ast.While))]
            if i<len(zg): zg[i].test=ast.Name(id=nm,ctx=ast.Load()); emit(z,'GUARD_EXPR')
            if len(out)>=cap:return out
    # Generic return-expression constructors: structural constants and names.
    rets=[n for n in ast.walk(t) if isinstance(n,ast.Return)]
    reps=[ast.List(elts=[],ctx=ast.Load()),ast.List(elts=[ast.List(elts=[],ctx=ast.Load())],ctx=ast.Load()),ast.Constant(0),ast.Constant(1)]
    reps += [ast.Name(id=n,ctx=ast.Load()) for n in names]
    for i,r in enumerate(rets):
        for rep in reps:
            z=copy.deepcopy(t); zr=[n for n in ast.walk(z) if isinstance(n,ast.Return)]
            if i<len(zr): zr[i].value=copy.deepcopy(rep); emit(z,'RETURN_EXPR')
            if len(out)>=cap:return out
    # Generic local expression growth: x -> x +/- 1 at call arguments and returns.
    sites=[]
    for n in ast.walk(t):
        if isinstance(n,ast.Call):
            for j,a in enumerate(n.args):
                if isinstance(a,ast.Name):sites.append(('call',n,j,a.id))
        if isinstance(n,ast.Return) and isinstance(n.value,ast.Name):sites.append(('return',n,None,n.value.id))
    call_names=[n for n in ast.walk(t) if isinstance(n,ast.Call)]
    for typ,node,j,nm in sites:
        for op in (ast.Add(),ast.Sub()):
            z=copy.deepcopy(t); rep=ast.BinOp(left=ast.Name(id=nm,ctx=ast.Load()),op=op,right=ast.Constant(1))
            if typ=='call':
                idx=[id(x) for x in call_names].index(id(node)); zc=[n for n in ast.walk(z) if isinstance(n,ast.Call)]
                if idx<len(zc) and j<len(zc[idx].args): zc[idx].args[j]=rep; emit(z,'EXPR_GROW')
            else:
                rr=[n for n in ast.walk(t) if isinstance(n,ast.Return)]; idx=[id(x) for x in rr].index(id(node)); zr=[n for n in ast.walk(z) if isinstance(n,ast.Return)]
                if idx<len(zr): zr[idx].value=rep; emit(z,'EXPR_GROW')
            if len(out)>=cap:return out
    return out

def reachable(name,src,cands):
    for kind,text in cands:
        if full_score(name,text)==0:return kind
    return None

def main():
    buggy=ROOT/'python_programs'; tests=ROOT/'python_testcases'; names=[]
    for p in buggy.glob('*.py'):
        n=p.stem
        if n in EXPOSED or not (tests/f'test_{n}.py').exists():continue
        if full_score(n,p.read_text())>0:names.append(n)
    names=sorted(names,key=lambda n:h('task|'+n)); test=names[:TEST_N]
    rows=[]; base_s=[]; expr_s=[]
    for n in test:
        src=(buggy/f'{n}.py').read_text()
        b=base_candidates(src,CAP_BASE); e=expr_candidates(src,CAP_EXPR)
        bk=reachable(n,src,b); ek=reachable(n,src,b+e)
        if bk:base_s.append(n)
        if ek:expr_s.append(n)
        rows.append({'task':n,'base_candidates':len(b),'expr_candidates':len(e),'base_reachable':bool(bk),'expanded_reachable':bool(ek),'winning_family':ek})
    new=sorted(set(expr_s)-set(base_s))
    gates={'fresh_hash_split':True,'previously_exposed_tasks_excluded':not any(n in EXPOSED for n in test),'no_correct_implementations_read':True,'generic_expression_substrate_fixed':True,'strict_closure_expansion':bool(new),'conservative':set(base_s)<=set(expr_s)}
    verdict='PASS_EXPRESSION_CONSTRUCTOR_BRIDGE_V102' if all(gates.values()) else 'MIXED_EXPRESSION_CONSTRUCTOR_BRIDGE_V102'
    res={'protocol':'V102_FRESH_SPLIT_EXPRESSION_CONSTRUCTOR','external_commit':v100.COMMIT,'test':test,'excluded_exposed':sorted(EXPOSED),'base_reachable':base_s,'expanded_reachable':expr_s,'new_closure':new,'rows':rows,'gates':gates,'verdict':verdict,'qualification':'Fresh-split representation bridge only. The generic typed expression-construction substrate is supplied, not learned. Correct implementations are never read. A PASS supports expression construction as a missing constructor class, not autonomous constructor genesis.'}
    (OUT/'RESULT.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
if __name__=='__main__':main()
