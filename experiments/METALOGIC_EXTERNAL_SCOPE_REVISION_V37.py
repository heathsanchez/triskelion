import ast, hashlib, json, subprocess, tempfile
from pathlib import Path

OUT=Path('artifacts/external_scope_revision_v37'); OUT.mkdir(parents=True,exist_ok=True)
SEED='V37_EXTERNAL_SCOPE_REVISION_20260814'
REPOS=[
 ('requests','https://github.com/psf/requests.git','8068356288978c4f54661ae6f95afe0e0831885e'),
 ('flask','https://github.com/pallets/flask.git','2a8a38b051fc248865730bf3511bf2e2ea325e81'),
 ('rich','https://github.com/Textualize/rich.git','9d8f9a372cc5916fd4781fec207ced7ddac2f08f'),
]
SCOPES=['ANY','IF_TEST','RETURN','ASSERT','WHILE_TEST','OTHER']

def dump(src):
    return ast.dump(ast.parse(src),include_attributes=False)

def classify(tree,node):
    parents={}
    for p in ast.walk(tree):
        for c in ast.iter_child_nodes(p): parents[id(c)]=p
    cur=node
    while id(cur) in parents:
        p=parents[id(cur)]
        if isinstance(p,ast.If) and any(cur is x or cur in list(ast.walk(x)) for x in [p.test]): return 'IF_TEST'
        if isinstance(p,ast.While) and any(cur is x or cur in list(ast.walk(x)) for x in [p.test]): return 'WHILE_TEST'
        if isinstance(p,ast.Assert) and any(cur is x or cur in list(ast.walk(x)) for x in [p.test]): return 'ASSERT'
        if isinstance(p,ast.Return): return 'RETURN'
        cur=p
    return 'OTHER'

def compare_rows(src):
    t=ast.parse(src); out=[]
    for n in ast.walk(t):
        if isinstance(n,ast.Compare) and len(n.ops)==1 and isinstance(n.ops[0],(ast.Lt,ast.LtE)):
            out.append((n,classify(t,n),type(n.ops[0]).__name__))
    return out

def mutate_positive(src):
    t=ast.parse(src); target=None
    for n,ctx,op in compare_rows(src):
        if ctx=='IF_TEST' and op=='Lt': target=(getattr(n,'lineno',0),getattr(n,'col_offset',0)); break
    if target is None: return None
    class T(ast.NodeTransformer):
        def visit_Compare(self,n):
            self.generic_visit(n)
            if (getattr(n,'lineno',0),getattr(n,'col_offset',0))==target and len(n.ops)==1 and isinstance(n.ops[0],ast.Lt): n.ops[0]=ast.LtE()
            return n
    T().visit(t); ast.fix_missing_locations(t); return ast.unparse(t)+'\n'

def apply_rule(src,scope):
    t=ast.parse(src); ctxmap={(getattr(n,'lineno',0),getattr(n,'col_offset',0)):ctx for n,ctx,op in compare_rows(src)}
    class T(ast.NodeTransformer):
        def visit_Compare(self,n):
            self.generic_visit(n)
            ctx=ctxmap.get((getattr(n,'lineno',0),getattr(n,'col_offset',0)),'OTHER')
            if len(n.ops)==1 and isinstance(n.ops[0],ast.LtE) and (scope=='ANY' or ctx==scope): n.ops[0]=ast.Lt()
            return n
    T().visit(t); ast.fix_missing_locations(t); return ast.unparse(t)+'\n'

def meta(rn,commit,path,fn,src):
    sid=f'{rn}|{commit}|{path}|{fn}|{hashlib.sha256(src.encode()).hexdigest()}'
    return {'repo':rn,'commit':commit,'path':path,'function':fn,'rank':hashlib.sha256((SEED+'|'+sid).encode()).hexdigest(),'source':src}

pool=[]
for rn,url,commit in REPOS:
    root=Path(tempfile.mkdtemp())/rn
    subprocess.run(['git','clone','-q',url,str(root)],check=True)
    subprocess.run(['git','checkout','-q',commit],cwd=root,check=True)
    for p in sorted(root.rglob('*.py')):
        try:
            if p.stat().st_size>250000: continue
            tr=ast.parse(p.read_text(encoding='utf-8'))
        except Exception: continue
        for fn in [n for n in ast.walk(tr) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]:
            try: src=ast.unparse(fn)+'\n'; rows=compare_rows(src)
            except Exception: continue
            if rows: pool.append(meta(rn,commit,str(p.relative_to(root)),fn.name,src))

for x in pool:
    rows=compare_rows(x['source'])
    x['if_lt']=sum(ctx=='IF_TEST' and op=='Lt' for _,ctx,op in rows)
    x['if_lte']=sum(ctx=='IF_TEST' and op=='LtE' for _,ctx,op in rows)
    x['nonif_lte']=sum(ctx!='IF_TEST' and op=='LtE' for _,ctx,op in rows)
    x['lte_total']=sum(op=='LtE' for _,ctx,op in rows)

