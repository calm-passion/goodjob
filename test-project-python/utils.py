# ── 基础数学工具 ──────────────────────────────────────────────────────────────

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Division by zero")
    return a / b


# ── 递归函数 ───────────────────────────────────────────────────────────────────

def factorial(n):
    """普通递归：阶乘"""
    if n <= 1:
        return 1
    return multiply(n, factorial(subtract(n, 1)))

def fibonacci(n):
    """树形递归：斐波那契"""
    if n <= 1:
        return n
    return add(fibonacci(subtract(n, 1)), fibonacci(subtract(n, 2)))

def sum_to(n, acc=0):
    """尾递归：累加"""
    if n <= 0:
        return acc
    return sum_to(subtract(n, 1), add(acc, n))


# ── 互相递归：判断奇偶 ─────────────────────────────────────────────────────────

def is_even(n):
    if n == 0:
        return True
    return is_odd(subtract(n, 1))

def is_odd(n):
    if n == 0:
        return False
    return is_even(subtract(n, 1))


# ── 列表处理（调用库函数） ─────────────────────────────────────────────────────

def sum_list(lst):
    return sum(lst)  # built-in, will be ignored

def average(lst):
    return divide(sum_list(lst), len(lst))

def filter_positive(lst):
    return [x for x in lst if x > 0]

def map_double(lst):
    return [multiply(x, 2) for x in lst]

def process_list(lst):
    """长链式调用：过滤 → 翻倍 → 求平均"""
    positive = filter_positive(lst)
    doubled = map_double(positive)
    return average(doubled)
