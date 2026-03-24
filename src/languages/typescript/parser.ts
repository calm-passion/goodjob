import * as ts from 'typescript';
import { isFunctionLike } from './utils';

/**
 * 收集函数体内所有直接的 CallExpression 节点。
 * 不递归进入嵌套函数定义（避免将内部函数的调用归到外层函数名下）。
 */
export function collectCallExpressions(
  funcNode: ts.FunctionLikeDeclaration,
): ts.CallExpression[] {
  const results: ts.CallExpression[] = [];

  function visit(node: ts.Node, isRoot: boolean): void {
    // 跳过嵌套函数定义的内部（非根节点的函数体）
    if (!isRoot && isFunctionLike(node)) return;

    if (ts.isCallExpression(node)) {
      results.push(node);
    }

    ts.forEachChild(node, (child) => visit(child, false));
  }

  // 从函数体开始遍历（若无 body 则跳过，如抽象方法）
  if (funcNode.body) {
    ts.forEachChild(funcNode.body, (child) => visit(child, false));
  }

  return results;
}
