import os, json
import river_client as river

API=os.environ['RIVER_API_KEY']
BASE='Qwen/Qwen3.5-9B'
CKPT='river://1e1687ce-6742-4b4e-9de4-e0349f62626c/weights/A_training'
client=river.Client(api_key=API,timeout=180.0)
heldout=['violet','hidden','green']
prompts=[f'Learned transformation A.\nInput: {s}\nOutput:' for s in heldout]
with client.session(project='metalogic-v2-diagnostic') as sess:
    print('CHECKPOINT_RAW_NO_STOP',flush=True)
    groups=sess.sample(prompts=prompts,base_model=BASE,checkpoint=CKPT,max_tokens=24,temperature=0.0)
    for s,g in zip(heldout,groups):
        x=g[0] if isinstance(g,list) else g
        print(json.dumps({'input':s,'text':x.text,'tokens':x.tokens,'stop_reason':x.stop_reason}),flush=True)
    print('CHECKPOINT_STOP_NEWLINE',flush=True)
    groups=sess.sample(prompts=prompts,base_model=BASE,checkpoint=CKPT,max_tokens=24,temperature=0.0,stop=['\n'])
    for s,g in zip(heldout,groups):
        x=g[0] if isinstance(g,list) else g
        print(json.dumps({'input':s,'text':x.text,'tokens':x.tokens,'stop_reason':x.stop_reason}),flush=True)
