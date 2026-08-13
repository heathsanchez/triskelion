import os, json, hashlib, random, time
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

PROTOCOL = {
  "name":"METALOGIC_WAKE_SLEEP_STAIRCASE_V2",
  "date":"2026-08-13",
  "seed":20260813,
  "base_model":"Qwen/Qwen3.5-9B",
  "lora_rank":8,
  "lr":2e-4,
  "grad_clip_norm":1.0,
  "train_steps_A":2,
  "train_steps_new_primitive":2,
  "batch_examples":16,
  "heldout_n":8,
  "max_tokens":32,
  "threshold":0.75,
  "controls":["LINEAGE","COLD","WRONG_LINEAGE"],
  "claim_boundary":"Synthetic mechanistic test of cross-session neural inheritance and compositional developmental advantage; not external-task or open-ended self-improvement evidence."
}
OUT=Path("artifacts/wake_sleep_staircase_v2"); OUT.mkdir(parents=True,exist_ok=True)
PH=hashlib.sha256(json.dumps(PROTOCOL,sort_keys=True,separators=(",",":")).encode()).hexdigest()
(OUT/"PRECOMMIT.json").write_text(json.dumps({"protocol_sha256":PH,"protocol":PROTOCOL},indent=2))

def log(event, **kw):
    rec={"t":time.time(),"event":event,**kw}
    print(json.dumps(rec),flush=True)
    with (OUT/"TRACE.jsonl").open("a") as f: f.write(json.dumps(rec)+"\n")

api=os.environ["RIVER_API_KEY"]
client=river.Client(api_key=api, timeout=180.0)
assert client.health_check() is True
caps=list(client.get_capabilities())
base=PROTOCOL["base_model"]
if base not in caps: raise RuntimeError(f"Required base unavailable: {base}; caps={caps}")
log("base",base=base)
tok=AutoTokenizer.from_pretrained(base,trust_remote_code=True)
EOS=tok.eos_token_id
if EOS is None: raise RuntimeError("EOS missing")

# Primitive capabilities. Each generation is trained only on the NEW primitive.
def A(s): return "ka-"+s
def B(s): return s[::-1]
def C(s): return s+"-zu"
def W1(s): return s.upper()
def W2(s): return "xx-"+s

train_words=["amber","quiet","silver","paper","winter","copper","scarlet","gentle","marble","rapid","bright","soft","blue","little","warm","clear"]
heldout=["violet","hidden","green","crimson","golden","silent","orange","secret"]

# Primitive prompts are deliberately identical in form; names are arbitrary labels.
def primitive_prompt(label,s): return f"Learned transformation {label}.\nInput: {s}\nOutput:"
def compose_prompt(labels,s): return f"Apply learned transformations {' then '.join(labels)} in that order.\nInput: {s}\nOutput:"

def datum(p,c):
    pids=tok(p,add_special_tokens=False)["input_ids"]
    cids=tok(" "+c,add_special_tokens=False)["input_ids"]+[EOS]
    ids=pids+cids
    return {"input_ids":ids,"target_tokens":ids[1:]+[EOS],"weights":[0.0]*(len(pids)-1)+[1.0]*(len(cids)+1)}

def primitive_batch(label,fn,domain):
    return [datum(primitive_prompt(label,s),fn(s)) for s in domain]

def sample_text(x):
    if isinstance(x,list):
        while isinstance(x,list) and x: x=x[0]
    return getattr(x,"text",str(x)).strip()

def eval_prompts(model,prompts,golds,tag):
    log("eval_before",tag=tag,n=len(prompts))
    groups=model.sample(prompts=prompts,max_tokens=PROTOCOL["max_tokens"],temperature=0.0,stop=["\n"])
    outs=[]
    for g in groups:
        x=g[0] if isinstance(g,list) else g
        outs.append(sample_text(x))
    rows=[{"prompt":p,"gold":g,"output":o,"ok":o==g} for p,g,o in zip(prompts,golds,outs)]
    acc=sum(r["ok"] for r in rows)/len(rows)
    log("eval_after",tag=tag,accuracy=acc)
    return {"accuracy":acc,"rows":rows}

