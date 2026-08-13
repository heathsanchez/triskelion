import json,importlib.util,itertools,collections,random,statistics
from pathlib import Path
spec=importlib.util.spec_from_file_location('av2','experiments/METALOGIC_ALPHABET_FALSIFICATION_V2.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
E=m.E; OPS=m.OPS
OUT=Path('artifacts/reusable_words_v19');OUT.mkdir(parents=True,exist_ok=True)

# Frozen test: do short contiguous operator words recur across genuinely different domains,
# and do words learned from other domains compress held-out cognitive programs better than shuffled controls?
def ngrams(seq,n): return [tuple(seq[i:i+n]) for i in range(len(seq)-n+1)]

domains=sorted(set(x[0] for x in E))
# Discover only motifs supported by >=3 distinct domains; this prevents one-domain idioms becoming 'universal words'.
support=collections.defaultdict(set); counts=collections.Counter()
for d,_,_,prog in E:
    for n in (2,3,4):
        for g in set(ngrams(prog,n)):
            support[g].add(d); counts[g]+=1
words={g for g,ds in support.items() if len(ds)>=3}

# Greedy dictionary coding: one word token replaces a matching operator subsequence.
def code_len(prog,dictionary):
    p=tuple(prog); n=len(p); dp=[10**9]*(n+1); dp[0]=0
    for i in range(n):
        dp[i+1]=min(dp[i+1],dp[i]+1)
        for w in dictionary:
            L=len(w)
            if p[i:i+L]==w: dp[i+L]=min(dp[i+L],dp[i]+1)
    return dp[n]

# Leave-one-domain-out dictionary discovery. Held-out domain never contributes to its word inventory.
folds=[]; raw_total=compressed_total=shuffle_total=0
rng=random.Random(20260813)
for held in domains:
    train=[x for x in E if x[0]!=held]; test=[x for x in E if x[0]==held]
    sup=collections.defaultdict(set)
    for d,_,_,p in train:
        for n in (2,3,4):
            for g in set(ngrams(p,n)): sup[g].add(d)
    dic={g for g,ds in sup.items() if len(ds)>=3}
    # matched random dictionaries preserve word lengths/count, but destroy operator order/identity.
    shuffled=[]
    for rep in range(200):
        rd=set()
        for w in dic:
            z=list(w); rng.shuffle(z)
            # additional cyclic substitution breaks accidental identical permutations
            if tuple(z)==w and len(z)>1: z=z[1:]+z[:1]
            rd.add(tuple(z))
        shuffled.append(rd)
    raw=sum(len(x[3]) for x in test)
    comp=sum(code_len(x[3],dic) for x in test)
    sh=[sum(code_len(x[3],rd) for x in test) for rd in shuffled]
    shmean=statistics.mean(sh) if sh else raw
    folds.append({'held_domain':held,'n':len(test),'dictionary_size':len(dic),'raw_tokens':raw,'word_tokens':comp,'compression':1-comp/raw if raw else 0,'shuffle_mean_tokens':shmean,'beats_shuffle':comp<shmean})
    raw_total+=raw; compressed_total+=comp; shuffle_total+=shmean

# Cross-layer motif audit: word must occur in >=2 of four coarse layers.
layer_of={'math':'reasoning','science':'reasoning','coding':'execution','river':'development','development':'development','memory':'memory','collider':'reasoning','representation':'reasoning','ecology':'system','search':'system','system':'system'}
word_layers={}
for w in words:
    ls=set()
    for d,_,_,p in E:
        if w in ngrams(p,len(w)): ls.add(layer_of[d])
    word_layers['>'.join(w)]=sorted(ls)

# Ablate word/chunking entirely: raw token length is baseline. Also compare a flat dictionary of single operators (same as raw).
R={
 'alphabet':OPS,'n_events':len(E),'n_domains':len(domains),'global_cross_domain_words':len(words),
 'top_words':[{'word':list(w),'domains':sorted(support[w]),'count':counts[w],'layers':word_layers['>'.join(w)]} for w in sorted(words,key=lambda w:(-len(support[w]),-counts[w],-len(w),w))[:30]],
 'folds':folds,'raw_tokens':raw_total,'compressed_tokens':compressed_total,'shuffle_mean_tokens':shuffle_total,
 'compression_gain':1-compressed_total/raw_total,
 'shuffle_gain':1-shuffle_total/raw_total,
 'cross_layer_words':sum(len(v)>=2 for v in word_layers.values()),
}
R['gates']={
 'recurrent_words_exist':len(words)>=5,
 'heldout_compression':R['compression_gain']>=0.15,
 'beats_shuffled_words':compressed_total+1e-9<shuffle_total,
 'most_domains_benefit':sum(f['compression']>0 for f in folds)>=int(0.7*len(folds)),
 'cross_layer_reuse':R['cross_layer_words']>=3,
}
R['verdict']='PASS_REUSABLE_OPERATOR_WORDS_V19' if all(R['gates'].values()) else 'MIXED_REUSABLE_OPERATOR_WORDS_V19'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))