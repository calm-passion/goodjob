import * as path from 'path';
import { execSync } from 'child_process';
import { LanguageAnalyzer, AnalyzerContext, FunctionNode } from '../base';
import { GraphNode } from '../../types';

// ── Types ──────────────────────────────────────────────────────────────────────

interface JavaCall {
  type: 'name' | 'attr';
  name?: string;
  obj?: string | null;
  attr?: string;
}

interface JavaFuncInfo {
  name: string;
  class_name: string | null;
  is_top_level: boolean;
  start_line: number;
  end_line: number;
  calls: JavaCall[];
}

interface JavaFileInfo {
  functions: JavaFuncInfo[];
  imports: Array<{ local_name: string; resolved_path: string | null }>;
  error?: string;
}

interface JavaFuncNode {
  info: JavaFuncInfo;
  filePath: string;
}

// ── Analyzer context ───────────────────────────────────────────────────────────

class JavaAnalyzerContext implements AnalyzerContext {
  private nodeCache = new Map<string, JavaFuncNode>();
  private importMap = new Map<string, Map<string, string | null>>();

  constructor(fileData: Record<string, JavaFileInfo>) {
    this.buildIndices(fileData);
  }

  private nodeKey(filePath: string, className: string | null, methodName: string): string {
    return `${filePath}::${className ?? ''}::${methodName}`;
  }

  private buildIndices(fileData: Record<string, JavaFileInfo>): void {
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

  private lookupByName(name: string, filePath: string): JavaFuncNode | undefined {
    for (const node of this.nodeCache.values()) {
      if (node.filePath === filePath && node.info.name === name) return node;
    }
    return undefined;
  }

  private lookupGlobally(name: string): JavaFuncNode | undefined {
    for (const node of this.nodeCache.values()) {
      if (node.info.name === name) return node;
    }
    return undefined;
  }

  private resolveCall(
    call: JavaCall,
    filePath: string,
    imports: Map<string, string | null>,
  ): JavaFuncNode | undefined {
    if (call.type === 'name' && call.name) {
      // 1. Same file
      const local = this.lookupByName(call.name, filePath);
      if (local) return local;
      // 2. Check if the name matches an imported class name (constructor call)
      const srcFile = imports.get(call.name);
      if (srcFile) {
        return this.lookupByName(call.name, srcFile);
      }
      return undefined;
    }

    if (call.type === 'attr' && call.attr && call.obj) {
      // ClassName.staticMethod() or obj.instanceMethod()
      const srcFile = imports.get(call.obj);
      if (srcFile) {
        return this.lookupByName(call.attr, srcFile);
      }
      // Fallback: search all loaded files (handles this.method, super.method)
      return this.lookupGlobally(call.attr);
    }

    return undefined;
  }

  // ── AnalyzerContext interface ─────────────────────────────────────────────────

  getRootFunctions(entryFile: string): FunctionNode[] {
    const roots: JavaFuncNode[] = [];
    for (const node of this.nodeCache.values()) {
      if (node.filePath === entryFile && node.info.is_top_level) {
        roots.push(node);
      }
    }
    roots.sort((a, b) => a.info.start_line - b.info.start_line);
    return roots;
  }

  getCallees(fn: FunctionNode): FunctionNode[] {
    const jFn = fn as JavaFuncNode;
    const imports = this.importMap.get(jFn.filePath) ?? new Map();
    const callees: JavaFuncNode[] = [];

    for (const call of jFn.info.calls) {
      const resolved = this.resolveCall(call, jFn.filePath, imports);
      if (resolved && !callees.includes(resolved)) {
        callees.push(resolved);
      }
    }
    return callees;
  }

  toGraphNode(fn: FunctionNode): Omit<GraphNode, 'childs'> {
    const jFn = fn as JavaFuncNode;
    const { info, filePath } = jFn;
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

// ── Subprocess runner ──────────────────────────────────────────────────────────

function runExtractor(entryFile: string): Record<string, JavaFileInfo> {
  const script = path.join(__dirname, 'extract_java.py');
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
    'Java 分析失败：请确保已安装 Python 3（python 或 python3 命令可用）',
  );
}

// ── Exported analyzer ─────────────────────────────────────────────────────────

export const javaAnalyzer: LanguageAnalyzer = {
  extensions: ['.java'],

  initialize(entryFile: string): AnalyzerContext {
    const fileData = runExtractor(entryFile);
    return new JavaAnalyzerContext(fileData);
  },
};
