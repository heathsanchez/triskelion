from __future__ import annotations

import argparse
import json
from pathlib import Path

from developmental_ir.runtime import (
    CapabilityArchive,
    archive_from_v6_result,
    compile_c_expr,
)


def cmd_export_v6(args):
    archive = archive_from_v6_result(args.result)
    archive.save(args.out)
    print(json.dumps({
        "capabilities": len(archive.ids()),
        "pack_hash": archive.pack_hash(),
        "out": str(args.out),
    }, sort_keys=True))


def cmd_verify_pack(args):
    archive = CapabilityArchive.load(args.pack)
    print(json.dumps({
        "verified": True,
        "capabilities": len(archive.ids()),
        "pack_hash": archive.pack_hash(),
    }, sort_keys=True))


def cmd_emit_c(args):
    archive = CapabilityArchive.load(args.pack)
    term = json.loads(Path(args.term).read_text())
    names = [f"x{i}" for i in range(args.arity)]
    print(compile_c_expr(term, archive, names))


def build_parser():
    p = argparse.ArgumentParser(prog="developmental-ir-v0")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("export-v6", help="export authoritative V6 learned language as a verified pack")
    e.add_argument("--result", required=True, type=Path)
    e.add_argument("--out", required=True, type=Path)
    e.set_defaults(func=cmd_export_v6)

    v = sub.add_parser("verify-pack", help="independently reverify a capability pack")
    v.add_argument("pack", type=Path)
    v.set_defaults(func=cmd_verify_pack)

    c = sub.add_parser("emit-c", help="transparently lower a JSON term to a C uint64 expression")
    c.add_argument("--pack", required=True, type=Path)
    c.add_argument("--term", required=True, type=Path)
    c.add_argument("--arity", required=True, type=int)
    c.set_defaults(func=cmd_emit_c)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
