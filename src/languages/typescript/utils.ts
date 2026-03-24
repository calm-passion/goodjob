import * as ts from 'typescript';

/**
 * 安全地获取属性名/标识符文本，优先使用 .text 属性（不依赖父链），
 * 回退到 getText(sourceFile)（需要 sourceFile 有效）。
 */
function getPropertyNameText(name: ts.PropertyName | ts.BindingName, sourceFile: ts.SourceFile): string {
  if (ts.isIdentifier(name) || ts.isStringLiteral(name) || ts.isNumericLiteral(name)) {
    return name.text;
  }
  // 计算属性名等情况，尝试 getText
  try {
    return name.getText(sourceFile);
  } catch {
    return '<computed>';
  }
}

/**
 * 判断节点是否为函数类节点（覆盖所有函数形式）
 */
export function isFunctionLike(node: ts.Node): node is ts.FunctionLikeDeclaration {
  return (
    ts.isFunctionDeclaration(node) ||
    ts.isArrowFunction(node) ||
    ts.isMethodDeclaration(node) ||
    ts.isFunctionExpression(node) ||
    ts.isConstructorDeclaration(node) ||
    ts.isGetAccessorDeclaration(node) ||
    ts.isSetAccessorDeclaration(node)
  );
}

/**
 * 获取函数节点的名称，覆盖所有函数形式：
 * - FunctionDeclaration / MethodDeclaration → 直接取 name
 * - ArrowFunction / FunctionExpression → 查父节点取变量名/属性名
 * - Constructor → "constructor"
 * - Getter/Setter → "get name" / "set name"
 * - 匿名 → "<anonymous@L行号>"
 */
export function getFunctionName(
  node: ts.FunctionLikeDeclaration,
  sourceFile: ts.SourceFile,
): string {
  if (ts.isConstructorDeclaration(node)) {
    return 'constructor';
  }

  if (ts.isGetAccessorDeclaration(node)) {
    return `get ${getPropertyNameText(node.name, sourceFile)}`;
  }

  if (ts.isSetAccessorDeclaration(node)) {
    return `set ${getPropertyNameText(node.name, sourceFile)}`;
  }

  if (ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node)) {
    if (node.name) {
      return getPropertyNameText(node.name, sourceFile);
    }
  }

  // 箭头函数或函数表达式：从父节点推断名称
  if (ts.isArrowFunction(node) || ts.isFunctionExpression(node)) {
    const parent = node.parent;
    if (parent) {
      if (ts.isVariableDeclaration(parent) && ts.isIdentifier(parent.name)) {
        return parent.name.text;
      }
      if (ts.isPropertyDeclaration(parent) || ts.isPropertyAssignment(parent)) {
        if (ts.isIdentifier(parent.name) || ts.isStringLiteral(parent.name)) {
          return getPropertyNameText(parent.name, sourceFile);
        }
      }
    }
  }

  // 兜底：匿名函数，附带行号
  const line = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile)).line + 1;
  return `<anonymous@L${line}>`;
}

/**
 * 获取函数节点的位置字符串，格式："startLine_endLine"（1-based）
 */
export function getLocation(node: ts.Node, sourceFile: ts.SourceFile): string {
  const start = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile)).line + 1;
  const end = sourceFile.getLineAndCharacterOfPosition(node.getEnd()).line + 1;
  return `${start}_${end}`;
}
