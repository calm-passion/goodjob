import { GraphNode } from '../types';

/**
 * 将图节点序列化为格式化 JSON 字符串。
 * 若入口文件只有一个根函数，输出单个对象；否则输出数组。
 */
export function serializeGraph(roots: GraphNode[]): string {
  const output = roots.length === 1 ? roots[0] : roots;
  return JSON.stringify(output, null, 2);
}
