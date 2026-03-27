// 工具函数类
public class Utils {

    // ── 递归函数 ─────────────────────────────────────────────

    public static long factorial(int n) {
        if (n <= 1) return 1;
        return n * factorial(n - 1);   // 自递归
    }

    public static long fibonacci(int n) {
        if (n <= 1) return n;
        return fibonacci(n - 1) + fibonacci(n - 2);   // 自递归
    }

    // ── 普通函数 ─────────────────────────────────────────────

    public static int sumTo(int n) {
        int total = 0;
        for (int i = 1; i <= n; i++) total += i;
        return total;
    }

    // ── 互相递归 ─────────────────────────────────────────────

    public static boolean isEven(int n) {
        if (n == 0) return true;
        return isOdd(n - 1);
    }

    public static boolean isOdd(int n) {
        if (n == 0) return false;
        return isEven(n - 1);
    }

    // ── 长链调用：chainA → B → C → D → E ──────────────────

    public static void chainE() { /* 叶节点 */ }
    public static void chainD() { chainE(); }
    public static void chainC() { chainD(); }
    public static void chainB() { chainC(); }
    public static void chainA() { chainB(); }

    // ── BasicClass：构造链 + 方法循环引用 ─────────────────────

    public static class BasicClass {
        private int value;

        public BasicClass(int value) {
            this.value = value;
            methodA();   // 构造时调用
        }

        public void methodA() {
            methodB();
        }

        public void methodB() {
            methodC();   // methodB → methodC → methodB 循环
        }

        public void methodC() {
            methodB();
        }

        public int getValue() {
            return value;
        }

        public void setValue(int v) {
            this.value = v;
            methodA();
        }

        public static void staticMethod() { /* 叶节点 */ }
    }
}
