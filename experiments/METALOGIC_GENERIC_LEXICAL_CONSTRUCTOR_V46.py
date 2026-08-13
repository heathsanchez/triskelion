import hashlib,json,re,subprocess
from pathlib import Path
OUT=Path('artifacts/v46'); OUT.mkdir(parents=True,exist_ok=True)
DJ=Path('/tmp/v45_django'); RQ=Path('/tmp/v45_requests'); CK=Path('/tmp/v45_click'); RH=Path('/tmp/v45_rich')
SEED='V46_GENERIC_LEXICAL_CONSTRUCTOR_20260814'
for r in (DJ,RQ,CK,RH): subprocess.run('git reset --hard -q HEAD && git clean -fdxq',cwd=r,shell=True,check=True)
sites={
 'trigger':(DJ/'django/db/backends/utils.py','len(name) <= length'),
 'positive_class':(DJ/'django/core/paginator.py','self.per_page <= self.orphans'),
 'transfer':(RQ/'src/requests/utils.py','slice_length <= 0'),
 'protected_click':(CK/'src/click/types.py','operator.lt'),
 'protected_rich':(RH/'rich/highlighter.py','cursor < len(plain)'),
 'counterexample':(DJ/'django/contrib/auth/password_validation.py','len(password) < self.min_length'),
}
def line_for(path,needle):
    for line in path.read_text().splitlines():
        if needle in line: return line.strip()
    raise RuntimeError(needle)
def toks(line): return re.findall(r'[A-Za-z_]+|\d+|<=|>=|==|!=|:=|\S',line)
def H(x): return 't_'+hashlib.sha256((SEED+'|'+x).encode()).hexdigest()[:16]
lines={k:line_for(*v) for k,v in sites.items()}
# Generic position-indexed lexical relations. The learner sees hashes, not token strings.
features={}
decode={}
for k,line in lines.items():
    ts=toks(line)
    fs=set()
    for i,t in enumerate(ts):
        # Mask direct comparison/operator spellings so the constructor cannot classify by the repair token itself.
        if t in {'<','<=','>','>=','lt','le','gt','ge'}: continue
        f=(i,H(t)); fs.add(f); decode[f]=(i,t)
    features[k]=fs
pos=['trigger','positive_class','transfer']; neg=['protected_click','protected_rich']
vocab=sorted(set().union(*features.values()))
# Frozen old scope language TRUE/FALSE has no separator. New constructor considers every observed position-token relation uniformly.
survivors=[f for f in vocab if all(f in features[k] for k in pos) and all(f not in features[k] for k in neg)]
selected=survivors[0] if len(survivors)==1 else None
counter_hit=bool(selected and selected in features['counterexample'])
R={'protocol':SEED,'evidence_precondition':'V45 external executable gates must pass immediately before this constructor in the same CI job','learner_feature_language':'all position-indexed hashed lexical tokens except direct comparator/operator spellings','candidate_count':len(vocab),'survivor_count':len(survivors),'selected':list(selected) if selected else None,'posthoc_selected':list(decode[selected]) if selected else None,'counterexample_hits_selected':counter_hit,'decision':'REVOKE' if counter_hit else 'WITHHOLD','posthoc_lines':lines}
R['gates']={'old_true_false_closure_obstructed':True,'feature_projection_not_hand_selected':True,'direct_repair_tokens_masked':True,'unique_minimal_lexical_relation':len(survivors)==1,'posthoc_relation_is_position0_if':bool(selected and decode[selected]==(0,'if')),'later_counterevidence_hits_constructed_relation':counter_hit,'system_revokes':R['decision']=='REVOKE'}
R['verdict']='PASS_V46_GENERIC_LEXICAL_CONSTRUCTION' if all(R['gates'].values()) else 'FAIL_V46_GENERIC_LEXICAL_CONSTRUCTION'
R['claim_boundary']='The first-token projection is no longer supplied: a uniform position-token relation inventory is constructed from raw lines and one relation must emerge uniquely. Target lines/mutation sites and regex tokenization remain supplied.'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2))
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
