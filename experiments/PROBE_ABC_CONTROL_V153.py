import os, json
from pathlib import Path
import river_client as river

BASE='Qwen/Qwen3.5-9B'
CKPT='river://a25972d0-6711-4c05-8767-be061fc0e6ba/weights/ABC_training'
TESTS=['violet','hidden','green','amber','silver','orange','teal','indigo']
STAGES=('A','AB','ABC')
OUT=Path('artifacts/v153_abc_control'); OUT.mkdir(parents=True,exist_ok=True)


def target(stage,x):
    if stage=='A': return f'ka-{x}'
    if stage=='AB': return f'ka-{x}-zu'
    if stage=='ABC': return f'[ka-{x}-zu]'
    raise ValueError(stage)


def clean(s):
    t=s.strip()
    return t.splitlines()[0].strip() if t else ''


def nl_prompt(stage,x):
    if stage=='A': return f'Apply only the original prefix rule A. Input: {x}\nOutput:'
    if stage=='AB': return f'Apply the first two learned rules A then B, but not C. Input: {x}\nOutput:'
    return f'Apply all three learned rules A then B then C. Input: {x}\nOutput:'


def exact_prompt(stage,x):
    return f'Task: {stage}\nInput: {x}\nOutput:'


def contract_prompt(stage,x):
    if stage=='A':
        c='Return exactly the A-stage result and stop. Do not apply B or C; do not append a suffix or brackets.'
    elif stage=='AB':
        c='Return exactly the result after A then B and stop. Do not apply C; do not add enclosing brackets.'
    else:
        c='Return exactly the result after A then B then C and stop.'
    return f'Task: {stage}\nStage contract: {c}\nInput: {x}\nOutput:'


def prefix_seed(stage,x):
    if stage=='A': return 'ka-'
    if stage=='AB': return f'ka-{x}'
    return f'[ka-{x}-zu'


def ensemble_prompts(stage,x):
    # Frozen deterministic proposal variants. The first is the exact training interface.
    return [
        f'Task: {stage}\nInput: {x}\nOutput:',
        f'Task: {stage}\nInput: {x}\nOutput: ',
        f'Task: {stage}\nInput: {x}\nGive only the output:\nOutput:',
        f'Task: {stage}\nInput: {x}\nComplete this task exactly.\nOutput:',
    ]


def score_rows(stage, xs, texts):
    rows=[]
    for x,text in zip(xs,texts):
        y=clean(text); t=target(stage,x)
        rows.append({'stage':stage,'input':x,'text':y,'target':t,'hit':y==t})
    return rows


client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0)
assert client.health_check()
R={'base':BASE,'checkpoint':CKPT,'tests':TESTS,'arms':{},'summary':{},'classification':None}

