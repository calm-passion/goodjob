import { GraphNode } from '../types';

/**
 * 不透明的函数节点类型。
 * 各语言实现内部使用具体类型，builder 层通过此接口操作。
 */
export type FunctionNode = object;

/**
 * 分析上下文：由 LanguageAnalyzer.initialize() 创建，
 * 封装了语言相关的所有分析能力，供 builder 调用。
 */
export interface AnalyzerContext {
  /**
   * 获取入口文件中的顶层函数节点列表，作为图构建的起点。
   */
  getRootFunctions(entryFile: string): FunctionNode[];

  /**
   * 获取某函数调用的所有被调函数节点（跨文件解析）。
   * 实现内部负责过滤外部包（node_modules）和语言内置库。
   */
  getCallees(fn: FunctionNode): FunctionNode[];

  /**
   * 将函数节点转为 GraphNode 的基础信息（不含 childs）。
   */
  toGraphNode(fn: FunctionNode): Omit<GraphNode, 'childs'>;
}

/**
 * 语言分析器接口。
 * 新增语言支持时，实现此接口并在 registry.ts 中注册即可。
 */
export interface LanguageAnalyzer {
  /** 该分析器支持的文件扩展名列表，如 ['.ts', '.tsx'] */
  extensions: string[];

  /**
   * 初始化分析器，返回可供 builder 使用的分析上下文。
   * @param entryFile 入口文件的绝对路径
   */
  initialize(entryFile: string): AnalyzerContext;
}
