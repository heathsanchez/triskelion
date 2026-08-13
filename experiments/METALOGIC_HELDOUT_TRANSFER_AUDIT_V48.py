import hashlib,json,re
from pathlib import Path
OUT=Path('artifacts/v48'); OUT.mkdir(parents=True,exist_ok=True)
SEED='V48_HELDOUT_TRANSFER_AUDIT_20260814'
r47=json.loads(Path('artifacts/v47b/RESULT.json').read_text())
r45=json.loads(Path('artifacts/v45/RESULT.json').read_text())
train_pos=['trigger','positive_class']; train_neg=['protected_click','protected_rich']; held='transfer'; later='counterexample'
lines={k:r47['mined'][k]['causal'][0]['text'] for k in r47['mined'] if len(r47['mined'][k]['causal'])==1}
def atoms(line): return re.findall(r'[A-Za-z_]+|\d+',line)
def H(x): return 'a_'+hashlib.sha256((SEED+'|'+x).encode()).hexdigest()[:16]
features={}; decode={}
for k,line in lines.items():
    fs=set()
    for i,t in enumerate(atoms(line)):
        f=(i,H(t)); fs.add(f); decode[f]=(i,t)
    features[k]=fs
vocab=sorted(set().union(*(features[k] for k in train_pos+train_neg)))
survivors=[f for f in vocab if all(f in features[k] for k in train_pos) and all(f not in features[k] for k in train_neg)]
selected=survivors[0] if len(survivors)==1 else None
held_hit=bool(selected and selected in features[held]); later_hit=bool(selected and selected in features[later])
transfer=r45['transfer']; counter=r45['counter']
R={'protocol':SEED,'construction_examples':train_pos+train_neg,'held_out_from_construction':held,'feature_language':'position-indexed hashed identifier/number atoms only','candidate_count':len(vocab),'survivor_count':len(survivors),'selected':list(selected) if selected else None,'posthoc_selected':list(decode[selected]) if selected else None,'heldout_membership_checked_after_selection':held_hit,'heldout_behavior_from_same_run':transfer,'later_counterevidence_membership':later_hit,'later_behavior_from_same_run':counter,'decision':'REVOKE' if later_hit and counter['base'] and not counter['after'] else 'WITHHOLD'}
R['gates']={'requests_excluded_from_category_construction':held not in train_pos+train_neg,'unique_category_from_calibration_only':len(survivors)==1,'posthoc_category_is_position0_if':bool(selected and decode[selected]==(0,'if')),'heldout_requests_matches_category':held_hit,'heldout_requests_transfer_causal':not transfer['cold'] and transfer['warm'],'heldout_transfer_ablation_fails':not transfer['ablated'],'later_counterexample_matches_category':later_hit,'later_external_behavior_falsifies':counter['base'] and not counter['after'],'system_revokes':R['decision']=='REVOKE'}
R['verdict']='PASS_V48_HELDOUT_TRANSFER_AUDIT' if all(R['gates'].values()) else 'FAIL_V48_HELDOUT_TRANSFER_AUDIT'
R['claim_boundary']='Requests is excluded from category construction, but its site and executable behavior were acquired earlier in the same overall run by V45/V47b. This establishes held-out use by the constructor, not a temporally sealed episode. V49 should hide the entire Requests episode until after category commitment.'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2)); print(json.dumps(R,indent=2))
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
