import os,json,ast,subprocess,tempfile,sys,signal
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

BASE='Qwen/Qwen3.5-9B'; SEED=20260903; LR=5e-5; TH=0.75; MAX_STEPS=8
REPO='https://github.com/jkoppel/QuixBugs.git'; COMMIT='4257f44b0ff1181dedaedee6a447e133219fcebf'
PROGRAMS={
 'A':('find_first_in_sorted',['CMP']),
 'B':('bitcount',['BIN']),
 'AB_TEST':('find_in_sorted',['CMP','BIN']),
 'C':('bucketsort',['CONST']),
 'ABC_TEST':('get_factors',['CMP','BIN','CONST']),
}
TRAIN=list(range(16)); HELD=list(range(100,108)); OUT=Path('artifacts/primitive_composition_v15'); OUT.mkdir(parents=True,exist_ok=True)
root=Path(tempfile.mkdtemp())/'qb'; subprocess.run(['git','clone','-q',REPO,str(root)],check=True); subprocess.run(['git','checkout','-q',COMMIT],cwd=root,check=True); sys.path.insert(0,str(root))
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0); assert client.health_check(); tok=AutoTokenizer.from_pretrained(BASE); EOS=tok.eos_token_id

class Timeout(Exception): pass
def alarm(*a): raise Timeout()
signal.signal(signal.SIGALRM,alarm)
CMP={ast.Lt:ast.LtE,ast.LtE:ast.Lt,ast.Gt:ast.GtE,ast.GtE:ast.Gt,ast.Eq:ast.NotEq,ast.NotEq:ast.Eq}
BIN={ast.Add:ast.Sub,ast.Sub:ast.Add,ast.BitAnd:ast.BitXor,ast.BitXor:ast.BitAnd}

def tests_for(name):
    rows=[]
    for line in (root/'json_testcases'/f'{name}.json').read_text().splitlines():
        if line.strip(): rows.append(json.loads(line))
    return rows

def rename_locals(src,name,suffix):
    tree=ast.parse(src); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    loc=set(a.arg for a in fn.args.args)
    for n in ast.walk(fn):
        if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store): loc.add(n.id)
    mp={x:f'{x}_{suffix}' for x in sorted(loc) if x!=name}
    class R(ast.NodeTransformer):
        def visit_arg(self,n):
            if n.arg in mp:n.arg=mp[n.arg]
            return n
        def visit_Name(self,n):
            if n.id in mp:n.id=mp[n.id]
            return n
    tree=R().visit(tree); ast.fix_missing_locations(tree); return ast.unparse(tree)+'\n'

def transform(src,name,kind,index=0,repair=False):
    tree=ast.parse(src); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name); seen=-1; done=False
    class T(ast.NodeTransformer):
        def visit_Compare(self,n):
            nonlocal seen,done
            self.generic_visit(n)
            if kind=='CMP' and len(n.ops)==1 and type(n.ops[0]) in CMP:
                seen+=1
                if seen==index:n.ops[0]=CMP[type(n.ops[0])]();done=True
            return n
        def visit_BinOp(self,n):
            nonlocal seen,done
            self.generic_visit(n)
            if kind=='BIN' and type(n.op) in BIN:
                seen+=1
                if seen==index:n.op=BIN[type(n.op)]();done=True
            return n
        def visit_Constant(self,n):
            nonlocal seen,done
            if kind=='CONST' and isinstance(n.value,int) and not isinstance(n.value,bool):
                seen+=1
                if seen==index:n.value += (-1 if repair else 1);done=True
            return n
    T().visit(fn); ast.fix_missing_locations(tree)
    if not done:raise RuntimeError((name,kind,index))
    return ast.unparse(tree)+'\n'

def mutate(src,name,ops):
    for op in ops:src=transform(src,name,op,0,False)
    return src

def repair(src,name,plan):
    for op,idx in plan:src=transform(src,name,op,idx,op=='CONST')
    return src

