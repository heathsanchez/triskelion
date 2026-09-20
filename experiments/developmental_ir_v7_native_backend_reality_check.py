#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import re
import statistics
import subprocess
import tempfile
import time

PROTOCOL="DEVELOPMENTAL_IR_V7_NATIVE_BACKEND_REALITY_CHECK"
PRECOMMIT="a820dc2c66789f0d877b68ff7d86bceed8e08c3c"
INVOCATIONS=20_000
OUTER_ITERS=1_000
RUNS=7
MASK64="UINT64_MAX"

def H(*xs:object)->str:
    return hashlib.sha256("|".join(map(str,xs)).encode()).hexdigest()

def hnum(*xs:object)->int:
    return int(H(*xs)[:16],16)

def parse_expr(s:str):
    s=s.strip()
    i=0
    def rec():
        nonlocal i
        if s.startswith("D(",i):
            i+=2
            a=rec()
            assert s[i]==","
            i+=1
            b=rec()
            assert s[i]==")"
            i+=1
            return ("D",a,b)
        j=i
        while i<len(s) and (s[i].isalnum() or s[i]=="_"):
            i+=1
        tok=s[j:i]
        assert tok
        return tok
    e=rec()
    assert i==len(s)
    return e

def expr_cost(e)->int:
    if isinstance(e,str): return 0
    return 1+expr_cost(e[1])+expr_cost(e[2])

def expr_eval(e,arity:int)->int:
    rows=1<<arity
    mask=(1<<rows)-1
    def var(j:int)->int:
        out=0
        for r in range(rows):
            if (r>>j)&1: out|=1<<r
        return out
    if isinstance(e,str):
        if e=="1": return mask
        if e.startswith("x"): return var(int(e[1:]))
        raise KeyError(e)
    a=expr_eval(e[1],arity); b=expr_eval(e[2],arity)
    return ((~a)&mask)&b

def c_expr(e,args:list[str])->str:
    if isinstance(e,str):
        if e=="1": return MASK64
        if e.startswith("x"): return args[int(e[1:])]
        raise KeyError(e)
    return f"((~({c_expr(e[1],args)})) & ({c_expr(e[2],args)}))"

def load_language():
    p=Path("results/developmental_ir_v6_blind_grammar_expansion/result.json")
    data=json.loads(p.read_text())
    rows=data["final_language"]
    macros=[]
    ok=True
    for idx,row in enumerate(rows):
        ar=int(row["arity"]); table=int(row["table"])
        e=parse_expr(row["expression"])
        verified=expr_eval(e,ar)==table
        ok &= verified
        macros.append({
            "idx":idx,"arity":ar,"table":table,"expr":e,
            "cost":int(row["cost"]),"reuse":int(row["frozen_reuse"]),
            "verified":verified,
        })
    assert len(macros)==24
    return macros,ok

def choose_weighted(macros:list[dict],j:int)->int:
    weights=[max(1,int(m["reuse"])) for m in macros]
    total=sum(weights)
    x=hnum("DIR-V7-MACRO",j)%total
    s=0
    for i,w in enumerate(weights):
        s+=w
        if x<s: return i
    return len(macros)-1

def invocation_stream(macros:list[dict]):
    out=[]
    for j in range(INVOCATIONS):
        mi=choose_weighted(macros,j)
        ar=macros[mi]["arity"]
        args=[hnum("DIR-V7-ARG",j,k)%8 for k in range(ar)]
        dst=hnum("DIR-V7-DST",j)%8
        out.append((mi,args,dst))
    return out

