import os,json,re,types
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

BASE='Qwen/Qwen3.5-9B'; SEED=20260831; LR=2e-4; TH=0.75; MAX_STEPS=6
OUT=Path('artifacts/quixbugs_lifelong_v12'); OUT.mkdir(parents=True,exist_ok=True)
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0); assert client.health_check()
tok=AutoTokenizer.from_pretrained(BASE); EOS=tok.eos_token_id
TRAIN=list(range(16)); HELD=list(range(100,108))

TESTS={
 'A':[([[]],[]),([[30]],[30]),([[10,'-',5,'-',2]],[10,5,'-',2,'-']),([[34,'-',12,'/',5]],[34,12,5,'/','-']),([[4,'+',9,'*',9,'-',10,'+',13]],[4,9,9,'*','+',10,'-',13,'+'])],
 'B':[([1],[]),([100],[2,2,5,5]),([101],[101]),([104],[2,2,2,13]),([2],[2]),([63],[3,3,7]),([9837],[3,3,1093])],
 'C':[([127],7),([128],1),([3005],9),([13],3),([27],4),([834],4),([256],1)]
}

def spec(task,k):
    z=str(k)
    if task=='A':
        arg='tokens'+z; prec='prec'+z; out='out'+z; stack='stack'+z; item='item'+z
        src=f'''def target({arg}):\n    {prec}={{'+':1,'-':1,'*':2,'/':2}}\n    {out}=[]\n    {stack}=[]\n    for {item} in {arg}:\n        if isinstance({item}, int):\n            {out}.append({item})\n        else:\n            while {stack} and {prec}[{item}] <= {prec}[{stack}[-1]]:\n                {out}.append({stack}.pop())\n            # PATCH_HERE\n    while {stack}:\n        {out}.append({stack}.pop())\n    return {out}\n'''
        line=f'{stack}.append({item})'
    elif task=='B':
        n='num'+z; i='div'+z
        src=f'''def target({n}):\n    if {n} == 1:\n        return []\n    for {i} in range(2, int({n} ** 0.5) + 1):\n        if {n} % {i} == 0:\n            return [{i}] + target({n} // {i})\n    # PATCH_HERE\n'''
        line=f'return [{n}]'
    else:
        n='value'+z; c='count'+z
        src=f'''def target({n}):\n    {c}=0\n    while {n}:\n        # PATCH_HERE\n        {c} += 1\n    return {c}\n'''
        line=f'{n} &= {n} - 1'
    return src,line

def prompt(task,k):
    src,_=spec(task,k)
    examples='; '.join(f'{x[0]} -> {x[1]}' for x in TESTS[task][:3])
    return f'''Repair this Python function. Replace # PATCH_HERE with exactly one Python line.\nFailing/expected examples: {examples}\n\n{src}\nReturn ONLY the replacement line.'''

def datum(task,k):
    p=tok(prompt(task,k),add_special_tokens=False)['input_ids']; _,line=spec(task,k)
    b=tok(' '+line,add_special_tokens=False)['input_ids']+[EOS]; ids=p+b
    return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(p)-1)+[1.0]*(len(b)+1)}

def clean_line(text):
    t=text.strip().splitlines()[0].strip() if text.strip() else ''
    t=t.strip('`').strip()
    if t.startswith('python '): t=t[7:].strip()
    return t

def verify(task,k,line):
    src,_=spec(task,k)
    indent='            ' if task=='A' else ('    ' if task=='B' else '        ')
    patched=src.replace('            # PATCH_HERE' if task=='A' else ('    # PATCH_HERE' if task=='B' else '        # PATCH_HERE'),indent+line)
    ns={}
    try: exec(compile(patched,'<candidate>','exec'),ns,ns)
    except Exception: return False
    fn=ns['target']
    for args,exp in TESTS[task]:
        try: got=fn(*args)
        except Exception: return False
        if got!=exp: return False
    return True

def ev(m,task):
    gs=m.sample(prompts=[prompt(task,k) for k in HELD],max_tokens=24,temperature=0.0)
    lines=[clean_line(g[0].text) for g in gs]
    ok=[verify(task,k,line) for k,line in zip(HELD,lines)]
    return sum(ok)/len(ok),lines

def stage(m,tag,batch,protected):
    curve=[]
    for st in range(1,MAX_STEPS+1):
        fb=m.forward_backward(batch,loss_fn='cross_entropy'); m.optim_step(lr=LR,grad_clip_norm=1.0)
        scores={}; samples={}
        for t in protected:
            scores[t],samples[t]=ev(m,t)
        joint=min(scores.values()); row={'step':st,'loss':float(fb.metrics['loss']),'scores':scores,'joint':joint,'samples':samples}; curve.append(row)
        print(json.dumps({'stage':tag,'step':st,'scores':scores,'joint':joint}),flush=True)
        if joint>=TH:
            ck=m.save_weights(f'quix_{tag}_step{st}',mode='training').path
            return curve,ck,st
    ck=m.save_weights(f'quix_{tag}_final',mode='training').path
    return curve,ck,None

def reload_eval(ck,tasks,label):
    with client.session(project='ml-v12-reload-'+label) as s:
        m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=ck)
        return {t:ev(m,t)[0] for t in tasks}

R={'source':'QuixBugs@4257f44b0ff1181dedaedee6a447e133219fcebf','stages':{}}
# A: shunting_yard missing opstack append
with client.session(project='ml-v12-A') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED))
    curve,ckA,dose=stage(m,'A',[datum('A',k) for k in TRAIN],['A'])
post=reload_eval(ckA,['A'],'A'); R['stages']['A']={'dose':dose,'curve':curve,'checkpoint':ckA,'post_reload':post}
if dose is None or post['A']<TH:
    R['verdict']='FAIL_A'; (OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2)); raise SystemExit
# B: get_factors, 25% protected A replay
with client.session(project='ml-v12-B') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=ckA)
    batch=[datum('B',k) for k in TRAIN[:12]]+[datum('A',k) for k in TRAIN[12:16]]
    curve,ckB,dose=stage(m,'AB',batch,['A','B'])
post=reload_eval(ckB,['A','B'],'AB'); R['stages']['AB']={'dose':dose,'curve':curve,'checkpoint':ckB,'post_reload':post}
if dose is None or min(post.values())<TH:
    R['verdict']='FAIL_AB'; (OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2)); raise SystemExit
# C: bitcount, 25% protected replay split A/B
with client.session(project='ml-v12-C') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=ckB)
    batch=[datum('C',k) for k in TRAIN[:12]]+[datum('A',k) for k in TRAIN[12:14]]+[datum('B',k) for k in TRAIN[14:16]]
    curve,ckC,dose=stage(m,'ABC',batch,['A','B','C'])
post=reload_eval(ckC,['A','B','C'],'ABC'); R['stages']['ABC']={'dose':dose,'curve':curve,'checkpoint':ckC,'post_reload':post}
R['verdict']='PASS_EXTERNAL_CODING_ACCUMULATION' if dose is not None and min(post.values())>=TH else 'FAIL_ABC'
print(json.dumps(R,indent=2),flush=True); (OUT/'RESULT.json').write_text(json.dumps(R,indent=2))
