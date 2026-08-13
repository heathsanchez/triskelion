import os, json, math, random
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

BASE='Qwen/Qwen3.5-9B'
SEED=20260903
LR=5e-5
TH=0.75
RANK=32
BATCH=18
MAX_STEPS=10
OUT=Path('artifacts/neural_quotient_revision_v69')
OUT.mkdir(parents=True,exist_ok=True)

random.seed(SEED)
client=river.Client(api_key=os.environ['RIVER_API_KEY'], timeout=180.0)
assert client.health_check()
tok=AutoTokenizer.from_pretrained(BASE)
EOS=tok.eos_token_id

# These labels point to explicit verified Lawbook nodes. River is only trained to route.
ROUTES={
 'Q54': {
   'train':[
     'Parentheses trace stays nonnegative on every observed prefix.',
     'Weak parenthesis evidence shows no prefix underflow.',
     'Observed parenthesis sample never crosses below depth zero.',
     'Under the weak parenthesis verifier, the candidates remain observationally merged.'
   ],
   'held':[
     'Weak-scope parenthesis observation has no negative prefix.',
     'Current parenthesis evidence preserves the coarse equivalence class.'
   ]},
 'C54': {
   'train':[
     'Parentheses trace ends with unmatched opening depth although no prefix went negative.',
     'Protected parenthesis evidence detects positive residual depth at termination.',
     'A separator reveals unmatched opens remaining at the end.',
     'Stronger parenthesis authority splits the weak class using final nonzero depth.'
   ],
   'held':[
     'Protected parenthesis observation reveals leftover opening depth.',
     'The separator is final positive depth after all parentheses are consumed.'
   ]},
 'Q57': {
   'train':[
     'Observed palindrome increment does not require full carry overflow.',
     'Weak palindrome evidence stays within ordinary middle-digit increment cases.',
     'Current palindrome samples avoid the all-nines boundary.',
     'Under weak palindrome evidence the two implementations remain merged.'
   ],
   'held':[
     'Weak-scope palindrome case has no complete carry overflow.',
     'Current palindrome observation preserves the coarse equivalence class.'
   ]},
 'C57': {
   'train':[
     'Protected palindrome evidence reaches the all-nines carry-overflow case.',
     'A separator exposes incorrect output length after full decimal carry.',
     'Stronger palindrome authority distinguishes the all-nine boundary.',
     'The weak palindrome quotient splits on complete carry overflow.'
   ],
   'held':[
     'Protected palindrome observation is an all-nines overflow boundary.',
     'The separator concerns output length after total carry propagation.'
   ]},
 'Q66': {
   'train':[
     'Weak LIS evidence does not expose a reduction of the stored longest length.',
     'Observed LIS traces keep the coarse state update behavior equivalent.',
     'Current LIS samples do not reveal the harmful longest-state overwrite.',
     'Under weak LIS evidence the implementations remain observationally merged.'
   ],
   'held':[
     'Weak-scope LIS observation preserves the coarse equivalence class.',
     'Current LIS evidence does not reveal the state-regression distinction.'
   ]},
 'C66': {
   'train':[
     'Protected LIS evidence exposes a later shorter candidate overwriting the global longest state.',
     'A separator shows the stored LIS length can regress when it should remain maximal.',
     'Stronger LIS authority distinguishes monotone max retention from direct overwrite.',
     'The weak LIS quotient splits on global longest-state regression.'
   ],
   'held':[
     'Protected LIS observation exposes regression of the global longest length.',
     'The separator distinguishes max-retention from replacing longest with a smaller value.'
   ]}
}

PARENTS=['Q54','Q57','Q66']
CHILDREN=['C54','C57','C66']
ALL=PARENTS+CHILDREN

def prompt(text):
    return ('Route this observation to the correct verified Lawbook node. '
            'Return ONLY one node id.\nObservation: '+text+'\nNode:')

def datum(label, text):
    p=tok(prompt(text), add_special_tokens=False)['input_ids']
    b=tok(' '+label, add_special_tokens=False)['input_ids']+[EOS]
    ids=p+b
    return {'input_ids':ids,
            'target_tokens':ids[1:]+[EOS],
            'weights':[0.0]*(len(p)-1)+[1.0]*(len(b)+1)}

def parse(text):
    s=text.strip().splitlines()[0].strip() if text.strip() else ''
    s=s.replace('`','').strip()
    return s.split()[0].strip('.,;:') if s else ''

def eval_routes(model, labels):
    prompts=[]; truth=[]
    for lab in labels:
        for text in ROUTES[lab]['held']:
            prompts.append(prompt(text)); truth.append(lab)
    gens=model.sample(prompts=prompts, max_tokens=8, temperature=0.0)
    pred=[parse(g[0].text) for g in gens]
    by={}
    for lab in labels:
        idx=[i for i,t in enumerate(truth) if t==lab]
        by[lab]=sum(pred[i]==lab for i in idx)/len(idx)
    return by, pred

def make_pool(label, n, cursor):
    xs=ROUTES[label]['train']; out=[]
    for i in range(n): out.append(datum(label, xs[(cursor+i)%len(xs)]))
    return out

