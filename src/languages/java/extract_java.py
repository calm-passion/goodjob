#!/usr/bin/env python3
"""
Java function call analyzer for the function_graph tool.
Outputs JSON in the same format as the Python extractor.
"""

import re
import sys
import json
import os
import bisect

# ── Constants ──────────────────────────────────────────────────────────────────

JAVA_MODIFIERS = frozenset([
    'public', 'private', 'protected', 'static', 'final', 'abstract',
    'synchronized', 'native', 'default', 'strictfp', 'transient', 'volatile',
])

JAVA_CONTROL_FLOW = frozenset([
    'if', 'else', 'while', 'for', 'switch', 'do', 'try', 'catch',
    'finally', 'return', 'throw', 'break', 'continue', 'case',
    'default', 'assert', 'instanceof',
])

JAVA_KEYWORDS = JAVA_MODIFIERS | JAVA_CONTROL_FLOW | frozenset([
    'class', 'interface', 'enum', 'extends', 'implements', 'import',
    'package', 'new', 'super', 'this', 'null', 'true', 'false', 'void',
    'int', 'long', 'double', 'float', 'boolean', 'char', 'byte', 'short',
])

JAVA_CALL_EXCLUDE = JAVA_CONTROL_FLOW | frozenset([
    'new', 'super', 'this', 'assert', 'instanceof',
    'void', 'int', 'long', 'double', 'float', 'boolean', 'char', 'byte', 'short',
    'synchronized',
])


# ── Source cleaning ────────────────────────────────────────────────────────────

def clean_source(source):
    """Remove Java comments and string/char literals, preserving newlines."""
    out = []
    i = 0
    n = len(source)

    while i < n:
        # Block comment /* ... */
        if source[i:i+2] == '/*':
            j = source.find('*/', i + 2)
            if j == -1:
                out.append('\n' * source[i:].count('\n'))
                break
            out.append('\n' * source[i:j+2].count('\n'))
            i = j + 2

        # Line comment // ...
        elif source[i:i+2] == '//':
            j = source.find('\n', i)
            out.append('\n')
            i = (j + 1) if j != -1 else n

        # String literal "..."
        elif source[i] == '"':
            # Check for text block """...""" (Java 13+)
            if source[i:i+3] == '"""':
                j = source.find('"""', i + 3)
                if j == -1:
                    out.append('\n' * source[i:].count('\n'))
                    break
                out.append('\n' * source[i:j+3].count('\n'))
                i = j + 3
            else:
                out.append('"')
                i += 1
                while i < n:
                    if source[i] == '\\':
                        out.append(' ')
                        i = min(i + 2, n)
                    elif source[i] == '"':
                        out.append('"')
                        i += 1
                        break
                    else:
                        out.append('\n' if source[i] == '\n' else ' ')
                        i += 1

        # Char literal '...'
        elif source[i] == "'":
            i += 1
            while i < n:
                if source[i] == '\\':
                    i = min(i + 2, n)
                elif source[i] == "'":
                    i += 1
                    break
                else:
                    i += 1

        else:
            out.append(source[i])
            i += 1

    return ''.join(out)


# ── Line number utilities ──────────────────────────────────────────────────────

def build_line_map(source):
    starts = [0]
    for idx, ch in enumerate(source):
        if ch == '\n':
            starts.append(idx + 1)
    return starts


def pos_to_line(pos, line_starts):
    return bisect.bisect_right(line_starts, pos)


# ── Signature parsing ──────────────────────────────────────────────────────────

def try_parse_java_class(sig):
    """Try to interpret sig as a Java class/interface/enum/record declaration."""
    m = re.search(
        r'\b(?:class|interface|enum|record)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        sig,
    )
    if m:
        return {'name': m.group(1)}
    return None


def try_parse_java_method(sig, current_class):
    """
    Try to interpret sig as a Java method or constructor definition.
    Returns {'name': str, 'class_name': str|None} or None.
    """
    sig = sig.strip()
    if not sig:
        return None

    # Remove annotations: @Override, @SuppressWarnings("unchecked"), etc.
    sig = re.sub(r'@\w+(?:\s*\([^)]*\))?\s*', '', sig).strip()
    if not sig:
        return None

    # Remove 'throws ExceptionType, ...' clause
    sig = re.sub(r'\s+throws\s+\w+(?:\s*,\s*\w+)*\s*$', '', sig).strip()

    if not sig.endswith(')'):
        return None

    # Find matching '(' from the end (accounts for generic params in arg types)
    depth = 0
    paren_open = -1
    for k in range(len(sig) - 1, -1, -1):
        if sig[k] == ')':
            depth += 1
        elif sig[k] == '(':
            depth -= 1
            if depth == 0:
                paren_open = k
                break
    if paren_open < 0:
        return None

    before_paren = sig[:paren_open].strip()
    if not before_paren:
        return None

    # Lambda or assignment: has '=' before name
    if '=' in before_paren:
        return None

    # Find method name: last identifier before '('
    name_m = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*$', before_paren)
    if not name_m:
        return None

    method_name = name_m.group(1)

    # Must not be a Java keyword
    if method_name in JAVA_KEYWORDS:
        return None

    # Token before the method name must not be a control-flow keyword
    before_name = before_paren[:name_m.start()].strip()
    if before_name:
        prev_tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', before_name)
        if prev_tokens and prev_tokens[-1] in JAVA_CONTROL_FLOW:
            return None

    return {'name': method_name, 'class_name': current_class}


# ── Call extraction ────────────────────────────────────────────────────────────

