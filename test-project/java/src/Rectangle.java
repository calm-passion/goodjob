// ── 单继承 ──────────────────────────────────────────────────────

public class Rectangle extends Shape {
    private double width;
    private double height;

    public Rectangle(double width, double height) {
        this.width = width;
        this.height = height;
    }

    @Override
    public double area() {
        return width * height;
    }

    @Override
    public double perimeter() {
        return 2 * (width + height);
    }
}

// ── 多级继承 + super 调用 ────────────────────────────────────────

class Square extends Rectangle {

    public Square(double side) {
        super(side, side);
    }

    @Override
    public double area() {
        return super.area();   // 调用 Rectangle.area（多态）
    }
}

// ── 接口 ────────────────────────────────────────────────────────

interface Printable {
    void print();
}

// ── 多重：继承 + 实现接口 ────────────────────────────────────────

class ColoredCircle extends Circle implements Printable {
    private String color;

    public ColoredCircle(double radius, String color) {
        super(radius);
        this.color = color;
    }

    @Override
    public double area() {
        return super.area();   // 调用 Circle.area（多态）
    }

    @Override
    public void print() {
        area();
        describe();   // 继承自 Shape（跨层调用）
    }
}

// ── 三级继承链 ──────────────────────────────────────────────────

class GradientCircle extends ColoredCircle {
    private String gradient;

    public GradientCircle(double radius, String color, String gradient) {
        super(radius, color);
        this.gradient = gradient;
    }

    @Override
    public double area() {
        return super.area();   // 调用 ColoredCircle.area
    }

    @Override
    public void describe() {
        super.describe();      // 调用 Shape.describe（跨层）
        area();
    }
}
