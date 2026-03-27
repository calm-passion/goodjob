import * as path from 'path';
import { execSync } from 'child_process';
import { LanguageAnalyzer, AnalyzerContext, FunctionNode } from '../base';
import { GraphNode } from '../../types';

// ── Types ──────────────────────────────────────────────────────────────────────

interface GoCall {
  type: 'name' | 'attr';
  name?: string;
  obj?: string | null;
  attr?: string;
}

interface GoFuncInfo {
  name: string;
  class_name: string | null;   // receiver type, e.g. "Calculator"
  is_top_level: boolean;
  start_line: number;
  end_line: number;
  calls: GoCall[];
}

interface GoFileInfo {
  functions: GoFuncInfo[];
  imports: Array<{ local_name: string; resolved_path: string | null }>;
  error?: string;
}

interface GoFuncNode {
  info: GoFuncInfo;
  filePath: string;
}

// ── Analyzer context ───────────────────────────────────────────────────────────

class GoAnalyzerContext implements AnalyzerContext {
  private nodeCache = new Map<string, GoFuncNode>();
  private importMap = new Map<string, Map<string, string | null>>();

  constructor(fileData: Record<string, GoFileInfo>) {
    this.buildIndices(fileData);
  }

  private nodeKey(filePath: string, receiver: string | null, funcName: string): string {
    return `${filePath}::${receiver ?? ''}::${funcName}`;
  }

  private buildIndices(fileData: Record<string, GoFileInfo>): void {
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

  private lookupByName(name: string, filePath: string): GoFuncNode | undefined {
    for (const node of this.nodeCache.values()) {
      if (node.filePath === filePath && node.info.name === name) return node;
    }
    return undefined;
  }

  private lookupGlobally(name: string): GoFuncNode | undefined {
    for (const node of this.nodeCache.values()) {
      if (node.info.name === name) return node;
    }
    return undefined;
  }

  /** Resolve a pkg alias to the first file path in its package. */
  private pkgFirstFile(pkgAlias: string, imports: Map<string, string | null>): string | null {
    return imports.get(pkgAlias) ?? null;
  }

  private resolveCall(
    call: GoCall,
    filePath: string,
    imports: Map<string, string | null>,
  ): GoFuncNode | undefined {
    if (call.type === 'name' && call.name) {
      // 1. Same file (or same package files loaded alongside)
      const local = this.lookupByName(call.name, filePath);
      if (local) return local;
      // 2. All same-package files (already in nodeCache)
      const global = this.lookupGlobally(call.name);
      if (global) return global;
      return undefined;
    }

    if (call.type === 'attr' && call.attr && call.obj) {
      // pkg.FuncName() or recv.Method()
      const srcFile = this.pkgFirstFile(call.obj, imports);
      if (srcFile) {
        return this.lookupByName(call.attr, srcFile);
      }
      // Fallback: search all files (handles receiver.method calls)
      return this.lookupGlobally(call.attr);
    }

    return undefined;
  }

  // ── AnalyzerContext interface ─────────────────────────────────────────────────

  getRootFunctions(entryFile: string): FunctionNode[] {
    const roots: GoFuncNode[] = [];
    for (const node of this.nodeCache.values()) {
      if (node.filePath === entryFile && node.info.is_top_level) {
        roots.push(node);
      }
    }
    roots.sort((a, b) => a.info.start_line - b.info.start_line);
    return roots;
  }

  getCallees(fn: FunctionNode): FunctionNode[] {
    const goFn = fn as GoFuncNode;
    const imports = this.importMap.get(goFn.filePath) ?? new Map();
    const callees: GoFuncNode[] = [];

    for (const call of goFn.info.calls) {
      const resolved = this.resolveCall(call, goFn.filePath, imports);
      if (resolved && !callees.includes(resolved)) {
        callees.push(resolved);
      }
    }
    return callees;
  }

  toGraphNode(fn: FunctionNode): Omit<GraphNode, 'childs'> {
    const goFn = fn as GoFuncNode;
    const { info, filePath } = goFn;
    const displayName = info.class_name
      ? `(${info.class_name}) ${info.name}`
      : info.name;
    return {
      function_name: displayName,
      definition_file_path: filePath,
      location: `${info.start_line}_${info.end_line}`,
    };
  }
}

// ── Subprocess runner ──────────────────────────────────────────────────────────

function runExtractor(entryFile: string): Record<string, GoFileInfo> {
  const script = path.join(__dirname, 'extract_go.py');
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
    'Go 分析失败：请确保已安装 Python 3（python 或 python3 命令可用）',
  );
}

// ── Exported analyzer ─────────────────────────────────────────────────────────

export const goAnalyzer: LanguageAnalyzer = {
  extensions: ['.go'],

  initialize(entryFile: string): AnalyzerContext {
    const fileData = runExtractor(entryFile);
    return new GoAnalyzerContext(fileData);
  },
};