def pick(xs,n): return sorted(xs,key=lambda z:z['rank'])[:n]
# Calibration uses source-distinct repositories. Positive cases are mutations of correct Requests IF-test '<' functions with no pre-existing <=.
train_pos=pick([x for x in pool if x['repo']=='requests' and x['if_lt']>0 and x['lte_total']==0],8)
# Protected Flask functions contain genuine <= outside IF_TEST and no <= inside IF_TEST, so broad rewriting is harmful but IF_TEST scope preserves them.
train_protected=pick([x for x in pool if x['repo']=='flask' and x['nonif_lte']>0 and x['if_lte']==0],8)
# Held-out transfer is entirely Rich: unseen positives plus unseen protected behaviours.
held_pos=pick([x for x in pool if x['repo']=='rich' and x['if_lt']>0 and x['lte_total']==0],12)
held_protected=pick([x for x in pool if x['repo']=='rich' and x['nonif_lte']>0 and x['if_lte']==0],12)
# Contradictory external evidence: genuine <= inside IF_TEST means the learned scoped rule would corrupt correct code.
contradictions=pick([x for x in pool if x['repo']!='requests' and x['if_lte']>0],8)

def positive_ok(x,scope=None):
    mut=mutate_positive(x['source'])
    if mut is None: return False
    if scope is None: return dump(mut)==dump(x['source'])
    return dump(apply_rule(mut,scope))==dump(x['source'])

def protected_ok(x,scope): return dump(apply_rule(x['source'],scope))==dump(x['source'])

def score(scope,pos,prot): return sum(positive_ok(x,scope) for x in pos),sum(protected_ok(x,scope) for x in prot)

counts={'pool':len(pool),'train_pos':len(train_pos),'train_protected':len(train_protected),'held_pos':len(held_pos),'held_protected':len(held_protected),'contradictions':len(contradictions)}
old_fail=bool(train_pos) and all(not positive_ok(x,None) for x in train_pos)
local_any=bool(train_pos) and all(positive_ok(x,'ANY') for x in train_pos)
any_break=sum(not protected_ok(x,'ANY') for x in train_protected)
survivors=[]; scores={}
for s in SCOPES:
    p,n=score(s,train_pos,train_protected); scores[s]={'positive':p,'protected':n}
    if p==len(train_pos) and n==len(train_protected) and train_pos and train_protected: survivors.append(s)
selected=survivors[0] if len(survivors)==1 else None
held_scoped=score(selected,held_pos,held_protected) if selected else (0,0)
held_any=score('ANY',held_pos,held_protected)
contradiction_regressions=sum(not protected_ok(x,selected) for x in contradictions) if selected else 0
# Revision policy: keep only if all current protected evidence survives. Contradiction inside the selected scope revokes because current grammar has no narrower semantic predicate.
decision={'action':'REVOKE','scope':selected,'reason':'new external source-of-truth cases contradict retained structural scope'} if selected and contradiction_regressions>0 else {'action':'KEEP','scope':selected}

pub=lambda xs:[{k:v for k,v in x.items() if k!='source'} for x in xs]
R={'protocol':'V37 fixed-commit external source-grounded scope/revision ratchet','seed':SEED,'operator':'REPAIR_LTE_TO_LT','scope_grammar':SCOPES,'repositories':[{'name':a,'commit':c} for a,_,c in REPOS],'counts':counts,'source_selection':{'train_positive':pub(train_pos),'train_protected':pub(train_protected),'held_positive':pub(held_pos),'held_protected':pub(held_protected),'contradictions':pub(contradictions)},'scope_search':{'survivors':survivors,'selected':selected,'scores':scores},'heldout':{'scoped_positive':held_scoped[0],'scoped_protected':held_scoped[1],'fossil_positive':held_any[0],'fossil_protected':held_any[1]},'contradiction_regressions':contradiction_regressions,'revision_decision':decision}
R['gates']={
 'adequate_external_examples':min(counts['train_pos'],counts['train_protected'],counts['held_pos'],counts['held_protected'],counts['contradictions'])>=3,
 'old_state_fails_mutated_trigger_cases':old_fail,
 'provisional_unscoped_rule_repairs_all_triggers':local_any,
 'unscoped_rule_corrupts_external_valid_code':any_break>0,
 'unique_scope_discovered':selected=='IF_TEST',
 'scope_transfers_source_distinct':held_scoped==(len(held_pos),len(held_protected)) and bool(held_pos) and bool(held_protected),
 'revision_ablation_fossilizes_bad_rule':held_any[0]==len(held_pos) and held_any[1]<len(held_protected),
 'new_external_counterevidence_falsifies_scope':contradiction_regressions>0,
 'system_revokes_falsified_scope':decision['action']=='REVOKE',
}
R['verdict']='PASS_EXTERNAL_SCOPE_REVISION_V37' if all(R['gates'].values()) else 'MIXED_EXTERNAL_SCOPE_REVISION_V37'
R['interpretation_boundary']='External code is independently authored and frozen at fixed commits. Correctness authority is exact AST restoration/preservation against repository source-of-truth, not package behavioral tests; this establishes source-grounded scoped revision, not semantic correctness under deployment.'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2))
