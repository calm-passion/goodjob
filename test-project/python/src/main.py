from utils import factorial, fibonacci, sum_to, is_even, chain_a
from models import BasicClass, Circle, Rectangle, Square, ColoredCircle, GradientCircle, TreeNode

# ── 主函数：串联所有测试场景 ───────────────────────────────────────────────────

def main():
    run_functions()
    run_classes()
    run_inheritance()
    run_tree()
    ping()

# ── 普通函数调用 + 递归 ────────────────────────────────────────────────────────

def run_functions():
    factorial(6)
    fibonacci(8)
    sum_to(10)
    is_even(4)
    chain_a()       # 长链：chain_a → b → c → d → e

# ── 类实例化 + 方法调用 ────────────────────────────────────────────────────────

def run_classes():
    obj = BasicClass(1)   # 构造函数 → method_a → method_b → method_c(循环)
    obj.method_a()
    BasicClass.static_method()

# ── 继承 + 多态 ────────────────────────────────────────────────────────────────

def run_inheritance():
    c  = Circle(5)
    r  = Rectangle(3, 4)
    s  = Square(6)
    cc = ColoredCircle(3, 'red')
    gc = GradientCircle(4, 'blue', 'linear')

    c.describe()      # Shape.describe → Circle.area + Circle.perimeter
    r.area()
    r.perimeter()
    s.area()          # Square.area → super → Rectangle.area
    cc.print_info()   # ColoredCircle.print_info → super.area + Shape.describe
    gc.describe()     # GradientCircle.describe → super.describe + self.area

# ── 树结构：构造 / 递归 / 析构 ────────────────────────────────────────────────

def run_tree():
    root = TreeNode(10)
    root.add_child(5)
    root.add_child(7)
    root.total_sum()
    root.depth()
    root.destroy()

# ── 循环调用 ────────────────────────────────────────────────────────────────────

def ping():
    pong()

def pong():
    ping()    # 循环：ping ↔ pong
