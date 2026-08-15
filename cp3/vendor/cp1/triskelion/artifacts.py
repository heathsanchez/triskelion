from __future__ import annotations

import ast


class _GuardZeroDivision(ast.NodeTransformer):
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.generic_visit(node)
        if len(node.args.args) < 2:
            return node
        denominator = node.args.args[-1].arg
        division_returns = [
            item for item in node.body
            if isinstance(item, ast.Return)
            and isinstance(item.value, ast.BinOp)
            and isinstance(item.value.op, ast.Div)
            and isinstance(item.value.right, ast.Name)
            and item.value.right.id == denominator
        ]
        if not division_returns:
            return node
        guard = ast.If(
            test=ast.Compare(
                left=ast.Name(id=denominator, ctx=ast.Load()),
                ops=[ast.Eq()], comparators=[ast.Constant(value=0)],
            ),
            body=[ast.Return(value=ast.Constant(value=0.0))], orelse=[],
        )
        node.body.insert(0, guard)
        return node


class _RoundDivision(ast.NodeTransformer):
    def visit_Return(self, node: ast.Return) -> ast.AST:
        self.generic_visit(node)
        if isinstance(node.value, ast.BinOp) and isinstance(node.value.op, ast.Div):
            node.value = ast.Call(
                func=ast.Name(id="round", ctx=ast.Load()),
                args=[node.value, ast.Constant(value=2)], keywords=[],
            )
        return node


def guard_zero_division(source: str) -> str:
    tree = _GuardZeroDivision().visit(ast.parse(source))
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n"


def round_division(source: str) -> str:
    tree = _RoundDivision().visit(ast.parse(source))
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n"


ARTIFACTS = {
    "guard_zero_division": guard_zero_division,
    "round_division": round_division,
}


def apply_artifact(name: str, source: str) -> str:
    try:
        return ARTIFACTS[name](source)
    except KeyError as exc:
        raise ValueError(f"unknown artifact: {name}") from exc
