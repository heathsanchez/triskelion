#!/usr/bin/env python3
import ast, importlib.util, json, os
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v93',HERE/'METALOGIC_V93_MULTISCALE_EDIT_ONTOLOGY.py'); v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
def events_for_function(n):
 try:
  a=ast.parse((v.ROOT/'python_programs'/f'{n}.py').read_text()); b=ast.parse((v.ROOT/'correct_python_programs'/f'{n}.py').read_text())
  fa=next((x for x in a.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))),None); fb=next((x for x in b.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))),None)
  if fa is None or fb is None:return []
  ev=[]; v.diff(fa,fb,(),ev); return ev
 except Exception:return []
v.events_for=events_for_function
v.main()
p=Path(os.environ.get('OUT_DIR','results/v93b'))/'RESULT.json'; r=json.loads(p.read_text()); r['protocol']='V93B_FUNCTION_ONLY_MULTISCALE_EDIT_ONTOLOGY'; r['verdict']='PASS_FUNCTION_ONLY_MULTISCALE_V93B' if all(r['gates'].values()) else 'MIXED_FUNCTION_ONLY_MULTISCALE_V93B'; r['qualification']='Comparator-only correction of V93: identical multiscale cross-validation, but edit extraction is restricted to the target function AST so QuixBugs top-level reference/doc strings cannot dominate recurrence.'; p.write_text(json.dumps(r,indent=2)); print(json.dumps(r,indent=2))
