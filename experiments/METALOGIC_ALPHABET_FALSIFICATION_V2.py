import json,statistics,itertools,collections
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score

OPS=['DISTINGUISH','GENERATE','RELATE','PROBE','CONSTRAIN','SELECT','COMPOSE','RETAIN','TRANSDUCE','RECURSE']
OUT=Path('artifacts/alphabet_falsification_v2');OUT.mkdir(parents=True,exist_ok=True)
# Frozen before outcomes. Each item is a transition description plus the decisive missing/next operation
# and a minimal operator program. Items span cognition, system architecture, memory, and development.
E=[
('math','A Lean attempt fails because the goal contains a dependency the current repair vocabulary cannot express. The failure must first be localized as a representational mismatch.','DISTINGUISH',['DISTINGUISH','TRANSDUCE']),
('math','Two rival explanations remain for a failed proof and both fit the current trace. Choose the cheapest lemma instance whose outcome would separate them.','PROBE',['RELATE','PROBE','CONSTRAIN','SELECT']),
('math','A repeated proof move succeeds independently on several held-out theorems and now needs admission as a reusable theorem schema.','RETAIN',['CONSTRAIN','SELECT','RETAIN']),
('math','A global kernel representation repeatedly fails while a stabilizer relation exposes the missing x-dependence. Move the problem into the new representation.','TRANSDUCE',['DISTINGUISH','TRANSDUCE','CONSTRAIN']),
('math','Several verified lemmas jointly imply a new theorem but no single lemma suffices. Build the lawful closure over the retained lemmas.','COMPOSE',['RELATE','COMPOSE','CONSTRAIN']),
('coding','A program repair passes visible tests but protected tests reveal a regression. The candidate must not be promoted.','SELECT',['CONSTRAIN','SELECT']),
('coding','The same exception-flow obstruction appears in a different independently authored package after the primitive was previously learned. Reuse the retained primitive.','RETAIN',['RELATE','RETAIN']),
('coding','Three independently learned AST repair primitives are all callable, but a new bug requires two of them simultaneously and the model emits only the newest one.','COMPOSE',['DISTINGUISH','COMPOSE','CONSTRAIN']),
('coding','A fresh mutation produces an unfamiliar runtime residual and there are several possible edit sites. Execute a diagnostic case that maximizes discrimination among sites.','PROBE',['DISTINGUISH','PROBE']),
('coding','Broad random patch generation is wasting budget after the residual has narrowed to one syntax family. Restrict generation to that family.','CONSTRAIN',['DISTINGUISH','CONSTRAIN','GENERATE']),
('river','After learning a successor skill, the old skill falls from 100 percent to zero although both tasks have distinct labels. Preserve the old behavior during further updates.','RETAIN',['DISTINGUISH','CONSTRAIN','RETAIN']),
('river','At update three old and new skills are both perfect; update four destroys the new skill. The developmental controller must checkpoint now rather than continue optimizing.','SELECT',['CONSTRAIN','SELECT','RETAIN']),
('river','A training checkpoint is saved, the session closes, and the next generation must restore the same learned state in a new session.','TRANSDUCE',['RETAIN','TRANSDUCE']),
('river','Correct ancestry makes a successor capability cheaper to learn than cold or wrong ancestry. The changed learner must alter what it attempts next.','RECURSE',['RETAIN','RECURSE']),
('river','A model has retained CMP BIN and CONST separately but does not solve unseen combinations. Search lawful subsets of retained capabilities and let execution decide.','COMPOSE',['RELATE','COMPOSE','CONSTRAIN','SELECT']),
('river','Sparse replay oscillates between old and new policies. Find a joint state satisfying protected purposes rather than blindly replaying a fixed ratio.','CONSTRAIN',['DISTINGUISH','CONSTRAIN','SELECT']),
('ecology','The same initial observations can correspond to different operators. Ask for the observation whose possible outcomes most reduce ambiguity.','PROBE',['RELATE','PROBE']),
('ecology','Independent cheap tasks rarely recur, so memory adds cost without benefit; allocate effort to evidence gathering and adaptive search instead.','SELECT',['CONSTRAIN','SELECT']),
('ecology','In a recurrent environment previously verified routes recur often enough to save work. Store and route through the recurring successful pattern.','RETAIN',['RELATE','SELECT','RETAIN']),
('ecology','A stale learned route proposes the wrong answer in a hostile ambiguity class. External execution rejects it and the route must be rolled back.','CONSTRAIN',['RETAIN','CONSTRAIN','SELECT']),
('science','Two theories make the same predictions on all measurements taken so far. Design the smallest experiment on which their predictions differ.','PROBE',['RELATE','PROBE','CONSTRAIN']),
('science','A new observation violates the current model in a systematic way. Record the discrepancy before inventing another theory.','DISTINGUISH',['DISTINGUISH']),
('science','Several observations share a repeated residual pattern. Propose a new invariant that could explain the common structure.','GENERATE',['DISTINGUISH','RELATE','GENERATE']),
('science','A candidate invariant survives independent experiments and counterexamples and should become part of the standing model.','RETAIN',['CONSTRAIN','SELECT','RETAIN']),
('science','A useful theory is expressed in one coordinate system but a new phenomenon becomes simple only after changing variables.','TRANSDUCE',['DISTINGUISH','TRANSDUCE']),
('collider','Two distant domains contain structurally similar motifs. Compare their typed features and identify shared and conflicting invariants.','RELATE',['RELATE']),
('collider','Two epiphanies conflict at the surface but can both be subsumed by a higher-order invariant. Construct that higher-level object.','COMPOSE',['RELATE','COMPOSE']),
('collider','A collision yields five speculative operator candidates. Produce additional cases whose outcomes distinguish which candidate generalizes.','PROBE',['GENERATE','PROBE','CONSTRAIN']),
('collider','Repeated higher-order invariants overlap heavily. Compress them into a minimal non-redundant Lawbook without losing supported distinctions.','COMPOSE',['RELATE','COMPOSE','SELECT','RETAIN']),
('collider','An analogy is elegant but has never survived an external authority boundary. Keep it advisory rather than promoting it.','CONSTRAIN',['CONSTRAIN','SELECT']),
('representation','A route repeatedly fails for the same reason even after local repairs. Determine whether the obstruction lies in the route, representation, or world.','DISTINGUISH',['DISTINGUISH','RELATE']),
('representation','A function representation cannot express a latent relation with unique midpoint behavior. Replace the object language with the relation representation.','TRANSDUCE',['DISTINGUISH','TRANSDUCE']),
('representation','An adapter between two worlds may discard an invariant needed by the target. Test preservation before allowing the translation.','CONSTRAIN',['TRANSDUCE','CONSTRAIN']),
('representation','Several representation portals solve different instances of one obstruction family. Abstract a reusable portal-selection rule.','COMPOSE',['RELATE','COMPOSE','SELECT','RETAIN']),
('memory','A raw failed attempt contains useful evidence but is not trustworthy knowledge. Store it as an episode with provenance rather than a law.','RETAIN',['DISTINGUISH','RETAIN']),
('memory','A Lawbook entry is repeatedly superseded by a more general verified law. Demote the narrow entry and retain the general one.','SELECT',['RELATE','CONSTRAIN','SELECT','RETAIN']),
('memory','The explicit Lawbook capability has become repeatedly useful and expensive to retrieve. Compile it into neural weights while preserving the explicit source.','TRANSDUCE',['SELECT','RETAIN','TRANSDUCE','CONSTRAIN']),
('memory','A neural capability remains cheap but its explicit provenance is lost. Recover the authoritative source record before allowing further promotion.','TRANSDUCE',['DISTINGUISH','TRANSDUCE','CONSTRAIN']),
('development','The learner sees the same residual family repeatedly. Use its prior developmental history to choose a different strategy on the next occurrence.','RECURSE',['RETAIN','RECURSE','SELECT']),
('development','A successful composition recurs across unrelated tasks. Chunk it into a named higher-level capability for future use.','RETAIN',['COMPOSE','CONSTRAIN','SELECT','RETAIN']),
('development','Current skills are stable but the learner has no evidence about which frontier would be most informative next. Choose an intervention that resolves the most consequential uncertainty.','PROBE',['RECURSE','PROBE','SELECT']),
('development','A developmental policy repeatedly reduces discovery cost on protected held-out tasks. Promote the policy so future learning uses it.','RECURSE',['CONSTRAIN','SELECT','RETAIN','RECURSE']),
('development','A later generation starts with capabilities earlier generations had to discover laboriously. Use that inherited structure as the starting state, not as prompt context only.','RECURSE',['RETAIN','TRANSDUCE','RECURSE']),
('search','A huge candidate law space contains mostly unstable or trivial dynamics. Generate diverse candidates but preserve only viable structured survivors.','SELECT',['GENERATE','CONSTRAIN','SELECT']),
('search','Survivors repeatedly use the same few mechanisms. Remove redundant mechanisms while preserving verified survivor coverage.','COMPOSE',['RELATE','COMPOSE','CONSTRAIN','SELECT']),
('search','Search has plateaued because all proposals use the same representation. Introduce a qualitatively different representational family.','GENERATE',['DISTINGUISH','GENERATE','TRANSDUCE']),
('search','The residual has narrowed enough that exhaustive local closure is cheaper than continued open-ended generation. Change the search allocation accordingly.','SELECT',['DISTINGUISH','CONSTRAIN','SELECT']),
('system','The generator proposes fluent candidates but confidence cannot authorize memory admission. Route every serious candidate through an external authority boundary.','CONSTRAIN',['GENERATE','CONSTRAIN']),
('system','The verifier reports what survived, what failed, and what remains residual. Convert that boundary record into the next discriminated state.','DISTINGUISH',['CONSTRAIN','DISTINGUISH']),
('system','The same operator language must describe a cognitive step, a memory transformation, and a whole subsystem without changing semantics. Define typed interfaces across those layers.','TRANSDUCE',['RELATE','TRANSDUCE','CONSTRAIN']),
('system','The architecture keeps accumulating bespoke atlases whose functions overlap. Refactor them into programs over a smaller common operator substrate.','COMPOSE',['DISTINGUISH','RELATE','COMPOSE','SELECT']),
]