def eval_A(model,tag):
    return eval_prompts(model,[primitive_prompt("A",s) for s in heldout],[A(s) for s in heldout],tag)

def eval_AB(model,tag):
    return eval_prompts(model,[compose_prompt(["A","B"],s) for s in heldout],[B(A(s)) for s in heldout],tag)

def eval_ABC(model,tag):
    return eval_prompts(model,[compose_prompt(["A","B","C"],s) for s in heldout],[C(B(A(s))) for s in heldout],tag)

def train_steps(model,label,fn,domain,n,tag):
    batch=primitive_batch(label,fn,domain)
    curve=[]
    for i in range(1,n+1):
        log("fb_before",tag=tag,step=i,batch=len(batch))
        fb=model.forward_backward(batch,loss_fn="cross_entropy")
        loss=float(fb.metrics.get("loss",float("nan")))
        log("fb_after",tag=tag,step=i,loss=loss)
        op=model.optim_step(lr=PROTOCOL["lr"],grad_clip_norm=PROTOCOL["grad_clip_norm"])
        log("optim_after",tag=tag,step=i,model_step=model.step)
        curve.append({"step":i,"loss":loss})
    return curve

def make_model(sess,checkpoint=None):
    kw=dict(base_model=base,lora=river.LoraConfig(rank=PROTOCOL["lora_rank"],seed=PROTOCOL["seed"]))
    if checkpoint is not None: kw["checkpoint"]=checkpoint
    return sess.create_model(**kw)

results={"protocol_sha256":PH,"base_model":base,"stages":{},"gates":{}}

# WAKE A -> SLEEP checkpoint. Also construct equally-trained wrong ancestor W1.
with client.session(project="metalogic-v2-A") as sess:
    lineage=make_model(sess)
    wrong=make_model(sess)
    train_steps(lineage,"A",A,train_words,PROTOCOL["train_steps_A"],"A_lineage")
    train_steps(wrong,"W1",W1,train_words,PROTOCOL["train_steps_A"],"A_wrong")
    a_eval=eval_A(lineage,"A_lineage_heldout")
    ckA=lineage.save_weights("A_training",mode="training")
    ckW1=wrong.save_weights("W1_training",mode="training")
    results["stages"]["A"]={"heldout":a_eval["accuracy"],"checkpoint":ckA.path,"wrong_checkpoint":ckW1.path}
    log("sleep_A",checkpoint=ckA.path)

# NEW SESSION: resume A. Train only B primitive on A-transformed strings.
# Cold sees same B evidence; wrong resumes W1 then sees same B evidence.
B_domain=[A(s) for s in train_words]
with client.session(project="metalogic-v2-AB") as sess:
    lineage=make_model(sess,ckA.path)
    cold=make_model(sess)
    wrong=make_model(sess,ckW1.path)
    pre={"lineage":eval_AB(lineage,"AB_lineage_pre")["accuracy"],"cold":eval_AB(cold,"AB_cold_pre")["accuracy"],"wrong":eval_AB(wrong,"AB_wrong_pre")["accuracy"]}
    curves={}
    for name,m in [("lineage",lineage),("cold",cold),("wrong",wrong)]:
        curves[name]=[]
        batch=primitive_batch("B",B,B_domain)
        for step in range(1,PROTOCOL["train_steps_new_primitive"]+1):
            log("fb_before",tag=f"AB_{name}",step=step,batch=len(batch))
            fb=m.forward_backward(batch,loss_fn="cross_entropy")
            loss=float(fb.metrics.get("loss",float("nan")))
            log("fb_after",tag=f"AB_{name}",step=step,loss=loss)
            m.optim_step(lr=PROTOCOL["lr"],grad_clip_norm=PROTOCOL["grad_clip_norm"])
            ev=eval_AB(m,f"AB_{name}_step{step}")
            curves[name].append({"step":step,"loss":loss,"accuracy":ev["accuracy"]})
    ckAB=lineage.save_weights("AB_training",mode="training")
    # Build wrong two-generation ancestor: W1 + B has equal new-evidence budget but wrong first ancestor.
    ckW1B=wrong.save_weights("W1B_training",mode="training")
    results["stages"]["AB"]={"pre":pre,"curves":curves,"checkpoint":ckAB.path,"wrong_checkpoint":ckW1B.path}
    log("sleep_AB",checkpoint=ckAB.path)

