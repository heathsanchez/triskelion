import ast,json,random,collections,itertools
from pathlib import Path
SEED=20261012
CTRL_REPS=2000
SRC=Path('experiments/METALOGIC_ALPHABET_FALSIFICATION_V2.py')
OUT=Path('artifacts/scale_holdout_grammar_v71');OUT.mkdir(parents=True,exist_ok=True)
random.seed(SEED)
SCALE={'math':'task','coding':'task','science':'task','search':'task','collider':'representation','representation':'representation','ecology':'control','river':'architecture','memory':'architecture','development':'architecture','system':'architecture'}

def load_events():
 t=ast.parse(SRC.read_text())
 for n in t.body:
  if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='E' for x in n.targets): return ast.literal_eval(n.value)
 raise RuntimeError('E missing')
E=load_events(); P=[tuple(x[3]) for x in E]; D=[x[0] for x in E]; S=[SCALE[d] for d in D]; SCALES=sorted(set(S))

def grams(p,k): return [tuple(p[i:i+k]) for i in range(len(p)-k+1)]
def dictionary(ids):
 c=collections.Counter(); meta=collections.defaultdict(set)
 for i in ids:
  for k in range(2,min(5,len(P[i]))+1):
   for m in set(grams(P[i],k)): c[m]+=1;meta[m].add(D[i])
 return sorted([m for m,n in c.items() if n>=3 and len(meta[m])>=2],key=lambda x:(-len(x),x))
def clen(p,dic):
 i=0;z=0
 while i<len(p):
  hit=next((m for m in dic if tuple(p[i:i+len(m)])==m),None)
  if hit:i+=len(hit)
  else:i+=1
  z+=1
 return z

def train_ngram(ids):
 nxt={1:collections.defaultdict(collections.Counter),2:collections.defaultdict(collections.Counter),3:collections.defaultdict(collections.Counter)}
 uni=collections.Counter()
 for i in ids:
  p=P[i];uni.update(p)
  for j in range(1,len(p)):
   for k in (1,2,3):
    if j>=k:nxt[k][tuple(p[j-k:j])][p[j]]+=1
 return nxt,uni
def predict(prefix,model):
 nxt,uni=model
 for k in (3,2,1):
  if len(prefix)>=k and tuple(prefix[-k:]) in nxt[k]: return nxt[k][tuple(prefix[-k:])].most_common(1)[0][0]
 return uni.most_common(1)[0][0]

def eval_pred(train,test):
 m=train_ngram(train);base=m[1].most_common(1)[0][0];a=b=n=0
 rows=[]
 for i in test:
  p=P[i]
  for j in range(1,len(p)):
   y=p[j];q=predict(p[:j],m);a+=q==y;b+=base==y;n+=1;rows.append((q,y,base))
 return a/n if n else 0,b/n if n else 0,rows

folds=[];raw_total=comp_total=0;correct=base_correct=pred_n=0
for sc in SCALES:
 tr=[i for i in range(len(P)) if S[i]!=sc];te=[i for i in range(len(P)) if S[i]==sc]
 dic=dictionary(tr);raw=sum(len(P[i]) for i in te);comp=sum(clen(P[i],dic) for i in te)
 acc,base,rows=eval_pred(tr,te)
 folds.append({'held_scale':sc,'train_events':len(tr),'test_events':len(te),'dictionary_size':len(dic),'raw':raw,'compressed':comp,'compression':(raw-comp)/raw,'next_op_accuracy':acc,'majority_accuracy':base})
 raw_total+=raw;comp_total+=comp;correct+=sum(q==y for q,y,_ in rows);base_correct+=sum(z==y for _,y,z in rows);pred_n+=len(rows)
compression=(raw_total-comp_total)/raw_total;acc=correct/pred_n;base=base_correct/pred_n

# Whole-scale shuffled control: preserve operator multiset and program length in training traces only.
ctrl_comp=[];ctrl_acc=[]
for rep in range(CTRL_REPS):
 rr=cc=0;ca=cb=nn=0
 for sc in SCALES:
  tr=[i for i in range(len(P)) if S[i]!=sc];te=[i for i in range(len(P)) if S[i]==sc]
  orig={i:P[i] for i in tr}
  for i in tr:
   q=list(P[i]);random.shuffle(q);P[i]=tuple(q)
  dic=dictionary(tr);m=train_ngram(tr);baseop=m[1].most_common(1)[0][0]
  for i in te:
   rr+=len(P[i]);cc+=clen(P[i],dic)
   for j in range(1,len(P[i])):
    y=P[i][j];ca+=predict(P[i][:j],m)==y;cb+=baseop==y;nn+=1
  for i,v in orig.items():P[i]=v
 ctrl_comp.append((rr-cc)/rr);ctrl_acc.append(ca/nn if nn else 0)
ctrl_comp_mean=sum(ctrl_comp)/len(ctrl_comp);ctrl_acc_mean=sum(ctrl_acc)/len(ctrl_acc)
comp_p=(1+sum(x>=compression for x in ctrl_comp))/(CTRL_REPS+1);acc_p=(1+sum(x>=acc for x in ctrl_acc))/(CTRL_REPS+1)
R={'seed':SEED,'control_reps':CTRL_REPS,'folds':folds,'whole_scale_compression':compression,'shuffled_compression_mean':ctrl_comp_mean,'compression_p':comp_p,'whole_scale_next_op_accuracy':acc,'majority_accuracy':base,'shuffled_next_op_mean':ctrl_acc_mean,'next_op_p':acc_p}
R['gates']={'every_scale_compresses':all(f['compression']>0 for f in folds),'compression_ge_20pct':compression>=0.20,'compression_beats_shuffle':compression>=ctrl_comp_mean+0.08 and comp_p<=0.01,'prediction_beats_majority':acc>=base+0.15,'prediction_beats_shuffle':acc>=ctrl_acc_mean+0.15 and acc_p<=0.01}
R['verdict']='PASS_SCALE_HOLDOUT_GRAMMAR_V71' if all(R['gates'].values()) else 'MIXED_SCALE_HOLDOUT_GRAMMAR_V71'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))
