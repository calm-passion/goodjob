from utils import add, multiply, subtract, divide, factorial, average

# ── 向量类（类方法互调 + 外部函数） ──────────────────────────────────────────

class Vector:
    def __init__(self, data):
        self.data = list(data)
        self._validate()

    def _validate(self):
        if not self.data:
            raise ValueError("Vector cannot be empty")

    def dot(self, other):
        pairs = [multiply(a, b) for a, b in zip(self.data, other.data)]
        return sum(pairs)

    def magnitude(self):
        return self.dot(self) ** 0.5

    def scale(self, factor):
        return Vector([multiply(v, factor) for v in self.data])

    def add_vec(self, other):
        return Vector([add(a, b) for a, b in zip(self.data, other.data)])

    @staticmethod
    def zeros(n):
        return Vector([0] * n)

    @staticmethod
    def ones(n):
        return Vector([1] * n)


# ── 计算器类：链式调用 + 递归函数 ─────────────────────────────────────────────

class Calculator:
    def __init__(self, initial=0):
        self.history = [initial]

    def _current(self):
        return self.history[-1]

    def _record(self, value):
        self.history.append(value)
        return self

    def plus(self, n):
        return self._record(add(self._current(), n))

    def minus(self, n):
        return self._record(subtract(self._current(), n))

    def times(self, n):
        return self._record(multiply(self._current(), n))

    def divided_by(self, n):
        return self._record(divide(self._current(), n))

    def apply_factorial(self):
        return self._record(factorial(self._current()))

    def result(self):
        return self._current()

    def history_average(self):
        return average(self.history)


# ── 树节点：析构语义 + 递归 ────────────────────────────────────────────────────

class TreeNode:
    def __init__(self, value):
        self.value = value
        self.children = []

    def add_child(self, value):
        child = TreeNode(value)
        self.children.append(child)
        return child

    def total_sum(self):
        return add(self.value, sum_children(self.children))

    def depth(self):
        return tree_depth(self)

    def destroy(self):
        clear_tree(self)


def sum_children(children):
    """递归求子树之和"""
    if not children:
        return 0
    head = children[0]
    rest = children[1:]
    return add(head.total_sum(), sum_children(rest))

def tree_depth(node):
    """递归求树深度"""
    if not node.children:
        return 1
    return add(1, max(tree_depth(c) for c in node.children))

def clear_tree(node):
    """递归清空树节点（析构语义）"""
    for child in node.children:
        clear_tree(child)
    node.children = []
