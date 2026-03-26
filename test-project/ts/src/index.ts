import { a6 } from './aaa';
import { BasicClass, isEven, factorial } from './utils';
import { runShapes } from './shapes';

// ── 主函数：嵌套函数 + 跨文件调用 + 类实例化 ──────────────────────────────────

function main(): void {
  // 嵌套函数（内部定义）
  function nested(): void {
    a2();
  }

  nested();
  a1();
  a6();           // 跨文件：index → aaa → index (a1)
  runShapes();    // 跨文件：index → shapes

  // 类实例化 → 构造函数 → 方法链
  const obj = new BasicClass(1);
  obj.methodA();

  // 跨文件函数调用
  isEven(4);
  factorial(5);
}

// ── 循环调用链：a1 → a2 → a3 → a4 → a2 ─────────────────────────────────────

export function a1(): void {
  a1();   // 自递归
  a2();
  a3();
}

function a2(): void {
  a3();
  a4();
}

function a3(): void {
  a4();
}

function a4(): void {
  a2(); // 循环：a2 → a3 → a4 → a2
}

// ── 长链式调用 ─────────────────────────────────────────────────────────────────

function chainA(): void { chainB(); }
function chainB(): void { chainC(); }
function chainC(): void { chainD(); }
function chainD(): void { chainE(); }
function chainE(): void { } // 叶节点
