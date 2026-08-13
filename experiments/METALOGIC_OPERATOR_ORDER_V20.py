import json,importlib.util,itertools,math,statistics,collections,random
from pathlib import Path
spec=importlib.util.spec_from_file_location('av2','experiments/METALOGIC_ALPHABET_FALSIFICATION_V2.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
E=m.E;OPS=m.OPS; OUT=Path('artifacts/operator_order_v20');OUT.mkdir(parents=True,exist_ok=True)

def fit_bigram(train,alpha=.25):
    uni=collections.Counter(); bi=collections.Counter()
    for _,_,_,p in train:
        seq=['<S>']+p+['</S>']
        for a in seq[:-1]: uni[a]+=1
        for a,b in zip(seq,seq[1:]): bi[(a,b)]+=1
    vocab=OPS+['</S>'];V=len(vocab)
    def logp(p):
        seq=['<S>']+list(p)+['</S>'];s=0
        for a,b in zip(seq,seq[1:]): s+=math.log((bi[(a,b)]+alpha)/(uni[a]+alpha*V))
        return s
    return logp

def perms(p):
    ps=set(itertools.permutations(p))
    return ps

domains=sorted(set(x[0] for x in E));rows=[];preferred=ties=total=0;margins=[]
for held in domains:
    train=[x for x in E if x[0]!=held];test=[x for x in E if x[0]==held and len(x[3])>=2]
    score=fit_bigram(train)
    for d,text,dec,p in test:
        candidates=perms(p);gold=tuple(p);gs=score(gold);other=[score(q) for q in candidates if q!=gold]
        if not other: continue
        best=max(other);margin=gs-best;margins.append(margin);total+=1
        if margin>1e-12: preferred+=1
        elif abs(margin)<=1e-12: ties+=1
        rows.append({'domain':held,'program':p,'gold_logp':gs,'best_permuted_logp':best,'margin':margin,'n_permutations':len(candidates),'gold_strictly_best':margin>1e-12})
# Pairwise directionality for recurrent two-letter words.
pair_counts=collections.Counter()
for _,_,_,p in E:
    for a,b in zip(p,p[1:]): pair_counts[(a,b)]+=1
pair_direction=[]
for a,b in itertools.combinations(OPS,2):
    ab=pair_counts[(a,b)];ba=pair_counts[(b,a)]
    if ab+ba>=3: pair_direction.append({'a':a,'b':b,'a_to_b':ab,'b_to_a':ba,'asymmetry':abs(ab-ba)/(ab+ba)})
R={'n_ordered_events':total,'gold_strictly_preferred':preferred,'ties':ties,'preference_rate':preferred/total if total else 0,'mean_margin':statistics.mean(margins) if margins else 0,'median_margin':statistics.median(margins) if margins else 0,'rows':rows,'directional_pairs':sorted(pair_direction,key=lambda x:-x['asymmetry'])}
R['gates']={'order_predictable_cross_domain':R['preference_rate']>=0.60,'positive_mean_margin':R['mean_margin']>0,'directional_pairs_exist':sum(x['asymmetry']>=0.5 for x in pair_direction)>=3}
R['verdict']='PASS_OPERATOR_ORDER_GRAMMAR_V20' if all(R['gates'].values()) else 'MIXED_OPERATOR_ORDER_GRAMMAR_V20'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2))