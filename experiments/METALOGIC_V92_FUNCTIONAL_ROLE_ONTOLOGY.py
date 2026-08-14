#!/usr/bin/env python3
import ast, copy, hashlib, json, os, re, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT=Path(os.environ.get('QUIXBUGS_DIR','/tmp/QuixBugs'))
OUT=Path(os.environ.get('OUT_DIR','results/v92')); OUT.mkdir(parents=True,exist_ok=True)
SEED='V92_FUNCTIONAL_ROLE_ONTOLOGY_2026-08-14'
COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
BUDGET_TRAIN=110
BUDGET_TEST=150
SUPPORT_MIN=2

def h(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()

def run_test(name,text):
    p=ROOT/'python_programs'/f'{name}.py'; old=p.read_text()
    try:
        p.write_text(text)
        r=subprocess.run([sys.executable,'-m','pytest','-q',f'python_testcases/test_{name}.py','--timeout=4'],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=22)
        out=r.stdout or ''
        if r.returncode==0: return 0
        m=re.search(r'(\d+) failed',out)
        if m:return int(m.group(1))
        m=re.search(r'(\d+) error',out)
        if m:return 100+int(m.group(1))
        return 99
    except Exception:return 999
    finally:p.write_text(old)

def names_in(tree): return sorted({n.id for n in ast.walk(tree) if isinstance(n,ast.Name)})
def func_names(tree): return {n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
def call_name(c):
    if isinstance(c.func,ast.Name): return c.func.id
    if isinstance(c.func,ast.Attribute): return c.func.attr
    return ''

def role_for(node,parent,field,ancestors,fns):
    chain=ancestors+[parent] if parent else ancestors
    for a in reversed(chain):
        if isinstance(a,(ast.If,ast.While,ast.IfExp,ast.Assert)) and getattr(a,'test',None) is not None and node in list(ast.walk(a.test)):return 'CONTROL_GUARD'
        if isinstance(a,ast.For) and node in list(ast.walk(a.iter)):return 'ITERATION_SOURCE'
        if isinstance(a,ast.comprehension) and node in list(ast.walk(a.iter)):return 'ITERATION_SOURCE'
        if isinstance(a,ast.Call) and node in list(ast.walk(a)):
            cn=call_name(a)
            if cn in fns:return 'RECURSIVE_ARGUMENT'
            if cn in {'enumerate','range','zip','map','filter','sorted','reversed'}:return 'ITERATION_SOURCE'
            if cn in {'add','append','extend','update','push','enqueue'}:return 'STATE_UPDATE'
            return 'CALL_ARGUMENT'
        if isinstance(a,ast.Return) and a.value is not None and node in list(ast.walk(a.value)):return 'RETURN_FLOW'
        if isinstance(a,ast.Subscript) and node in list(ast.walk(a.slice)):return 'INDEX_KEY'
        if isinstance(a,(ast.Assign,ast.AnnAssign,ast.NamedExpr)) and getattr(a,'value',None) is not None and node in list(ast.walk(a.value)):return 'ASSIGN_SOURCE'
        if isinstance(a,ast.AugAssign):return 'ACCUMULATE'
        if isinstance(a,ast.Compare):return 'COMPARISON_BOUNDARY'
        if isinstance(a,(ast.BinOp,ast.UnaryOp,ast.BoolOp)):return 'VALUE_TRANSFORM'
    return 'OTHER_VALUE'

OP_REPL={
 ast.Lt:[ast.LtE,ast.Gt,ast.Eq], ast.LtE:[ast.Lt,ast.GtE,ast.Eq],
 ast.Gt:[ast.GtE,ast.Lt,ast.Eq], ast.GtE:[ast.Gt,ast.LtE,ast.Eq],
 ast.Eq:[ast.NotEq,ast.Lt,ast.LtE], ast.NotEq:[ast.Eq],
 ast.Add:[ast.Sub,ast.Mult,ast.FloorDiv], ast.Sub:[ast.Add,ast.Mult],
 ast.Mult:[ast.Add,ast.Sub,ast.FloorDiv], ast.FloorDiv:[ast.Div,ast.Mult], ast.Mod:[ast.FloorDiv,ast.Mult],
 ast.And:[ast.Or], ast.Or:[ast.And], ast.Not:[ast.USub], ast.USub:[ast.Not]
}
MUT_TYPES=(ast.Name,ast.Constant,ast.cmpop,ast.operator,ast.boolop,ast.unaryop)

def collect_sites(tree):
    fns=func_names(tree); nms=names_in(tree); sites=[]
    def rec(node,parent=None,field='root',anc=None):
        anc=[] if anc is None else anc
        if isinstance(node,MUT_TYPES): sites.append((node,parent,field,list(anc),role_for(node,parent,field,anc,fns)))
        if isinstance(node,ast.AST):
            for f in getattr(node,'_fields',()):
                v=getattr(node,f)
                if isinstance(v,ast.AST):rec(v,node,f,anc+[node])
                elif isinstance(v,list):
                    for x in v:
                        if isinstance(x,ast.AST):rec(x,node,f,anc+[node])
    rec(tree)
    return sites,nms

def replace_nth(tree,target_idx,new_node):
    k=-1
    class X(ast.NodeTransformer):
        def generic_visit(self,node):
            nonlocal k
            if isinstance(node,MUT_TYPES):
                k+=1
                if k==target_idx:return copy.deepcopy(new_node)
            return super().generic_visit(node)
    z=X().visit(copy.deepcopy(tree)); return ast.fix_missing_locations(z)

def candidates(src,allowed_roles=None,cap=200):
    try:tree=ast.parse(src)
    except:return []
    sites,nms=collect_sites(tree); out=[]
    for idx,(node,parent,field,anc,role) in enumerate(sites):
        if allowed_roles is not None and role not in allowed_roles:continue
        reps=[]
        if isinstance(node,ast.Name):
            reps=[ast.Name(id=x,ctx=copy.deepcopy(node.ctx)) for x in nms if x!=node.id][:6]
        elif isinstance(node,ast.Constant) and isinstance(node.value,(int,float,bool)):
            reps=[ast.Constant(v) for v in (-1,0,1,2) if v!=node.value]
        else:
            for typ,alts in OP_REPL.items():
                if isinstance(node,typ):reps=[a() for a in alts]; break
        for rep in reps:
            try:
                z=replace_nth(tree,idx,rep); out.append((role,ast.unparse(z)))
            except Exception:pass
            if len(out)>=cap:return out
    return out

def probe_roles(name,cap):
    src=(ROOT/'python_programs'/f'{name}.py').read_text(); base=run_test(name,src); best_by={}; tested=0
    for role,text in candidates(src,None,cap*2):
        if tested>=cap:break
        f=run_test(name,text); tested+=1
        if f<base and (role not in best_by or f<best_by[role]):best_by[role]=f
    return base,best_by,tested

def solve(name,roles,cap):
    src=(ROOT/'python_programs'/f'{name}.py').read_text(); base=run_test(name,src); tested=0
    if base==0:return True,None,0
    for role,text in candidates(src,roles,cap*2):
        if tested>=cap:break
        tested+=1
        if run_test(name,text)==0:return True,role,tested
    return False,None,tested

def main():
    names=[p.stem for p in (ROOT/'python_programs').glob('*.py') if (ROOT/'python_testcases'/f'test_{p.stem}.py').exists() and run_test(p.stem,p.read_text())>0]
    names=sorted(names,key=h); train=names[:12]; test=names[12:]
    support=Counter(); probe=[]
    for n in train:
        base,best,tested=probe_roles(n,BUDGET_TRAIN)
        for r in best:support[r]+=1
        probe.append({'task':n,'base_fail':base,'improved_roles':best,'tested':tested})
    learned=[r for r,c in support.most_common() if c>=SUPPORT_MIN]
    all_roles=['CONTROL_GUARD','ITERATION_SOURCE','RECURSIVE_ARGUMENT','STATE_UPDATE','CALL_ARGUMENT','RETURN_FLOW','INDEX_KEY','ASSIGN_SOURCE','ACCUMULATE','COMPARISON_BOUNDARY','VALUE_TRANSFORM','OTHER_VALUE']
    null_pool=[r for r in sorted(all_roles,key=lambda x:h('null|'+x)) if r not in learned]
    shuffled=null_pool[:len(learned)]
    k0=['COMPARISON_BOUNDARY']
    rows=[]; a=[];b=[];q=[];u=[]
    for n in test:
        x,_,_=solve(n,k0,BUDGET_TEST)
        y,ry,_=solve(n,list(dict.fromkeys(k0+learned)),BUDGET_TEST)
        z,rz,_=solve(n,list(dict.fromkeys(k0+shuffled)),BUDGET_TEST)
        w,rw,_=solve(n,all_roles,BUDGET_TEST)
        if x:a.append(n)
        if y:b.append(n)
        if z:q.append(n)
        if w:u.append(n)
        rows.append({'task':n,'k0':x,'learned':y,'null':z,'unrestricted':w,'learned_role':ry,'null_role':rz,'unrestricted_role':rw})
    new=sorted(set(b)-set(a)); nullnew=sorted(set(q)-set(a)); ceilingnew=sorted(set(u)-set(a))
    gates={'preexisting_external_corpus':True,'correct_implementations_never_read':True,'nonempty_verifier_induced_functional_roles':bool(learned),'conservative_growth':set(a).issubset(set(b)),'heldout_closure_strictly_expands':bool(new),'learned_roles_beat_matched_null':len(new)>len(nullnew)}
    verdict='PASS_VERIFIER_INDUCED_FUNCTIONAL_ONTOLOGY_V92' if all(gates.values()) else 'MIXED_VERIFIER_INDUCED_FUNCTIONAL_ONTOLOGY_V92'
    res={'protocol':'V92_VERIFIER_INDUCED_FUNCTIONAL_ONTOLOGY','external_commit':COMMIT,'seed':SEED,'train':train,'test':test,'role_support':dict(support),'learned_roles':learned,'matched_null_roles':shuffled,'probe_rows':probe,'k0_solved':a,'learned_solved':b,'null_solved':q,'unrestricted_solved':u,'new_closure':new,'null_new_closure':nullnew,'unrestricted_new_closure':ceilingnew,'rows':rows,'gates':gates,'verdict':verdict,'qualification':'Natural bridge. Functional roles are induced solely from verifier-improving generic mutations on the training split; held-out correct implementations are never read. Roles are coarse dataflow/control categories, still supplied as a generic observational vocabulary. A PASS would show transfer of verifier-induced functional role selection, not autonomous invention of the role vocabulary.'}
    (OUT/'RESULT.json').write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
if __name__=='__main__':main()
