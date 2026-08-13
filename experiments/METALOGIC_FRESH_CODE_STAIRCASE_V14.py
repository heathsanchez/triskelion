import os,json,ast,subprocess,tempfile,sys,signal
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

BASE='Qwen/Qwen3.5-9B'; SEED=20260901; LR=5e-5; TH=0.75; MAX_STEPS=8
REPO='https://github.com/jkoppel/QuixBugs.git'; COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
TASKS={'A':('find_first_in_sorted',['CMP']),'AB':('get_factors',['CMP','BIN']),'ABC':('quicksort',['CMP','BIN','CONST'])}
TRAIN=list(range(16)); HELD=list(range(100,108)); OUT=Path('artifacts/fresh_code_v14'); OUT.mkdir(parents=True,exist_ok=True)
root=Path(tempfile.mkdtemp())/'qb'; subprocess.run(['git','clone','-q',REPO,str(root)],check=True); subprocess.run(['git','checkout','-q',COMMIT],cwd=root,check=True); sys.path.insert(0,str(root))
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0); assert client.health_check(); tok=AutoTokenizer.from_pretrained(BASE); EOS=tok.eos_token_id

class Timeout(Exception): pass
def alarm(*a): raise Timeout()
signal.signal(signal.SIGALRM,alarm)

def tests_for(name):
    rows=[]
    for line in (root/'json_testcases'/f'{name}.json').read_text().splitlines():
        if line.strip(): rows.append(json.loads(line))
    return rows

def rename_locals(src,name,suffix):
    tree=ast.parse(src); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    locals_=set(a.arg for a in fn.args.args)
    for n in ast.walk(fn):
        if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store): locals_.add(n.id)
    mp={x:f'{x}_{suffix}' for x in sorted(locals_) if x!=name}
    class R(ast.NodeTransformer):
        def visit_arg(self,n):
            if n.arg in mp: n.arg=mp[n.arg]
            return n
        def visit_Name(self,n):
            if n.id in mp: n.id=mp[n.id]
            return n
    tree=R().visit(tree); ast.fix_missing_locations(tree); return ast.unparse(tree)+'\n'

def change_op(src,name,kind,index=0,inverse=False):
    tree=ast.parse(src); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name); seen=-1; done=False
    cmp_f={ast.Lt:ast.LtE,ast.LtE:ast.Lt,ast.Gt:ast.GtE,ast.GtE:ast.Gt,ast.Eq:ast.NotEq,ast.NotEq:ast.Eq}
    bin_f={ast.Add:ast.Sub,ast.Sub:ast.Add,ast.BitAnd:ast.BitXor,ast.BitXor:ast.BitAnd}
    class T(ast.NodeTransformer):
        def visit_Compare(self,n):
            nonlocal seen,done
            self.generic_visit(n)
            if kind=='CMP' and len(n.ops)==1 and type(n.ops[0]) in cmp_f:
                seen+=1
                if seen==index: n.ops[0]=cmp_f[type(n.ops[0])](); done=True
            return n
        def visit_BinOp(self,n):
            nonlocal seen,done
            self.generic_visit(n)
            if kind=='BIN' and type(n.op) in bin_f:
                seen+=1
                if seen==index: n.op=bin_f[type(n.op)](); done=True
            return n
        def visit_Constant(self,n):
            nonlocal seen,done
            if kind=='CONST' and isinstance(n.value,int) and not isinstance(n.value,bool):
                seen+=1
                if seen==index: n.value=n.value-1 if inverse else n.value+1; done=True
            return n
    # reset seen per transform kind; only visit target function to avoid doc/helper noise
    newfn=T().visit(fn); ast.fix_missing_locations(tree)
    if not done: raise RuntimeError((name,kind,index))
    return ast.unparse(tree)+'\n'

def mutate(src,name,ops):
    for op in ops: src=change_op(src,name,op,0,False)
    return src

def repair(src,name,plan):
    for op,idx in plan: src=change_op(src,name,op,idx,op=='CONST')
    return src

def run_source(name,src,tests):
    ns={'__name__':'candidate'}
    try: exec(compile(src,'<cand>','exec'),ns,ns); fn=ns[name]
    except Exception: return False,None,None,None
    for args,exp in tests:
        try:
            signal.alarm(1); got=fn(*args); signal.alarm(0)
        except Exception as e:
            signal.alarm(0); return False,args,repr(e),exp
        if got!=exp: return False,args,got,exp
    return True,None,None,None

def variant(task,k):
    name,ops=TASKS[task]; src=(root/'correct_python_programs'/f'{name}.py').read_text(); src=rename_locals(src,name,k); mut=mutate(src,name,ops); ok,args,got,exp=run_source(name,mut,tests_for(name)); assert not ok
    residual=f'input={args!r}; observed={got!r}; expected={exp!r}'
    target=';'.join(f'{op}@0' for op in ops)
    return name,mut,residual,target

def prompt(task,k):
    name,src,res,_=variant(task,k)
    return f'''A Python function was freshly mutated after checkout. Repair it using only this DSL: CMP@i, BIN@i, CONST@i separated by semicolons. Indices are zero-based among eligible AST nodes of that kind. Return ONLY the repair plan.\nProgram: {name}\nVerified residual: {res}\n\n{src}'''