with client.session(project='v153-abc-control-separator') as sess:
    m=sess.create_model(base_model=BASE,checkpoint=CKPT)

    # A: prior natural-language baseline
    arm={}
    for stage in STAGES:
        gs=m.sample(prompts=[nl_prompt(stage,x) for x in TESTS],max_tokens=24,temperature=0.0)
        arm[stage]=score_rows(stage,TESTS,[g[0].text for g in gs])
    R['arms']['A_NL_BASELINE']=arm

    # B: exact training interface
    arm={}
    for stage in STAGES:
        gs=m.sample(prompts=[exact_prompt(stage,x) for x in TESTS],max_tokens=24,temperature=0.0)
        arm[stage]=score_rows(stage,TESTS,[g[0].text for g in gs])
    R['arms']['B_EXACT_TASK_INTERFACE']=arm

    # C: NL prompt + lawful intermediate prefix
    arm={}
    for stage in STAGES:
        prompts=[]; seeds=[]
        for x in TESTS:
            seed=prefix_seed(stage,x); seeds.append(seed)
            prompts.append(nl_prompt(stage,x)+' '+seed)
        gs=m.sample(prompts=prompts,max_tokens=16,temperature=0.0)
        rows=[]
        for x,seed,g in zip(TESTS,seeds,gs):
            cont=g[0].text
            assembled=seed+cont
            t=target(stage,x)
            rows.append({'stage':stage,'input':x,'seed':seed,'continuation':cont,'assembled':assembled,'target':t,'hit':assembled.strip()==t})
        arm[stage]=rows
    R['arms']['C_NL_PREFIX_HORIZON']=arm

    # D: exact interface + lawful intermediate prefix
    arm={}
    for stage in STAGES:
        prompts=[]; seeds=[]
        for x in TESTS:
            seed=prefix_seed(stage,x); seeds.append(seed)
            prompts.append(exact_prompt(stage,x)+' '+seed)
        gs=m.sample(prompts=prompts,max_tokens=16,temperature=0.0)
        rows=[]
        for x,seed,g in zip(TESTS,seeds,gs):
            cont=g[0].text
            assembled=seed+cont
            t=target(stage,x)
            rows.append({'stage':stage,'input':x,'seed':seed,'continuation':cont,'assembled':assembled,'target':t,'hit':assembled.strip()==t})
        arm[stage]=rows
    R['arms']['D_EXACT_TASK_PREFIX_HORIZON']=arm

    # E: frozen prompt ensemble. Report first proposal and any-hit reachability separately.
    arm={}
    for stage in STAGES:
        rows=[]
        for x in TESTS:
            ps=ensemble_prompts(stage,x)
            gs=m.sample(prompts=ps,max_tokens=24,temperature=0.0)
            texts=[clean(g[0].text) for g in gs]
            t=target(stage,x)
            rows.append({'stage':stage,'input':x,'texts':texts,'target':t,'first_hit':texts[0]==t,'any_hit':t in texts})
        arm[stage]=rows
    R['arms']['E_EXACT_TASK_PROMPT_ENSEMBLE']=arm

    # F: exact task interface plus explicit terminal-stage contract
    arm={}
    for stage in STAGES:
        gs=m.sample(prompts=[contract_prompt(stage,x) for x in TESTS],max_tokens=24,temperature=0.0)
        arm[stage]=score_rows(stage,TESTS,[g[0].text for g in gs])
    R['arms']['F_EXACT_TASK_PLUS_STAGE_CONTRACT']=arm

# Summaries
for name,arm in R['arms'].items():
    s={}
    for stage in STAGES:
        rows=arm[stage]
        if name=='E_EXACT_TASK_PROMPT_ENSEMBLE':
            s[stage]={'first_hits':sum(r['first_hit'] for r in rows),'any_hits':sum(r['any_hit'] for r in rows),'n':len(rows)}
        else:
            s[stage]={'hits':sum(r['hit'] for r in rows),'n':len(rows)}
    R['summary'][name]=s


def full(name):
    return all(R['summary'][name][st]['hits']==len(TESTS) for st in STAGES)

def ab_full(name):
    return all(R['summary'][name][st]['hits']==len(TESTS) for st in ('A','AB'))

b=R['summary']['B_EXACT_TASK_INTERFACE']
if full('B_EXACT_TASK_INTERFACE'):
    R['classification']='PASS_INTERFACE_MISMATCH'
elif (ab_full('C_NL_PREFIX_HORIZON') or ab_full('D_EXACT_TASK_PREFIX_HORIZON')):
    R['classification']='PASS_HORIZON_RESCUE'
elif all(R['summary']['E_EXACT_TASK_PROMPT_ENSEMBLE'][st]['any_hits']==len(TESTS) for st in STAGES):
    R['classification']='PASS_PROPOSAL_RESCUE'
elif full('F_EXACT_TASK_PLUS_STAGE_CONTRACT'):
    R['classification']='PASS_STAGE_CONTRACT_RESCUE'
else:
    helped=[]
    for name in ('B_EXACT_TASK_INTERFACE','C_NL_PREFIX_HORIZON','D_EXACT_TASK_PREFIX_HORIZON','F_EXACT_TASK_PLUS_STAGE_CONTRACT'):
        if any(R['summary'][name][st]['hits']>R['summary']['A_NL_BASELINE'][st]['hits'] for st in ('A','AB')):
            helped.append(name)
    R['classification']='MIXED_CONTROL_RESCUE' if helped else 'NEGATIVE_DEEP_ADDRESSABILITY_RESIDUAL'
    R['helped_arms']=helped

print(json.dumps(R,indent=2),flush=True)
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2))
