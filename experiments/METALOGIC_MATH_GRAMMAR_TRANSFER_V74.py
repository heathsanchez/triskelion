import ast,json,math,random,itertools,collections
from pathlib import Path
SEED=20261015
CTRL=2000
random.seed(SEED)
SRC=Path('experiments/METALOGIC_ALPHABET_FALSIFICATION_V2.py')
OUT=Path('artifacts/math_grammar_transfer_v74');OUT.mkdir(parents=True,exist_ok=True)

def load_events():
 t=ast.parse(SRC.read_text())
 for n in t.body:
  if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='E' for x in n.targets):
   return ast.literal_eval(n.value)
 raise RuntimeError('E not found')
E=load_events()
OPS=['DISTINGUISH','GENERATE','RELATE','PROBE','CONSTRAIN','SELECT','COMPOSE','RETAIN','TRANSDUCE','RECURSE']
train=[x for x in E if x[0]!='math']
test=[x for x in E if x[0]=='math']

def grams(p,k):return [tuple(p[i:i+k]) for i in range(len(p)-k+1)]
def infer_motifs(events):
 c=collections.Counter(); dm=collections.defaultdict(set)
 for d,desc,target,p in events:
  for k in range(2,min(4,len(p))+1):
   for m in set(grams(p,k)): c[m]+=1; dm[m].add(d)
 cand=[]
 for m,n in c.items():
  standalone=n*(len(m)-1)-(len(m)+1)
  if n>=3 and len(dm[m])>=2 and standalone>0:cand.append(m)
 cand=sorted(cand,key=lambda m:(-len(m),m))
 baseline=sum(len(x[3]) for x in events)
 def parse_cost(p,dic):
  n=len(p);dp=[999]*(n+1);dp[n]=0
  for i in range(n-1,-1,-1):
   dp[i]=1+dp[i+1]
   for m in dic:
    if tuple(p[i:i+len(m)])==m:dp[i]=min(dp[i],1+dp[i+len(m)])
  return dp[0]
 def total(dic):return sum(parse_cost(x[3],dic) for x in events)+sum(len(m)+1 for m in dic)
 if len(cand)<=22:
  best=(baseline,())
  for mask in range(1<<len(cand)):
   dic=tuple(cand[j] for j in range(len(cand)) if mask>>j&1);cc=total(dic)
   if cc<best[0] or (cc==best[0] and (len(dic),dic)<(len(best[1]),best[1])):best=(cc,dic)
  return list(best[1])
 dic=[];cur=baseline
 while True:
  opts=sorted((total(dic+[m]),m) for m in cand if m not in dic)
  if not opts or opts[0][0]>=cur:break
  cur,m=opts[0];dic.append(m)
 return dic

def transition_counts(events):
 uni=collections.Counter();bi=collections.Counter();starts=collections.Counter();lens=collections.Counter()
 for _,_,_,p in events:
  lens[len(p)]+=1
  if p:starts[p[0]]+=1
  for a in p:uni[a]+=1
  for a,b in zip(p,p[1:]):bi[(a,b)]+=1
 return uni,bi,starts,lens

def score_program(p,motifs,counts,use_motifs=True):
 uni,bi,starts,lens=counts;N=sum(uni.values()); B=sum(bi.values())
 # Smoothed negative log likelihood plus a real learned-motif compression bonus.
 s=-math.log((starts[p[0]]+1)/(sum(starts.values())+len(OPS)))
 s+=-math.log((lens[len(p)]+1)/(sum(lens.values())+5))
 for a in p:s+=0.25*(-math.log((uni[a]+1)/(N+len(OPS))))
 for a,b in zip(p,p[1:]):s+=-math.log((bi[(a,b)]+1)/(sum(v for (x,y),v in bi.items() if x==a)+len(OPS)))
 if use_motifs:
  # reward non-overlapping maximum-length motif coverage, learned only from non-math
  i=0;covered=0
  while i<len(p):
   hits=[m for m in motifs if tuple(p[i:i+len(m)])==m]
   if hits:
    m=max(hits,key=len);covered+=len(m)-1;i+=len(m)
   else:i+=1
  s-=1.25*covered
 return s

def candidates_for(gold,target):
 L=len(gold)
 # all same-length programs over operators seen in training, but require target appears at least once;
 # for L=4 this is <=3439 candidates after filtering, deterministic and exhaustive.
 return [p for p in itertools.product(OPS,repeat=L) if target in p]

def evaluate(events,motifs,counts,use_motifs):
 rows=[]
 for d,desc,target,g in events:
  g=tuple(g);cs=candidates_for(g,target)
  scored=sorted((score_program(p,motifs,counts,use_motifs),p) for p in cs)
  # deterministic midrank among score ties
  gs=score_program(g,motifs,counts,use_motifs)
  better=sum(s<gs-1e-12 for s,p in scored);equal=sum(abs(s-gs)<=1e-12 for s,p in scored)
  rank=better+(equal+1)/2
  rows.append({'description':desc,'target':target,'gold':list(g),'candidate_count':len(cs),'rank':rank,'percentile':1-(rank-1)/len(cs),'top10':rank<=10,'top50':rank<=50})
 return rows

def summarize(rows):
 return {'mean_percentile':sum(r['percentile'] for r in rows)/len(rows),'mean_reciprocal_rank':sum(1/r['rank'] for r in rows)/len(rows),'top10':sum(r['top10'] for r in rows),'top50':sum(r['top50'] for r in rows)}

motifs=infer_motifs(train);counts=transition_counts(train)
macro=evaluate(test,motifs,counts,True);primitive=evaluate(test,[],counts,False)
SM=summarize(macro);SP=summarize(primitive)
# Null: preserve every training program's operator multiset and length but destroy order, re-infer motifs/transitions, score held-out math.
null=[]
for _ in range(CTRL):
 sh=[]
 for d,desc,target,p in train:
  q=list(p);random.shuffle(q);sh.append((d,desc,target,q))
 mm=infer_motifs(sh);cc=transition_counts(sh);rr=evaluate(test,mm,cc,True);null.append(summarize(rr)['mean_percentile'])
null_mean=sum(null)/len(null);pval=(1+sum(x>=SM['mean_percentile'] for x in null))/(CTRL+1)
# Ablate each learned motif one at a time.
abl=[]
for m in motifs:
 rr=evaluate(test,[x for x in motifs if x!=m],counts,True);abl.append({'removed':list(m),**summarize(rr)})
R={'seed':SEED,'control_reps':CTRL,'train_n':len(train),'heldout_math_n':len(test),'learned_motifs':[list(x) for x in motifs],'macro':SM,'primitive':SP,'rows_macro':macro,'rows_primitive':primitive,'shuffle_mean_percentile':null_mean,'shuffle_p':pval,'ablations':abl}
R['gates']={
 'all_math_hidden':len(test)==5 and all(x[0]!='math' for x in train),
 'motifs_nonempty':len(motifs)>=2,
 'macro_beats_primitive':SM['mean_percentile']>=SP['mean_percentile']+0.05,
 'macro_high_rank':SM['mean_percentile']>=0.80,
 'beats_shuffle':SM['mean_percentile']>=null_mean+0.05 and pval<=0.01,
 'at_least_one_top10':SM['top10']>=1,
}
R['verdict']='PASS_MATH_GRAMMAR_TRANSFER_V74' if all(R['gates'].values()) else 'MIXED_MATH_GRAMMAR_TRANSFER_V74'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))
