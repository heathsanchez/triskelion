import os, json, ast, subprocess, tempfile, sys, signal, hashlib
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

BASE='Qwen/Qwen3.5-9B'
REPO='https://github.com/jkoppel/QuixBugs.git'
COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
TH=0.75; LR=5e-5; STEPS=8; BATCH=16
PRACTICE_SUFFIXES=list(range(16)); HELD_SUFFIXES=list(range(100,108))
C_PRACTICE=['find_in_sorted','get_factors']
J_PRACTICE=['gcd','is_valid_parenthesization']
C_HELD=['possible_change','quicksort','sieve','subsequences']
OUT=Path('artifacts/ikkf_v1_portable_capability'); OUT.mkdir(parents=True,exist_ok=True)

C_PATH=Path('capabilities/IKKF_C_CMP_BIN_V1.json')
J_PATH=Path('capabilities/IKKF_J_CMP_CONST_V1.json')
C=json.loads(C_PATH.read_text()); J=json.loads(J_PATH.read_text())
C_PLAN=[tuple(x) for x in C['plan']]; J_PLAN=[tuple(x) for x in J['plan']]

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

root=Path(tempfile.mkdtemp())/'qb'
subprocess.run(['git','clone','-q',REPO,str(root)],check=True)
subprocess.run(['git','checkout','-q',COMMIT],cwd=root,check=True)
sys.path.insert(0,str(root))
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=240.0); assert client.health_check()
tok=AutoTokenizer.from_pretrained(BASE); EOS=tok.eos_token_id

class Timeout(Exception): pass
def alarm(*a): raise Timeout()
signal.signal(signal.SIGALRM,alarm)
CMP={ast.Lt:ast.LtE,ast.LtE:ast.Lt,ast.Gt:ast.GtE,ast.GtE:ast.Gt,ast.Eq:ast.NotEq,ast.NotEq:ast.Eq}
BIN={ast.Add:ast.Sub,ast.Sub:ast.Add,ast.BitAnd:ast.BitXor,ast.BitXor:ast.BitAnd}

def tests_for(name):
    return [json.loads(x) for x in (root/'json_testcases'/f'{name}.json').read_text().splitlines() if x.strip()]

def rename_locals(src,name,suffix):
    tree=ast.parse(src); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    loc=set(a.arg for a in fn.args.args)
    for n in ast.walk(fn):
        if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store): loc.add(n.id)
    mp={x:f'{x}_{suffix}' for x in sorted(loc) if x!=name}
    class R(ast.NodeTransformer):
        def visit_arg(self,n):
            if n.arg in mp: n.arg=mp[n.arg]
            return n
        def visit_Name(self,n):
            if n.id in mp: n.id=mp[n.id]
            return n
    tree=R().visit(tree); ast.fix_missing_locations(tree); return ast.unparse(tree)+'\n'

def transform(src,name,kind,index=0,repair=False):
    tree=ast.parse(src); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    seen=-1; done=False
    class T(ast.NodeTransformer):
        def visit_Compare(self,n):
            nonlocal seen,done
            self.generic_visit(n)
            if kind=='CMP' and len(n.ops)==1 and type(n.ops[0]) in CMP:
                seen+=1
                if seen==index: n.ops[0]=CMP[type(n.ops[0])](); done=True
            return n
        def visit_BinOp(self,n):
            nonlocal seen,done
            self.generic_visit(n)
            if kind=='BIN' and type(n.op) in BIN:
                seen+=1
                if seen==index: n.op=BIN[type(n.op)](); done=True
            return n
        def visit_Constant(self,n):
            nonlocal seen,done
            if kind=='CONST' and isinstance(n.value,int) and not isinstance(n.value,bool):
                seen+=1
                if seen==index: n.value += (-1 if repair else 1); done=True
            return n
    T().visit(fn); ast.fix_missing_locations(tree)
    if not done: raise RuntimeError((name,kind,index))
    return ast.unparse(tree)+'\n'

def apply_plan(src,name,plan,repair=False):
    for op,idx in plan: src=transform(src,name,op,idx,repair=(repair and op=='CONST'))
    return src

