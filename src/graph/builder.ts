import { GraphNode } from '../types';
import { AnalyzerContext, FunctionNode } from '../languages/base';

/**
 * 递归构建函数调用图节点。
 *
 * 设计要点：
 * - analysisCache：记录每个函数的被调函数列表，确保每个函数只分析一次
 * - pathInProgress：当前 DFS 路径，用于检测真正的循环调用（A→B→A）
 * - 每次调用都创建新的 GraphNode 对象，保证所有调用引用都被记录在各调用方的 childs 中
 *
 * 这样实现满足：
 *   1. 同一函数只分析一次（getCallees 只调用一次，结果缓存）
 *   2. 所有调用引用都记录（每个调用方的 childs 都包含被调函数的完整节点）
 *   3. 循环调用安全（通过 pathInProgress 检测当前路径中的环）
 */
function buildNode(
  fn: FunctionNode,
  ctx: AnalyzerContext,
  analysisCache: Map<FunctionNode, FunctionNode[]>,
  pathInProgress: Set<FunctionNode>,
): GraphNode {
  const base = ctx.toGraphNode(fn);

  // 当前路径中已有此函数 → 循环调用，打断递归
  if (pathInProgress.has(fn)) {
    return {
      ...base,
      function_name: `${base.function_name} [circular]`,
      childs: null,
    };
  }

  // 获取被调函数列表（只分析一次，之后从缓存读取）
  let callees: FunctionNode[];
  if (analysisCache.has(fn)) {
    callees = analysisCache.get(fn)!;
  } else {
    callees = ctx.getCallees(fn);
    analysisCache.set(fn, callees);
  }

  // 将当前函数加入路径集合，构建子节点，再移除
  pathInProgress.add(fn);

  const childs = callees.map((callee) =>
    buildNode(callee, ctx, analysisCache, pathInProgress),
  );

  pathInProgress.delete(fn);

  return {
    ...base,
    childs: childs.length > 0 ? childs : null,
  };
}

/**
 * 构建完整的函数调用图。
 * @param entryFile 入口文件的绝对路径
 * @param ctx 语言分析上下文
 * @returns 根节点列表（对应入口文件中所有顶层函数）
 */
export function buildGraph(entryFile: string, ctx: AnalyzerContext): GraphNode[] {
  const analysisCache = new Map<FunctionNode, FunctionNode[]>();

  const rootFunctions = ctx.getRootFunctions(entryFile);

  if (rootFunctions.length === 0) {
    throw new Error(`入口文件中未找到任何函数: ${entryFile}`);
  }

  return rootFunctions.map((fn) => buildNode(fn, ctx, analysisCache, new Set()));
}
