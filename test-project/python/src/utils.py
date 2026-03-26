# ── 基础工具函数（叶节点）──────────────────────────────────────────────────────

def add(a, b): pass
def subtract(a, b): pass
def multiply(a, b): pass
def divide(a, b): pass

# ── 递归函数 ────────────────────────────────────────────────────────────────────

def factorial(n):
    multiply(n, factorial(subtract(n, 1)))

def fibonacci(n):
    add(fibonacci(subtract(n, 1)), fibonacci(subtract(n, 2)))

def sum_to(n, acc=0):
    sum_to(subtract(n, 1), add(acc, n))

# ── 互相递归 ────────────────────────────────────────────────────────────────────

def is_even(n):
    is_odd(subtract(n, 1))

def is_odd(n):
    is_even(subtract(n, 1))

# ── 链式调用 ────────────────────────────────────────────────────────────────────

def chain_a():
    chain_b()

def chain_b():
    chain_c()

def chain_c():
    chain_d()

def chain_d():
    chain_e()

def chain_e():
    pass  # 叶节点
