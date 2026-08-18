#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
B=Path('blind-di-o1o2'); cold=json.loads((B/'cold_result.json').read_text()); dev=json.loads((B/'developed_result.json').read_text()); pre=json.loads((B/'precommit.json').read_text())
cr=bool(cold.get('reach_o2')); dr=bool(dev.get('reach_o2'))
if (not cr) and dr: verdict='PASS_DI_O1_O2_DEPENDENCY'
elif cr and dr: verdict='NO_DEPENDENCY_BOTH_REACH'
elif (not cr) and (not dr):
    verdict='PARTIAL_DEVELOPED_EXPOSED_ONLY' if dev.get('verdict')=='PARTIAL_O2_EXPOSED_ONLY' else 'VALID_NEGATIVE_NEITHER_REACH'
else: verdict='REVERSE_OR_ANOMALOUS'
out={'protocol':'DI_O1_O2_DEPENDENCY_V1','v2_result_sha256':pre['v2_result_sha256'],'o1_proposal_sha256':pre['o1_proposal_sha256'],'common_exposed_sha256':pre['exposed_sha256'],'budget':pre['budget'],'cold':{'reach_o2':cr,'verdict':cold.get('verdict'),'prompt_sha256':cold.get('prompt_sha256'),'admissible_candidate_count':cold.get('admissible_candidate_count'),'selected':cold.get('selected'),'protected_transfer_count':(cold.get('protected_transfer') or {}).get('transfer_success_count')},'developed':{'reach_o2':dr,'verdict':dev.get('verdict'),'prompt_sha256':dev.get('prompt_sha256'),'admissible_candidate_count':dev.get('admissible_candidate_count'),'selected':dev.get('selected'),'protected_transfer_count':(dev.get('protected_transfer') or {}).get('transfer_success_count')},'verdict':verdict}
(B/'result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
