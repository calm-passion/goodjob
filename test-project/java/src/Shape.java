// ── 抽象基类：模板方法调用抽象方法 ──────────────────────────────

public abstract class Shape {

    public abstract double area();
    public abstract double perimeter();

    // 模板方法：在基类中调用子类实现
    public void describe() {
        area();
        perimeter();
    }
}
