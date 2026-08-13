import ast, hashlib, json, subprocess, tempfile, itertools
from pathlib import Path

OUT=Path('artifacts/external_scope_revision_v37'); OUT.mkdir(parents=True,exist_ok=True)
SEED='V37B_EXTERNAL_SCOPE_REVISION_20260814'
REPOS=[
 ('requests','https://github.com/psf/requests.git','8068356288978c4f54661ae6f95afe0e0831885e'),
 ('flask','https://github.com/pallets/flask.git','2a8a38b051fc248865730bf3511bf2e2ea325e81'),
 ('rich','https://github.com/Textualize/rich.git','9d8f9a372cc5916fd4781fec207ced7ddac2f08f'),
 ('click','https://github.com/pallets/click.git','9c4dfdaebe0e6b2aabc566eb81f6f10eb5cd6ea1'),
 ('httpx','https://github.com/encode/httpx.git','b5addb64f0161ff6bfe94c124ef76f6a1fba5254'),
]
SCOPES=['ANY','IF_TEST','RETURN','ASSERT','WHILE_TEST','OTHER']
DIRECTIONS=[('LTE_TO_LT','LtE','Lt'),('LT_TO_LTE','Lt','LtE')]

def dump(src): return ast.dump(ast.parse(src),include_attributes=False)

def classify(tree,node):
    parents={}
    for p in ast.walk(tree):
        for c in ast.iter_child_nodes(p): parents[id(c)]=p
    cur=node
    while id(cur) in parents:
        p=parents[id(cur)]
        if isinstance(p,ast.If) and cur in list(ast.walk(p.test)): return 'IF_TEST'
        if isinstance(p,ast.While) and cur in list(ast.walk(p.test)): return 'WHILE_TEST'
        if isinstance(p,ast.Assert) and cur in list(ast.walk(p.test)): return 'ASSERT'
        if isinstance(p,ast.Return): return 'RETURN'
        cur=p
    return 'OTHER'

def rows(src):
    t=ast.parse(src); out=[]
    for n in ast.walk(t):
        if isinstance(n,ast.Compare) and len(n.ops)==1 and isinstance(n.ops[0],(ast.Lt,ast.LtE)):
            out.append((n,classify(t,n),type(n.ops[0]).__name__))
    return out

def opclass(name): return ast.Lt if name=='Lt' else ast.LtE

def mutate_positive(src,truth_op,wrong_op):
    t=ast.parse(src); target=None
    for n,ctx,op in rows(src):
        if ctx=='IF_TEST' and op==truth_op:
            target=(getattr(n,'lineno',0),getattr(n,'col_offset',0)); break
    if target is None:return None
    A=opclass(truth_op);B=opclass(wrong_op)
    class T(ast.NodeTransformer):
        def visit_Compare(self,n):
            self.generic_visit(n)
            if (getattr(n,'lineno',0),getattr(n,'col_offset',0))==target and len(n.ops)==1 and isinstance(n.ops[0],A): n.ops[0]=B()
            return n
    T().visit(t);ast.fix_missing_locations(t);return ast.unparse(t)+'\n'

def apply_rule(src,scope,input_op,output_op):
    t=ast.parse(src);ctxmap={(getattr(n,'lineno',0),getattr(n,'col_offset',0)):ctx for n,ctx,op in rows(src)}
    A=opclass(input_op);B=opclass(output_op)
    class T(ast.NodeTransformer):
        def visit_Compare(self,n):
            self.generic_visit(n);ctx=ctxmap.get((getattr(n,'lineno',0),getattr(n,'col_offset',0)),'OTHER')
            if len(n.ops)==1 and isinstance(n.ops[0],A) and (scope=='ANY' or ctx==scope):n.ops[0]=B()
            return n
    T().visit(t);ast.fix_missing_locations(t);return ast.unparse(t)+'\n'

def meta(rn,commit,path,fn,src):
    sid=f'{rn}|{commit}|{path}|{fn}|{hashlib.sha256(src.encode()).hexdigest()}'
    return {'repo':rn,'commit':commit,'path':path,'function':fn,'rank':hashlib.sha256((SEED+'|'+sid).encode()).hexdigest(),'source':src}

pool=[]
for rn,url,commit in REPOS:
    root=Path(tempfile.mkdtemp())/rn;subprocess.run(['git','clone','-q',url,str(root)],check=True);subprocess.run(['git','checkout','-q',commit],cwd=root,check=True)
    for p in sorted(root.rglob('*.py')):
        try:
            if p.stat().st_size>250000:continue
            tr=ast.parse(p.read_text(encoding='utf-8'))
        except Exception:continue
        for fn in [n for n in ast.walk(tr) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]:
            try:src=ast.unparse(fn)+'\n'; rr=rows(src)
            except Exception:continue
            if rr:pool.append(meta(rn,commit,str(p.relative_to(root)),fn.name,src))
for x in pool:
    rr=rows(x['source'])
    for op in ('Lt','LtE'):
        x[f'if_{op}']=sum(ctx=='IF_TEST' and z==op for _,ctx,z in rr)
        x[f'nonif_{op}']=sum(ctx!='IF_TEST' and z==op for _,ctx,z in rr)
        x[f'total_{op}']=sum(z==op for _,ctx,z in rr)

def candidates(direction,rn,kind):
    _,input_op,truth_op=direction
    xs=[x for x in pool if x['repo']==rn]
    if kind=='pos': return [x for x in xs if x[f'if_{truth_op}']>0 and x[f'total_{input_op}']==0]
    if kind=='prot': return [x for x in xs if x[f'nonif_{input_op}']>0 and x[f'if_{input_op}']==0]
    if kind=='contra': return [x for x in xs if x[f'if_{input_op}']>0]
    raise ValueError(kind)

