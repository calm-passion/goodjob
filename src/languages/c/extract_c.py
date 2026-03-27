#!/usr/bin/env python3
"""
C/C++ function call analyzer for the function_graph tool.
Handles C (.c/.h) and C++ (.cpp/.cc/.cxx/.hpp) files.
Outputs JSON in the same format as the Python extractor.
"""

import re
import sys
import json
import os
import bisect

# ── Constants ──────────────────────────────────────────────────────────────────

CPP_EXTS = frozenset(['.cpp', '.cc', '.cxx', '.hpp', '.hxx'])

CONTROL_FLOW_KWS = frozenset([
    'if', 'else', 'while', 'for', 'switch', 'do', 'return',
    'goto', 'break', 'continue', 'case', 'default',
    'catch', 'try', 'throw',
])

FUNC_NAME_EXCLUDED = frozenset([
    'if', 'else', 'while', 'for', 'switch', 'do', 'return',
    'goto', 'break', 'continue', 'case', 'default',
    'catch', 'try', 'throw', 'namespace', 'class', 'struct',
    'union', 'enum', 'typedef', 'sizeof', 'typeof', 'alignof',
    'new', 'delete', 'template', 'typename',
    'public', 'private', 'protected', 'using', 'friend',
    'static', 'extern', 'inline', 'register', 'volatile',
    'const', 'constexpr', 'consteval', 'constinit',
    'mutable', 'explicit', 'virtual', 'override', 'final',
    'noexcept', 'nullptr', 'true', 'false', 'this',
    'void', 'int', 'char', 'float', 'double', 'long', 'short',
    'unsigned', 'signed', 'bool', 'wchar_t', 'auto',
    'static_cast', 'dynamic_cast', 'reinterpret_cast', 'const_cast',
])

CALL_EXCLUDE_KWS = frozenset([
    'if', 'else', 'while', 'for', 'switch', 'do', 'return',
    'goto', 'break', 'continue', 'case', 'default',
    'catch', 'try', 'throw', 'sizeof', 'typeof', 'alignof',
    'new', 'delete', 'assert', 'offsetof',
    'static_cast', 'dynamic_cast', 'reinterpret_cast', 'const_cast',
])


# ── Source cleaning ────────────────────────────────────────────────────────────

def clean_source(source):
    """
    Remove C/C++ comments and string/char literals.
    Preserves newlines for line number tracking.
    Keeps #include directives; blanks out other preprocessor lines.
    """
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
            out.append("'")
            i += 1
            while i < n:
                if source[i] == '\\':
                    out.append(' ')
                    i = min(i + 2, n)
                elif source[i] == "'":
                    out.append("'")
                    i += 1
                    break
                else:
                    out.append('\n' if source[i] == '\n' else ' ')
                    i += 1

        # Preprocessor directive
        elif source[i] == '#' and (i == 0 or source[i - 1] == '\n'):
            end = i
            while end < n:
                if source[end] == '\\' and end + 1 < n and source[end + 1] == '\n':
                    end += 2
                elif source[end] == '\n':
                    break
                else:
                    end += 1
            directive = source[i:end]
            stripped = directive.lstrip('#').lstrip()
            if stripped.startswith('include'):
                out.append(directive)  # keep #include lines
            else:
                out.append('\n' * directive.count('\n'))
            i = end

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

def try_parse_func_sig(sig, is_cpp=False):
    """
    Try to interpret `sig` as a C/C++ function definition signature.
    Returns {'name': str, 'qualified_class': str|None} or None.
    """
    sig = sig.strip()
    if not sig:
        return None

    if is_cpp:
        # Remove access specifiers that may prefix the signature
        sig = re.sub(r'\b(?:public|private|protected)\s*:', '', sig).strip()
        if not sig:
            return None

        # Strip C++ initializer list:  ClassName(params) : m_x(x), ...
        # Find the first standalone ':' (not '::') AFTER removing the params
        # Strategy: find closing ) of params, then look for ':' after it
        paren_depth = 0
        init_colon = -1
        for k, ch in enumerate(sig):
            if ch == '(':
                paren_depth += 1
            elif ch == ')':
                paren_depth -= 1
                if paren_depth == 0:
                    # Look for ':' after this ) that is not '::'
                    rest = sig[k + 1:]
                    m = re.search(r'(?<!:):(?!:)', rest)
                    if m:
                        init_colon = k + 1 + m.start()
                    break
        if init_colon > 0:
            sig = sig[:init_colon].strip()

        # Strip trailing return type: ) -> ReturnType
        sig = re.sub(r'\)\s*->\s*.+$', ')', sig.rstrip())

        # Strip trailing qualifiers: ) const override final noexcept = 0 ...
        sig = re.sub(
            r'\)\s*(?:(?:const|volatile|override|final|'
            r'noexcept(?:\s*\([^)]*\))?|'
            r'=\s*(?:0|default|delete))\s*)*$',
            ')',
            sig,
        )

    if not sig.endswith(')'):
        return None

    # Find matching '(' (from the end)
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

    # Assignment before '(' → not a function definition
    if '=' in before_paren:
        return None

    # Extract function name (last qualified identifier before '(')
    if is_cpp:
        name_m = re.search(
            r'([~]?[a-zA-Z_][a-zA-Z0-9_]*'
            r'(?:::[~]?[a-zA-Z_][a-zA-Z0-9_]*)*)\s*$',
            before_paren,
        )
    else:
        name_m = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*$', before_paren)

    if not name_m:
        return None

    qualified = name_m.group(1)
    parts = qualified.split('::')
    func_name = parts[-1].strip()
    clean_name = func_name.lstrip('~')

    if not clean_name or clean_name in FUNC_NAME_EXCLUDED:
        return None

    # Token before function name must not be a control-flow keyword
    before_name = before_paren[:name_m.start()].strip()
    if before_name:
        prev_tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', before_name)
        if prev_tokens and prev_tokens[-1] in CONTROL_FLOW_KWS:
            return None

    qualified_class = '::'.join(parts[:-1]) if len(parts) > 1 else None
    return {'name': func_name, 'qualified_class': qualified_class}


