import ast,json,random,collections,itertools
from pathlib import Path
SEED=20261013
CTRL=1000
SRC=Path('experiments/METALOGIC_ALPHABET_FALSIFICATION_V2.py')
OUT=Path('artifacts/mdl_motif_basis_v72');OUT.mkdir(parents=True,exist_ok=True)
random.seed(SEED)
SCALE={'math':'task','coding':'task','science':'task','search':'task','collider':'representation','representation':'representation','ecology':'control','river':'architecture','memory':'architecture','development':'architecture','system':'architecture'}

def load_events():
 t=ast.parse(SRC.read_text())
 for n in t.body:
  if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='E' for x in n.targets): return ast.literal_eval(n.value)
 raise RuntimeError
E=load_events();P=[tuple(x[3]) for x in E];D=[x[0] for x in E];S=[SCALE[d] for d in D];SCALES=sorted(set(S))

def grams(p,k):return [tuple(p[i:i+k]) for i in range(len(p)-k+1)]
def pool(programs,domains,scales):
 c=collections.Counter();dm=collections.defaultdict(set);sm=collections.defaultdict(set)
 for i,p in enumerate(programs):
  for k in range(2,min(4,len(p))+1):
   for m in set(grams(p,k)):c[m]+=1;dm[m].add(domains[i]);sm[m].add(scales[i])
 out=[]
 for m,n in c.items():
  standalone=n*(len(m)-1)-(len(m)+1)
  if n>=3 and len(dm[m])>=2 and len(sm[m])>=2 and standalone>0:out.append(m)
 return sorted(out,key=lambda m:(-len(m),m))

def parse_cost(p,dic):
 n=len(p);dp=[99]*(n+1);dp[n]=0
 for i in range(n-1,-1,-1):
  dp[i]=1+dp[i+1]
  for m in dic:
   if tuple(p[i:i+len(m)])==m:dp[i]=min(dp[i],1+dp[i+len(m)])
 return dp[0]
def total_cost(programs,dic):return sum(parse_cost(p,dic) for p in programs)+sum(len(m)+1 for m in dic)

def infer(programs,domains,scales):
 cand=pool(programs,domains,scales);baseline=sum(len(p) for p in programs)
 # Exact subset search if candidate pool is modest; otherwise deterministic forward/backward MDL.
 if len(cand)<=22:
  best=(baseline,())
  for mask in range(1<<len(cand)):
   dic=tuple(cand[j] for j in range(len(cand)) if mask>>j&1);c=total_cost(programs,dic)
   if c<best[0] or (c==best[0] and (len(dic),dic)<(len(best[1]),best[1])):best=(c,dic)
  exact=True
 else:
  dic=[];cur=baseline
  while True:
   opts=[(total_cost(programs,dic+[m]),m) for m in cand if m not in dic];opts.sort()
   if not opts or opts[0][0]>=cur:break
   cur,m=opts[0];dic.append(m)
  changed=True
  while changed:
   changed=False
   for m in list(dic):
    q=[x for x in dic if x!=m];c=total_cost(programs,q)
    if c<cur:dic=q;cur=c;changed=True;break
  best=(cur,tuple(dic));exact=False
 return {'candidate_count':len(cand),'dictionary':best[1],'cost':best[0],'baseline':baseline,'saving':(baseline-best[0])/baseline,'exact':exact}

full=infer(P,D,S)
# Whole-scale omission: infer independently without one scale; report overlap and held-scale compression using that dictionary.
folds=[]
for sc in SCALES:
 ids=[i for i in range(len(P)) if S[i]!=sc];te=[i for i in range(len(P)) if S[i]==sc]
 r=infer([P[i] for i in ids],[D[i] for i in ids],[S[i] for i in ids]);dic=list(r['dictionary'])
 raw=sum(len(P[i]) for i in te);enc=sum(parse_cost(P[i],dic) for i in te)
 a=set(full['dictionary']);b=set(dic);jac=len(a&b)/len(a|b) if a|b else 1
 folds.append({'held_scale':sc,'train_dictionary':[list(x) for x in dic],'jaccard_to_full':jac,'held_raw':raw,'held_encoded':enc,'held_compression':(raw-enc)/raw if raw else 0})

# Null repeats the full induction on within-program order shuffles, preserving operators and lengths.
ctrl=[];sizes=[]
for _ in range(CTRL):
 q=[]
 for p in P:
  z=list(p);random.shuffle(z);q.append(tuple(z))
 r=infer(q,D,S);ctrl.append(r['saving']);sizes.append(len(r['dictionary']))
mean=sum(ctrl)/len(ctrl);pval=(1+sum(x>=full['saving'] for x in ctrl))/(CTRL+1)
R={'seed':SEED,'control_reps':CTRL,'full':{'candidate_count':full['candidate_count'],'dictionary':[list(x) for x in full['dictionary']],'cost':full['cost'],'baseline':full['baseline'],'saving':full['saving'],'exact':full['exact']},'scale_folds':folds,'shuffle_saving_mean':mean,'shuffle_dictionary_size_mean':sum(sizes)/len(sizes),'shuffle_p':pval}
R['gates']={'basis_nonempty':len(full['dictionary'])>=2,'basis_small':len(full['dictionary'])<=7,'mdl_saving_ge_10pct':full['saving']>=0.10,'beats_shuffle':full['saving']>=mean+0.07 and pval<=0.01,'every_scale_transfer_positive':all(f['held_compression']>0 for f in folds)}
R['verdict']='PASS_MDL_MOTIF_BASIS_V72' if all(R['gates'].values()) else 'MIXED_MDL_MOTIF_BASIS_V72'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))