def generate_source(kind:str,macros:list[dict],stream:list[tuple],top6:set[int])->str:
    lines=[
        "#include <stdint.h>",
        "#include <inttypes.h>",
        "#include <stdio.h>",
        "#include <stdlib.h>",
        "#include <time.h>",
        "",
        "static inline uint64_t mix64(uint64_t x) {",
        "  x ^= x >> 30; x *= UINT64_C(0xbf58476d1ce4e5b9);",
        "  x ^= x >> 27; x *= UINT64_C(0x94d049bb133111eb);",
        "  x ^= x >> 31; return x;",
        "}",
        "",
    ]
    if kind!="expanded":
        for m in macros:
            quals="static inline"
            if kind=="outline" or (kind=="hybrid" and m["idx"] not in top6):
                quals="__attribute__((noinline)) static"
            params=", ".join(f"uint64_t x{k}" for k in range(m["arity"]))
            body=c_expr(m["expr"],[f"x{k}" for k in range(m["arity"])])
            lines.append(f"{quals} uint64_t cap_{m['idx']}({params}) {{ return {body}; }}")
        lines.append("")
    lines += [
        "int main(int argc, char **argv) {",
        "  uint64_t seed = argc > 1 ? strtoull(argv[1], NULL, 0) : UINT64_C(1);",
        "  uint64_t r[8];",
        "  for (int i=0;i<8;i++) r[i]=mix64(seed + (uint64_t)i*UINT64_C(0x9e3779b97f4a7c15));",
        "  struct timespec t0,t1;",
        "  clock_gettime(CLOCK_MONOTONIC, &t0);",
        f"  for (int outer=0; outer<{OUTER_ITERS}; ++outer) {{",
    ]
    for mi,args,dst in stream:
        m=macros[mi]
        argv=[f"r[{a}]" for a in args]
        if kind=="expanded":
            rhs=c_expr(m["expr"],argv)
        else:
            rhs=f"cap_{mi}("+", ".join(argv)+")"
        lines.append(f"    r[{dst}] = {rhs};")
    lines += [
        "    r[outer & 7] ^= mix64((uint64_t)outer + seed);",
        "  }",
        "  clock_gettime(CLOCK_MONOTONIC, &t1);",
        "  uint64_t checksum=0;",
        "  for (int i=0;i<8;i++) checksum ^= mix64(r[i] + (uint64_t)i);",
        "  uint64_t ns=(uint64_t)(t1.tv_sec-t0.tv_sec)*UINT64_C(1000000000) + (uint64_t)(t1.tv_nsec-t0.tv_nsec);",
        "  printf(\"checksum=%\" PRIu64 \" ns=%\" PRIu64 \"\\n\", checksum, ns);",
        "  return 0;",
        "}",
        "",
    ]
    return "\n".join(lines)

def text_size(binary:Path)->int:
    out=subprocess.check_output(["size","-A",str(binary)],text=True)
    for line in out.splitlines():
        parts=line.split()
        if parts and parts[0]==".text":
            return int(parts[1])
    raise RuntimeError("missing .text")

def compile_one(src:Path,binp:Path)->float:
    t=time.perf_counter()
    subprocess.run(["gcc","-O3","-std=c11","-D_POSIX_C_SOURCE=200809L",str(src),"-o",str(binp)],check=True)
    return time.perf_counter()-t

def run_one(binary:Path)->tuple[int,int]:
    out=subprocess.check_output([str(binary),"0x123456789abcdef"],text=True)
    m=re.search(r"checksum=(\d+) ns=(\d+)",out)
    if not m: raise RuntimeError(out)
    return int(m.group(1)),int(m.group(2))