def try_parse_class_sig(sig):
    """
    Try to interpret `sig` as a C++ class/struct definition.
    Returns {'name': str} or None.
    """
    m = re.search(
        r'\b(?:class|struct)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        r'(?:\s+final)?\s*(?:[:{]|$)',
        sig,
    )
    if m:
        return {'name': m.group(1)}
    return None


# ── Call extraction ────────────────────────────────────────────────────────────

def find_calls(body, is_cpp=False):
    """Find function/method calls directly inside a function body."""
    calls = []
    seen = set()

    for m in re.finditer(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', body):
        name = m.group(1)
        if name in CALL_EXCLUDE_KWS:
            continue

        before = body[:m.start()].rstrip()

        if before.endswith('.') or before.endswith('->'):
            obj_m = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\.|->)\s*$', before)
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

    # C++: new ClassName(...) → constructor call
    if is_cpp:
        for m in re.finditer(r'\bnew\s+([a-zA-Z_][a-zA-Z0-9_:]*)\s*[(<]', body):
            cls = m.group(1).split('::')[-1]
            key = ('name', cls)
            if key not in seen:
                seen.add(key)
                calls.append({'type': 'name', 'name': cls})

        # C++ direct initialization: ClassName varname(args)
        # Heuristic: first identifier starts with uppercase (class name convention)
        for m in re.finditer(
            r'\b([A-Z][a-zA-Z0-9_]*)\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(',
            body,
        ):
            cls = m.group(1)
            if cls not in FUNC_NAME_EXCLUDED and cls not in CALL_EXCLUDE_KWS:
                key = ('name', cls)
                if key not in seen:
                    seen.add(key)
                    calls.append({'type': 'name', 'name': cls})

    return calls


# ── Include resolution ─────────────────────────────────────────────────────────

def get_includes(source, file_path, is_cpp=False):
    """
    Parse local #include "..." directives and resolve them to absolute paths.
    For each .h header, also looks for the corresponding source file.
    """
    dir_path = os.path.dirname(file_path)
    result = []
    seen = set()

    for m in re.finditer(r'#include\s+"([^"]+)"', source):
        rel = m.group(1)
        resolved = os.path.normpath(os.path.join(dir_path, rel))
        if not os.path.exists(resolved):
            continue

        base = os.path.splitext(os.path.basename(resolved))[0]
        header_dir = os.path.dirname(resolved)

        if resolved not in seen:
            seen.add(resolved)
            result.append({'local_name': base, 'resolved_path': resolved})

        # Also find the corresponding source file for this header
        src_exts = ['.cpp', '.cc', '.cxx'] if is_cpp else ['.c']
        for ext in src_exts:
            src = os.path.normpath(os.path.join(header_dir, base + ext))
            if os.path.exists(src) and src not in seen and src != file_path:
                seen.add(src)
                result.append({'local_name': base + '_impl', 'resolved_path': src})

    return result


# ── File parser ────────────────────────────────────────────────────────────────

def parse_file(file_path):
    """Parse a C/C++ source file and return extracted function/import data."""
    ext = os.path.splitext(file_path)[1].lower()
    is_cpp = ext in CPP_EXTS

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
    except IOError as e:
        return {'error': str(e), 'functions': [], 'imports': []}

    imports = get_includes(source, file_path, is_cpp)
    cleaned = clean_source(source)
    line_starts = build_line_map(cleaned)

    functions = []
    n = len(cleaned)
    i = 0

    # Stack: {'type': 'func'|'class'|'other', 'name', 'class_name',
    #         'depth', 'start_line', 'body_start'}
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

            if is_cpp:
                cls_info = try_parse_class_sig(sig)
                if cls_info:
                    stack.append({
                        'type': 'class', 'name': cls_info['name'],
                        'class_name': None, 'depth': brace_depth,
                        'start_line': start_line, 'body_start': i + 1,
                    })
                    pushed = True

            if not pushed:
                func_info = try_parse_func_sig(sig, is_cpp)
                if func_info:
                    cls = func_info.get('qualified_class') or current_class()
                    stack.append({
                        'type': 'func', 'name': func_info['name'],
                        'class_name': cls, 'depth': brace_depth,
                        'start_line': start_line, 'body_start': i + 1,
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
                    calls = find_calls(body, is_cpp)
                    functions.append({
                        'name': entry['name'],
                        'class_name': entry['class_name'],
                        'is_top_level': True,
                        'start_line': entry['start_line'],
                        'end_line': pos_to_line(i, line_starts),
                        'calls': calls,
                    })

        elif ch == ';' and brace_depth == 0:
            sig_buf = []

        else:
            sig_buf.append(ch)

        i += 1

    return {'functions': functions, 'imports': imports}


# ── Recursive analysis ─────────────────────────────────────────────────────────

def analyze_recursive(entry_file):
    entry_file = os.path.normpath(os.path.abspath(entry_file))
    results = {}
    queue = [entry_file]

    while queue:
        fp = queue.pop(0)
        if fp in results:
            continue
        info = parse_file(fp)
        results[fp] = info
        for imp in info.get('imports', []):
            rp = imp.get('resolved_path')
            if rp and rp not in results:
                queue.append(rp)

    return results


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'usage: extract_c.py <entry_file>'}))
        sys.exit(1)
    print(json.dumps(analyze_recursive(sys.argv[1]), ensure_ascii=False))
