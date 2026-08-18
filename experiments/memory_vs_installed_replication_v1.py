#!/usr/bin/env python3
import json
from pathlib import Path
from experiments.developmental_loop_capstone_v1 import one_episode, enumerate_u

def main():
    episodes=[]
    u9=enumerate_u(9)
    for i in range(100,200):
        seed=f"METALOGIC_DEVELOPMENTAL_LOOP_CAPSTONE_V1:{i:03d}"
        e=one_episode(seed); o2=e["O2"]["sem"]; B=e["O2"]["B"]
        mem=u9.get(o2); min_u=None if mem is None else mem.size; gap=None if min_u is None else min_u-B
        separator=e["O2"]["development"] and not e["O2"]["memory_inline"]
        core=all(e["gates"][k] for k in ["G1_old_closure_obstruction","G2_nonpreenumerated_verified_synthesis","G3_install_changes_reachability","G7_ablate_restore"])
        episodes.append({"seed":seed,"separator":separator,"B":B,"o2":o2,"min_u_size_le9":min_u,"gap":gap,"core":core})
    nsep=sum(x["separator"] for x in episodes); core=sum(x["core"] for x in episodes)
    positive=0; h3=True
    for x in episodes:
        if x["separator"]:
            if x["min_u_size_le9"] is None: positive+=1
            else:
                h3 &= x["gap"]>0
                positive += x["gap"]>0
    gates={"H1":core==100,"H2":nsep>=35,"H3":bool(h3),"H4":positive>=25}
    verdict="PASS_MEMORY_VS_INSTALLED_REPLICATION_V1" if all(gates.values()) else "VALID_NEGATIVE_MEMORY_VS_INSTALLED_REPLICATION_V1"
    result={"protocol":"MEMORY_VS_INSTALLED_REPLICATION_V1","fresh_seeds":"100..199","core_passes":core,"memory_separators":nsep,"positive_cost_gap_or_censored":positive,"gates":gates,"verdict":verdict}
    out=Path("results/memory_vs_installed_replication_v1"); out.mkdir(parents=True,exist_ok=True); (out/"summary.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2)); return 0 if all(gates.values()) else 2
if __name__=="__main__": raise SystemExit(main())