# Basic closure and compression.
program_lengths=[len(x[3]) for x in E]
coverage=sum(all(op in OPS for op in x[3]) for x in E)/len(E)
support=collections.Counter(op for x in E for op in x[3])
decisive=collections.Counter(x[2] for x in E)
abl={op:sum(op not in x[3] for x in E)/len(E) for op in OPS}
# Forced merge: count pairs of events whose distinct decisive operations become indistinguishable.
merge_damage={}
for a,b in itertools.combinations(OPS,2):
    damage=sum(1 for x in E for y in E if x is not y and {x[2],y[2]}=={a,b})//2
    merge_damage[f'{a}+{b}']=damage

# Leave-one-domain-out text -> decisive operator. This tests whether the fixed distinctions are learnable
# from natural residual descriptions, not whether an LLM can invent the ontology.
domains=sorted(set(x[0] for x in E));folds=[];preds=[]
for d in domains:
    tr=[x for x in E if x[0]!=d];te=[x for x in E if x[0]==d]
    if not te or len(set(x[2] for x in tr))<2:continue
    clf=Pipeline([('tf',TfidfVectorizer(ngram_range=(1,2),min_df=1,sublinear_tf=True)),('lr',LogisticRegression(max_iter=3000,class_weight='balanced'))])
    clf.fit([x[1] for x in tr],[x[2] for x in tr]);p=clf.predict([x[1] for x in te]);acc=accuracy_score([x[2] for x in te],p)
    folds.append({'domain':d,'n':len(te),'accuracy':acc,'gold':[x[2] for x in te],'pred':list(p)});preds.extend(zip([x[2] for x in te],p))
