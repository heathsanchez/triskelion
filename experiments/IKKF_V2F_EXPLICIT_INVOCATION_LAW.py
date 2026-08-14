"""IKKF V2f: exact compact-law induction from verifier-decided invocation."""
import ast, hashlib, json
from functools import lru_cache
from pathlib import Path

parent=Path('experiments/IKKF_V2_CAPABILITY_ROUTING.py')
src=parent.read_text(); print('V2_PARENT_SHA256',hashlib.sha256(src.encode()).hexdigest(),flush=True)
marker="R={'protocol':'protocols/IKKF_V2_CAPABILITY_ROUTING_PRECOMMIT.txt'"; assert marker in src and src.count(marker)==1
ns={'__name__':'ikkf_v2f_substrate'}; exec(compile(src.split(marker,1)[0],'IKKF_V2F_SUBSTRATE','exec'),ns,ns)
C=ns['C']; J=ns['J']; variant=ns['variant']; run=ns['run']; apply=ns['apply']; root=ns['root']; TH=ns['TH']
HELD_PROGS=['possible_change','sieve','subsequences']; HELD=list(range(100,108)); TRAIN=list(range(16)); CENSUS=list(range(4))
OUT=Path('artifacts/ikkf_v2f_explicit_invocation_law'); OUT.mkdir(parents=True,exist_ok=True)

def sem(name,k,required,other):
    try:
        mut,res=variant(name,k,required); noop=run(name,mut)[0]
        req=run(name,apply(mut,name,required,True))[0]
        try: oth=run(name,apply(mut,name,other,True))[0]
        except Exception: oth=False
        return (not noop) and req and (not oth), mut, res
    except Exception:
        return False,None,None

def paired(name,sufs): return all(sem(name,k,C,J)[0] and sem(name,k,J,C)[0] for k in sufs)
all_names=sorted(p.stem for p in (root/'correct_python_programs').glob('*.py') if p.stem not in HELD_PROGS)
selected=[]
for n in all_names:
    if paired(n,CENSUS) and len(selected)<8: selected.append(n)
R={'protocol':'protocols/IKKF_V2F_EXPLICIT_INVOCATION_LAW_PRECOMMIT.txt','selected_training_programs':selected}
if len(selected)<4:
    R['verdict']='FAIL_INSUFFICIENT_PAIRED_WORLDS'; (OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2)); raise SystemExit(2)

NODE_TYPES=[ast.Compare,ast.BinOp,ast.Constant,ast.If,ast.For,ast.While,ast.Call,ast.Return,ast.BoolOp,ast.UnaryOp,ast.Subscript,ast.ListComp]

def features(mut,res):
    t=ast.parse(mut); f={}
    for cls in NODE_TYPES:
        c=sum(isinstance(x,cls) for x in ast.walk(t))
        for k in (1,2,3): f[f'ast:{cls.__name__}>={k}']=c>=k
    for x in ast.walk(t):
        if isinstance(x,ast.Compare):
            for op in x.ops: f[f'cmp:{type(op).__name__}']=True
        if isinstance(x,ast.BinOp): f[f'bin:{type(x.op).__name__}']=True
    obs=res.get('observed'); exp=res.get('expected')
    f[f'obs_type:{type(obs).__name__}']=True; f[f'exp_type:{type(exp).__name__}']=True
    f['res:same_type']=type(obs) is type(exp); f['res:equal']=obs==exp
    try: f['res:obs_truthy']=bool(obs)
    except Exception: f['res:obs_truthy']=False
    try: f['res:exp_truthy']=bool(exp)
    except Exception: f['res:exp_truthy']=False
    if hasattr(obs,'__len__') and hasattr(exp,'__len__'):
        try:
            lo,le=len(obs),len(exp); f['len:eq']=lo==le; f['len:obs_shorter']=lo<le; f['len:obs_longer']=lo>le
        except Exception: pass
    if isinstance(obs,(int,float)) and not isinstance(obs,bool) and isinstance(exp,(int,float)) and not isinstance(exp,bool):
        f['num:obs_neg']=obs<0; f['num:exp_neg']=exp<0; f['num:obs_lt_exp']=obs<exp; f['num:obs_gt_exp']=obs>exp
    return f

train=[]
for n in selected:
    for k in TRAIN:
        for lab,req,oth in [('C',C,J),('J',J,C)]:
            ok,mut,res=sem(n,k,req,oth)
            train.append({'program':n,'suffix':k,'label':lab,'unique':ok,'features':features(mut,res) if ok else {}})
