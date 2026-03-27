import * as path from 'path';
import { execSync } from 'child_process';
import { LanguageAnalyzer, AnalyzerContext, FunctionNode } from '../base';
import { GraphNode } from '../../types';

// ── Shared types (same JSON schema as Python extractor) ───────────────────────

interface CCall {
  type: 'name' | 'attr';
  name?: string;
  obj?: string | null;
  attr?: string;
}

interface CFuncInfo {
  name: string;
  class_name: string | null;
  is_top_level: boolean;
  start_line: number;
  end_line: number;
  calls: CCall[];
}

interface CFileInfo {
  functions: CFuncInfo[];
  imports: Array<{ local_name: string; resolved_path: string | null }>;
  error?: string;
}

// ── Internal function node ─────────────────────────────────────────────────────

interface CFuncNode {
  info: CFuncInfo;
  filePath: string;
}

// ── Analyzer context ───────────────────────────────────────────────────────────

class CAnalyzerContext implements AnalyzerContext {
  private nodeCache = new Map<string, CFuncNode>();
  private importMap = new Map<string, Map<string, string | null>>();

  constructor(fileData: Record<string, CFileInfo>) {
    this.buildIndices(fileData);
  }

  private nodeKey(filePath: string, className: string | null, funcName: string): string {
    return `${filePath}::${className ?? ''}::${funcName}`;
  }

  private buildIndices(fileData: Record<string, CFileInfo>): void {
    for (const [filePath, info] of Object.entries(fileData)) {
      for (const fn of info.functions) {
        const key = this.nodeKey(filePath, fn.class_name, fn.name);
        if (!this.nodeCache.has(key)) {
          this.nodeCache.set(key, { info: fn, filePath });
        }
      }
      const imports = new Map<string, string | null>();
      for (const imp of info.imports) {
        imports.set(imp.local_name, imp.resolved_path);
      }
      this.importMap.set(filePath, imports);
    }
  }

  // ── Lookup helpers ────────────────────────────────────────────────────────────

  private lookupByName(name: string, filePath: string): CFuncNode | undefined {
    // 1. Exact match in this file (any class)
    for (const node of this.nodeCache.values()) {
      if (node.filePath === filePath && node.info.name === name) return node;
    }
    return undefined;
  }

  private lookupGlobally(name: string): CFuncNode | undefined {
    for (const node of this.nodeCache.values()) {
      if (node.info.name === name) return node;
    }
    return undefined;
  }

  private resolveCall(
    call: CCall,
    filePath: string,
    imports: Map<string, string | null>,
  ): CFuncNode | undefined {
    if (call.type === 'name' && call.name) {
      // 1. Same file
      const local = this.lookupByName(call.name, filePath);
      if (local) return local;

      // 2. Search all imported/included files
      for (const [, resolvedPath] of imports) {
        if (!resolvedPath) continue;
        const found = this.lookupByName(call.name, resolvedPath);
        if (found) return found;
      }
      return undefined;
    }

    if (call.type === 'attr' && call.attr) {
      // C++ method call: obj.method() or obj->method()
      // We don't track types, so search all loaded files
      return this.lookupGlobally(call.attr);
    }

    return undefined;
  }

  // ── AnalyzerContext interface ──────────────────────────────────────────────────

  getRootFunctions(entryFile: string): FunctionNode[] {
    const roots: CFuncNode[] = [];
    for (const node of this.nodeCache.values()) {
      if (node.filePath === entryFile && node.info.is_top_level) {
        roots.push(node);
      }
    }
    roots.sort((a, b) => a.info.start_line - b.info.start_line);
    return roots;
  }

  getCallees(fn: FunctionNode): FunctionNode[] {
    const cFn = fn as CFuncNode;
    const imports = this.importMap.get(cFn.filePath) ?? new Map();
    const callees: CFuncNode[] = [];

    for (const call of cFn.info.calls) {
      const resolved = this.resolveCall(call, cFn.filePath, imports);
      if (resolved && !callees.includes(resolved)) {
        callees.push(resolved);
      }
    }
    return callees;
  }

  toGraphNode(fn: FunctionNode): Omit<GraphNode, 'childs'> {
    const cFn = fn as CFuncNode;
    const { info, filePath } = cFn;
    const displayName = info.class_name
      ? `${info.class_name}::${info.name}`
      : info.name;
    return {
      function_name: displayName,
      definition_file_path: filePath,
      location: `${info.start_line}_${info.end_line}`,
    };
  }
}

// ── Subprocess runner ──────────────────────────────────────────────────────────

function runExtractor(entryFile: string): Record<string, CFileInfo> {
  const script = path.join(__dirname, 'extract_c.py');
  let output: string | undefined;

  for (const py of ['python', 'python3']) {
    try {
      output = execSync(`${py} "${script}" "${entryFile}"`, {
        encoding: 'utf-8',
        timeout: 30_000,
      });
      return JSON.parse(output);
    } catch {
      // try next
    }
  }
  throw new Error(
    'C 分析失败：请确保已安装 Python 3（python 或 python3 命令可用）',
  );
}

// ── Exported analyzers ────────────────────────────────────────────────────────

export const cAnalyzer: LanguageAnalyzer = {
  extensions: ['.c', '.h'],

  initialize(entryFile: string): AnalyzerContext {
    const fileData = runExtractor(entryFile);
    return new CAnalyzerContext(fileData);
  },
};

export const cppAnalyzer: LanguageAnalyzer = {
  extensions: ['.cpp', '.cc', '.cxx', '.hpp'],

  initialize(entryFile: string): AnalyzerContext {
    const fileData = runExtractor(entryFile);
    return new CAnalyzerContext(fileData);
  },
};
