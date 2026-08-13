import os, json, hashlib, random, platform, importlib.metadata
from pathlib import Path
import river_client as river
from transformers import AutoTokenizer

PROTOCOL = {
  "name":"METALOGIC_NEURAL_DEVELOPMENTAL_STAIRCASE_V1",
  "date":"2026-08-13",
  "seed":20260813,
  "allowed_base_models":["Qwen/Qwen3.6-35B-A3B-FP8","Qwen/Qwen3.5-9B"],
  "lora_rank":8,
  "lr":2e-4,
  "grad_clip_norm":1.0,
  "max_tokens":40,
  "train_steps_per_dose":4,
  "batch_size":4,
  "max_doses":4,
  "heldout_n":8,
  "threshold":0.75,
  "stages":["A","AB","ABC"],
  "controls":["LINEAGE","COLD","WRONG_LINEAGE"],
  "claim_boundary":"Synthetic mechanistic test of neural developmental compounding; not external-task or open-ended self-improvement evidence."
}
OUT=Path("artifacts/neural_staircase_v1"); OUT.mkdir(parents=True,exist_ok=True)
canon=json.dumps(PROTOCOL,sort_keys=True,separators=(",",":")); PH=hashlib.sha256(canon.encode()).hexdigest()
(OUT/"PRECOMMIT.json").write_text(json.dumps({"protocol_sha256":PH,"protocol":PROTOCOL},indent=2))
print("PROTOCOL_SHA256",PH)

api_key=os.environ.get("RIVER_API_KEY","").strip()
if not api_key: raise RuntimeError("RIVER_API_KEY missing")
client=river.Client(api_key=api_key)
if client.health_check() is not True: raise RuntimeError("River health check failed")
caps=list(client.get_capabilities())
base=next((m for m in PROTOCOL["allowed_base_models"] if m in caps),None)
if base is None: raise RuntimeError(f"No predeclared model available. capabilities={caps}")
print("BASE_MODEL",base)

tok=AutoTokenizer.from_pretrained(base,trust_remote_code=True)
eos=tok.eos_token_id
if eos is None: raise RuntimeError("No EOS token")

def fA(s): return "ka-"+s
def fB(s): return s[::-1]
def fC(s): return s+"-zu"
def target(stage,s):
    if stage=="A": return fA(s)
    if stage=="AB": return fB(fA(s))
    if stage=="ABC": return fC(fB(fA(s)))
    raise KeyError(stage)

def prompt(stage,s): return f"Policy {stage}\ninput={s}\nReturn exactly the transformed string."

def datum(p,c):
    pids=tok(p,add_special_tokens=False)["input_ids"]
    cids=tok(" "+c,add_special_tokens=False)["input_ids"]+[eos]
    ids=pids+cids; t=ids[1:]+[eos]
    n=max(0,len(pids)-1); w=[0.0]*n+[1.0]*(len(t)-n)
    return {"input_ids":ids,"target_tokens":t,"weights":w}

def extract(x):
    if isinstance(x,(list,tuple)) and x: x=x[0]
    if isinstance(x,str): return x.strip()
    if hasattr(x,"text"): return str(x.text).strip()
    if isinstance(x,dict):
        for k in ("text","output_text","completion"):
            if k in x: return str(x[k]).strip()
    return str(x).strip()

def sample(model,p): return extract(model.sample(p,max_tokens=PROTOCOL["max_tokens"],temperature=0.0,stop=["\n"]))

def eval_stage(model,stage,words):
    rows=[]
    for s in words:
        y=sample(model,prompt(stage,s)); gold=target(stage,s)
        rows.append({"input":s,"output":y,"gold":gold,"ok":y==gold})
    return {"accuracy":sum(r["ok"] for r in rows)/len(rows),"rows":rows}

def train_dose(model,stage,examples,dose_index):
    rng=random.Random(PROTOCOL["seed"]+1000*PROTOCOL["stages"].index(stage)+dose_index)
    losses=[]
    for step in range(PROTOCOL["train_steps_per_dose"]):
        batch=[rng.choice(examples) for _ in range(PROTOCOL["batch_size"])]
        data=[datum(prompt(stage,s),target(stage,s)) for s in batch]
        fb=model.forward_backward(data=data,loss_fn="cross_entropy")
        m=getattr(fb,"metrics",{})
        raw=m.get("loss") if isinstance(m,dict) else getattr(m,"loss",None)
        try: losses.append(float(raw))
        except Exception: losses.append(None)
        model.optim_step(lr=PROTOCOL["lr"],grad_clip_norm=PROTOCOL["grad_clip_norm"])
    return losses

train_words=["amber","quiet","silver","paper","winter","copper","scarlet","gentle","marble","rapid","bright","soft","blue","little","warm","clear"]
heldout=["violet","hidden","green","crimson","golden","silent","orange","secret"]
wrongA_words=["north","south","east","west","alpha","beta","gamma","delta"]

def wp(stage,s): return f"Policy W\ninput={s}\nReturn exactly the transformed string."
def wt(s): return s.upper()
def train_wrong(model):
    rng=random.Random(PROTOCOL["seed"]+777)
    for dose in range(2):
        for step in range(PROTOCOL["train_steps_per_dose"]):
            batch=[rng.choice(wrongA_words) for _ in range(PROTOCOL["batch_size"])]
            data=[datum(wp("W",s),wt(s)) for s in batch]
            model.forward_backward(data=data,loss_fn="cross_entropy")
            model.optim_step(lr=PROTOCOL["lr"],grad_clip_norm=PROTOCOL["grad_clip_norm"])

