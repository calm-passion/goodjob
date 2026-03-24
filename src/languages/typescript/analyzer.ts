import * as ts from 'typescript';
import * as path from 'path';
import { LanguageAnalyzer, AnalyzerContext, FunctionNode } from '../base';
import { GraphNode } from '../../types';
import { collectCallExpressions } from './parser';
import { isFunctionLike, getFunctionName, getLocation } from './utils';

/** 外部包/内置库路径特征，匹配时跳过 */
const EXTERNAL_PATH_PATTERNS = [
  `${path.sep}node_modules${path.sep}`,
  '/node_modules/',
  '\\node_modules\\',
];

function isExternalPath(filePath: string): boolean {
  return EXTERNAL_PATH_PATTERNS.some((p) => filePath.includes(p));
}

/**
 * TypeScript 分析上下文实现
 * 使用 TypeChecker 直接解析符号，全程在 AST 节点对象层面操作，无位置转换。
 */
class TypeScriptAnalyzerContext implements AnalyzerContext {
  private program: ts.Program;
  private checker: ts.TypeChecker;

  constructor(program: ts.Program, checker: ts.TypeChecker) {
    this.program = program;
    this.checker = checker;
  }

  getRootFunctions(entryFile: string): FunctionNode[] {
    const sourceFile = this.program.getSourceFile(entryFile);
    if (!sourceFile) {
      throw new Error(`找不到入口文件的 SourceFile: ${entryFile}`);
    }

    const roots: ts.FunctionLikeDeclaration[] = [];

    // 收集顶层函数声明（包括 export）
    ts.forEachChild(sourceFile, (node) => {
      if (isFunctionLike(node)) {
        roots.push(node);
      }
      // 处理 export default function / export function
      if (
        ts.isExportAssignment(node) &&
        isFunctionLike((node as ts.ExportAssignment).expression as ts.Node)
      ) {
        roots.push((node as ts.ExportAssignment).expression as unknown as ts.FunctionLikeDeclaration);
      }
    });

    // 若没有顶层函数声明，尝试找顶层变量声明中的箭头函数/函数表达式
    if (roots.length === 0) {
      ts.forEachChild(sourceFile, (node) => {
        if (ts.isVariableStatement(node)) {
          for (const decl of node.declarationList.declarations) {
            if (decl.initializer && isFunctionLike(decl.initializer)) {
              roots.push(decl.initializer as ts.FunctionLikeDeclaration);
            }
          }
        }
      });
    }

    return roots;
  }

  getCallees(fn: FunctionNode): FunctionNode[] {
    const funcNode = fn as ts.FunctionLikeDeclaration;
    const callExprs = collectCallExpressions(funcNode);
    const callees: ts.FunctionLikeDeclaration[] = [];

    for (const callExpr of callExprs) {
      const expr = callExpr.expression;

      // 确定要查 Symbol 的目标节点
      let targetNode: ts.Node;
      if (ts.isIdentifier(expr)) {
        targetNode = expr;
      } else if (ts.isPropertyAccessExpression(expr)) {
        targetNode = expr.name; // 只取方法名标识符，不取对象本身
      } else {
        continue; // 动态调用（如 obj[key]()），跳过
      }

      // 通过 TypeChecker 直接解析 Symbol
      let symbol = this.checker.getSymbolAtLocation(targetNode);
      if (!symbol) continue;

      // 解引用 import 别名（跨文件解析的关键）
      // import { a6 } from "./aaa" 中，a6 的 Symbol 是 Alias，需要解引用到真实声明
      if (symbol.flags & ts.SymbolFlags.Alias) {
        symbol = this.checker.getAliasedSymbol(symbol);
      }

      const declarations = symbol.getDeclarations();
      if (!declarations || declarations.length === 0) continue;

      // 找实现体：有 body 的 FunctionLike，过滤重载签名、.d.ts、外部包
      const decl = declarations.find(
        (d) =>
          isFunctionLike(d) &&
          (d as ts.FunctionLikeDeclaration).body !== undefined &&
          !d.getSourceFile().fileName.endsWith('.d.ts') &&
          !isExternalPath(d.getSourceFile().fileName),
      ) as ts.FunctionLikeDeclaration | undefined;

      if (!decl) continue;

      if (!callees.includes(decl)) {
        callees.push(decl);
      }
    }

    return callees;
  }

  toGraphNode(fn: FunctionNode): Omit<GraphNode, 'childs'> {
    const funcNode = fn as ts.FunctionLikeDeclaration;
    const sourceFile = funcNode.getSourceFile();
    return {
      function_name: getFunctionName(funcNode, sourceFile),
      definition_file_path: sourceFile.fileName,
      location: getLocation(funcNode, sourceFile),
    };
  }
}

/**
 * TypeScript 语言分析器（实现 LanguageAnalyzer 接口）
 */
export const typescriptAnalyzer: LanguageAnalyzer = {
  extensions: ['.ts', '.tsx'],

  initialize(entryFile: string): AnalyzerContext {
    const entryDir = path.dirname(entryFile);
    const tsconfigPath = ts.findConfigFile(entryDir, ts.sys.fileExists, 'tsconfig.json');

    if (!tsconfigPath) {
      throw new Error(
        `在 ${entryDir} 及其父目录中找不到 tsconfig.json，请确保被分析项目有 TypeScript 配置`,
      );
    }

    const configFile = ts.readConfigFile(tsconfigPath, ts.sys.readFile);
    if (configFile.error) {
      throw new Error(
        `读取 tsconfig 失败: ${ts.flattenDiagnosticMessageText(configFile.error.messageText, '\n')}`,
      );
    }

    const configDir = path.dirname(tsconfigPath);
    const parsedConfig = ts.parseJsonConfigFileContent(
      configFile.config,
      ts.sys,
      configDir,
    );

    // 确保入口文件一定在 fileNames 中
    const fileNames = parsedConfig.fileNames.includes(entryFile)
      ? parsedConfig.fileNames
      : [...parsedConfig.fileNames, entryFile];

    const program = ts.createProgram(fileNames, parsedConfig.options);
    const checker = program.getTypeChecker();

    return new TypeScriptAnalyzerContext(program, checker);
  },
};
