import ast, copy, itertools, json, math, random, collections
from fractions import Fraction
from pathlib import Path

SEED=20261016
INSTANCES=20
SHUFFLE_REPS=500
LABEL_REPS=500
MAX_LEN=5
SRC=Path('experiments/METALOGIC_ALPHABET_FALSIFICATION_V2.py')
OUT=Path('artifacts/executable_math_control_v75');OUT.mkdir(parents=True,exist_ok=True)
OPS=['DISTINGUISH','GENERATE','RELATE','PROBE','CONSTRAIN','SELECT','COMPOSE','RETAIN','TRANSDUCE','RECURSE']
random.seed(SEED)

# Frozen scientific gates.
GATESPEC={
 'all_families_solvable':True,
 'beats_random_expectation':True,
 'beats_unigram':True,
 'shuffle_p_max':0.05,
 'label_permutation_p_max':0.05,
}

def load_nonmath():
 t=ast.parse(SRC.read_text())
 for n in t.body:
  if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='E' for x in n.targets):
   E=ast.literal_eval(n.value);return [tuple(x[3]) for x in E if x[0]!='math']
 raise RuntimeError('E not found')
TRAIN=load_nonmath()

def fit_bigram(seqs):
 c=collections.Counter();ctx=collections.Counter();alpha=1.0;v=len(OPS)+1
 for s in seqs:
  z=('^',)+tuple(s)+('$',)
  for a,b in zip(z,z[1:]):c[a,b]+=1;ctx[a]+=1
 def nll(p):
  z=('^',)+tuple(p)+('$',);r=0.0
  for a,b in zip(z,z[1:]):r-=math.log((c[a,b]+alpha)/(ctx[a]+alpha*v))
  return r
 return nll

def fit_unigram(seqs):
 c=collections.Counter(x for s in seqs for x in s);n=sum(c.values());alpha=1.0;v=len(OPS)
 def nll(p):return sum(-math.log((c[x]+alpha)/(n+alpha*v)) for x in p)+0.2*len(p)
 return nll

# ---------- independent exact ground truth ----------
def brute_components(n,edges):
 a=[set() for _ in range(n)]
 for u,v in edges:a[u].add(v);a[v].add(u)
 seen=set();k=0
 for s in range(n):
  if s in seen:continue
  k+=1;st=[s];seen.add(s)
  while st:
   u=st.pop()
   for v in a[u]:
    if v not in seen:seen.add(v);st.append(v)
 return k

def brute_rank(M):
 A=[[Fraction(x) for x in r] for r in M];m=len(A);n=len(A[0]);r=0
 for c in range(n):
  p=next((i for i in range(r,m) if A[i][c]),None)
  if p is None:continue
  A[r],A[p]=A[p],A[r];q=A[r][c];A[r]=[x/q for x in A[r]]
  for i in range(m):
   if i!=r and A[i][c]:
    q=A[i][c];A[i]=[x-q*y for x,y in zip(A[i],A[r])]
  r+=1
  if r==m:break
 return r

def canon_rotation(x):return min(tuple(x[i:]+x[:i]) for i in range(len(x)))
def brute_reach(n,edges,s,t):
 a=[[] for _ in range(n)]
 for u,v in edges:a[u].append(v)
 seen={s};st=[s]
 while st:
  u=st.pop()
  for v in a[u]:
   if v not in seen:seen.add(v);st.append(v)
 return t in seen

def brute_modrec(a,b,m,x,n):
 for _ in range(n):x=(a*x+b)%m
 return x

# ---------- frozen instance generator ----------
def make_instances(fam,seed):
 r=random.Random(seed);out=[]
 for _ in range(INSTANCES):
  if fam=='parity':
   n=r.randint(5,18);x=[r.randrange(2) for _ in range(n)]
   y=sum(x[i]!=x[i+1] for i in range(n-1))%2;out.append({'raw':x,'truth':y})
  elif fam=='components':
   n=r.randint(5,9);edges=[]
   for i in range(n):
    for j in range(i+1,n):
     if r.random()<0.23:edges.append((i,j))
   out.append({'raw':(n,edges),'truth':brute_components(n,edges)})
  elif fam=='rank':
   m=r.randint(3,5);n=r.randint(3,5);M=[[r.randint(-3,3) for _ in range(n)] for _ in range(m)]
   if r.random()<0.5 and m>1:M[-1]=M[0][:]
   out.append({'raw':M,'truth':brute_rank(M)})
  elif fam=='orbits':
   k=r.randint(3,5);rows=[]
   for _j in range(r.randint(6,12)):
    z=[r.randrange(4) for _q in range(k)]
    if rows and r.random()<0.35:
     base=list(r.choice(rows));h=r.randrange(k);z=base[h:]+base[:h]
    rows.append(tuple(z))
   out.append({'raw':rows,'truth':len({canon_rotation(list(x)) for x in rows})})
  elif fam=='reach':
   n=r.randint(5,9);edges=[]
   for i in range(n):
    for j in range(n):
     if i!=j and r.random()<0.16:edges.append((i,j))
   s,t=r.sample(range(n),2);out.append({'raw':(n,edges,s,t),'truth':brute_reach(n,edges,s,t)})
  elif fam=='modrec':
   m=r.choice([17,19,23,29,31]);a=r.randrange(1,m);b=r.randrange(m);x=r.randrange(m);n=r.randint(8,40)
   out.append({'raw':(a,b,m,x,n),'truth':brute_modrec(a,b,m,x,n)})
 return out

