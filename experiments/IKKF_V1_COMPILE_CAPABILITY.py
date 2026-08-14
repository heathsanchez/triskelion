import hashlib,json,math,os
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer
import IKKF_V1_RUNTIME as rt

IN=Path('incoming/CAPABILITY.json');OUT=Path('artifacts/ikkf_v1_compile');OUT.mkdir(parents=True,exist_ok=True)
cap=json.loads(IN.read_text()); claimed=cap['package_sha256']; tmp=dict(cap);tmp.pop('package_sha256',None)
canonical=(json.dumps(tmp,sort_keys=True,separators=(',',':'))+'\n').encode();cap_hash=hashlib.sha256(canonical).hexdigest()
assert cap_hash==claimed,(cap_hash,claimed)
plan=[tuple(x) for x in cap['plan']]
assert cap['target_family']=='AB_TEST'
assert cap['dependencies']==['A','B']
assert all(rt.verified('AB_TEST',k,plan) for k in rt.TRAIN)

client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0);assert client.health_check();tok=AutoTokenizer.from_pretrained(rt.BASE);EOS=tok.eos_token_id

def direct_eval(m,key):
    gs=m.sample(prompts=[rt.prompt(key,k) for k in rt.HELD],max_tokens=24,temperature=0.0);ok=[];samples=[]
    for k,g in zip(rt.HELD,gs):
        text=g[0].text;samples.append(text.strip().splitlines()[0] if text.strip() else '')
        p=rt.parse_plan(text);ok.append(bool(p) and rt.verified(key,k,p))
    return sum(ok)/len(ok),samples

def scores(m,keys):return {k:direct_eval(m,k)[0] for k in keys}

def datum(key,k,p):
    assert rt.verified(key,k,p)
    a=tok(rt.prompt(key,k),add_special_tokens=False)['input_ids'];b=tok(' '+rt.plan_text(p),add_special_tokens=False)['input_ids']+[EOS];ids=a+b
    return {'input_ids':ids,'target_tokens':ids[1:]+[EOS],'weights':[0.0]*(len(a)-1)+[1.0]*(len(b)+1)}

def allocate(current):
    new_n=10 if current.get('AB_TEST',0)<rt.TH else 6;protected=['A','B','C'];rem=rt.BATCH-new_n
    alloc={k:1 for k in protected};rem2=rem-len(protected)
    deficits={k:max(0.0,rt.TH-current.get(k,0.0)) for k in protected};weights={k:deficits[k]+0.05 for k in protected};Z=sum(weights.values()) or 1
    raw={k:rem2*weights[k]/Z for k in protected}
    for k in protected:alloc[k]+=int(math.floor(raw[k]))
    left=rem-sum(alloc.values())
    for k in sorted(protected,key=lambda x:(raw[x]-math.floor(raw[x]),deficits[x]),reverse=True)[:left]:alloc[k]+=1
    return new_n,alloc

def compile_once(label):
    primitive=rt.PRIMITIVES;curve=[];cursor={k:0 for k in ['AB_TEST','A','B','C']}
    with client.session(project=f'ikkf-v1-{label}') as s:
        m=s.create_model(base_model=rt.BASE,lora=river.LoraConfig(rank=32,seed=rt.SEED),checkpoint=rt.CHECKPOINT)
        current=scores(m,['A','B','C','AB_TEST'])
        for st in range(1,rt.MAX_STEPS+1):
            if min(current.values())>=rt.TH:break
            new_n,alloc=allocate(current);batch=[]
            for _ in range(new_n):
                k=rt.TRAIN[cursor['AB_TEST']%len(rt.TRAIN)];cursor['AB_TEST']+=1;batch.append(datum('AB_TEST',k,plan))
            for key,n in alloc.items():
                for _ in range(n):
                    k=rt.TRAIN[cursor[key]%len(rt.TRAIN)];cursor[key]+=1;batch.append(datum(key,k,primitive[key]))
            assert len(batch)==rt.BATCH
            fb=m.forward_backward(batch,loss_fn='cross_entropy');m.optim_step(lr=rt.LR,grad_clip_norm=1.0)
            current=scores(m,['A','B','C','AB_TEST']);row={'step':st,'loss':float(fb.metrics['loss']),'new_n':new_n,'protected_alloc':alloc,'scores':current,'joint':min(current.values())};curve.append(row);print(json.dumps({'compile':label,**row}),flush=True)
        ck=m.save_weights(f'ikkf_v1_{label}',mode='training').path
    with client.session(project=f'ikkf-v1-{label}-reload') as s:
        m=s.create_model(base_model=rt.BASE,lora=river.LoraConfig(rank=32,seed=rt.SEED),checkpoint=ck);post=scores(m,['A','B','C','AB_TEST'])
    return {'capability_hash':cap_hash,'curve':curve,'checkpoint':ck,'post_reload':post}

def baseline(label):
    with client.session(project=f'ikkf-v1-baseline-{label}') as s:
        m=s.create_model(base_model=rt.BASE,lora=river.LoraConfig(rank=32,seed=rt.SEED),checkpoint=rt.CHECKPOINT);return scores(m,['A','B','C','AB_TEST'])

base_before=baseline('before');first=compile_once('first');uninstall=baseline('uninstall');second=compile_once('second')
R={'protocol':'IKKF_V1_PORTABLE_CAPABILITY','capability_id':cap['capability_id'],'capability_hash':cap_hash,'base_before':base_before,'first_compile':first,'uninstall':uninstall,'second_compile':second}
R['gates']={
 'baseline_heldout_fails':base_before['AB_TEST']<rt.TH,
 'first_compile_passes':first['post_reload']['AB_TEST']>=rt.TH,
 'ancestors_survive_first_compile':min(first['post_reload'][k] for k in ['A','B','C'])>=rt.TH,
 'first_reload_passes':min(first['post_reload'].values())>=rt.TH,
 'uninstall_restores_failure':uninstall['AB_TEST']<rt.TH,
 'second_compile_passes':second['post_reload']['AB_TEST']>=rt.TH,
 'ancestors_survive_second_compile':min(second['post_reload'][k] for k in ['A','B','C'])>=rt.TH,
 'second_reload_passes':min(second['post_reload'].values())>=rt.TH,
 'same_capability_hash_both_compiles':first['capability_hash']==second['capability_hash']==claimed,
}
R['verdict']='PASS_IKKF_V1_PORTABLE_CAPABILITY' if all(R['gates'].values()) else 'FAIL_IKKF_V1_PORTABLE_CAPABILITY'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)+'\n');print(json.dumps(R,indent=2),flush=True)
if R['verdict']!='PASS_IKKF_V1_PORTABLE_CAPABILITY':raise SystemExit(3)
