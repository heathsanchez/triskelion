import json, ast, collections, itertools, math
from pathlib import Path

# Read the frozen alphabet corpus as literals without executing its sklearn/numpy analysis.
src=Path('experiments/METALOGIC_ALPHABET_FALSIFICATION_V2.py').read_text()
tree=ast.parse(src)
vals={}
for node in tree.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in {'E','OPS'}:
        vals[node.targets[0].id]=ast.literal_eval(node.value)
E=vals['E']; OPS=vals['OPS']
OUT=Path('artifacts/metamath_v23');OUT.mkdir(parents=True,exist_ok=True)
programs=[(d,tuple(p)) for d,_,_,p in E]
domains=sorted(set(d for d,_ in programs))

def precedence(rows):
    cnt=collections.Counter(); co=collections.Counter()
    for d,p in rows:
        pos={x:i for i,x in enumerate(p)}
        for x,y in itertools.combinations(sorted(pos),2):
            co[(x,y)]+=1
            if pos[x]<pos[y]: cnt[(x,y)]+=1
            else: cnt[(y,x)]+=1
    laws=[]
    for x,y in itertools.combinations(OPS,2):
        n=co.get(tuple(sorted((x,y))),0)
        if not n: continue
        xy=cnt[(x,y)]; yx=cnt[(y,x)]
        if xy+yx!=n: continue
        conf=max(xy,yx)/n; direction=(x,y) if xy>=yx else (y,x)
        laws.append((direction[0],direction[1],n,conf))
    return laws

full_laws=precedence(programs)
robust=[]
for x,y,n,conf in full_laws:
    if conf<0.9 or n<3: continue
    ok=True; supports=[]
    for held in domains:
        ls=precedence([(d,p) for d,p in programs if d!=held])
        hit=[z for z in ls if z[0]==x and z[1]==y]
        if hit:
            supports.append(hit[0][2])
            if hit[0][3]<0.9: ok=False
    if ok and supports:
        robust.append({'before':x,'after':y,'support':n,'confidence':conf,'min_lodo_support':min(supports)})

adj=collections.Counter()
for d,p in programs: adj.update(zip(p,p[1:]))
rewrites=[]
for x in OPS:
  for y in OPS:
    if x==y: continue
    axy=adj[(x,y)]; ayx=adj[(y,x)]
    if axy>=3 and axy>=4*max(1,ayx):
        rewrites.append({'from':[y,x],'to':[x,y],'forward':axy,'reverse':ayx})

def ngrams(p,n):return [p[i:i+n] for i in range(len(p)-n+1)]
support=collections.defaultdict(set); counts=collections.Counter()
for d,p in programs:
    for n in (2,3,4):
        for g in set(ngrams(p,n)): support[g].add(d); counts[g]+=1
words=[g for g,ds in support.items() if len(ds)>=3]
maxwords=[]
for w in words:
    dominated=False
    for v in words:
        if len(v)<=len(w): continue
        if any(v[i:i+len(w)]==w for i in range(len(v)-len(w)+1)) and len(support[v])>=len(support[w]):
            dominated=True;break
    if not dominated:maxwords.append(w)

def code_len(p,dic):
    N=len(p);dp=[999]*(N+1);dp[0]=0
    for i in range(N):
        dp[i+1]=min(dp[i+1],dp[i]+1)
        for w in dic:
            if p[i:i+len(w)]==w:dp[i+len(w)]=min(dp[i+len(w)],dp[i]+1)
    return dp[N]
raw=sum(len(p) for _,p in programs); coded=sum(code_len(p,maxwords) for _,p in programs)

graph={o:set() for o in OPS}
for (x,y),n in adj.items():
    if n:graph[x].add(y)
stack=[];on=set();ind={};low={};scc=[];counter=[0]
def visit(v):
    ind[v]=low[v]=counter[0];counter[0]+=1;stack.append(v);on.add(v)
    for w in graph[v]:
        if w not in ind:visit(w);low[v]=min(low[v],low[w])
        elif w in on:low[v]=min(low[v],ind[w])
    if low[v]==ind[v]:
        c=[]
        while True:
            w=stack.pop();on.remove(w);c.append(w)
            if w==v:break
        scc.append(sorted(c))
for o in OPS:
    if o not in ind:visit(o)

def entropy(counter):
    n=sum(counter.values())
    if not n:return 0.0
    return -sum((v/n)*math.log2(v/n) for v in counter.values())
roles=[]
for o in OPS:
    pre=collections.Counter();post=collections.Counter()
    for d,p in programs:
        for i,x in enumerate(p):
            if x!=o:continue
            if i:pre[p[i-1]]+=1
            if i+1<len(p):post[p[i+1]]+=1
    roles.append({'op':o,'support':sum(o in p for _,p in programs),'pre_entropy':entropy(pre),'post_entropy':entropy(post),'pre':dict(pre),'post':dict(post)})

R={'n_events':len(E),'domains':domains,'robust_precedence_laws':robust,'rewrite_candidates':rewrites,
   'maximal_cross_domain_words':[{'word':list(w),'domains':sorted(support[w]),'count':counts[w]} for w in sorted(maxwords,key=lambda z:(-len(support[z]),-len(z),z))],
   'raw_tokens':raw,'coded_tokens':coded,'compression':1-coded/raw,'scc':scc,'roles':roles}
R['gates']={'robust_laws':len(robust)>=5,'noncommutative_rewrites':len(rewrites)>=3,'cross_domain_words':len(maxwords)>=3,'grammar_compresses':1-coded/raw>=0.20,'semantic_cycle_exists':any(len(c)>=3 for c in scc)}
R['verdict']='PASS_METAMATH_V23' if all(R['gates'].values()) else 'MIXED_METAMATH_V23'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))