results={"protocol_sha256":PH,"base_model":base,"controls":{},"gates":{}}
with client.session(project="metalogic-neural-developmental-staircase-v1") as sess:
    lineage=sess.create_model(base_model=base,lora=river.LoraConfig(rank=PROTOCOL["lora_rank"],seed=PROTOCOL["seed"]))
    coldA=sess.create_model(base_model=base,lora=river.LoraConfig(rank=PROTOCOL["lora_rank"],seed=PROTOCOL["seed"]))
    coldAB=sess.create_model(base_model=base,lora=river.LoraConfig(rank=PROTOCOL["lora_rank"],seed=PROTOCOL["seed"]))
    coldABC=sess.create_model(base_model=base,lora=river.LoraConfig(rank=PROTOCOL["lora_rank"],seed=PROTOCOL["seed"]))
    wrongAB=sess.create_model(base_model=base,lora=river.LoraConfig(rank=PROTOCOL["lora_rank"],seed=PROTOCOL["seed"]))
    wrongABC=sess.create_model(base_model=base,lora=river.LoraConfig(rank=PROTOCOL["lora_rank"],seed=PROTOCOL["seed"]))

    A_curve=[]
    for dose in range(1,PROTOCOL["max_doses"]+1):
        train_dose(lineage,"A",train_words,dose); train_dose(coldA,"A",train_words,dose)
        ev=eval_stage(lineage,"A",heldout); A_curve.append({"dose":dose,"accuracy":ev["accuracy"]})
        if ev["accuracy"]>=PROTOCOL["threshold"]: break
    A_dose=A_curve[-1]["dose"] if A_curve[-1]["accuracy"]>=PROTOCOL["threshold"] else None
    ckA=lineage.save_weights("stage_A",mode="inference")

    train_wrong(wrongAB); train_wrong(wrongABC)

    def learn_curve(model,stage):
        curve=[]
        for dose in range(1,PROTOCOL["max_doses"]+1):
            train_dose(model,stage,train_words,dose)
            ev=eval_stage(model,stage,heldout); curve.append({"dose":dose,"accuracy":ev["accuracy"]})
            if ev["accuracy"]>=PROTOCOL["threshold"]: return curve,dose
        return curve,None
    AB_lineage_curve,AB_lineage_dose=learn_curve(lineage,"AB")
    AB_cold_curve,AB_cold_dose=learn_curve(coldAB,"AB")
    AB_wrong_curve,AB_wrong_dose=learn_curve(wrongAB,"AB")
    ckAB=lineage.save_weights("stage_AB",mode="inference")

    train_wrong(wrongABC)

    ABC_lineage_curve,ABC_lineage_dose=learn_curve(lineage,"ABC")
    ABC_cold_curve,ABC_cold_dose=learn_curve(coldABC,"ABC")
    ABC_wrong_curve,ABC_wrong_dose=learn_curve(wrongABC,"ABC")
    ckABC=lineage.save_weights("stage_ABC",mode="inference")

    finalA=eval_stage(lineage,"A",heldout)
    finalAB=eval_stage(lineage,"AB",heldout)
    finalABC=eval_stage(lineage,"ABC",heldout)

    results["controls"]={
      "A":{"lineage_curve":A_curve,"dose_to_threshold":A_dose},
      "AB":{"lineage_curve":AB_lineage_curve,"cold_curve":AB_cold_curve,"wrong_curve":AB_wrong_curve,
             "lineage_dose":AB_lineage_dose,"cold_dose":AB_cold_dose,"wrong_dose":AB_wrong_dose},
      "ABC":{"lineage_curve":ABC_lineage_curve,"cold_curve":ABC_cold_curve,"wrong_curve":ABC_wrong_curve,
              "lineage_dose":ABC_lineage_dose,"cold_dose":ABC_cold_dose,"wrong_dose":ABC_wrong_dose},
      "retention":{"A":finalA["accuracy"],"AB":finalAB["accuracy"],"ABC":finalABC["accuracy"]},
      "checkpoints":{"A":repr(ckA),"AB":repr(ckAB),"ABC":repr(ckABC)}
    }

def better(x,y):
    if x is None: return False
    if y is None: return True
    return x<y
results["gates"]={
  "G1_A_acquired": A_dose is not None,
  "G2_AB_lineage_faster_than_cold": better(AB_lineage_dose,AB_cold_dose),
  "G3_AB_lineage_faster_than_wrong": better(AB_lineage_dose,AB_wrong_dose),
  "G4_ABC_lineage_faster_than_cold": better(ABC_lineage_dose,ABC_cold_dose),
  "G5_ABC_lineage_faster_than_wrong": better(ABC_lineage_dose,ABC_wrong_dose),
  "G6_no_catastrophic_loss_A": results["controls"]["retention"]["A"]>=0.50,
  "G7_final_ABC_acquired": results["controls"]["retention"]["ABC"]>=PROTOCOL["threshold"]
}
results["verdict"]="PASS_NEURAL_DEVELOPMENTAL_STAIRCASE_V1" if all(results["gates"].values()) else "FAIL_OR_MIXED_NEURAL_DEVELOPMENTAL_STAIRCASE_V1"
(OUT/"FINAL_RESULT.json").write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
print("FINAL_VERDICT",results["verdict"])