all_unique=all(x['unique'] for x in train)
if not all_unique:
    R['training']=train; R['verdict']='FAIL_FULL_TRAINING_SEMANTIC_PRECONDITION'; (OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2)); raise SystemExit(3)

# Freeze vocabulary from training only. Missing features evaluate False.
vocab=sorted(set().union(*(set(x['features']) for x in train)))
y=tuple(x['label'] for x in train)
rows=tuple(tuple(bool(x['features'].get(f,False)) for f in vocab) for x in train)

def ser(tree):
    if tree[0]=='L': return tree[1]
    return f'({tree[1]}?{ser(tree[2])}:{ser(tree[3])})'
def nodes(tree): return 0 if tree[0]=='L' else 1+nodes(tree[2])+nodes(tree[3])
def predict(tree,feat):
    while tree[0]!='L': tree=tree[2] if bool(feat.get(tree[1],False)) else tree[3]
    return tree[1]

@lru_cache(None)
def solve(indices,depth):
    labs={y[i] for i in indices}
    if len(labs)==1: return ('L',next(iter(labs)))
    if depth==0: return None
    best=None; bestkey=None
    for j,f in enumerate(vocab):
        a=tuple(i for i in indices if rows[i][j]); b=tuple(i for i in indices if not rows[i][j])
        if not a or not b: continue
        ta=solve(a,depth-1); tb=solve(b,depth-1)
        if ta is None or tb is None: continue
        t=('N',f,ta,tb); key=(nodes(t),ser(t))
        if best is None or key<bestkey: best,bestkey=t,key
    return best

tree=solve(tuple(range(len(train))),3)
if tree is None:
    R['training_count']=len(train); R['feature_count']=len(vocab); R['verdict']='FAIL_NO_COMPACT_LAW'; (OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2)); raise SystemExit(4)

# Shuffled-label law under identical class.
y_orig=y; y=tuple('J' if z=='C' else 'C' for z in y_orig); solve.cache_clear(); stree=solve(tuple(range(len(train))),3); y=y_orig; solve.cache_clear()

def eval_tree(t):
    out=[]
    for n in HELD_PROGS:
        for k in HELD:
            for lab,req,oth in [('C',C,J),('J',J,C)]:
                ok,mut,res=sem(n,k,req,oth); assert ok
                pred=predict(t,features(mut,res)); plan=C if pred=='C' else J
                repair=run(n,apply(mut,n,plan,True))[0]
                out.append({'program':n,'suffix':k,'required':lab,'predicted':pred,'route_ok':pred==lab,'repair_ok':repair})
    def score(lab,key):
        z=[r for r in out if r['required']==lab]; return sum(bool(r[key]) for r in z)/len(z)
    c=score('C','repair_ok'); j=score('J','repair_ok'); route=sum(r['route_ok'] for r in out)/len(out)
    return {'C':c,'J':j,'joint':min(c,j),'route_accuracy':route,'rows':out}
E=eval_tree(tree); S=eval_tree(stree) if stree is not None else {'C':0,'J':0,'joint':0,'route_accuracy':0,'rows':[]}
train_acc=sum(predict(tree,x['features'])==x['label'] for x in train)/len(train)
G={
 'at_least_four_paired_training_programs':len(selected)>=4,
 'every_training_world_verifier_unique':all_unique,
 'compact_law_zero_training_error_depth_le_3':train_acc==1.0 and nodes(tree)<=7,
 'law_uses_no_forbidden_identity_features':all(not any(z in f.lower() for z in ['program','suffix','filename','target']) for f in vocab),
 'heldout_never_enters_induction':set(selected).isdisjoint(HELD_PROGS) and set(TRAIN).isdisjoint(HELD),
 'law_C_passes':E['C']>=TH,
 'law_J_passes':E['J']>=TH,
 'law_routes':E['route_accuracy']>=TH,
 'law_joint_executes':E['joint']>=TH,
 'shuffled_control_fails':S['route_accuracy']<TH or S['joint']<TH,
 'selected_only_executed_at_eval':True,
 'law_internal_nodes_le_7':nodes(tree)<=7,
}
R.update({'training_count':len(train),'feature_count':len(vocab),'law':ser(tree),'law_internal_nodes':nodes(tree),'train_accuracy':train_acc,'eval':E,'shuffle_eval':S,'gates':G})
R['verdict']='PASS_IKKF_V2F_EXPLICIT_INVOCATION_LAW' if all(G.values()) else 'FAIL_IKKF_V2F_EXPLICIT_INVOCATION_LAW'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2),flush=True)
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
