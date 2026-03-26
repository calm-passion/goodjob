import { multiply, add } from './utils';

// ── 抽象基类：模板方法调用抽象方法 ────────────────────────────────────────────

abstract class Shape {
  abstract area(): number;
  abstract perimeter(): number;

  // 模板方法：在基类中调用子类实现
  describe(): void {
    this.area();
    this.perimeter();
  }
}

// ── 单继承 ──────────────────────────────────────────────────────────────────────

class Circle extends Shape {
  constructor(private r: number) { super(); }

  area(): number {
    multiply(Math.PI, multiply(this.r, this.r));
    return 0;
  }
  perimeter(): number {
    multiply(2, multiply(Math.PI, this.r));
    return 0;
  }
}

class Rectangle extends Shape {
  constructor(private w: number, private h: number) { super(); }

  area(): number {
    multiply(this.w, this.h);
    return 0;
  }
  perimeter(): number {
    multiply(2, add(this.w, this.h));
    return 0;
  }
}

// ── 多级继承 + super 调用（多态覆写）─────────────────────────────────────────

class Square extends Rectangle {
  constructor(side: number) { super(side, side); }

  area(): number {
    return super.area(); // 调用 Rectangle.area（多态）
  }
}

// ── 接口 ────────────────────────────────────────────────────────────────────────

interface Printable {
  print(): void;
}

// ── 多重：继承 + 实现接口 + 再次覆写 super ────────────────────────────────────

class ColoredCircle extends Circle implements Printable {
  constructor(r: number, private color: string) { super(r); }

  area(): number {
    return super.area(); // 调用 Circle.area（多态）
  }

  print(): void {
    this.area();
    this.describe(); // 继承自 Shape（跨层调用）
  }
}

// ── 三级继承链 ─────────────────────────────────────────────────────────────────

class GradientCircle extends ColoredCircle {
  constructor(r: number, color: string, private gradient: string) {
    super(r, color);
  }

  area(): number {
    return super.area(); // 调用 ColoredCircle.area
  }

  describe(): void {
    super.describe(); // 调用 Shape.describe（跨层）
    this.area();
  }
}

// ── 入口函数 ────────────────────────────────────────────────────────────────────

export function runShapes(): void {
  const c = new Circle(5);
  const r = new Rectangle(3, 4);
  const s = new Square(6);
  const cc = new ColoredCircle(3, 'red');
  const gc = new GradientCircle(4, 'blue', 'linear');

  c.describe();    // Shape.describe → Circle.area + Circle.perimeter
  r.area();
  r.perimeter();
  s.area();        // Square.area → super → Rectangle.area
  cc.print();      // ColoredCircle.print → super.area (Circle.area) + Shape.describe
  gc.describe();   // GradientCircle.describe → super.describe (Shape) + this.area
}
