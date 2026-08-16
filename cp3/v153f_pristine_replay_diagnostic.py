#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import v145_precompiled_runner  # noqa: F401
import bugsinpy_four_arm as base
import bugsinpy_exact_runtime as exact_runtime
import structured_edit_protocol_v2 as sed
from v153d_rival_payload_projection_diagnostic import project_edit_payloads

T2=("youtube-dl",32)
RAW_ARM="D_PLUS_RAW_T1"
TARGET_FILE="youtube_dl/utils.py"
base.native_test=exact_runtime.native_test


def sha_bytes(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def frozen_payloads(rr: dict[str, Any]) -> tuple[str,str,dict[str,Any]]:
    c1=next(a for a in rr["attempts"] if a.get("call")==1)
    c2=next(a for a in rr["attempts"] if a.get("call")==2)
    p1=sed.extract_edits(c1["response"]["text"]); h1=sha_text(p1)
    accepted,audit=project_edit_payloads(c2["response"]["text"])
    seen=set(); selected=None
    for p in accepted:
        h=p["payload_sha256"]; dup=h in seen; seen.add(h)
        if selected is None and h!=h1 and not dup: selected=p
    if selected is None: raise ValueError("no distinct projected rival")
    return p1,selected["payload"],{"call1_sha256":h1,"rival_sha256":selected["payload_sha256"],"rival_ordinal":selected["ordinal"],"projection_audit":audit}


def replay_mode(bugsinpy: Path,p1: str,p2: str,mode: str,seed: int) -> dict[str,Any]:
    with tempfile.TemporaryDirectory(prefix=f"v153f-{mode}-{seed}-") as td:
        work=base.checkout_buggy(bugsinpy,T2[0],T2[1],Path(td))
        out={"mode":mode,"source_before_sha256":sha_bytes(work/TARGET_FILE)}
        try:
            if mode=="CALL1_STATE_RELATIVE":
                sed.apply_edits(work,p1); out["source_after_call1_sha256"]=sha_bytes(work/TARGET_FILE)
            sed.apply_edits(work,p2); out["source_after_rival_sha256"]=sha_bytes(work/TARGET_FILE)
        except Exception as exc:
            out.update(status="TRANSPORT_FAILURE",error=f"{exc.__class__.__name__}: {exc}")
            return out
        verdict=exact_runtime.native_test(bugsinpy,work)
        out["native_verdict"]=verdict
        if verdict.get("infrastructure_error"): out.update(status="R10",error=verdict["infrastructure_error"])
        elif verdict.get("passed"): out["status"]="VERIFIED_SOLVED"
        else: out["status"]="VERIFIED_FAILED"
        return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--v153-result",type=Path,required=True); ap.add_argument("--bugsinpy",type=Path,required=True); ap.add_argument("--out",type=Path,required=True); args=ap.parse_args()
    if args.out.exists(): raise SystemExit("output exists")
    args.out.mkdir(parents=True)
    srcb=args.v153_result.read_bytes(); src=json.loads(srcb)

    # Mandatory pristine cache seed.
    with tempfile.TemporaryDirectory(prefix="v153f-pristine-") as td:
        work=base.checkout_buggy(args.bugsinpy,T2[0],T2[1],Path(td)); f=work/TARGET_FILE
        before=sha_bytes(f); baseline=exact_runtime.native_test(args.bugsinpy,work); after=sha_bytes(f)
        template_root=v145_precompiled_runner.TEMPLATE_ROOT if False else None
        # import module object only after monkeypatch import above
        import v145_precompiled_runner as apparatus
        marker=apparatus._template(T2[0],T2[1])/".v145_precompiled"
        gate={"source_before_sha256":before,"source_after_sha256":after,"baseline_passed":baseline.get("passed"),"baseline_infrastructure_error":baseline.get("infrastructure_error"),"template_marker_exists":marker.exists()}
        if baseline.get("infrastructure_error") or baseline.get("passed") or before!=after or not marker.exists():
            result={"canonical_id":"V153F_PRISTINE_REPLAY_DIAGNOSTIC","model_calls":0,"pristine_gate":gate,"verdict":"R10_PRISTINE_GATE_FAILURE"}
            (args.out/"V153F_RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(json.dumps(result,indent=2)); return

    rows=[]
    for rr in src.get("rows",{}).get(RAW_ARM,[]):
        row={"seed":rr.get("seed")}
        try: p1,p2,meta=frozen_payloads(rr); row.update(meta)
        except Exception as exc: row.update(status="FROZEN_PAYLOAD_ERROR",error=f"{exc.__class__.__name__}: {exc}"); rows.append(row); continue
        row["baseline_relative"]=replay_mode(args.bugsinpy,p1,p2,"BASELINE_RELATIVE",rr["seed"])
        row["call1_state_relative"]=replay_mode(args.bugsinpy,p1,p2,"CALL1_STATE_RELATIVE",rr["seed"])
        rows.append(row)

    def count(mode,key): return sum(1 for r in rows if r.get(mode,{}).get("status")==key)
    summary={
      "raw_seeds":len(rows),
      "baseline_reaches":sum(1 for r in rows if r.get("baseline_relative",{}).get("status") in {"VERIFIED_FAILED","VERIFIED_SOLVED"}),
      "baseline_solves":count("baseline_relative","VERIFIED_SOLVED"),
      "stateful_reaches":sum(1 for r in rows if r.get("call1_state_relative",{}).get("status") in {"VERIFIED_FAILED","VERIFIED_SOLVED"}),
      "stateful_solves":count("call1_state_relative","VERIFIED_SOLVED"),
      "r10":sum(1 for r in rows for m in ("baseline_relative","call1_state_relative") if r.get(m,{}).get("status")=="R10"),
    }
    result={"canonical_id":"V153F_PRISTINE_REPLAY_DIAGNOSTIC","source_v153_sha256":hashlib.sha256(srcb).hexdigest(),"model_calls":0,"pristine_gate":gate,"rows":rows,"summary":summary,"verdict":"DIAGNOSTIC_V153F_PRISTINE_REPLAY_COMPLETE" if summary["r10"]==0 else "R10_DIAGNOSTIC_INCONCLUSIVE"}
    p=args.out/"V153F_RESULT.json"; p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(p.read_text())

if __name__=="__main__": main()
