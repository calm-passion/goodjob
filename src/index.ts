import * as fs from 'fs';
import * as path from 'path';
import { getAnalyzer } from './languages/registry';
import { buildGraph } from './graph/builder';
import { serializeGraph } from './graph/serializer';

/**
 * 解析 CLI 参数，格式：-key="value" 或 -key=value
 */
function parseArgs(argv: string[]): Record<string, string> {
  const result: Record<string, string> = {};
  const pattern = /^-(\w+)=["']?([^"']+)["']?$/;
  for (const arg of argv) {
    const match = arg.match(pattern);
    if (match) {
      result[match[1]] = match[2];
    }
  }
  return result;
}

function main(): void {
  console.log("修改")
  const args = parseArgs(process.argv.slice(2));

  if (!args['entry'] || !args['output']) {
    console.error('用法: function_graph -entry="<入口文件路径>" -output="<输出文件路径>"');
    console.error('示例: function_graph -entry="./src/index.ts" -output="./output/graph.json"');
    process.exit(1);
  }

  const cwd = process.cwd();
  const entryFile = path.resolve(cwd, args['entry']);
  const outputFile = path.resolve(cwd, args['output']);

  // 验证入口文件存在
  if (!fs.existsSync(entryFile)) {
    console.error(`入口文件不存在: ${entryFile}`);
    process.exit(1);
  }

  // 确保输出目录存在
  const outputDir = path.dirname(outputFile);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  console.log(`分析入口: ${entryFile}`);

  // 获取对应语言的分析器
  const analyzer = getAnalyzer(entryFile);

  // 初始化分析上下文
  console.log('初始化语言服务...');
  const ctx = analyzer.initialize(entryFile);

  // 构建函数调用图
  console.log('构建函数调用图...');
  const roots = buildGraph(entryFile, ctx);

  // 序列化并写出
  const json = serializeGraph(roots);
  fs.writeFileSync(outputFile, json, 'utf-8');

  console.log(`完成，输出至: ${outputFile}`);
}

main();