def run_source(name,src,tests):
    ns={'__name__':'candidate'}
    try:exec(compile(src,'<cand>','exec'),ns,ns);fn=ns[name]
    except Exception:return False,None,None,None
    for args,exp in tests:
        try:signal.alarm(1);got=fn(*args);signal.alarm(0)
        except Exception as e:signal.alarm(0);return False,args,repr(e),exp
        if got!=exp:return False,args,got,exp
    return True,None,None,None

def variant(key,k):
    name,ops=PROGRAMS[key]; src=(root/'correct_python_programs'/f'{name}.py').read_text(); src=rename_locals(src,name,k); mut=mutate(src,name,ops); ok,args,got,exp=run_source(name,mut,tests_for(name)); assert not ok,(key,k)
    residual=f'input={args!r}; observed={got!r}; expected={exp!r}'
    target=';'.join(f'{op}@0' for op in ops)
    return name,mut,residual,target

def prompt(key,k):
    name,src,res,_=variant(key,k)
    return f'''A Python function was freshly mutated after checkout. Repair it using only this DSL: CMP@i, BIN@i, CONST@i separated by semicolons. Indices are zero-based among eligible AST nodes of that kind. Return ONLY the repair plan.\nProgram: {name}\nVerified residual: {res}\n\n{src}'''

def datum(key,k):
    p=tok(prompt(key,k),add_special_tokens=False)['input_ids']; target=variant(key,k)[3]; b=tok(' '+target,add_special_tokens=False)['input_ids']+[EOS]; ids=p+b
    return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(p)-1)+[1.0]*(len(b)+1)}

def parse_plan(text):
    t=text.strip().splitlines()[0].strip() if text.strip() else ''; out=[]
    for part in t.split(';'):
        part=part.strip()
        if not part:continue
        if '@' not in part:return None
        op,idx=part.split('@',1);op=op.strip()
        if op not in {'CMP','BIN','CONST'}:return None
        try:i=int(idx.strip())
        except:return None
        if i<0 or i>20:return None
        out.append((op,i))
    return out or None

def verify(key,k,text):
    plan=parse_plan(text)
    if plan is None:return False
    name,mut,_,_=variant(key,k)
    try:fixed=repair(mut,name,plan)
    except:return False
    return run_source(name,fixed,tests_for(name))[0]

def ev(m,key):
    gs=m.sample(prompts=[prompt(key,k) for k in HELD],max_tokens=24,temperature=0.0); texts=[g[0].text for g in gs]; ok=[verify(key,k,t) for k,t in zip(HELD,texts)]
    return sum(ok)/len(ok),[t.strip().splitlines()[0] if t.strip() else '' for t in texts]

def train_stage(m,tag,batch,protected):
    curve=[]
    for st in range(1,MAX_STEPS+1):
        fb=m.forward_backward(batch,loss_fn='cross_entropy');m.optim_step(lr=LR,grad_clip_norm=1.0)
        scores={};samples={}
        for key in protected:scores[key],samples[key]=ev(m,key)
        joint=min(scores.values());row={'step':st,'loss':float(fb.metrics['loss']),'scores':scores,'joint':joint,'samples':samples};curve.append(row);print(json.dumps({'stage':tag,'step':st,'scores':scores,'joint':joint}),flush=True)
        if joint>=TH:
            ck=m.save_weights(f'v15_{tag}_step{st}',mode='training').path;return curve,ck,st
    return curve,m.save_weights(f'v15_{tag}_final',mode='training').path,None

def reload_eval(ck,keys,label):
    with client.session(project='ml-v15-reload-'+label) as s:
        m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=ck);return {k:ev(m,k)[0] for k in keys}

