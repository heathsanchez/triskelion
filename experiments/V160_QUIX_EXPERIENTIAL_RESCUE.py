import os,json,re
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

BASE='Qwen/Qwen3.5-9B'; SEED=20260831; LR=2e-4; MAX_INTERFERENCE_STEPS=12; TH=0.75
AB_CK='river://ae6fa294-181b-46af-b078-429ce7e6c882/weights/quix_AB_step1'
OUT=Path('artifacts/v160_quix_experiential_rescue'); OUT.mkdir(parents=True,exist_ok=True)
TRAIN=list(range(16)); EXPERIENCE=[80,81]; HELD=list(range(100,108))
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0); assert client.health_check()
tok=AutoTokenizer.from_pretrained(BASE); EOS=tok.eos_token_id

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
    marker='            # PATCH_HERE' if task=='A' else ('    # PATCH_HERE' if task=='B' else '        # PATCH_HERE')
    indent='            ' if task=='A' else ('    ' if task=='B' else '        ')
    patched=src.replace(marker,indent+line)
    ns={}
    try: exec(compile(patched,'<candidate>','exec'),ns,ns)
    except Exception: return False
    fn=ns['target']
    for args,exp in TESTS[task]:
        try: got=fn(*args)
        except Exception: return False
        if got!=exp: return False
    return True

def sample_lines(m,task,ks,prompt_fn=prompt):
    gs=m.sample(prompts=[prompt_fn(task,k) for k in ks],max_tokens=24,temperature=0.0)
    return [clean_line(g[0].text) for g in gs]

def eval_task(m,task,ks=HELD,prompt_fn=prompt):
    lines=sample_lines(m,task,ks,prompt_fn)
    oks=[verify(task,k,line) for k,line in zip(ks,lines)]
    return {'hits':sum(oks),'n':len(ks),'lines':lines,'oks':oks}

def learn_template(lines,ks):
    # Generic anti-unification for this frozen renaming protocol: the same numeric world id
    # may recur multiple times in a verified repair line. No protected held-out answer is used.
    templ=None
    for line,k in zip(lines,ks):
        t=re.sub(rf'(?<!\d){k}(?!\d)','{K}',line)
        if templ is None: templ=t
        elif t!=templ: return None
    return templ

def instantiate(templ,k):
    return None if templ is None else templ.replace('{K}',str(k))

R={'protocol':{
 'source':'QuixBugs@4257f44b0ff1181dedaedee6a447e133219fcebf',
 'starting_checkpoint':AB_CK,
 'interference':'train only task C from stable AB checkpoint using original LR and batch size; stop at first verified A or B score < 0.75, max 12 updates',
 'experience':'two pre-interference verified outputs per prior task on worlds 80,81, disjoint from train 0..15 and protected held-out 100..107',
 'arms':['neural_only','raw_verified_memory','compiled_experiential_map','shuffled_map'],
 'map_learning':'anti-unify only the two verified repair-line strings by replacing their shared numeric world id with a slot; freeze before held-out evaluation',
 'claim_boundary':'bounded executable coding repair under frozen variable-renaming protocol; not unrestricted program repair'
 },'pre_experience':{},'interference_curve':[]}

# Phase 1: collect and verify prior experience from the stable AB checkpoint.
with client.session(project='v160-experience') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=AB_CK)
    maps={}
    for task in ['A','B']:
        lines=sample_lines(m,task,EXPERIENCE)
        oks=[verify(task,k,line) for k,line in zip(EXPERIENCE,lines)]
        templ=learn_template(lines,EXPERIENCE) if all(oks) else None
        R['pre_experience'][task]={'worlds':EXPERIENCE,'lines':lines,'verified':oks,'template':templ}
        maps[task]=templ
    R['starting_eval']={t:eval_task(m,t) for t in ['A','B','C']}

if any(maps[t] is None for t in ['A','B']):
    R['verdict']='EXPERIENCE_MAP_NOT_LEARNED'; json.dump(R,open(OUT/'RESULT.json','w'),indent=2); print(json.dumps(R,indent=2)); raise SystemExit

