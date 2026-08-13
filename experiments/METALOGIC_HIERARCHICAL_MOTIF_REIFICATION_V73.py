import ast,json,random,collections,itertools
from pathlib import Path
SEED=20261014
CTRL=5000
SRC=Path('experiments/METALOGIC_ALPHABET_FALSIFICATION_V2.py')
OUT=Path('artifacts/hierarchical_motif_reification_v73');OUT.mkdir(parents=True,exist_ok=True)
random.seed(SEED)
SCALE={'math':'task','coding':'task','science':'task','search':'task','collider':'representation','representation':'representation','ecology':'control','river':'architecture','memory':'architecture','development':'architecture','system':'architecture'}
BASE=[('CONSTRAIN','SELECT','RETAIN'),('CONSTRAIN','SELECT'),('DISTINGUISH','TRANSDUCE'),('RELATE','COMPOSE'),('SELECT','RETAIN')]
NAMES={m:'K'+str(i+1) for i,m in enumerate(BASE)}

def load_events():
 t=ast.parse(SRC.read_text())
 for n in t.body:
  if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='E' for x in n.targets): return ast.literal_eval(n.value)
 raise RuntimeError
E=load_events();P=[tuple(x[3]) for x in E];D=[x[0] for x in E];S=[SCALE[d] for d in D]

def reify(p,motifs,names):
 # longest-first deterministic parsing
 ms=sorted(motifs,key=lambda m:(-len(m),m));out=[];i=0
 while i<len(p):
  hit=next((m for m in ms if tuple(p[i:i+len(m)])==m),None)
  if hit:out.append(names[hit]);i+=len(hit)
  else:out.append(p[i]);i+=1
 return tuple(out)
def grams(p,k):return [tuple(p[i:i+k]) for i in range(len(p)-k+1)]
def mine(programs):
 c=collections.Counter();dom=collections.defaultdict(set);sc=collections.defaultdict(set)
 for i,p in enumerate(programs):
  for k in (2,3,4):
   if len(p)<k:continue
   for m in set(grams(p,k)):c[m]+=1;dom[m].add(D[i]);sc[m].add(S[i])
 rows=[]
 for m,n in c.items():
  if n>=3 and len(dom[m])>=2 and len(sc[m])>=2:
   rows.append({'motif':m,'support':n,'domains':len(dom[m]),'scales':len(sc[m])})
 return sorted(rows,key=lambda r:(-r['support'],-r['scales'],-r['domains'],r['motif']))

Q=[reify(p,BASE,NAMES) for p in P];OBS=mine(Q)
# Higher-order score rewards support, cross-domain/scale, and actual use of at least one macro.
def score(rows):
 vals=[]
 for r in rows:
  if any(str(x).startswith('K') for x in r['motif']): vals.append((r['support']-2)*(r['domains']-1)*(r['scales']-1))
 return sum(vals),len(vals)
obs_score,obs_n=score(OBS)

# Matched random chunkings: preserve the same motif lengths and corpus, but choose random observed ngrams
# with the same lengths; reify and score exactly as the discovered basis.
pools={k:sorted(set(m for p in P for m in grams(p,k))) for k in (2,3)}
ctrl=[];ctrl_n=[]
for _ in range(CTRL):
 chosen=[]
 # V72 basis has one length3 and four length2 macros.
 chosen.append(random.choice(pools[3])); chosen+=random.sample(pools[2],4)
 chosen=list(dict.fromkeys(chosen))
 names={m:'K'+str(i+1) for i,m in enumerate(chosen)}
 z=[reify(p,chosen,names) for p in P];r=mine(z);s,n=score(r);ctrl.append(s);ctrl_n.append(n)
pval=(1+sum(x>=obs_score for x in ctrl))/(CTRL+1);mean=sum(ctrl)/len(ctrl)

# Whole-scale holdout: basis remains frozen from V72; ask whether second-level motifs containing macros
# recur in every scale and whether at least one second-level motif spans >=3 scales.
macro_rows=[r for r in OBS if any(str(x).startswith('K') for x in r['motif'])]
scale_hits={sc:sum(1 for i,p in enumerate(Q) if S[i]==sc and any(tuple(r['motif']) in grams(p,len(r['motif'])) for r in macro_rows)) for sc in sorted(set(S))}
R={'seed':SEED,'base_motifs':[list(x) for x in BASE],'macro_map':{'K'+str(i+1):list(m) for i,m in enumerate(BASE)},'reified_programs':[list(x) for x in Q],'higher_order_motifs':[{'motif':list(r['motif']),'support':r['support'],'domains':r['domains'],'scales':r['scales']} for r in macro_rows],'higher_order_score':obs_score,'higher_order_count':obs_n,'random_chunk_score_mean':mean,'random_chunk_count_mean':sum(ctrl_n)/len(ctrl_n),'random_chunk_p':pval,'scale_hits':scale_hits}
R['gates']={'higher_order_exists':obs_n>=2,'higher_order_cross_scale':any(r['scales']>=3 for r in macro_rows),'beats_random_chunking':obs_score>=mean*1.5 and pval<=0.01,'every_scale_has_macro_hierarchy':all(v>0 for v in scale_hits.values())}
R['verdict']='PASS_HIERARCHICAL_MOTIF_REIFICATION_V73' if all(R['gates'].values()) else 'MIXED_HIERARCHICAL_MOTIF_REIFICATION_V73'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))