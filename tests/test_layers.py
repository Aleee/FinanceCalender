import ast
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent / "base"
FORBIDDEN = ("gui", "PySide6.QtWidgets", "PySide6.QtGui", "pyqtgraph")


def runtime_imports(tree: ast.Module) -> list[str]:
    type_checking_nodes = {id(node) for statement in ast.walk(tree)
                           if isinstance(statement, ast.If) and ast.unparse(statement.test) == "TYPE_CHECKING"
                           for node in ast.walk(statement)}
    names: list[str] = []
    for node in ast.walk(tree):
        if id(node) in type_checking_nodes:
            continue
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


@pytest.mark.parametrize("path", sorted(BASE_DIR.glob("*.py")), ids=lambda path: path.name)
def test_base_does_not_depend_on_gui(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    bad = [name for name in runtime_imports(tree)
           if any(name == forbidden or name.startswith(forbidden + ".") for forbidden in FORBIDDEN)]
    assert bad == []
