#!/usr/bin/env python3
"""
Python function call analyzer for function_graph tool.
Reads entry file, recursively follows local imports, outputs JSON.
"""
import ast
import json
import os
import sys


# ── Call extraction ────────────────────────────────────────────────────────────

def get_calls(func_body):
    """
    Collect call expressions directly inside a function body.
    Does NOT descend into nested function/class definitions.
    """
    calls = []

    def visit(node):
        # Skip nested function/class bodies
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.append({"type": "name", "name": func.id})
            elif isinstance(func, ast.Attribute):
                obj = func.value
                calls.append({
                    "type": "attr",
                    "obj": obj.id if isinstance(obj, ast.Name) else None,
                    "attr": func.attr,
                })
        for child in ast.iter_child_nodes(node):
            visit(child)

    for stmt in func_body:
        visit(stmt)

    return calls


# ── Function collection ────────────────────────────────────────────────────────

def collect_functions(node, class_name, is_module_level):
    """
    Recursively collect function definitions from an AST node.
    - class_name:       enclosing class name (None for module-level / nested)
    - is_module_level:  True only for functions directly under the module
    """
    result = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.append({
                "name": child.name,
                "class_name": class_name,
                "is_top_level": is_module_level,
                "start_line": child.lineno,
                "end_line": child.end_lineno,
                "calls": get_calls(child.body),
            })
            # Collect nested functions (not top-level, same class context)
            result.extend(collect_functions(child, class_name, False))

        elif isinstance(child, ast.ClassDef):
            # Methods are never "top-level" roots
            result.extend(collect_functions(child, child.name, False))

    return result


# ── Import collection ──────────────────────────────────────────────────────────

def resolve_module(module_name, from_dir, level, project_root):
    """Resolve a module name to an absolute file path, or None if external."""
    base = from_dir
    if level > 0:
        for _ in range(level - 1):
            base = os.path.dirname(base)
    else:
        base = project_root

    parts = module_name.split(".") if module_name else []
    as_file = os.path.join(base, *parts) + ".py" if parts else None
    as_pkg  = os.path.join(base, *parts, "__init__.py") if parts else None

    if as_file and os.path.exists(as_file):
        return os.path.normpath(as_file)
    if as_pkg and os.path.exists(as_pkg):
        return os.path.normpath(as_pkg)
    return None


def collect_imports(tree, file_path, project_root):
    """
    Return a list of { local_name, resolved_path } for each imported name.
    resolved_path is None for external / built-in packages.
    """
    imports = []
    file_dir = os.path.dirname(file_path)

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                local = alias.asname if alias.asname else top
                imports.append({
                    "local_name": local,
                    "resolved_path": resolve_module(top, file_dir, 0, project_root),
                })

        elif isinstance(node, ast.ImportFrom):
            level = node.level or 0
            module = node.module or ""
            resolved = resolve_module(module, file_dir, level, project_root) if module else None

            # from . import something  (no module name, just dots)
            if not resolved and level > 0:
                base = file_dir
                for _ in range(level - 1):
                    base = os.path.dirname(base)
                init = os.path.join(base, "__init__.py")
                resolved = os.path.normpath(init) if os.path.exists(init) else None

            for alias in node.names:
                if alias.name == "*":
                    continue
                local = alias.asname if alias.asname else alias.name
                imports.append({
                    "local_name": local,
                    "resolved_path": resolved,
                })

    return imports


# ── Per-file analysis ──────────────────────────────────────────────────────────

def analyze_file(file_path, project_root):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)
    except (SyntaxError, IOError) as e:
        return {"error": str(e), "functions": [], "imports": []}

    return {
        "functions": collect_functions(tree, None, True),
        "imports": collect_imports(tree, file_path, project_root),
    }


# ── Recursive entry ────────────────────────────────────────────────────────────

def analyze_recursive(entry_file):
    entry_file = os.path.normpath(os.path.abspath(entry_file))
    project_root = os.path.dirname(entry_file)
    results = {}
    queue = [entry_file]

    while queue:
        fp = queue.pop(0)
        if fp in results:
            continue
        info = analyze_file(fp, project_root)
        results[fp] = info
        for imp in info.get("imports", []):
            rp = imp.get("resolved_path")
            if rp and rp not in results:
                queue.append(rp)

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: extract.py <entry_file>"}))
        sys.exit(1)
    print(json.dumps(analyze_recursive(sys.argv[1]), ensure_ascii=False))
