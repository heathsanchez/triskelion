import json, re, time
from pathlib import Path

OUT=Path('artifacts/v55c');OUT.mkdir(parents=True,exist_ok=True)
MODEL='Qwen/Qwen2.5-Coder-0.5B-Instruct'

# Frozen held-out decision set. The model must decide whether the verified widening operator should apply.
# Labels are determined by executable boundary semantics encoded in the task descriptions, not shown to the model.
TASKS=[
 ('h1','if n < limit: return n','At n == limit the value must still be accepted.','WIDEN'),
 ('h2','if len(name) < max_len: return name','A name whose length equals max_len must remain unchanged.','WIDEN'),
 ('h3','if page < last_page: return page','The last_page itself is a valid page.','WIDEN'),
 ('h4','if score < threshold: return "ok"','A score equal to threshold is still ok.','WIDEN'),
 ('h5','if count < capacity: append(x)','The final free slot at count == capacity must be usable.','WIDEN'),
 ('h6','if age < minimum: reject()','Age exactly equal to minimum must NOT be rejected.','KEEP'),
 ('n1','while i < len(xs): i += 1','The loop must stop before indexing len(xs).','KEEP'),
 ('n2','while cursor < len(text): cursor += 1','Reading text[len(text)] would be out of bounds.','KEEP'),
 ('n3','return x < upper','upper itself must be excluded.','KEEP'),
 ('n4','assert value < maximum','value == maximum must violate the assertion.','KEEP'),
 ('n5','operator.lt(value, bound)','The API is explicitly an open upper bound.','KEEP'),
 ('n6','if retries < max_retries: retry()','At retries == max_retries no further retry is allowed.','KEEP'),
]

VERIFIED_CARD='''VERIFIED CAPABILITY CARD\nOperator: WIDEN_LT_TO_LE (< -> <=).\nScope: use only when executable evidence says equality belongs to the accepted side of a boundary.\nDo not apply to open bounds, loop/index guards, or cases where equality is explicitly rejected.\nAuthority: external tests; if scope evidence conflicts, KEEP/revoke rather than generalize.\n'''
RAW_MEMORY='''PAST OUTCOMES (unverified raw memory):\n- `if len(name) < length` changed to <= and a test passed.\n- `while cursor < len(text)` changed to <= and a test failed.\nThese are past observations, not a verified rule.\n'''

from transformers import AutoTokenizer,AutoModelForCausalLM
import torch

tok=AutoTokenizer.from_pretrained(MODEL)
model=AutoModelForCausalLM.from_pretrained(MODEL,torch_dtype=torch.float32,device_map='cpu')
model.eval()

def ask(task,arm):
    _,code,req,_=task
    extra='' if arm=='A_NO_MEMORY' else RAW_MEMORY if arm=='B_RAW_MEMORY' else VERIFIED_CARD
    prompt=f'''You are choosing whether to apply one code transformation.\n{extra}\nCODE: {code}\nREQUIREMENT: {req}\nAction choices: WIDEN means replace the relevant `<` with `<=`. KEEP means leave it strict.\nAnswer exactly WIDEN or KEEP.'''
    messages=[{'role':'user','content':prompt}]
    text=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
    inp=tok(text,return_tensors='pt')
    with torch.no_grad():out=model.generate(**inp,max_new_tokens=6,do_sample=False,pad_token_id=tok.eos_token_id)
    ans=tok.decode(out[0][inp['input_ids'].shape[1]:],skip_special_tokens=True).strip().upper()
    m=re.search(r'\b(WIDEN|KEEP)\b',ans)
    return m.group(1) if m else 'OTHER',ans

rows=[]
for arm in ('A_NO_MEMORY','B_RAW_MEMORY','C_VERIFIED_LAYER'):
    correct=0
    for task in TASKS:
        pred,raw=ask(task,arm);gold=task[3];correct+=pred==gold
        rows.append({'arm':arm,'id':task[0],'gold':gold,'pred':pred,'raw':raw})
    print(arm,correct,'/',len(TASKS))

scores={a:sum(r['pred']==r['gold'] for r in rows if r['arm']==a) for a in ('A_NO_MEMORY','B_RAW_MEMORY','C_VERIFIED_LAYER')}
# Protected subset measures over-generalisation; helpful subset measures useful transfer.
help_ids={x[0] for x in TASKS if x[3]=='WIDEN'};keep_ids={x[0] for x in TASKS if x[3]=='KEEP'}
def acc(arm,ids):
    xs=[r for r in rows if r['arm']==arm and r['id'] in ids];return sum(r['pred']==r['gold'] for r in xs)/len(xs)
sub={a:{'help':acc(a,help_ids),'protected':acc(a,keep_ids)} for a in scores}
R={'protocol':'V55C_MODEL_INTEGRATION_AB_20260814','model':MODEL,'tasks':len(TASKS),'scores':scores,'subset_accuracy':sub,'rows':rows}
R['gates']={'verified_layer_beats_no_memory':scores['C_VERIFIED_LAYER']>scores['A_NO_MEMORY'],'verified_layer_not_worse_than_raw':scores['C_VERIFIED_LAYER']>=scores['B_RAW_MEMORY'],'verified_layer_help_transfer':sub['C_VERIFIED_LAYER']['help']>=0.8,'verified_layer_protects_negatives':sub['C_VERIFIED_LAYER']['protected']>=0.8}
R['verdict']='PASS_V55C_MODEL_LAYER_SMOKE' if all(R['gates'].values()) else 'MIXED_V55C_MODEL_LAYER_SMOKE'
R['claim_boundary']='Small frozen decision benchmark on a 0.5B coding model. This tests whether an explicit verified capability card improves applicability decisions versus no memory/raw episodic memory; it is not a general coding benchmark or proof of economic value.'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps({'scores':scores,'subsets':sub,'gates':R['gates'],'verdict':R['verdict']},indent=2))
