#!/usr/bin/env python3
import ast, importlib.util, json, os
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v90',HERE/'METALOGIC_V90_PROTECTED_CONSTRUCTOR_CONFIRMATION.py'); v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
def func_ast_eq(a,b):
 try:
  ta,tb=ast.parse(a),ast.parse(b)
  fa=next((x for x in ta.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))),None)
  fb=next((x for x in tb.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))),None)
  if fa is None or fb is None:return False
  return ast.dump(fa,include_attributes=False)==ast.dump(fb,include_attributes=False)
 except Exception:return False
v.ast_eq=func_ast_eq
v.main()
p=Path(os.environ.get('OUT_DIR','results/v90b'))/'RESULT.json'
r=json.loads(p.read_text())
r['protocol']='V90B_PROTECTED_FUNCTION_AUDIT'
r['verdict']='PASS_PROTECTED_FUNCTION_AUDIT_V90B' if all(r['gates'].values()) else 'MIXED_PROTECTED_FUNCTION_AUDIT_V90B'
r['qualification']='Comparator-only correction of V90: identical split, search, candidate commitment and protected-reveal ordering. Protected agreement compares the target function AST, excluding unrelated top-level strings/reference material in QuixBugs correct modules.'
p.write_text(json.dumps(r,indent=2)); print(json.dumps(r,indent=2))
