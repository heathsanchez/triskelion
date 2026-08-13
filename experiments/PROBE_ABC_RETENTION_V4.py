import os, json
from river import Session, SamplingParams

CKPT='river://a25972d0-6711-4c05-8767-be061fc0e6ba/weights/ABC_training'
TESTS=['violet','hidden','green','amber','silver','orange','teal','indigo']

PROMPTS={
 'default': lambda x: f'Input: {x}\nOutput:',
 'ask_A': lambda x: f'Apply only the original prefix rule A. Input: {x}\nOutput:',
 'ask_AB': lambda x: f'Apply the first two learned rules A then B, but not C. Input: {x}\nOutput:',
 'ask_ABC': lambda x: f'Apply all three learned rules A then B then C. Input: {x}\nOutput:',
}

def norm(s):
    return s.strip().split('\n')[0].strip()

def targets(x):
    return {'A':f'ka-{x}','AB':f'ka-{x}-zu','ABC':f'[ka-{x}-zu]'}

out={'checkpoint':CKPT,'results':{}}
with Session(api_key=os.environ['RIVER_API_KEY'], timeout=180) as s:
    m=s.create_model('Qwen/Qwen3.5-9B', checkpoint=CKPT)
    for name,pfn in PROMPTS.items():
        rows=[]
        for x in TESTS:
            r=m.sample(pfn(x), sampling_params=SamplingParams(max_tokens=24, temperature=0.0))
            text=norm(r.text)
            t=targets(x)
            rows.append({'input':x,'text':text,'A':text==t['A'],'AB':text==t['AB'],'ABC':text==t['ABC']})
        out['results'][name]=rows
    # Prefix-completion probes: does the model complete the internal ancestor correctly when seeded?
    pref=[]
    for x in TESTS:
        for seed,label,expected in [
            (f'ka-{x}','Aseed_to_AB',f'-zu'),
            (f'ka-{x}-zu','ABseed_to_ABC',']'),
            (f'[ka-{x}','wrapped_Aseed',f'-zu]'),
        ]:
            prompt=f'Input: {x}\nOutput: {seed}'
            r=m.sample(prompt, sampling_params=SamplingParams(max_tokens=12, temperature=0.0))
            pref.append({'input':x,'probe':label,'seed':seed,'continuation':r.text,'expected_contains':expected,'hit':expected in r.text})
    out['prefix_completion']=pref

print(json.dumps(out,indent=2))
os.makedirs('artifacts/abc_retention_probe_v4',exist_ok=True)
json.dump(out,open('artifacts/abc_retention_probe_v4/RESULT.json','w'),indent=2)
