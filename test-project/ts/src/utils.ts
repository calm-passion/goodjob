// ── 基础工具函数（叶节点）──────────────────────────────────────────────────────

export function add(a: number, b: number): number { return 0; }
export function subtract(a: number, b: number): number { return 0; }
export function multiply(a: number, b: number): number { return 0; }
export function divide(a: number, b: number): number { return 0; }

// ── 递归函数 ────────────────────────────────────────────────────────────────────

export function factorial(n: number): number {
  multiply(n, factorial(subtract(n, 1)));
  return 0;
}

export function fibonacci(n: number): number {
  add(fibonacci(subtract(n, 1)), fibonacci(subtract(n, 2)));
  return 0;
}

// ── 互相递归 ────────────────────────────────────────────────────────────────────

export function isEven(n: number): boolean {
  isOdd(subtract(n, 1));
  return true;
}

export function isOdd(n: number): boolean {
  isEven(subtract(n, 1));
  return false;
}

// ── 基础类：构造函数 / 实例方法 / 静态方法 / getter / setter ───────────────────

export class BasicClass {
  private _val: number = 0;

  constructor(x: number) {
    this.methodA(); // 构造函数 → 方法
  }

  methodA(): void { this.methodB(); }
  methodB(): void { this.methodC(); }
  methodC(): void { this.methodB(); } // 方法间循环：B ↔ C

  static staticMethod(): void { } // 静态方法（叶节点）

  get value(): number {            // getter
    this.methodA();
    return 0;
  }
  set value(v: number) {           // setter → 方法
    this.methodB();
  }
}