# Phase 2: induce later interference, saving the first verified regression checkpoint.
regression_ck=None; regression_step=None
with client.session(project='v160-interference') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=AB_CK)
    batch=[datum('C',k) for k in TRAIN]
    for st in range(1,MAX_INTERFERENCE_STEPS+1):
        fb=m.forward_backward(batch,loss_fn='cross_entropy'); m.optim_step(lr=LR,grad_clip_norm=1.0)
        scores={t:eval_task(m,t) for t in ['A','B','C']}
        row={'step':st,'loss':float(fb.metrics['loss']),'hits':{t:scores[t]['hits'] for t in scores}}
        R['interference_curve'].append(row); print(json.dumps(row),flush=True)
        if scores['A']['hits']<6 or scores['B']['hits']<6:
            regression_ck=m.save_weights(f'v160_first_regression_step{st}',mode='training').path
            regression_step=st; break

R['regression_step']=regression_step; R['regression_checkpoint']=regression_ck
if regression_ck is None:
    R['verdict']='NO_INTERFERENCE_WITHIN_BUDGET'; json.dump(R,open(OUT/'RESULT.json','w'),indent=2); print(json.dumps(R,indent=2)); raise SystemExit

# Phase 3: freeze weights and compare arms on protected held-out worlds.
def raw_memory_prompt(task,k):
    src,_=spec(task,k); examples='; '.join(f'{x[0]} -> {x[1]}' for x in TESTS[task][:3])
    if task in ['A','B']:
        mem='\n'.join(f'Prior verified repair world {w}: {line}' for w,line in zip(EXPERIENCE,R['pre_experience'][task]['lines']))
    else: mem='No prior verified repair for this task.'
    return f'''Repair this Python function. Replace # PATCH_HERE with exactly one Python line.\nFailing/expected examples: {examples}\nVerified prior experience:\n{mem}\n\n{src}\nReturn ONLY the replacement line.'''

with client.session(project='v160-frozen-arms') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=SEED),checkpoint=regression_ck)
    neural={t:eval_task(m,t) for t in ['A','B','C']}
    rawmem={t:eval_task(m,t,prompt_fn=raw_memory_prompt) for t in ['A','B','C']}

compiled={}; shuffled={}
for task in ['A','B']:
    comp_lines=[instantiate(maps[task],k) for k in HELD]
    wrong_maps={'A':maps['B'],'B':maps['A']}
    wrong_lines=[instantiate(wrong_maps[task],k) for k in HELD]
    compiled[task]={'hits':sum(verify(task,k,line) for k,line in zip(HELD,comp_lines)),'n':len(HELD),'lines':comp_lines}
    shuffled[task]={'hits':sum(verify(task,k,line) for k,line in zip(HELD,wrong_lines)),'n':len(HELD),'lines':wrong_lines}
compiled['C']={'hits':neural['C']['hits'],'n':len(HELD),'lines':neural['C']['lines']}
shuffled['C']={'hits':neural['C']['hits'],'n':len(HELD),'lines':neural['C']['lines']}
R['arms']={'neural_only':neural,'raw_verified_memory':rawmem,'compiled_experiential_map':compiled,'shuffled_map':shuffled}

base_prior=neural['A']['hits']+neural['B']['hits']; raw_prior=rawmem['A']['hits']+rawmem['B']['hits']; comp_prior=compiled['A']['hits']+compiled['B']['hits']; shuf_prior=shuffled['A']['hits']+shuffled['B']['hits']
R['prior_task_totals']={'neural_only':base_prior,'raw_verified_memory':raw_prior,'compiled_experiential_map':comp_prior,'shuffled_map':shuf_prior,'max':16}
R['verdict']='PASS_REAL_CODING_EXPERIENTIAL_RESCUE' if comp_prior>max(base_prior,raw_prior) and comp_prior>shuf_prior else 'NO_DECISIVE_EXPERIENTIAL_RESCUE'
json.dump(R,open(OUT/'RESULT.json','w'),indent=2); print(json.dumps(R,indent=2),flush=True)
