#!/usr/bin/env python3
"""
Go function call analyzer for the function_graph tool.
Outputs JSON in the same format as the Python extractor.
"""

import re
import sys
import json
import os
import bisect

# ── Constants ──────────────────────────────────────────────────────────────────

# Go built-ins and keywords that should not appear as calls
GO_CALL_EXCLUDE = frozenset([
    'if', 'else', 'for', 'switch', 'select', 'case', 'default',
    'return', 'defer', 'go', 'chan', 'func', 'type', 'var', 'const',
    'package', 'import', 'break', 'continue', 'goto', 'fallthrough',
    # Built-in functions
    'make', 'new', 'append', 'len', 'cap', 'delete', 'copy',
    'close', 'panic', 'recover', 'print', 'println',
    'complex', 'real', 'imag',
    # Type conversions (common)
    'int', 'int8', 'int16', 'int32', 'int64',
    'uint', 'uint8', 'uint16', 'uint32', 'uint64', 'uintptr',
    'float32', 'float64', 'complex64', 'complex128',
    'bool', 'string', 'byte', 'rune', 'error', 'any',
])

# Go function definition regex
# Matches: func [( receiver )] Name [TypeParams] (
FUNC_RE = re.compile(
    r'^func\s+'
    r'(?:\(([^)]*)\)\s+)?'          # Optional receiver: (r ReceiverType) or (r *ReceiverType)
    r'([a-zA-Z_][a-zA-Z0-9_]*)'    # Function name
    r'\s*(?:\[[^\]]*\])?\s*'        # Optional type parameters [T any]
    r'\(',                           # Opening paren of parameter list
    re.MULTILINE,
)


# ── Source cleaning ────────────────────────────────────────────────────────────

def clean_source(source):
    """Remove Go comments and string/rune literals, preserving newlines."""
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

        # Raw string literal `...`
        elif source[i] == '`':
            i += 1
            while i < n and source[i] != '`':
                out.append('\n' if source[i] == '\n' else ' ')
                i += 1
            i += 1  # closing `

        # Interpreted string literal "..."
        elif source[i] == '"':
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

        # Rune literal '...'
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


# ── Receiver / package utilities ───────────────────────────────────────────────

def parse_receiver_type(recv_str):
    """Extract the base type name from a receiver like '(r *MyType)' or '(c Calculator)'."""
    if not recv_str:
        return None
    m = re.search(r'\*?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\[[^\]]*\])?\s*$', recv_str.strip())
    return m.group(1) if m else None