# NEW SESSION: resume AB. Train only C primitive on AB-transformed strings.
C_domain=[B(A(s)) for s in train_words]
with client.session(project="metalogic-v2-ABC") as sess:
    lineage=make_model(sess,ckAB.path)
    cold=make_model(sess)
    wrong=make_model(sess,ckW1B.path)
    pre={"lineage":eval_ABC(lineage,"ABC_lineage_pre")["accuracy"],"cold":eval_ABC(cold,"ABC_cold_pre")["accuracy"],"wrong":eval_ABC(wrong,"ABC_wrong_pre")["accuracy"]}
    curves={}
    for name,m in [("lineage",lineage),("cold",cold),("wrong",wrong)]:
        curves[name]=[]
        batch=primitive_batch("C",C,C_domain)
        for step in range(1,PROTOCOL["train_steps_new_primitive"]+1):
            log("fb_before",tag=f"ABC_{name}",step=step,batch=len(batch))
            fb=m.forward_backward(batch,loss_fn="cross_entropy")
            loss=float(fb.metrics.get("loss",float("nan")))
            log("fb_after",tag=f"ABC_{name}",step=step,loss=loss)
            m.optim_step(lr=PROTOCOL["lr"],grad_clip_norm=PROTOCOL["grad_clip_norm"])
            ev=eval_ABC(m,f"ABC_{name}_step{step}")
            curves[name].append({"step":step,"loss":loss,"accuracy":ev["accuracy"]})
    finalA=eval_A(lineage,"final_retention_A")
    finalAB=eval_AB(lineage,"final_retention_AB")
    finalABC=eval_ABC(lineage,"final_ABC")
    ckABC=lineage.save_weights("ABC_training",mode="training")
    results["stages"]["ABC"]={"pre":pre,"curves":curves,"retention":{"A":finalA["accuracy"],"AB":finalAB["accuracy"],"ABC":finalABC["accuracy"]},"checkpoint":ckABC.path}

# Precommitted effect metric: area under the two-step accuracy curve, including pre at step 0.
def auc(pre,curve): return pre+sum(x["accuracy"] for x in curve)
def stage_adv(stage):
    d=results["stages"][stage]
    L=auc(d["pre"]["lineage"],d["curves"]["lineage"])
    COLD=auc(d["pre"]["cold"],d["curves"]["cold"])
    WRONG=auc(d["pre"]["wrong"],d["curves"]["wrong"])
    return L,COLD,WRONG
abL,abC,abW=stage_adv("AB")
abcL,abcC,abcW=stage_adv("ABC")
ret=results["stages"]["ABC"]["retention"]
results["gates"]={
  "G1_A_acquired": results["stages"]["A"]["heldout"]>=PROTOCOL["threshold"],
  "G2_AB_lineage_auc_gt_cold": abL>abC,
  "G3_AB_lineage_auc_gt_wrong": abL>abW,
  "G4_ABC_lineage_auc_gt_cold": abcL>abcC,
  "G5_ABC_lineage_auc_gt_wrong": abcL>abcW,
  "G6_A_retained_after_ABC": ret["A"]>=0.50,
  "G7_final_ABC_acquired": ret["ABC"]>=PROTOCOL["threshold"]
}
results["effect"]={"AB":{"lineage_auc":abL,"cold_auc":abC,"wrong_auc":abW},"ABC":{"lineage_auc":abcL,"cold_auc":abcC,"wrong_auc":abcW}}
results["verdict"]="PASS_WAKE_SLEEP_STAIRCASE_V2" if all(results["gates"].values()) else "FAIL_OR_MIXED_WAKE_SLEEP_STAIRCASE_V2"
(OUT/"FINAL_RESULT.json").write_text(json.dumps(results,indent=2))
log("final",verdict=results["verdict"],gates=results["gates"])
print(json.dumps(results,indent=2),flush=True)