def run_experiment():
    macros,verified=load_language()
    stream=invocation_stream(macros)
    top6={m["idx"] for m in sorted(macros,key=lambda x:(x["reuse"],x["cost"],-x["idx"]),reverse=True)[:6]}
    kinds=("expanded","inline","outline","hybrid")

    srcs={k:generate_source(k,macros,stream,top6) for k in kinds}
    srcs2={k:generate_source(k,macros,stream,top6) for k in kinds}
    source_hashes={k:hashlib.sha256(srcs[k].encode()).hexdigest() for k in kinds}
    regen_ok=all(srcs[k]==srcs2[k] for k in kinds)
    stream_hash=hashlib.sha256(json.dumps(stream,separators=(",",":")).encode()).hexdigest()
    stream_hash2=hashlib.sha256(json.dumps(invocation_stream(macros),separators=(",",":")).encode()).hexdigest()

    metrics={}
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        for k in kinds:
            src=root/f"{k}.c"; binp=root/k
            src.write_text(srcs[k])
            ctime=compile_one(src,binp)
            checks=[]; times=[]
            for _ in range(RUNS):
                ch,ns=run_one(binp)
                checks.append(ch); times.append(ns)
            metrics[k]={
                "source_bytes":src.stat().st_size,
                "compile_seconds":ctime,
                "executable_bytes":binp.stat().st_size,
                "text_bytes":text_size(binp),
                "checksums":checks,
                "times_ns":times,
                "median_ns":int(statistics.median(times)),
            }

    all_checks=[m["checksums"] for m in metrics.values()]
    same_checksum=all(len(set(xs))==1 for xs in all_checks) and len({xs[0] for xs in all_checks})==1
    fastest=min(metrics["expanded"]["median_ns"],metrics["inline"]["median_ns"])

    gates={
        "N1_all_24_macros_reverified":verified,
        "N2_all_four_binaries_compile":len(metrics)==4,
        "N3_all_checksums_identical":same_checksum,
        "N4_inline_runtime_le_115pct_expanded":metrics["inline"]["median_ns"]<=1.15*metrics["expanded"]["median_ns"],
        "N5_outline_text_lt_60pct_expanded":metrics["outline"]["text_bytes"]<0.60*metrics["expanded"]["text_bytes"],
        "N6_hybrid_text_lt_75pct_expanded":metrics["hybrid"]["text_bytes"]<0.75*metrics["expanded"]["text_bytes"],
        "N7_hybrid_runtime_le_125pct_fastest":metrics["hybrid"]["median_ns"]<=1.25*fastest,
        "N8_inline_source_lt_35pct_expanded":metrics["inline"]["source_bytes"]<0.35*metrics["expanded"]["source_bytes"],
        "N9_outline_source_lt_35pct_expanded":metrics["outline"]["source_bytes"]<0.35*metrics["expanded"]["source_bytes"],
        "N10_hybrid_source_lt_35pct_expanded":metrics["hybrid"]["source_bytes"]<0.35*metrics["expanded"]["source_bytes"],
        "N11_some_nonexpanded_compiles_faster":min(metrics[k]["compile_seconds"] for k in ("inline","outline","hybrid"))<metrics["expanded"]["compile_seconds"],
        "N12_deterministic_regeneration":regen_ok and stream_hash==stream_hash2,
    }
    return {
        "macro_count":len(macros),
        "top6_inline_macro_indices":sorted(top6),
        "invocation_stream_hash":stream_hash,
        "source_hashes":source_hashes,
        "metrics":metrics,
        "gates":gates,
    }

def main()->int:
    r=run_experiment()
    gates=r["gates"]
    verdict="PASS_DEVELOPMENTAL_IR_V7_NATIVE_BACKEND_REALITY_CHECK" if all(gates.values()) else ("PARTIAL_DEVELOPMENTAL_IR_V7_NATIVE_BACKEND_REALITY_CHECK" if any(gates.values()) else "VALID_NEGATIVE_DEVELOPMENTAL_IR_V7_NATIVE_BACKEND_REALITY_CHECK")
    result={
        "protocol":PROTOCOL,"precommit_commit":PRECOMMIT,"verdict":verdict,
        "macro_count":r["macro_count"],"top6_inline_macro_indices":r["top6_inline_macro_indices"],
        "invocation_stream_hash":r["invocation_stream_hash"],"source_hashes":r["source_hashes"],
        "metrics":r["metrics"],"headline_gates":gates,
        "claim_boundary":"Native GCC reality check on one deterministic 64-bit Boolean workload. Runtime timing is runner-specific. A positive result supports backend engineering tradeoffs; it does not validate CAP=1 as literal CPU cost."
    }
    out=Path("results/developmental_ir_v7_native_backend_reality_check"); out.mkdir(parents=True,exist_ok=True)
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    summary={k:result[k] for k in ("verdict","macro_count","top6_inline_macro_indices","metrics","headline_gates","invocation_stream_hash")}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("="*110)
    print("DEVELOPMENTAL IR V7 — NATIVE BACKEND REALITY CHECK")
    print("="*110)
    print("verdict",verdict)
    for k,m in r["metrics"].items():
        print(k,json.dumps({x:m[x] for x in ("source_bytes","compile_seconds","executable_bytes","text_bytes","median_ns")},sort_keys=True))
    for k,v in gates.items(): print(k,"PASS" if v else "FAIL")
    print("stream_hash",r["invocation_stream_hash"])
    return 0

if __name__=="__main__":
    raise SystemExit(main())