def pick(xs,n):return sorted(xs,key=lambda z:z['rank'])[:n]
# Frozen structural role selector: maximize the weakest split support; tie-break only by seed hash.
plans=[]
names=[r[0] for r in REPOS]
for d in DIRECTIONS:
    for a,b,c,e,f in itertools.permutations(names,5):
        counts=[len(candidates(d,a,'pos')),len(candidates(d,b,'prot')),len(candidates(d,c,'pos')),len(candidates(d,e,'prot')),len(candidates(d,f,'contra'))]
        strength=min(counts)
        tie=hashlib.sha256((SEED+'|'+d[0]+'|'+','.join((a,b,c,e,f))).encode()).hexdigest()
        plans.append((strength,sum(min(z,12) for z in counts),tie,d,(a,b,c,e,f),counts))
plan=max(plans,key=lambda z:(z[0],z[1],''.join(chr(255-ord(c)) for c in z[2])))
strength,total_support,_,direction,roles,role_counts=plan
label,input_op,truth_op=direction
train_pos=pick(candidates(direction,roles[0],'pos'),8);train_prot=pick(candidates(direction,roles[1],'prot'),8)
held_pos=pick(candidates(direction,roles[2],'pos'),12);held_prot=pick(candidates(direction,roles[3],'prot'),12);contradictions=pick(candidates(direction,roles[4],'contra'),8)

def positive_ok(x,scope=None):
    mut=mutate_positive(x['source'],truth_op,input_op)
    if mut is None:return False
    if scope is None:return dump(mut)==dump(x['source'])
    return dump(apply_rule(mut,scope,input_op,truth_op))==dump(x['source'])
def protected_ok(x,scope):return dump(apply_rule(x['source'],scope,input_op,truth_op))==dump(x['source'])
def score(scope,pos,prot):return sum(positive_ok(x,scope) for x in pos),sum(protected_ok(x,scope) for x in prot)

counts={'pool':len(pool),'train_pos':len(train_pos),'train_protected':len(train_prot),'held_pos':len(held_pos),'held_protected':len(held_prot),'contradictions':len(contradictions)}
old_fail=bool(train_pos) and all(not positive_ok(x,None) for x in train_pos);local_any=bool(train_pos) and all(positive_ok(x,'ANY') for x in train_pos);any_break=sum(not protected_ok(x,'ANY') for x in train_prot)
survivors=[];scores={}
for s in SCOPES:
    p,n=score(s,train_pos,train_prot);scores[s]={'positive':p,'protected':n}
    if p==len(train_pos) and n==len(train_prot) and train_pos and train_prot:survivors.append(s)
selected=survivors[0] if len(survivors)==1 else None
held_scoped=score(selected,held_pos,held_prot) if selected else (0,0);held_any=score('ANY',held_pos,held_prot)
contradiction_regressions=sum(not protected_ok(x,selected) for x in contradictions) if selected else 0
decision={'action':'REVOKE','scope':selected,'reason':'new independently authored source-of-truth cases contradict retained structural scope'} if selected and contradiction_regressions>0 else {'action':'KEEP','scope':selected}
pub=lambda xs:[{k:v for k,v in x.items() if k!='source'} for x in xs]
per_repo={rn:{d[0]:{'pos':len(candidates(d,rn,'pos')),'prot':len(candidates(d,rn,'prot')),'contra':len(candidates(d,rn,'contra'))} for d in DIRECTIONS} for rn in names}
R={'protocol':'V37b fixed-commit external source-grounded scope/revision; frozen structural direction/role selector','seed':SEED,'direction':label,'operator':f'REPAIR_{input_op}_TO_{truth_op}','scope_grammar':SCOPES,'repositories':[{'name':a,'commit':c} for a,_,c in REPOS],'roles':{'train_positive':roles[0],'train_protected':roles[1],'held_positive':roles[2],'held_protected':roles[3],'contradiction':roles[4]},'role_raw_counts':role_counts,'per_repo_structural_support':per_repo,'counts':counts,'source_selection':{'train_positive':pub(train_pos),'train_protected':pub(train_prot),'held_positive':pub(held_pos),'held_protected':pub(held_prot),'contradictions':pub(contradictions)},'scope_search':{'survivors':survivors,'selected':selected,'scores':scores},'heldout':{'scoped_positive':held_scoped[0],'scoped_protected':held_scoped[1],'fossil_positive':held_any[0],'fossil_protected':held_any[1]},'contradiction_regressions':contradiction_regressions,'revision_decision':decision}
R['gates']={'adequate_external_examples':min(counts.values())>=3,'old_state_fails_mutated_trigger_cases':old_fail,'provisional_unscoped_rule_repairs_all_triggers':local_any,'unscoped_rule_corrupts_external_valid_code':any_break>0,'unique_scope_discovered':selected=='IF_TEST','scope_transfers_to_source_distinct_heldout':held_scoped==(len(held_pos),len(held_prot)) and roles[2]!=roles[0] and roles[3]!=roles[1],'revision_ablation_fossilizes_bad_rule':held_any[0]==len(held_pos) and held_any[1]<len(held_prot),'new_external_counterevidence_falsifies_scope':contradiction_regressions>0,'system_revokes_falsified_scope':decision['action']=='REVOKE'}
R['verdict']='PASS_EXTERNAL_SCOPE_REVISION_V37B' if all(R['gates'].values()) else 'MIXED_EXTERNAL_SCOPE_REVISION_V37B'
R['interpretation_boundary']='Independently authored code is frozen at fixed commits. Correctness authority is exact AST restoration/preservation against repository source-of-truth, not package behavioral tests. This tests external source-grounded scope/revision, not deployment-semantic correctness.'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))