def find_java_calls(body):
    """Find method call expressions inside a Java method body."""
    calls = []
    seen = set()

    for m in re.finditer(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', body):
        name = m.group(1)
        if name in JAVA_CALL_EXCLUDE:
            continue

        before = body[:m.start()].rstrip()

        if before.endswith('.'):
            obj_m = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\.\s*$', before)
            obj = obj_m.group(1) if obj_m else None
            key = ('attr', obj, name)
            if key not in seen:
                seen.add(key)
                calls.append({'type': 'attr', 'obj': obj, 'attr': name})
        else:
            key = ('name', name)
            if key not in seen:
                seen.add(key)
                calls.append({'type': 'name', 'name': name})

    # new ClassName(...)  →  constructor call
    for m in re.finditer(r'\bnew\s+([a-zA-Z_][a-zA-Z0-9_$]*(?:<[^>]*>)?)\s*\(', body):
        cls = re.sub(r'<.*>', '', m.group(1)).strip()
        key = ('name', cls)
        if key not in seen:
            seen.add(key)
            calls.append({'type': 'name', 'name': cls})

    return calls


# ── Import resolution ──────────────────────────────────────────────────────────

def find_java_source(class_name, project_root):
    """Search project_root recursively for ClassName.java."""
    target = class_name + '.java'
    for root, dirs, files in os.walk(project_root):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in ('build', 'target', '.gradle', 'out', 'bin')]
        if target in files:
            return os.path.normpath(os.path.join(root, target))
    return None


def get_java_imports(source, file_path, project_root):
    """
    Parse Java import statements.
    Returns list of {local_name, resolved_path}.
    """
    imports = []

    for m in re.finditer(r'^import\s+(?:static\s+)?([^\s;]+)\s*;', source, re.MULTILINE):
        full = m.group(1).strip()
        if full.endswith('*'):
            continue  # wildcard imports skipped
        parts = full.split('.')
        class_name = parts[-1]
        src = find_java_source(class_name, project_root)
        imports.append({'local_name': class_name, 'resolved_path': src})

    return imports


# ── File parser ────────────────────────────────────────────────────────────────

def parse_file(file_path, project_root):
    """Parse a Java source file and return extracted function/import data."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
    except IOError as e:
        return {'error': str(e), 'functions': [], 'imports': []}

    imports = get_java_imports(source, file_path, project_root)
    cleaned = clean_source(source)
    line_starts = build_line_map(cleaned)

    functions = []
    n = len(cleaned)
    i = 0

    stack = []
    brace_depth = 0
    sig_buf = []

    def current_class():
        for entry in reversed(stack):
            if entry['type'] == 'class':
                return entry['name']
        return None

    while i < n:
        ch = cleaned[i]

        if ch == '{':
            sig = ''.join(sig_buf).strip()
            sig_buf = []
            start_line = pos_to_line(i, line_starts)
            pushed = False

            cls_info = try_parse_java_class(sig)
            if cls_info:
                stack.append({
                    'type': 'class', 'name': cls_info['name'],
                    'class_name': None, 'depth': brace_depth,
                    'start_line': start_line, 'body_start': i + 1,
                })
                pushed = True

            if not pushed:
                method_info = try_parse_java_method(sig, current_class())
                if method_info:
                    stack.append({
                        'type': 'func',
                        'name': method_info['name'],
                        'class_name': method_info['class_name'],
                        'depth': brace_depth,
                        'start_line': start_line,
                        'body_start': i + 1,
                    })
                    pushed = True

            if not pushed:
                stack.append({
                    'type': 'other', 'name': None,
                    'class_name': None, 'depth': brace_depth,
                    'start_line': start_line, 'body_start': i + 1,
                })

            brace_depth += 1

        elif ch == '}':
            brace_depth -= 1
            sig_buf = []

            if stack and stack[-1]['depth'] == brace_depth:
                entry = stack.pop()
                if entry['type'] == 'func':
                    body = cleaned[entry['body_start']:i]
                    calls = find_java_calls(body)
                    functions.append({
                        'name': entry['name'],
                        'class_name': entry['class_name'],
                        'is_top_level': True,
                        'start_line': entry['start_line'],
                        'end_line': pos_to_line(i, line_starts),
                        'calls': calls,
                    })

        elif ch == ';':
            # Reset sig buffer after field declarations / statements at class scope
            # Only reset when we're at a class body depth (not inside a method)
            class_depths = {e['depth'] + 1 for e in stack if e['type'] == 'class'}
            if brace_depth in class_depths or brace_depth == 0:
                sig_buf = []

        else:
            sig_buf.append(ch)

        i += 1

    return {'functions': functions, 'imports': imports}


# ── Recursive analysis ─────────────────────────────────────────────────────────

def find_same_dir_java_files(entry_file):
    """Return all .java files in the same directory (same package/compilation unit)."""
    dir_path = os.path.dirname(entry_file)
    result = []
    try:
        for fname in sorted(os.listdir(dir_path)):
            if fname.endswith('.java'):
                fpath = os.path.normpath(os.path.join(dir_path, fname))
                if fpath != entry_file:
                    result.append(fpath)
    except OSError:
        pass
    return result


def analyze_recursive(entry_file):
    entry_file = os.path.normpath(os.path.abspath(entry_file))
    project_root = os.path.dirname(entry_file)
    results = {}

    # Include all .java files in the same directory (same package)
    queue = [entry_file] + find_same_dir_java_files(entry_file)

    while queue:
        fp = queue.pop(0)
        if fp in results:
            continue
        info = parse_file(fp, project_root)
        results[fp] = info
        for imp in info.get('imports', []):
            rp = imp.get('resolved_path')
            if rp and rp not in results:
                queue.append(rp)

    return results


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'usage: extract_java.py <entry_file>'}))
        sys.exit(1)
    print(json.dumps(analyze_recursive(sys.argv[1]), ensure_ascii=False))