def get_package_name(file_path):
    """Extract Go package name from file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith('//') or not line:
                    continue
                if line.startswith('package '):
                    parts = line.split()
                    return parts[1] if len(parts) > 1 else None
                break
    except IOError:
        pass
    return None


def find_same_package_files(entry_file):
    """Return all .go files in the same directory with the same package name."""
    dir_path = os.path.dirname(entry_file)
    pkg = get_package_name(entry_file)
    result = []
    try:
        for fname in sorted(os.listdir(dir_path)):
            if not fname.endswith('.go') or fname.endswith('_test.go'):
                continue
            fpath = os.path.normpath(os.path.join(dir_path, fname))
            if fpath != entry_file and get_package_name(fpath) == pkg:
                result.append(fpath)
    except OSError:
        pass
    return result


# ── Import resolution ──────────────────────────────────────────────────────────

def find_go_mod(start_dir):
    """Walk up from start_dir looking for go.mod, return (module_name, module_root)."""
    d = start_dir
    while True:
        mod_path = os.path.join(d, 'go.mod')
        if os.path.exists(mod_path):
            try:
                with open(mod_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('module '):
                            return line.split()[1], d
            except IOError:
                pass
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return None, None


def parse_go_imports(source, file_path):
    """
    Parse Go import declarations.
    Returns list of {local_name, resolved_path}.
    resolved_path is None for external packages.
    """
    dir_path = os.path.dirname(file_path)
    module_name, module_root = find_go_mod(dir_path)

    imports = []

    # Collect all import paths from single and block imports
    import_entries = []

    # Single: import "pkg"  or  import alias "pkg"
    for m in re.finditer(r'^import\s+(?:([a-zA-Z_][a-zA-Z0-9_]*)\s+)?"([^"]+)"',
                         source, re.MULTILINE):
        alias, pkg_path = m.group(1), m.group(2)
        import_entries.append((alias, pkg_path))

    # Block: import ( ... )
    for block_m in re.finditer(r'\bimport\s*\(([^)]+)\)', source, re.DOTALL):
        for line in block_m.group(1).splitlines():
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            m = re.match(r'^(?:([a-zA-Z_][a-zA-Z0-9_]*)\s+)?"([^"]+)"', line)
            if m:
                import_entries.append((m.group(1), m.group(2)))

    for alias, pkg_path in import_entries:
        pkg_name = alias or pkg_path.split('/')[-1]
        resolved = None

        # Try to resolve to a local directory
        if module_root and module_name and pkg_path.startswith(module_name):
            rel = pkg_path[len(module_name):].lstrip('/')
            pkg_dir = os.path.normpath(os.path.join(module_root, rel))
            if os.path.isdir(pkg_dir):
                # Find first non-test .go file in that package
                for fname in sorted(os.listdir(pkg_dir)):
                    if fname.endswith('.go') and not fname.endswith('_test.go'):
                        resolved = os.path.normpath(os.path.join(pkg_dir, fname))
                        break

        imports.append({'local_name': pkg_name, 'resolved_path': resolved})

    return imports


# ── Call extraction ────────────────────────────────────────────────────────────

def find_go_calls(body):
    """Find function/method call expressions inside a Go function body."""
    calls = []
    seen = set()

    for m in re.finditer(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', body):
        name = m.group(1)
        if name in GO_CALL_EXCLUDE:
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

    return calls


# ── Function body extraction ───────────────────────────────────────────────────

def find_body_end(cleaned, brace_start):
    """Find the position of the closing '}' matching the '{' at brace_start."""
    depth = 0
    i = brace_start
    n = len(cleaned)
    while i < n:
        if cleaned[i] == '{':
            depth += 1
        elif cleaned[i] == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


# ── File parser ────────────────────────────────────────────────────────────────

def parse_file(file_path):
    """Parse a Go source file and return extracted function/import data."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
    except IOError as e:
        return {'error': str(e), 'functions': [], 'imports': []}

    imports = parse_go_imports(source, file_path)
    cleaned = clean_source(source)
    line_starts = build_line_map(cleaned)

    functions = []

    for m in FUNC_RE.finditer(cleaned):
        recv_str = m.group(1)   # None for free functions
        func_name = m.group(2)

        # Find opening { of function body
        # In Go, '{' must be on the same line as the signature (no line break before {)
        brace_start = cleaned.find('{', m.end())
        if brace_start < 0:
            continue

        brace_end = find_body_end(cleaned, brace_start)
        if brace_end < 0:
            continue

        body = cleaned[brace_start + 1:brace_end]
        calls = find_go_calls(body)

        class_name = parse_receiver_type(recv_str) if recv_str else None
        start_line = pos_to_line(m.start(), line_starts)
        end_line = pos_to_line(brace_end, line_starts)

        functions.append({
            'name': func_name,
            'class_name': class_name,
            'is_top_level': True,
            'start_line': start_line,
            'end_line': end_line,
            'calls': calls,
        })

    return {'functions': functions, 'imports': imports}


# ── Recursive analysis ─────────────────────────────────────────────────────────

def analyze_recursive(entry_file):
    entry_file = os.path.normpath(os.path.abspath(entry_file))
    results = {}

    # Start with entry file + all same-package files
    queue = [entry_file] + find_same_package_files(entry_file)

    while queue:
        fp = queue.pop(0)
        if fp in results:
            continue
        info = parse_file(fp)
        results[fp] = info
        for imp in info.get('imports', []):
            rp = imp.get('resolved_path')
            if rp and rp not in results:
                # Also pull in all .go files from that package directory
                pkg_dir = os.path.dirname(rp)
                try:
                    for fname in sorted(os.listdir(pkg_dir)):
                        if fname.endswith('.go') and not fname.endswith('_test.go'):
                            fpath = os.path.normpath(os.path.join(pkg_dir, fname))
                            if fpath not in results:
                                queue.append(fpath)
                except OSError:
                    queue.append(rp)

    return results


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'usage: extract_go.py <entry_file>'}))
        sys.exit(1)
    print(json.dumps(analyze_recursive(sys.argv[1]), ensure_ascii=False))