def datum(task,k):
    p=tok(prompt(task,k),add_special_tokens=False)['input_ids']; target=variant(task,k)[3]; b=tok(' '+target,add_special_tokens=False)['input_ids']+[EOS]; ids=p+b
    return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(p)-1)+[1.0]*(len(b)+1)}

def parse_plan(text):
    t=text.strip().splitlines()[0].strip() if text.strip() else ''; out=[]
    for part in t.split(';'):
        part=part.strip()
        if not part: continue
        if '@' not in part: return None
        op,idx=part.split('@',1); op=op.strip();
        if op not in {'CMP','BIN','CONST'}: return None
        try: ii=int(idx.strip())
        except: return None
        if ii<0 or ii>20: return None
        out.append((op,ii))
    return out or None

def verify(task,k,text):
    plan=parse_plan(text)
    if plan is None: return False
    name,mut,_,_=variant(task,k)
    try: fixed=repair(mut,name,plan)
    except Exception: return False
    return run_source(name,fixed,tests_for(name))[0]

def ev(m,task):
    gs=m.sample(prompts=[prompt(task,k) for k in HELD],max_tokens=24,temperature=0.0); texts=[g[0].text for g in gs]; ok=[verify(task,k,t) for k,t in zip(HELD,texts)]
    return sum(ok)/len(ok),[t.strip().splitlines()[0] if t.strip() else '' for t in texts]

def stage(m,tag,batch,checks):
    curve=[]
    for st in range(1,MAX_STEPS+1):
        fb=m.forward_backward(batch,loss_fn='cross_entropy'); m.optim_step(lr=LR,grad_clip_norm=1.0)
        scores={}; samples={}
        for t in checks: scores[t],samples[t]=ev(m,t)
        joint=min(scores.values()); row={'step':st,'loss':float(fb.metrics['loss']),'scores':scores,'joint':joint,'samples':samples}; curve.append(row); print(json.dumps({'stage':tag,'step':st,'scores':scores,'joint':joint}),flush=True)
        if joint>=TH:
            ck=m.save_weights(f'fresh_{tag}_step{st}',mode='training').path; return curve,ck,st
    return curve,m.save_weights(f'fresh_{tag}_final',mode='training').path,None

def reload_eval(ck,tasks,label):
    with client.session(project='ml-v14-reload-'+label) as s:
        m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=ck); return {t:ev(m,t)[0] for t in tasks}

R={'source':COMMIT,'tasks':TASKS,'stages':{}}
with client.session(project='ml-v14-A') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED)); curve,ckA,doseA=stage(m,'A',[datum('A',k) for k in TRAIN],['A'])
postA=reload_eval(ckA,['A'],'A'); R['stages']['A']={'dose':doseA,'curve':curve,'checkpoint':ckA,'post_reload':postA}
if doseA is None or postA['A']<TH: R['verdict']='FAIL_A'; (OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2)); raise SystemExit
# AB lineage
with client.session(project='ml-v14-AB-lineage') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=ckA); batch=[datum('AB',k) for k in TRAIN[:12]]+[datum('A',k) for k in TRAIN[12:16]]; curveL,ckAB,doseL=stage(m,'AB_lineage',batch,['A','AB'])
postAB=reload_eval(ckAB,['A','AB'],'AB'); R['stages']['AB_lineage']={'dose':doseL,'curve':curveL,'checkpoint':ckAB,'post_reload':postAB}
# AB cold same AB evidence, no replay replaced by AB examples for matched batch size
with client.session(project='ml-v14-AB-cold') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED)); curveC,ckCold,doseC=stage(m,'AB_cold',[datum('AB',k) for k in TRAIN],['AB'])
R['stages']['AB_cold']={'dose':doseC,'curve':curveC}
if doseL is None or min(postAB.values())<TH: R['verdict']='FAIL_AB_LINEAGE'; (OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2)); raise SystemExit
# ABC lineage protected 25%
with client.session(project='ml-v14-ABC-lineage') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=ckAB); batch=[datum('ABC',k) for k in TRAIN[:12]]+[datum('A',k) for k in TRAIN[12:14]]+[datum('AB',k) for k in TRAIN[14:16]]; curve3,ckABC,dose3=stage(m,'ABC_lineage',batch,['A','AB','ABC'])
post3=reload_eval(ckABC,['A','AB','ABC'],'ABC'); R['stages']['ABC_lineage']={'dose':dose3,'curve':curve3,'checkpoint':ckABC,'post_reload':post3}
# ABC cold
with client.session(project='ml-v14-ABC-cold') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED)); curve3c,_,dose3c=stage(m,'ABC_cold',[datum('ABC',k) for k in TRAIN],['ABC'])
R['stages']['ABC_cold']={'dose':dose3c,'curve':curve3c}
R['gates']={'A_persist':postA['A']>=TH,'AB_joint_persist':min(postAB.values())>=TH,'ABC_joint_persist':min(post3.values())>=TH,'AB_lineage_not_slower':doseL is not None and (doseC is None or doseL<=doseC),'ABC_lineage_not_slower':dose3 is not None and (dose3c is None or dose3<=dose3c)}
R['verdict']='PASS_FRESH_CAUSAL_CODE_STAIRCASE' if all(R['gates'].values()) else 'MIXED_FRESH_CODE_STAIRCASE'
print(json.dumps(R,indent=2),flush=True); (OUT/'RESULT.json').write_text(json.dumps(R,indent=2))
