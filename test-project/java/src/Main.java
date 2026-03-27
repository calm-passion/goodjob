// ── 主入口：串联所有测试场景 ────────────────────────────────────

public class Main {

    public static void main(String[] args) {
        runFunctions();
        runClasses();
        runInheritance();
        runTree();
        ping();
    }

    // ── 普通函数调用 + 递归 ─────────────────────────────────────

    static void runFunctions() {
        Utils.factorial(6);
        Utils.fibonacci(8);
        Utils.sumTo(10);
        Utils.isEven(4);
        Utils.chainA();   // 长链：chainA → B → C → D → E
    }

    // ── 类实例化 + 方法调用 ─────────────────────────────────────

    static void runClasses() {
        Utils.BasicClass obj = new Utils.BasicClass(1); // 构造 → methodA → methodB → methodC(循环)
        obj.methodA();
        obj.setValue(42);
        Utils.BasicClass.staticMethod();
    }

    // ── 继承 + 多态 ─────────────────────────────────────────────

    static void runInheritance() {
        Circle c  = new Circle(5.0);
        Rectangle r = new Rectangle(3.0, 4.0);
        Square s  = new Square(6.0);
        ColoredCircle  cc = new ColoredCircle(3.0, "red");
        GradientCircle gc = new GradientCircle(4.0, "blue", "linear");

        c.describe();     // Shape.describe → Circle.area + Circle.perimeter
        r.area();
        r.perimeter();
        s.area();         // Square.area → super → Rectangle.area
        cc.print();       // ColoredCircle.print → super.area (Circle.area) + Shape.describe
        gc.describe();    // GradientCircle.describe → super.describe (Shape) + area
    }

    // ── 树结构：递归 ────────────────────────────────────────────

    static void runTree() {
        TreeNode root = new TreeNode(10);
        root.addChild(5);
        root.addChild(7);
        root.totalSum();
        root.depth();
        root.destroy();
    }

    // ── 循环调用：ping ↔ pong ────────────────────────────────────

    static void ping() {
        pong();
    }

    static void pong() {
        ping();   // 循环：ping ↔ pong
    }
}

// ── TreeNode：递归数据结构 ───────────────────────────────────────

class TreeNode {
    private int value;
    private java.util.List<TreeNode> children = new java.util.ArrayList<>();

    public TreeNode(int value) {
        this.value = value;
    }

    public void addChild(int val) {
        children.add(new TreeNode(val));
    }

    public int totalSum() {
        int sum = value;
        for (TreeNode child : children) {
            sum += child.totalSum();   // 递归
        }
        return sum;
    }

    public int depth() {
        if (children.isEmpty()) return 1;
        int max = 0;
        for (TreeNode child : children) {
            int d = child.depth();     // 递归
            if (d > max) max = d;
        }
        return max + 1;
    }

    public void destroy() {
        for (TreeNode child : children) {
            child.destroy();           // 递归
        }
        children.clear();
    }
}
