import os,json
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

BASE='Qwen/Qwen3.5-9B'; STEPS=8; BATCH=16; LR=5e-5
OUT=Path('artifacts/ikkf_v3'); pkg=json.loads((OUT/'CAPABILITY.json').read_text())
assert pkg['revision']['status']=='ACTIVE' and pkg['revision']['reverify_before_compile']
CAP='CAP_'+pkg['canonical_sha256'][:12]
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=240.0); assert client.health_check()
tok=AutoTokenizer.from_pretrained(BASE); EOS=tok.eos_token_id

# Package-only synthetic proceduralization. No repository source is read here.
def prompt(i,inscope):
    a=f'x{i}'; b=f'limit{i%7+1}'
    line=(f'if {a} < {b}:' if inscope else f'while {a} < {b}:')
    residual=f'boundary verifier reports equality case {i%5} differs from required inclusive behavior'
    return f'Installed actions: {CAP}, NOOP. Choose exactly one action for this context.\nSource: {line}\nVerifier residual: {residual}\nAction:'

def datum(i,inscope,invert=False):
    p=tok(prompt(i,inscope),add_special_tokens=False)['input_ids']
    use=(inscope != invert); target=CAP if use else 'NOOP'
    a=tok(' '+target,add_special_tokens=False)['input_ids']+[EOS]; ids=p+a
    return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(p)-1)+[1.0]*(len(a)+1)}

def compile_arm(project,seed,invert=False):
    examples=[datum(i,True,invert) for i in range(64)]+[datum(i,False,invert) for i in range(64)]
    curve=[]
    with client.session(project=project) as s:
        m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=32,seed=seed))
        for st in range(STEPS):
            # deterministic balanced 8 positive / 8 negative examples each step
            batch=[]
            for j in range(8):
                batch.append(examples[(st*8+j)%64]); batch.append(examples[64+((st*8+j)%64)])
            fb=m.forward_backward(batch,loss_fn='cross_entropy'); m.optim_step(lr=LR,grad_clip_norm=1.0)
            loss=float(fb.metrics['loss']); curve.append(loss); print(json.dumps({'arm':project,'step':st+1,'loss':loss}),flush=True)
        ck=m.save_weights(project+'-final',mode='training').path
    return {'checkpoint':ck,'seed':seed,'curve':curve,'inverted_scope':invert,'base':BASE,'inherited_checkpoint':False}

R={'capability_id':CAP,'capability_sha256':pkg['canonical_sha256'],'arms':{
 'C1':compile_arm('ikkf-v3-C1',20260921,False),
 'C2':compile_arm('ikkf-v3-C2',20260922,False),
 'W':compile_arm('ikkf-v3-W',20260923,True)
},'verdict':'PASS_IKKF_V3_COMPILE_ARTIFACTS'}
(OUT/'COMPILE_RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2),flush=True)
