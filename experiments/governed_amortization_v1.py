#!/usr/bin/env python3
import hashlib,json,statistics
from pathlib import Path
from experiments.developmental_loop_capstone_v1 import exact_l0_closure,enumerate_u,enumerate_installed,select_k,coherent_cegis,one_episode
HORIZONS=[1,2,4,8,12,16,24,32,48,64]
def main():
    l0=exact_l0_closure(); u7=enumerate_u(7); u11=enumerate_u(11); rows=[]
    for i in range(300,400):
        seed=f"METALOGIC_DEVELOPMENTAL_LOOP_CAPSTONE_V1:{i:03d}"; kt=select_k(seed,l0,u7); k,_=coherent_cegis(kt,u7); inst=enumerate_installed(k,11); joint=[]
        for sem,e in inst.items():
            if sem in l0 or sem==k.sem or sem not in u11: continue
            joint.append((hashlib.sha256(f"{seed}:FUTURE:{sem}".encode()).hexdigest(),sem,e.size,u11[sem].size))
        joint.sort()
        if len(joint)<64: rows.append({"seed":seed,"eligible":False,"joint_count":len(joint)}); continue
        seq=joint[:64]; curve={}; first=None
        for n in HORIZONS:
            M=sum(x[3] for x in seq[:n]); D=k.size+4+sum(x[2] for x in seq[:n]); curve[n]={"M":M,"D":D,"ratio":D/M,"saving":M-D}
            if first is None and D<M: first=n
        ep=one_episode(seed); core=all(ep["gates"][g] for g in ["G1_old_closure_obstruction","G2_nonpreenumerated_verified_synthesis","G3_install_changes_reachability","G7_ablate_restore"])
        rows.append({"seed":seed,"eligible":True,"first_break_even":first,"curve":curve,"core":core})
    es=[r for r in rows if r["eligible"]]; wins=[r for r in es if r["curve"][64]["D"]<r["curve"][64]["M"]]; M=sum(r["curve"][64]["M"] for r in es); D=sum(r["curve"][64]["D"] for r in es); ratios=[r["curve"][64]["ratio"] for r in es]; breaks=[r["first_break_even"] for r in es if r["first_break_even"] is not None]
    med=statistics.median(ratios); medb=statistics.median(breaks) if breaks else None; gates={"H1":len(es)>=90,"H2":len(wins)>=60,"H3":D<M,"H4":med<.95,"H5":medb is not None and medb<=32,"H6":all(r["core"] for r in es)}
    verdict="PASS_GOVERNED_AMORTIZATION_V1" if all(gates.values()) else "VALID_NEGATIVE_GOVERNED_AMORTIZATION_V1"; result={"protocol":"GOVERNED_AMORTIZATION_V1","eligible":len(es),"wins_at_64":len(wins),"population_M_64":M,"population_D_64":D,"population_saving_64":M-D,"median_ratio_64":med,"break_even_count":len(breaks),"median_first_break_even":medb,"gates":gates,"verdict":verdict}
    out=Path("results/governed_amortization_v1"); out.mkdir(parents=True,exist_ok=True); (out/"summary.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(json.dumps(result,indent=2)); return 0 if all(gates.values()) else 2
if __name__=="__main__": raise SystemExit(main())
