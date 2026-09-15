from argparse import ArgumentParser, ArgumentTypeError, Namespace
import ast
import os


class AnnotateFunction(ast.NodeTransformer):
    """Traverses an AST and add an annotation to the function at line."""

    def __init__(self, lineno, annotation):
        self.lineno = lineno
        self.annotation = annotation

    def visit_FunctionDef(self, node):
        if node.lineno <= self.lineno and self.lineno <= node.end_lineno:
            decorator = ast.Name(id=self.annotation, ctx=ast.Load())
            if not hasattr(node, "decorator_list"):
                node.decorator_list = []
            node.decorator_list.insert(0, decorator)
        return self.generic_visit(node)


def annotate(code: str, lineno: int, annotation: str):
    """Add an annotation to a function at a lineno."""
    src_tree = ast.parse(code)
    transformer = AnnotateFunction(lineno, annotation)
    mod_tree = transformer.visit(src_tree)
    ast.fix_missing_locations(mod_tree)
    return ast.unparse(mod_tree)


def parse_test_case(spec: str) -> tuple[str, int, int]:
    """Parse a test case specification (i.e, 'filename,lineno<,priority>') into a tuple"""
    try:
        parts = spec.split(",")
        filename = os.path.abspath(parts[0])
        lineno = int(parts[1])
        priority = int(parts[2]) if len(parts) == 3 else None
        return (filename, lineno, priority)
    except Exception as e:
        raise ArgumentTypeError(f"Invalid format: '{spec}'. Must be in 'filename,lineno<,priority>' format (e.g., main.py,12,4).")


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        "-t", 
        "--test",
        type=parse_test_case,
        action="append",
        default=[],
        help='a pytest test case in "filename,lineno<,priority>" format (repeat args for additional cases).',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for filename, lineno, priority in args.test:
        with open(filename, "r") as file:
            src_code = file.read()
        annotation = "pytest.mark.skip()" if priority is None else f"pytest.mark.order({priority})"
        mod_code = annotate(code=src_code, lineno=lineno, annotation=annotation)
        with open(filename, "w") as file:
            file.write(mod_code)


if __name__ == "__main__":
    main()