# ---------- operator semantics ----------
CHAINS={
 'parity':['DISTINGUISH','TRANSDUCE','SELECT'],
 'components':['RELATE','COMPOSE','CONSTRAIN','SELECT'],
 'rank':['TRANSDUCE','CONSTRAIN','SELECT'],
 'orbits':['TRANSDUCE','RELATE','CONSTRAIN','SELECT'],
 'reach':['RELATE','COMPOSE','SELECT'],
 'modrec':['RELATE','COMPOSE','TRANSDUCE','SELECT'],
}
FAMILIES=list(CHAINS)
DATA={f:make_instances(f,SEED+1009*i) for i,f in enumerate(FAMILIES)}

def apply_required(f,op,s):
 if f=='parity':
  if op=='DISTINGUISH' and 'ends' not in s:s['ends']=(s['raw'][0],s['raw'][-1]);return s
  if op=='TRANSDUCE' and 'ends' in s and 'value' not in s:s['value']=s['ends'][0]^s['ends'][1];return s
  if op=='SELECT' and 'value' in s and 'answer' not in s:s['answer']=s['value'];return s
 if f=='components':
  n,e=s['raw']
  if op=='RELATE' and 'adj' not in s:
   a=[set() for _ in range(n)]
   for u,v in e:a[u].add(v);a[v].add(u)
   s['adj']=a;return s
  if op=='COMPOSE' and 'adj' in s and 'closure' not in s:
   cl=[]
   for q in range(n):
    seen={q};st=[q]
    while st:
     u=st.pop()
     for v in s['adj'][u]:
      if v not in seen:seen.add(v);st.append(v)
    cl.append(frozenset(seen))
   s['closure']=cl;return s
  if op=='CONSTRAIN' and 'closure' in s and 'value' not in s:s['value']=len(set(s['closure']));return s
  if op=='SELECT' and 'value' in s and 'answer' not in s:s['answer']=s['value'];return s
 if f=='rank':
  if op=='TRANSDUCE' and 'rref' not in s:
   A=[[Fraction(x) for x in r] for r in s['raw']];m=len(A);n=len(A[0]);r=0
   for c in range(n):
    p=next((i for i in range(r,m) if A[i][c]),None)
    if p is None:continue
    A[r],A[p]=A[p],A[r];q=A[r][c];A[r]=[x/q for x in A[r]]
    for i in range(m):
     if i!=r and A[i][c]:
      q=A[i][c];A[i]=[x-q*y for x,y in zip(A[i],A[r])]
    r+=1
    if r==m:break
   s['rref']=A;return s
  if op=='CONSTRAIN' and 'rref' in s and 'value' not in s:s['value']=sum(any(x for x in row) for row in s['rref']);return s
  if op=='SELECT' and 'value' in s and 'answer' not in s:s['answer']=s['value'];return s
 if f=='orbits':
  if op=='TRANSDUCE' and 'canon' not in s:s['canon']=[canon_rotation(list(x)) for x in s['raw']];return s
  if op=='RELATE' and 'canon' in s and 'classes' not in s:
   s['classes']=collections.Counter(s['canon']);return s
  if op=='CONSTRAIN' and 'classes' in s and 'value' not in s:s['value']=len(s['classes']);return s
  if op=='SELECT' and 'value' in s and 'answer' not in s:s['answer']=s['value'];return s
 if f=='reach':
  n,e,src,tgt=s['raw']
  if op=='RELATE' and 'adj' not in s:
   a=[set() for _ in range(n)]
   for u,v in e:a[u].add(v)
   s['adj']=a;return s
  if op=='COMPOSE' and 'adj' in s and 'closure' not in s:
   cl=[]
   for q in range(n):
    seen={q};st=[q]
    while st:
     u=st.pop()
     for v in s['adj'][u]:
      if v not in seen:seen.add(v);st.append(v)
    cl.append(seen)
   s['closure']=cl;return s
  if op=='SELECT' and 'closure' in s and 'answer' not in s:s['answer']=tgt in s['closure'][src];return s
 if f=='modrec':
  a,b,m,x,n=s['raw']
  if op=='RELATE' and 'map' not in s:s['map']=(a,b,m);return s
  if op=='COMPOSE' and 'map' in s and 'power' not in s:
   A,B,M=s['map'];ra,rb=1,0;ba,bb=A,B;k=n
   while k:
    if k&1:ra,rb=(ba*ra)%M,(ba*rb+bb)%M
    ba,bb=(ba*ba)%M,(ba*bb+bb)%M;k//=2
   s['power']=(ra,rb,M);return s
  if op=='TRANSDUCE' and 'power' in s and 'value' not in s:
   A,B,M=s['power'];s['value']=(A*x+B)%M;return s
  if op=='SELECT' and 'value' in s and 'answer' not in s:s['answer']=s['value'];return s
 return None