loo_acc=sum(g==p for g,p in preds)/len(preds)
major=decisive.most_common(1)[0][0];major_acc=sum(x[2]==major for x in E)/len(E)
# Probe necessity: are PROBE events a coherent held-out class rather than aliases of generate/constrain?
probe_folds=[f for f in folds if 'PROBE' in f['gold']]
probe_pairs=[(g,p) for f in folds for g,p in zip(f['gold'],f['pred']) if g=='PROBE']
probe_recall=sum(p=='PROBE' for g,p in probe_pairs)/len(probe_pairs) if probe_pairs else 0
# Layer closure is declared by the frozen type signatures: each operator must have non-empty semantics on all four layers.
layer_map={
'DISTINGUISH':['notice residual','Residual/Obstruction Atlas','discriminated episode','reality creates next learning signal'],
'GENERATE':['imagine candidates','generator/constructor','candidate memory object','wake exploration'],
'RELATE':['compare/rival/analogy','graph/rival engine','memory links','alternative interaction'],
'PROBE':['ask/experiment/intervene','active query/separator','information-gain episode','self-directed evidence acquisition'],
'CONSTRAIN':['apply invariants','verifier/protected tests','validity boundary','viable region'],
'SELECT':['choose/promote/stop','router/promotion controller','admission/demotion','differential continuation'],
'COMPOSE':['bind capabilities','composer/closure','composite chunk','successor reachability'],
'RETAIN':['remember/automatize','episodic+Lawbook+weights','persistence','inheritance'],
'TRANSDUCE':['re-represent/express','portal/compiler/consolidator','episode-law-weights translation','wake-sleep/world interface'],
'RECURSE':['reflect/learn-to-learn','developmental controller','lineage/meta-policy','history changes future learning'],
}
layer_closure=all(len(v)==4 and all(v) for v in layer_map.values())

R={'alphabet':OPS,'n_events':len(E),'domains':domains,'coverage':coverage,'mean_program_length':statistics.mean(program_lengths),'median_program_length':statistics.median(program_lengths),'max_program_length':max(program_lengths),'support':support,'decisive_support':decisive,'ablation_remaining_coverage':abl,'merge_damage_top':sorted(merge_damage.items(),key=lambda z:z[1],reverse=True)[:15],'leave_one_domain_out':folds,'loo_accuracy':loo_acc,'majority_baseline':major_acc,'probe_recall':probe_recall,'layer_map':layer_map,'layer_closure':layer_closure}
R['gates']={
 'complete_encoding':coverage==1.0,
 'compact_programs':statistics.mean(program_lengths)<=3.5 and max(program_lengths)<=5,
 'all_operators_used':all(support[o]>0 for o in OPS),
 'all_decisive_classes_used':all(decisive[o]>0 for o in OPS),
 'prediction_beats_majority':loo_acc>=major_acc+0.15,
 'prediction_absolute':loo_acc>=0.45,
 'probe_is_predictable':probe_recall>=0.40,
 'layer_closure':layer_closure,
}
R['verdict']='PASS_INTERNAL_ALPHABET_FALSIFICATION_V2' if all(R['gates'].values()) else 'MIXED_INTERNAL_ALPHABET_FALSIFICATION_V2'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2,default=lambda x:dict(x)));print(json.dumps(R,indent=2,default=lambda x:dict(x)))
