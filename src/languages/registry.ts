import * as path from 'path';
import { LanguageAnalyzer } from './base';
import { typescriptAnalyzer } from './typescript/analyzer';
import { pythonAnalyzer } from './python/analyzer';
import { cAnalyzer, cppAnalyzer } from './c/analyzer';
import { goAnalyzer } from './go/analyzer';
import { javaAnalyzer } from './java/analyzer';

/**
 * 已注册的语言分析器列表。
 * 新增语言支持时，在此处添加对应的 analyzer 实例即可。
 */
const analyzers: LanguageAnalyzer[] = [
  typescriptAnalyzer,
  pythonAnalyzer,
  cAnalyzer,
  cppAnalyzer,
  goAnalyzer,
  javaAnalyzer,
];

/**
 * 根据文件扩展名获取对应的语言分析器。
 * @throws 若无对应分析器则报错（明确提示当前支持的扩展名）
 */
export function getAnalyzer(filePath: string): LanguageAnalyzer {
  const ext = path.extname(filePath).toLowerCase();
  const analyzer = analyzers.find((a) => a.extensions.includes(ext));

  if (!analyzer) {
    const supported = analyzers.flatMap((a) => a.extensions).join(', ');
    throw new Error(
      `不支持的文件类型: ${ext}\n当前支持: ${supported}`,
    );
  }

  return analyzer;
}