def run_program(f,p,item):
 s={'raw':copy.deepcopy(item['raw']),'audit':set()};need=set(CHAINS[f])
 for op in p:
  if op in need:
   z=apply_required(f,op,s)
   if z is None:return None
  else:
   if op in s['audit']:return None
   s['audit'].add(op) # executable but mathematically irrelevant control action
 return s.get('answer')

def typed_candidates(f):
 # Typed on the first instance; then exactness is checked on all held instances.
 first=DATA[f][0];out=[]
 for L in range(1,MAX_LEN+1):
  for p in itertools.permutations(OPS,L):
   r=run_program(f,p,first)
   # Keep any program whose ordered operations are executable, whether terminal or not.
   # Re-run prefix executability explicitly.
   s={'raw':copy.deepcopy(first['raw']),'audit':set()};ok=True;need=set(CHAINS[f])
   for op in p:
    if op in need:
     if apply_required(f,op,s) is None:ok=False;break
    else:s['audit'].add(op)
   if ok:out.append(p)
 return out

def succeeds(f,p):return all(run_program(f,p,x)==x['truth'] for x in DATA[f])

def first_rank(f,cands,score):
 order=sorted(cands,key=lambda p:(score(p),len(p),p))
 for i,p in enumerate(order,1):
  if succeeds(f,p):return i,p,len(order),sum(succeeds(f,q) for q in cands)
 return None,None,len(order),0

big=fit_bigram(TRAIN);uni=fit_unigram(TRAIN)
CANDS={f:typed_candidates(f) for f in FAMILIES}
rows=[]
for f in FAMILIES:
 rg,pg,n,k=first_rank(f,CANDS[f],big);ru,pu,_,_=first_rank(f,CANDS[f],uni)
 random_expect=(n+1)/(k+1) if k else float('inf')
 rows.append({'family':f,'typed_candidates':n,'successful_programs':k,'grammar_rank':rg,'grammar_program':pg,'unigram_rank':ru,'unigram_program':pu,'random_expected_rank':random_expect,'grammar_normalized':rg/random_expect if rg else None,'unigram_normalized':ru/random_expect if ru else None})

g_mean=sum(x['grammar_normalized'] for x in rows)/len(rows);u_mean=sum(x['unigram_normalized'] for x in rows)/len(rows)
# Order-destroyed non-math controls.
rng=random.Random(SEED+1);sh=[]
for _ in range(SHUFFLE_REPS):
 q=[]
 for s in TRAIN:
  z=list(s);rng.shuffle(z);q.append(tuple(z))
 sc=fit_bigram(q);vals=[]
 for f in FAMILIES:
  r,_,n,k=first_rank(f,CANDS[f],sc);vals.append(r/((n+1)/(k+1)))
 sh.append(sum(vals)/len(vals))
shuffle_p=(1+sum(x<=g_mean for x in sh))/(SHUFFLE_REPS+1)
# Semantic label-alignment control: transformations/verifiers stay fixed; only labels seen by grammar are permuted.
lp=[]
for _ in range(LABEL_REPS):
 z=OPS[:];rng.shuffle(z);mp=dict(zip(OPS,z))
 def sc(p):return big(tuple(mp[x] for x in p))
 vals=[]
 for f in FAMILIES:
  r,_,n,k=first_rank(f,CANDS[f],sc);vals.append(r/((n+1)/(k+1)))
 lp.append(sum(vals)/len(vals))
label_p=(1+sum(x<=g_mean for x in lp))/(LABEL_REPS+1)

R={'seed':SEED,'instances_per_family':INSTANCES,'max_program_length':MAX_LEN,'nonmath_train_traces':len(TRAIN),'families':FAMILIES,'chains':CHAINS,'rows':rows,'grammar_mean_normalized_rank':g_mean,'unigram_mean_normalized_rank':u_mean,'shuffle_mean':sum(sh)/len(sh),'shuffle_p':shuffle_p,'label_permutation_mean':sum(lp)/len(lp),'label_permutation_p':label_p,'gates':{}}
R['gates']={
 'all_families_solvable':all(x['successful_programs']>0 for x in rows),
 'beats_random_expectation':g_mean<1.0,
 'beats_unigram':g_mean<u_mean,
 'shuffle_p':shuffle_p<=GATESPEC['shuffle_p_max'],
 'label_permutation_p':label_p<=GATESPEC['label_permutation_p_max'],
}
R['verdict']='PASS_EXECUTABLE_MATH_CONTROL_V75' if all(R['gates'].values()) else 'MIXED_EXECUTABLE_MATH_CONTROL_V75'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2,default=list));print(json.dumps(R,indent=2,default=list))
