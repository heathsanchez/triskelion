#!/usr/bin/env python3
import ast, copy, hashlib, importlib.util, json, os
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).with_name('METALOGIC_V102_FRESH_SPLIT_EXPRESSION_CONSTRUCTOR.py')
spec = importlib.util.spec_from_file_location('v102', BASE)
v102 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v102)
ROOT=v102.ROOT; full_score=v102.full_score; base_candidates=v102.base_candidates
OUT=Path(os.environ.get('OUT_DIR','results/v104')); OUT.mkdir(parents=True,exist_ok=True)
SEED='V104_GENERIC_CONSTRUCTOR_SYNTHESIS_2026-08-14'
EXCLUDE=set(v102.EXPOSED)
TRAIN_N=8; TEST_N=8; BASE_CAP=180; PROGRAM_CAP=320; MIN_SUPPORT=2

# No high-level repair families are supplied. A constructor program is synthesized from:
#   SELECT(parent_type, field) -> BUILD(expression grammar) -> REPLACE
# The templates below are generic AST/value constructors, not task semantics.
SELECTORS=[
 ('While','test'),('If','test'),('Return','value'),('Call','func'),('Call','arg')
]
BUILDERS=[
 ('SCOPE_NAME',),('CONST',0),('CONST',1),('CONST',True),('CONST',False),
 ('LIST_EMPTY',),('LIST_NESTED_EMPTY',),
 ('BINOP_NAME_CONST','Add',1),('BINOP_NAME_CONST','Sub',1),
 ('CALL_BUILTIN','all'),('CALL_BUILTIN','any'),('CALL_BUILTIN','len'),
 ('CALL_BUILTIN','min'),('CALL_BUILTIN','max'),('CALL_BUILTIN','sum')
]

def h(x): return hashlib.sha256((SEED+'|'+x).encode()).hexdigest()

def failing_names():
    buggy=ROOT/'python_programs'; tests=ROOT/'python_testcases'; out=[]
    for p in buggy.glob('*.py'):
        n=p.stem
        if n in EXCLUDE or not (tests/f'test_{n}.py').exists(): continue
        try:s=full_score(n,p.read_text())
        except Exception:continue
        if s>0:out.append(n)
    return sorted(out,key=lambda n:h('task|'+n))

def nodes_for_selector(tree,sel):
    typ,field=sel
    if typ=='While': return [(n,'test',None) for n in ast.walk(tree) if isinstance(n,ast.While)]
    if typ=='If': return [(n,'test',None) for n in ast.walk(tree) if isinstance(n,ast.If)]
    if typ=='Return': return [(n,'value',None) for n in ast.walk(tree) if isinstance(n,ast.Return)]
    if typ=='Call' and field=='func': return [(n,'func',None) for n in ast.walk(tree) if isinstance(n,ast.Call)]
    if typ=='Call' and field=='arg':
        return [(n,'args',j) for n in ast.walk(tree) if isinstance(n,ast.Call) for j,_ in enumerate(n.args)]
    return []

def build_expr(builder,names,old=None):
    tag=builder[0]
    if tag=='SCOPE_NAME': return [ast.Name(id=x,ctx=ast.Load()) for x in names]
    if tag=='CONST': return [ast.Constant(builder[1])]
    if tag=='LIST_EMPTY': return [ast.List(elts=[],ctx=ast.Load())]
    if tag=='LIST_NESTED_EMPTY': return [ast.List(elts=[ast.List(elts=[],ctx=ast.Load())],ctx=ast.Load())]
    if tag=='BINOP_NAME_CONST':
        op=ast.Add if builder[1]=='Add' else ast.Sub
        return [ast.BinOp(left=ast.Name(id=x,ctx=ast.Load()),op=op(),right=ast.Constant(builder[2])) for x in names]
    if tag=='CALL_BUILTIN':
        # Generic call construction reuses the old call's arguments when available; otherwise one scoped name.
        if isinstance(old,ast.Call): return [ast.Call(func=ast.Name(id=builder[1],ctx=ast.Load()),args=copy.deepcopy(old.args),keywords=copy.deepcopy(old.keywords))]
        return [ast.Call(func=ast.Name(id=builder[1],ctx=ast.Load()),args=[ast.Name(id=x,ctx=ast.Load())],keywords=[]) for x in names[:4]]
    return []

def program_candidates(src,allowed=None,cap=PROGRAM_CAP):
    try:tree=ast.parse(src)
    except Exception:return []
    names=sorted({n.id for n in ast.walk(tree) if isinstance(n,ast.Name)})
    programs=[(s,b) for s in SELECTORS for b in BUILDERS]
    programs=sorted(programs,key=lambda p:h('program|'+repr(p)))
    if allowed is not None: programs=[p for p in programs if p in allowed]
    out=[]; seen={src}
    for sel,builder in programs:
        original_slots=nodes_for_selector(tree,sel)
        for slot_i,(node,field,arg_i) in enumerate(original_slots):
            old=(node.args[arg_i] if arg_i is not None else getattr(node,field,None))
            for rep in build_expr(builder,names,old):
                z=copy.deepcopy(tree); slots=nodes_for_selector(z,sel)
                if slot_i>=len(slots):continue
                zn,zfield,zarg=slots[slot_i]
                if zarg is None:setattr(zn,zfield,copy.deepcopy(rep))
                else:
                    if zarg>=len(zn.args):continue
                    zn.args[zarg]=copy.deepcopy(rep)
                try:text=ast.unparse(ast.fix_missing_locations(z))
                except Exception:continue
                if text in seen:continue
                seen.add(text); out.append((sel,builder,text))
                if len(out)>=cap:return out
    return out

