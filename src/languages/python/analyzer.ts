import * as path from 'path';
import { execSync } from 'child_process';
import { LanguageAnalyzer, AnalyzerContext, FunctionNode } from '../base';
import { GraphNode } from '../../types';

// ── Python extractor output types ─────────────────────────────────────────────

interface PyCall {
  type: 'name' | 'attr';
  name?: string;        // type='name': the called function name
  obj?: string | null;  // type='attr': object identifier (null if complex expression)
  attr?: string;        // type='attr': attribute / method name
}

interface PyFuncInfo {
  name: string;
  class_name: string | null;
  is_top_level: boolean;  // directly under module, not nested in another function/class
  start_line: number;
  end_line: number;
  calls: PyCall[];
}

interface PyFileInfo {
  functions: PyFuncInfo[];
  imports: Array<{ local_name: string; resolved_path: string | null }>;
  error?: string;
}

// ── Internal function node ─────────────────────────────────────────────────────

/**
 * Canonical Python function node.
 * builder.ts uses object identity for cache/cycle detection,
 * so we create exactly one instance per function and reuse it everywhere.
 */
interface PyFuncNode {
  info: PyFuncInfo;
  filePath: string;
}

// ── Analyzer context ───────────────────────────────────────────────────────────

class PythonAnalyzerContext implements AnalyzerContext {
  /** Canonical node store: `filePath::className::funcName` → PyFuncNode */
  private nodeCache = new Map<string, PyFuncNode>();
  /** filePath → import map (localName → resolved file path or null for external) */
  private importMap = new Map<string, Map<string, string | null>>();

  constructor(fileData: Record<string, PyFileInfo>) {
    this.buildIndices(fileData);
  }

  private nodeKey(filePath: string, className: string | null, funcName: string): string {
    return `${filePath}::${className ?? ''}::${funcName}`;
  }

  private buildIndices(fileData: Record<string, PyFileInfo>): void {
    for (const [filePath, info] of Object.entries(fileData)) {
      // Create one canonical PyFuncNode per function
      for (const fn of info.functions) {
        const key = this.nodeKey(filePath, fn.class_name, fn.name);
        if (!this.nodeCache.has(key)) {
          this.nodeCache.set(key, { info: fn, filePath });
        }
      }
      // Build import map for this file
      const imports = new Map<string, string | null>();
      for (const imp of info.imports) {
        imports.set(imp.local_name, imp.resolved_path);
      }
      this.importMap.set(filePath, imports);
    }
  }

  // ── Lookup helpers ───────────────────────────────────────────────────────────

  private getNode(filePath: string, className: string | null, funcName: string): PyFuncNode | undefined {
    return this.nodeCache.get(this.nodeKey(filePath, className, funcName));
  }

  /**
   * Look up a function by name in a specific file.
   * Searches both module-level functions and class methods.
   */
  private lookupInFile(name: string, filePath: string): PyFuncNode | undefined {
    // Exact key with no class
    const direct = this.getNode(filePath, null, name);
    if (direct) return direct;
    // Search methods in any class
    for (const [key, node] of this.nodeCache) {
      if (node.filePath === filePath && node.info.name === name) return node;
    }
    return undefined;
  }

  private lookupGlobally(name: string): PyFuncNode | undefined {
    for (const node of this.nodeCache.values()) {
      if (node.info.name === name) return node;
    }
    return undefined;
  }

  private resolveCall(
    call: PyCall,
    filePath: string,
    imports: Map<string, string | null>,
  ): PyFuncNode | undefined {
    if (call.type === 'name' && call.name) {
      // Direct call: foo()
      // 1. Same file
      const local = this.lookupInFile(call.name, filePath);
      if (local) return local;
      // 2. Imported name
      if (imports.has(call.name)) {
        const srcFile = imports.get(call.name);
        if (!srcFile) return undefined; // external
        return this.lookupInFile(call.name, srcFile);
      }
      return undefined;
    }

    if (call.type === 'attr' && call.attr) {
      const objName = call.obj;
      const methodName = call.attr;

      // module.func() — obj is a known imported module name
      if (objName && imports.has(objName)) {
        const srcFile = imports.get(objName);
        if (!srcFile) return undefined; // external
        return this.lookupInFile(methodName, srcFile);
      }

      // self.method() / obj.method() — search all loaded files
      return this.lookupGlobally(methodName);
    }

    return undefined;
  }

  // ── AnalyzerContext interface ─────────────────────────────────────────────────

  getRootFunctions(entryFile: string): FunctionNode[] {
    const roots: PyFuncNode[] = [];
    for (const node of this.nodeCache.values()) {
      if (
        node.filePath === entryFile &&
        node.info.class_name === null &&
        node.info.is_top_level
      ) {
        roots.push(node);
      }
    }
    // Sort by start line for deterministic output
    roots.sort((a, b) => a.info.start_line - b.info.start_line);
    return roots;
  }

  getCallees(fn: FunctionNode): FunctionNode[] {
    const pyFn = fn as PyFuncNode;
    const imports = this.importMap.get(pyFn.filePath) ?? new Map();
    const callees: PyFuncNode[] = [];

    for (const call of pyFn.info.calls) {
      const resolved = this.resolveCall(call, pyFn.filePath, imports);
      if (resolved && !callees.includes(resolved)) {
        callees.push(resolved);
      }
    }
    return callees;
  }

  toGraphNode(fn: FunctionNode): Omit<GraphNode, 'childs'> {
    const pyFn = fn as PyFuncNode;
    const { info, filePath } = pyFn;
    const displayName = info.class_name
      ? `${info.class_name}.${info.name}`
      : info.name;
    return {
      function_name: displayName,
      definition_file_path: filePath,
      location: `${info.start_line}_${info.end_line}`,
    };
  }
}

// ── Subprocess call ────────────────────────────────────────────────────────────

function runExtractor(entryFile: string): Record<string, PyFileInfo> {
  const script = path.join(__dirname, 'extract.py');
  const cmd = `"${entryFile}"`;

  let output: string;
  for (const py of ['python', 'python3']) {
    try {
      output = execSync(`${py} "${script}" ${cmd}`, {
        encoding: 'utf-8',
        timeout: 30_000,
      });
      return JSON.parse(output);
    } catch {
      // try next
    }
  }
  throw new Error(
    'Python 分析失败：请确保已安装 Python 3（python 或 python3 命令可用）',
  );
}

// ── Exported analyzer ─────────────────────────────────────────────────────────

export const pythonAnalyzer: LanguageAnalyzer = {
  extensions: ['.py'],

  initialize(entryFile: string): AnalyzerContext {
    const fileData = runExtractor(entryFile);
    return new PythonAnalyzerContext(fileData);
  },
};