def allocate(scores,new_label,protected):
    new_score=scores.get(new_label,0.0)
    new_n=10 if new_score<TH else 6
    rem=BATCH-new_n
    if not protected: return new_n,{}
    deficits={k:max(0.0,TH-scores.get(k,0.0)) for k in protected}
    alloc={k:1 for k in protected}
    rem2=max(0,rem-len(protected))
    weights={k:deficits[k]+0.05 for k in protected}
    Z=sum(weights.values()) or 1.0
    raw={k:rem2*weights[k]/Z for k in protected}
    for k in protected: alloc[k]+=int(math.floor(raw[k]))
    left=rem-sum(alloc.values())
    order=sorted(protected,key=lambda k:(raw[k]-math.floor(raw[k]),deficits[k]),reverse=True)
    for k in order[:max(0,left)]: alloc[k]+=1
    return new_n,alloc

def train_stage(model,tag,new_labels,protected):
    # stage0 can introduce multiple parent routes together; later stages introduce one child.
    cursors={k:0 for k in set(new_labels+protected)}
    active=protected+new_labels
    curve=[]
    for step in range(1,MAX_STEPS+1):
        scores,_=eval_routes(model,active)
        if min(scores.values())>=TH:
            ck=model.save_weights('v69_'+tag+'_step'+str(step-1),mode='training').path
            return curve,ck,step-1
        batch=[]
        if len(new_labels)>1:
            # balanced acquisition of parent routing vocabulary.
            each=BATCH//len(new_labels)
            for lab in new_labels:
                batch+=make_pool(lab,each,cursors[lab]);cursors[lab]+=each
        else:
            nl=new_labels[0]
            new_n,alloc=allocate(scores,nl,protected)
            batch+=make_pool(nl,new_n,cursors[nl]);cursors[nl]+=new_n
            for lab,n in alloc.items():
                batch+=make_pool(lab,n,cursors[lab]);cursors[lab]+=n
        while len(batch)<BATCH:
            lab=new_labels[len(batch)%len(new_labels)]
            batch+=make_pool(lab,1,cursors[lab]);cursors[lab]+=1
        batch=batch[:BATCH]
        fb=model.forward_backward(batch,loss_fn='cross_entropy')
        model.optim_step(lr=LR,grad_clip_norm=1.0)
        post,_=eval_routes(model,active)
        row={'step':step,'loss':float(fb.metrics['loss']),'scores':post,'joint':min(post.values())}
        curve.append(row); print(json.dumps({'stage':tag,**row}),flush=True)
    ck=model.save_weights('v69_'+tag+'_final',mode='training').path
    return curve,ck,None

def reload_eval(checkpoint,labels,label):
    with client.session(project='ml-v69-reload-'+label) as s:
        m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=RANK,seed=SEED),checkpoint=checkpoint)
        scores,pred=eval_routes(m,labels)
        return {'scores':scores,'pred':pred}

R={'protocol':'protocols/V69_PRECOMMIT.txt','base':BASE,'seed':SEED,'stages':{}}
ck=None
with client.session(project='ml-v69') as s:
    m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=RANK,seed=SEED))
    curve,ck,dose=train_stage(m,'parents',PARENTS,[])
    R['stages']['parents']={'curve':curve,'dose':dose,'checkpoint':ck}
    if dose is None: R['verdict']='FAIL_PARENTS'
    else:
        # reopen from saved checkpoint between epistemic revisions to make persistence explicit.
        pass

if R.get('verdict')=='FAIL_PARENTS':
    (OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2));raise SystemExit

current_ck=ck; protected=PARENTS[:]
for child in CHILDREN:
    with client.session(project='ml-v69-'+child) as s:
        m=s.create_model(base_model=BASE,lora=river.LoraConfig(rank=RANK,seed=SEED),checkpoint=current_ck)
        before,_=eval_routes(m,protected+[child])
        curve,new_ck,dose=train_stage(m,child,[child],protected)
    post=reload_eval(new_ck,protected+[child],child)
    R['stages'][child]={'before':before,'curve':curve,'dose':dose,'checkpoint':new_ck,'post_reload':post}
    if dose is None or min(post['scores'].values())<TH:
        R['verdict']='FAIL_'+child
        current_ck=new_ck
        break
    current_ck=new_ck; protected=protected+[child]

final=reload_eval(current_ck,ALL,'final')
R['final_reload']=final
R['gates']={
 'parents_present':all(final['scores'][k]>=TH for k in PARENTS),
 'children_present':all(final['scores'][k]>=TH for k in CHILDREN),
 'all_routes_joint':min(final['scores'].values())>=TH,
 'sequential_revision_completed':all(k in R['stages'] and R['stages'][k].get('dose') is not None for k in CHILDREN)
}
R['verdict']='PASS_NEURAL_QUOTIENT_REVISION' if all(R['gates'].values()) else R.get('verdict','MIXED_NEURAL_QUOTIENT_REVISION')
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2))
print(json.dumps(R,indent=2),flush=True)