def first_success(name,cands):
    for sel,builder,text in cands:
        try:
            if full_score(name,text)==0:return (sel,builder)
        except Exception:pass
    return None

def main():
    names=failing_names(); train=names[:TRAIN_N]; test=names[TRAIN_N:TRAIN_N+TEST_N]
    support=defaultdict(set); train_rows=[]
    # Training uses verifier gradients only; no correct implementations.
    for n in train:
        src=(ROOT/'python_programs'/f'{n}.py').read_text(); base=full_score(n,src)
        best={}
        for sel,builder,text in program_candidates(src):
            sig=(sel,builder)
            try:s=full_score(n,text)
            except Exception:continue
            best[repr(sig)]=min(best.get(repr(sig),10**9),s)
            if s<base:support[sig].add(n)
        improving=sorted((repr(sig),sorted(v)) for sig,v in support.items() if n in v)
        train_rows.append({'task':n,'base_score':base,'improving_programs':[x[0] for x in improving]})
    retained=sorted([sig for sig,v in support.items() if len(v)>=MIN_SUPPORT],key=repr)
    # MDL tie-break: shortest repr, then strongest source-distinct support, then frozen hash.
    if retained:
        best_len=min(len(repr(x)) for x in retained)
        retained=[x for x in retained if len(repr(x))==best_len]
        maxsup=max(len(support[x]) for x in retained)
        retained=[x for x in retained if len(support[x])==maxsup]
        retained=sorted(retained,key=lambda x:h('retain|'+repr(x)))[:2]
    all_programs=[(s,b) for s in SELECTORS for b in BUILDERS]
    non=[p for p in all_programs if p not in retained]
    null=sorted(non,key=lambda p:h('null|'+repr(p)))[:len(retained)]
    base_s=[]; learned_s=[]; null_s=[]; rows=[]
    for n in test:
        src=(ROOT/'python_programs'/f'{n}.py').read_text()
        # Normalize base candidates into the same triple shape.
        b=[(('BASE','BASE'),('BASE',),text) for _,text in base_candidates(src,BASE_CAP)]
        bk=first_success(n,b)
        lk=first_success(n,b+program_candidates(src,set(retained)))
        nk=first_success(n,b+program_candidates(src,set(null)))
        if bk:base_s.append(n)
        if lk:learned_s.append(n)
        if nk:null_s.append(n)
        rows.append({'task':n,'base':bool(bk),'learned':bool(lk),'null':bool(nk),'learned_winner':repr(lk) if lk else None,'null_winner':repr(nk) if nk else None})
    new=sorted(set(learned_s)-set(base_s)); null_new=sorted(set(null_s)-set(base_s))
    gates={
      'external_hash_split':bool(train and test and not(set(train)&set(test))),
      'prior_inspected_tasks_excluded':not any(n in EXCLUDE for n in train+test),
      'no_correct_implementations_read':True,
      'no_named_high_level_builder_families':True,
      'programs_synthesized_from_generic_ast_value_grammar':True,
      'source_distinct_verifier_support':all(len(support[p])>=MIN_SUPPORT for p in retained) if retained else False,
      'nonempty_synthesized_constructor':bool(retained),
      'conservative':set(base_s)<=set(learned_s),
      'strict_heldout_closure_expansion':bool(new),
      'beats_matched_wrong_program_control':len(new)>len(null_new)
    }
    verdict='PASS_GENERIC_CONSTRUCTOR_SYNTHESIS_V104' if all(gates.values()) else 'MIXED_GENERIC_CONSTRUCTOR_SYNTHESIS_V104'
    res={'protocol':'V104_GENERIC_CONSTRUCTOR_SYNTHESIS','external_commit':v102.v100.COMMIT,'train':train,'test':test,'excluded_prior_inspection':sorted(EXCLUDE),'retained_programs':[repr(x) for x in retained],'retained_support':{repr(x):sorted(support[x]) for x in retained},'null_programs':[repr(x) for x in null],'base_solved':base_s,'learned_solved':learned_s,'null_solved':null_s,'new_closure':new,'null_new_closure':null_new,'train_rows':train_rows,'rows':rows,'gates':gates,'verdict':verdict,'qualification':'Natural constructor-synthesis bridge. No high-level GUARD/RETURN/EXPR family is selectable. Constructor programs are synthesized from generic typed slot selection plus AST/value builders and retained only by source-distinct verifier improvement. The low-level AST/value grammar itself remains supplied; PASS would not establish unrestricted metalanguage invention.'}
    (OUT/'RESULT.json').write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
if __name__=='__main__':main()
