from utils import (
    add, factorial, fibonacci, sum_to,
    is_even, process_list,
)
from models import Vector, Calculator, TreeNode

# ── 基础链式调用 ───────────────────────────────────────────────────────────────

def calculate(x):
    sq = factorial(x)
    return add(sq, 1)


# ── 递归调用 ───────────────────────────────────────────────────────────────────

def run_recursion():
    f = factorial(6)
    fib = fibonacci(8)
    s = sum_to(10)
    even = is_even(4)
    print(f, fib, s, even)


# ── 列表处理长链 ───────────────────────────────────────────────────────────────

def run_data_processing():
    raw = [3, -1, 4, -1, 5, 9, -2, 6, 0]
    result = process_list(raw)
    print(result)


# ── 向量类（类方法 + 跨文件函数） ─────────────────────────────────────────────

def run_vector():
    v1 = Vector([1, 2, 3])
    v2 = Vector.ones(3)
    v3 = v1.add_vec(v2)
    scaled = v3.scale(2)
    dot = v1.dot(v2)
    mag = scaled.magnitude()
    print(dot, mag)


# ── 计算器：链式调用 + 递归函数 ───────────────────────────────────────────────

def run_calculator():
    calc = Calculator(5)
    result = calc.plus(3).times(2).minus(1).apply_factorial().result()
    avg = calc.history_average()
    print(result, avg)


# ── 树结构：构造/析构/递归 ────────────────────────────────────────────────────

def run_tree():
    root = TreeNode(10)
    child1 = root.add_child(5)
    child1.add_child(3)
    root.add_child(7)
    total = root.total_sum()
    depth = root.depth()
    print(total, depth)
    root.destroy()


# ── 循环调用测试 ───────────────────────────────────────────────────────────────

def ping():
    """循环调用：ping → pong → ping"""
    return pong()

def pong():
    return ping()


# ── 主入口 ─────────────────────────────────────────────────────────────────────

def main():
    print("--- calculate ---")
    print(calculate(5))

    print("--- recursion ---")
    run_recursion()

    print("--- data processing ---")
    run_data_processing()

    print("--- vector ---")
    run_vector()

    print("--- calculator ---")
    run_calculator()

    print("--- tree ---")
    run_tree()
