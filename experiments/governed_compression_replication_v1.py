#!/usr/bin/env python3
import hashlib,json,statistics
from pathlib import Path
from experiments.developmental_loop_capstone_v1 import exact_l0_closure,enumerate_u,enumerate_installed,select_k,coherent_cegis,one_episode

def main():
    l0=exact_l0_closure(); u7=enumerate_u(7); u9=enumerate_u(9); rows=[]
    for i in range(200,300):
        seed=f"METALOGIC_DEVELOPMENTAL_LOOP_CAPSTONE_V1:{i:03d}"; kt=select_k(seed,l0,u7); k,_=coherent_cegis(kt,u7); inst9=enumerate_installed(k,9)
        joint=[]
        for sem,e in inst9.items():
            if sem in l0 or sem==k.sem or sem not in u9: continue
            joint.append((hashlib.sha256(f"{seed}:FUTURE:{sem}".encode()).hexdigest(),sem,e.size,u9[sem].size))
        joint.sort(); sel=joint[:12]
        if len(sel)<12: rows.append({"seed":seed,"eligible":False,"joint_count":len(joint)}); continue
        M=sum(x[3] for x in sel); D=k.size+4+sum(x[2] for x in sel)
        core=all(one_episode(seed)["gates"][g] for g in ["G1_old_closure_obstruction","G2_nonpreenumerated_verified_synthesis","G3_install_changes_reachability","G7_ablate_restore"])
        rows.append({"seed":seed,"eligible":True,"M":M,"D":D,"ratio":D/M,"saving":M-D,"core":core})
    es=[r for r in rows if r["eligible"]]; wins=[r for r in es if r["D"]<r["M"]]; med=statistics.median(r["ratio"] for r in es); M=sum(r["M"] for r in es); D=sum(r["D"] for r in es)
    gates={"H1":len(es)>=90,"H2":len(wins)>=60,"H3":med<.90,"H4":D<M,"H5":all(r["core"] for r in es)}
    verdict="PASS_GOVERNED_COMPRESSION_REPLICATION_V1" if all(gates.values()) else "VALID_NEGATIVE_GOVERNED_COMPRESSION_REPLICATION_V1"
    result={"protocol":"GOVERNED_COMPRESSION_REPLICATION_V1","eligible":len(es),"wins_D_lt_M":len(wins),"median_D_over_M":med,"population_M":M,"population_D":D,"population_saving":M-D,"gates":gates,"verdict":verdict}
    out=Path("results/governed_compression_replication_v1"); out.mkdir(parents=True,exist_ok=True); (out/"summary.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(json.dumps(result,indent=2)); return 0 if all(gates.values()) else 2
if __name__=="__main__": raise SystemExit(main())
