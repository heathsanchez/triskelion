import os,json,random,importlib.util,re
from pathlib import Path
import river_client as river

spec=importlib.util.spec_from_file_location('av2','experiments/METALOGIC_ALPHABET_FALSIFICATION_V2.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
E=mod.E;OPS=mod.OPS
OUT=Path('artifacts/alphabet_semantic_v3');OUT.mkdir(parents=True,exist_ok=True)
BASE='Qwen/Qwen3.5-9B';SEED=20260903
codes={op:f'K{i+1}' for i,op in enumerate(OPS)}
defs={
'DISTINGUISH':'localize a meaningful discrepancy, novelty, missing distinction, or residual before choosing a remedy',
'GENERATE':'create new candidate hypotheses, representations, repairs, or continuations',
'RELATE':'compare alternatives, identify analogy, conflict, shared structure, or rival explanations',
'PROBE':'choose an information-producing question, experiment, query, or intervention that discriminates alternatives',
'CONSTRAIN':'apply an invariant, boundary, verifier, type condition, or protected requirement that defines admissibility',
'SELECT':'choose, reject, promote, demote, route, checkpoint, or stop among already available alternatives',
'COMPOSE':'bind multiple existing capabilities or structures into a larger lawful move or higher-order object',
'RETAIN':'preserve, store, inherit, replay, or automatize a capability or verified structure',
'TRANSDUCE':'change representation or move structure across interfaces or substrates while preserving relevant meaning',
'RECURSE':'use prior outcomes or developmental history to change future learning, strategy, or learning policy',
}

def make_prompt(text,mode,shuffle_map=None):
    if mode=='opaque_true': lines=[f"{codes[o]}: {defs[o]}" for o in OPS];labels=list(codes.values())
    elif mode=='opaque_shuffled': lines=[f"{codes[o]}: {defs[shuffle_map[o]]}" for o in OPS];labels=list(codes.values())
    elif mode=='opaque_labels_only': lines=[];labels=list(codes.values())
    elif mode=='natural_true': lines=[f"{o}: {defs[o]}" for o in OPS];labels=OPS
    else: raise ValueError(mode)
    glossary=('Operator definitions:\n'+'\n'.join(lines)+'\n\n') if lines else ''
    return f"""{glossary}Situation:\n{text}\n\nChoose the SINGLE operator that is the decisive missing or next move. At the very end write FINAL=<label>. Valid labels: {', '.join(labels)}."""

def parse(text,labels):
    t=text.upper().replace('`','').replace('*','')
    # Prefer explicit final marker, allowing reasoning before it.
    for lab in labels:
        if re.search(r'FINAL\s*=\s*'+re.escape(lab.upper())+r'\b',t): return lab
    # Otherwise use the last uniquely occurring label token.
    hits=[]
    for lab in labels:
        ms=list(re.finditer(r'(?<![A-Z0-9_])'+re.escape(lab.upper())+r'(?![A-Z0-9_])',t))
        if ms:hits.append((ms[-1].start(),lab))
    return max(hits)[1] if hits else None

rng=random.Random(8142026);perm=OPS.copy();rng.shuffle(perm);shuffle_map=dict(zip(OPS,perm))
client=river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=180.0);assert client.health_check()
R={'base':BASE,'n':len(E),'codes':codes,'shuffle_map':shuffle_map,'modes':{}}
with client.session(project='ml-alphabet-semantic-v3b') as s:
    m=s.create_model(base_model=BASE)
    for mode in ['opaque_true','opaque_shuffled','opaque_labels_only','natural_true']:
        prompts=[make_prompt(x[1],mode,shuffle_map) for x in E]
        max_tokens=64 if mode=='natural_true' else 24
        gens=m.sample(prompts=prompts,max_tokens=max_tokens,temperature=0.0)
        labels=list(codes.values()) if mode.startswith('opaque') else OPS
        pred=[parse(g[0].text,labels) for g in gens]
        gold=[codes[x[2]] if mode.startswith('opaque') else x[2] for x in E]
        ok=[p==g for p,g in zip(pred,gold)]
        by_domain={}
        for d in sorted(set(x[0] for x in E)):
            inds=[i for i,x in enumerate(E) if x[0]==d];by_domain[d]=sum(ok[i] for i in inds)/len(inds)
        by_op={}
        for op in OPS:
            inds=[i for i,x in enumerate(E) if x[2]==op];by_op[op]=sum(ok[i] for i in inds)/len(inds) if inds else None
        R['modes'][mode]={'accuracy':sum(ok)/len(ok),'parsed':sum(p is not None for p in pred)/len(pred),'by_domain':by_domain,'by_operator':by_op,'pred':pred,'gold':gold,'raw':[g[0].text for g in gens]}
R['gates']={
 'true_defs_above_chance':R['modes']['opaque_true']['accuracy']>=0.35,
 'true_defs_beat_shuffled':R['modes']['opaque_true']['accuracy']>=R['modes']['opaque_shuffled']['accuracy']+0.15,
 'true_defs_beat_labels_only':R['modes']['opaque_true']['accuracy']>=R['modes']['opaque_labels_only']['accuracy']+0.20,
 'natural_labels_usable':R['modes']['natural_true']['accuracy']>=0.50,
 'probe_semantic':R['modes']['opaque_true']['by_operator']['PROBE']>=0.50,
 'compose_semantic':R['modes']['opaque_true']['by_operator']['COMPOSE']>=0.50,
}
R['verdict']='PASS_ALPHABET_SEMANTIC_V3' if all(R['gates'].values()) else 'MIXED_ALPHABET_SEMANTIC_V3'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2));print(json.dumps(R,indent=2),flush=True)
