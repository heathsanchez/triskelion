import os, json
import river_client as river

CKPT='river://a25972d0-6711-4c05-8767-be061fc0e6ba/weights/ABC_training'
BASE='Qwen/Qwen3.5-9B'
TESTS=['violet','hidden','green','amber','silver','orange','teal','indigo']
PROMPTS={
 'default': lambda x: f'Input: {x}\nOutput:',
 'ask_A': lambda x: f'Apply only the original prefix rule A. Input: {x}\nOutput:',
 'ask_AB': lambda x: f'Apply the first two learned rules A then B, but not C. Input: {x}\nOutput:',
 'ask_ABC': lambda x: f'Apply all three learned rules A then B then C. Input: {x}\nOutput:',
}
def norm(s):
    t=s.strip(); return t.splitlines()[0].strip() if t else ''
def targets(x):
    return {'A':f'ka-{x}','AB':f'ka-{x}-zu','ABC':f'[ka-{x}-zu]'}
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0); assert client.health_check()
out={'checkpoint':CKPT,'results':{}}
with client.session() as sess:
    m=sess.create_model(base_model=BASE,checkpoint=CKPT)
    for name,pfn in PROMPTS.items():
        gs=m.sample(prompts=[pfn(x) for x in TESTS],max_tokens=24,temperature=0.0)
        rows=[]
        for x,g in zip(TESTS,gs):
            text=norm(g[0].text); t=targets(x)
            rows.append({'input':x,'text':text,'A':text==t['A'],'AB':text==t['AB'],'ABC':text==t['ABC']})
        out['results'][name]=rows
    pref=[]
    triples=[]
    for x in TESTS:
        triples += [
            (x,f'ka-{x}','Aseed_to_AB','-zu'),
            (x,f'ka-{x}-zu','ABseed_to_ABC',']'),
            (x,f'[ka-{x}','wrapped_Aseed','-zu]'),
        ]
    gs=m.sample(prompts=[f'Input: {x}\nOutput: {seed}' for x,seed,_,_ in triples],max_tokens=12,temperature=0.0)
    for (x,seed,label,expected),g in zip(triples,gs):
        cont=g[0].text
        pref.append({'input':x,'probe':label,'seed':seed,'continuation':cont,'expected_contains':expected,'hit':expected in cont})
    out['prefix_completion']=pref
print(json.dumps(out,indent=2))
os.makedirs('artifacts/abc_retention_probe_v4',exist_ok=True)
json.dump(out,open('artifacts/abc_retention_probe_v4/RESULT.json','w'),indent=2)