def run_source(name,src):
    ns={'__name__':'candidate'}
    try: exec(compile(src,'<cand>','exec'),ns,ns); fn=ns[name]
    except Exception as e: return False,None,repr(e),None
    for args,exp in tests_for(name):
        try: signal.alarm(1); got=fn(*args); signal.alarm(0)
        except Exception as e: signal.alarm(0); return False,args,repr(e),exp
        if got!=exp: return False,args,got,exp
    return True,None,None,None

def variant(name,suffix,plan):
    src=(root/'correct_python_programs'/f'{name}.py').read_text()
    src=rename_locals(src,name,suffix)
    mut=apply_plan(src,name,plan,repair=False)
    ok,args,got,exp=run_source(name,mut)
    if ok: raise AssertionError(f'mutation_did_not_fail:{name}:{suffix}:{plan}')
    residual=f'input={args!r}; observed={got!r}; expected={exp!r}'
    return mut,residual

def repair(mut,name,plan): return apply_plan(mut,name,plan,repair=True)

def verify_family(names,suffixes,plan):
    rows=[]
    for name in names:
        for k in suffixes:
            try:
                mut,_=variant(name,k,plan); fixed=repair(mut,name,plan); ok=run_source(name,fixed)[0]
            except Exception as e:
                ok=False; rows.append({'program':name,'suffix':k,'ok':False,'error':repr(e)}); continue
            rows.append({'program':name,'suffix':k,'ok':ok})
    return all(r['ok'] for r in rows),rows

def prompt(name,k,mutation_plan):
    src,res=variant(name,k,mutation_plan)
    return f'''A Python function was freshly mutated after checkout. Repair it using only this DSL: CMP@i, BIN@i, CONST@i separated by semicolons. Indices are zero-based among eligible AST nodes of that kind. Return ONLY the repair plan.\nProgram: {name}\nVerified residual: {res}\n\n{src}'''

def pt(plan): return ';'.join(f'{a}@{b}' for a,b in plan)
def parse_plan(text):
    t=text.strip().splitlines()[0].strip() if text.strip() else ''; out=[]
    for part in t.split(';'):
        part=part.strip()
        if not part: continue
        if '@' not in part: return None
        op,idx=part.split('@',1); op=op.strip()
        if op not in {'CMP','BIN','CONST'}: return None
        try: i=int(idx.strip())
        except: return None
        if i<0 or i>20: return None
        out.append((op,i))
    return out or None

def datum(name,k,plan):
    p=tok(prompt(name,k,plan),add_special_tokens=False)['input_ids']
    b=tok(' '+pt(plan),add_special_tokens=False)['input_ids']+[EOS]
    ids=p+b
    return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(p)-1)+[1.0]*(len(b)+1)}

def pooled_eval(model,names,mutation_plan):
    prompts=[]; meta=[]
    for name in names:
        for k in HELD_SUFFIXES:
            prompts.append(prompt(name,k,mutation_plan)); meta.append((name,k))
    gs=model.sample(prompts=prompts,max_tokens=24,temperature=0.0)
    rows=[]
    for (name,k),g in zip(meta,gs):
        text=g[0].text; plan=parse_plan(text)
        mut,_=variant(name,k,mutation_plan)
        try: fixed=repair(mut,name,plan) if plan else mut; ok=run_source(name,fixed)[0]
        except Exception: ok=False
        rows.append({'program':name,'suffix':k,'output':text.strip().splitlines()[0] if text.strip() else '', 'parsed':plan,'ok':ok})
    return sum(r['ok'] for r in rows)/len(rows),rows

def fresh_eval(project,seed):
    with client.session(project=project) as s:
        m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=seed))
        return pooled_eval(m,C_HELD,C_PLAN)