R={'source':COMMIT,'programs':PROGRAMS,'stages':{}}
# Generation A: learn CMP primitive only.
with client.session(project='ml-v15-A') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED));curve,ckA,doseA=train_stage(m,'A',[datum('A',k) for k in TRAIN],['A'])
postA=reload_eval(ckA,['A'],'A');R['stages']['A']={'dose':doseA,'curve':curve,'checkpoint':ckA,'post_reload':postA}
if doseA is None or postA['A']<TH:R['verdict']='FAIL_A';(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2));raise SystemExit
# Generation B: learn BIN primitive only while protecting A. Never train AB_TEST.
with client.session(project='ml-v15-B-lineage') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=ckA);batch=[datum('B',k) for k in TRAIN[:12]]+[datum('A',k) for k in TRAIN[12:16]];curve,ckB,doseB=train_stage(m,'B_lineage',batch,['A','B'])
postB=reload_eval(ckB,['A','B'],'B');R['stages']['B_lineage']={'dose':doseB,'curve':curve,'checkpoint':ckB,'post_reload':postB}
with client.session(project='ml-v15-B-cold') as s:
    coldB=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED));curveBC,ckBC,doseBC=train_stage(coldB,'B_cold',[datum('B',k) for k in TRAIN],['B']);ab_cold=ev(coldB,'AB_TEST')[0]
R['stages']['B_cold']={'dose':doseBC,'curve':curveBC,'AB_zero_shot':ab_cold}
if doseB is None or min(postB.values())<TH:R['verdict']='FAIL_B';(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2));raise SystemExit
# Zero-shot composite AB on source-distinct program after reload.
with client.session(project='ml-v15-AB-eval') as s:
    lineageB=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=ckB);ab_lineage,ab_samples=ev(lineageB,'AB_TEST')
R['AB_zero_shot']={'lineage':ab_lineage,'cold':ab_cold,'samples':ab_samples}
# Generation C: learn CONST only while protecting primitive A+B. Never train ABC_TEST or AB_TEST.
with client.session(project='ml-v15-C-lineage') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=ckB);batch=[datum('C',k) for k in TRAIN[:12]]+[datum('A',k) for k in TRAIN[12:14]]+[datum('B',k) for k in TRAIN[14:16]];curve,ckC,doseC=train_stage(m,'C_lineage',batch,['A','B','C'])
postC=reload_eval(ckC,['A','B','C'],'C');R['stages']['C_lineage']={'dose':doseC,'curve':curve,'checkpoint':ckC,'post_reload':postC}
with client.session(project='ml-v15-C-cold') as s:
    coldC=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED));curveCC,_,doseCC=train_stage(coldC,'C_cold',[datum('C',k) for k in TRAIN],['C']);abc_cold=ev(coldC,'ABC_TEST')[0]
R['stages']['C_cold']={'dose':doseCC,'curve':curveCC,'ABC_zero_shot':abc_cold}
if doseC is None or min(postC.values())<TH:R['verdict']='FAIL_C';(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2));raise SystemExit
# Zero-shot 3-primitive composition after reload; also make sure AB composition still exists.
with client.session(project='ml-v15-ABC-eval') as s:
    lineageC=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=ckC);abc_lineage,abc_samples=ev(lineageC,'ABC_TEST');ab_after_c=ev(lineageC,'AB_TEST')[0]
R['ABC_zero_shot']={'lineage':abc_lineage,'cold':abc_cold,'AB_after_C':ab_after_c,'samples':abc_samples}
R['gates']={
 'primitive_A_persist':postA['A']>=TH,
 'primitive_AB_persist':min(postB.values())>=TH,
 'AB_composition_lineage':ab_lineage>=TH,
 'AB_specific_advantage':ab_lineage>ab_cold,
 'primitive_ABC_persist':min(postC.values())>=TH,
 'AB_composition_retained':ab_after_c>=TH,
 'ABC_composition_lineage':abc_lineage>=TH,
 'ABC_specific_advantage':abc_lineage>abc_cold,
}
R['verdict']='PASS_PRIMITIVE_ONLY_DEVELOPMENTAL_COMPOSITION' if all(R['gates'].values()) else 'MIXED_PRIMITIVE_ONLY_COMPOSITION'
print(json.dumps(R,indent=2),flush=True);(OUT/'RESULT.json').write_text(json.dumps(R,indent=2))