def compile_capability(project,seed,practice_names,plan):
    examples=[datum(name,k,plan) for name in practice_names for k in PRACTICE_SUFFIXES]
    curve=[]
    with client.session(project=project) as s:
        m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=seed))
        for st in range(STEPS):
            batch=[examples[(st*BATCH+i)%len(examples)] for i in range(BATCH)]
            fb=m.forward_backward(batch,loss_fn='cross_entropy'); m.optim_step(lr=LR,grad_clip_norm=1.0)
            curve.append({'step':st+1,'loss':float(fb.metrics['loss'])})
            print(json.dumps({'project':project,**curve[-1]}),flush=True)
        score,rows=pooled_eval(m,C_HELD,C_PLAN)
        ck=m.save_weights(project+'-final',mode='training').path
    return {'score':score,'rows':rows,'curve':curve,'checkpoint':ck}

def reload_eval(ck):
    with client.session(project='ikkf-v1-reload') as s:
        m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=20260903),checkpoint=ck)
        return pooled_eval(m,C_HELD,C_PLAN)

R={
 'protocol':'protocols/IKKF_V1_PORTABLE_CAPABILITY_PRECOMMIT.txt',
 'base':BASE,'quixbugs_commit':COMMIT,'threshold':TH,
 'capability_C':{'path':str(C_PATH),'sha256':sha(C_PATH),'plan':C_PLAN},
 'capability_J':{'path':str(J_PATH),'sha256':sha(J_PATH),'plan':J_PLAN},
 'practice':{'C':C_PRACTICE,'J':J_PRACTICE,'suffixes':PRACTICE_SUFFIXES},
 'heldout':{'C':C_HELD,'suffixes':HELD_SUFFIXES},
 'arms':{},'verification':{}
}

# Verify only practice worlds before compilation; held-out semantic verification is deliberately delayed.
okC,rowsC=verify_family(C_PRACTICE,PRACTICE_SUFFIXES,C_PLAN)
okJ,rowsJ=verify_family(J_PRACTICE,PRACTICE_SUFFIXES,J_PLAN)
R['verification']['practice_C']={'ok':okC,'rows':rowsC}
R['verification']['practice_J']={'ok':okJ,'rows':rowsJ}
if not (okC and okJ):
    R['verdict']='FAIL_PRACTICE_VERIFICATION'; (OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2)); raise SystemExit

b0,b0rows=fresh_eval('ikkf-v1-B0',20260900); R['arms']['B0']={'score':b0,'rows':b0rows}
C1=compile_capability('ikkf-v1-C1',20260903,C_PRACTICE,C_PLAN); R['arms']['C1']=C1
C2=compile_capability('ikkf-v1-C2',20260904,C_PRACTICE,C_PLAN); R['arms']['C2']=C2
Jarm=compile_capability('ikkf-v1-J',20260905,J_PRACTICE,J_PLAN); R['arms']['J']=Jarm
u,urows=fresh_eval('ikkf-v1-U',20260906); R['arms']['U']={'score':u,'rows':urows}
r,rrows=reload_eval(C1['checkpoint']); R['arms']['R']={'score':r,'rows':rrows}

# Only now open the semantic held-out gate for the explicit capability itself.
okH,rowsH=verify_family(C_HELD,HELD_SUFFIXES,C_PLAN)
R['verification']['heldout_C']={'ok':okH,'rows':rowsH}
R['gates']={
 'practice_C_verified':okC,
 'practice_J_verified':okJ,
 'cold_fails':b0<TH,
 'compile_C1_passes':C1['score']>=TH,
 'compile_C2_passes':C2['score']>=TH,
 'independent_recompile':C1['score']>=TH and C2['score']>=TH,
 'decoy_fails':Jarm['score']<TH,
 'uninstall_restores_failure':u<TH,
 'reload_preserves_C':r>=TH,
 'heldout_never_trained':set(C_HELD).isdisjoint(C_PRACTICE+J_PRACTICE) and set(HELD_SUFFIXES).isdisjoint(PRACTICE_SUFFIXES),
 'no_inherited_checkpoint':True,
 'heldout_semantic_C_verified':okH,
}
R['verdict']='PASS_IKKF_V1_PORTABLE_CAPABILITY' if all(R['gates'].values()) else 'FAIL_IKKF_V1_PORTABLE_CAPABILITY'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2),flush=True)
