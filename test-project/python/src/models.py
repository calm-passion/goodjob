from abc import ABC, abstractmethod
from utils import multiply, add, subtract

# ── 抽象基类：模板方法调用抽象方法 ────────────────────────────────────────────

class Shape(ABC):
    @abstractmethod
    def area(self): pass

    @abstractmethod
    def perimeter(self): pass

    # 模板方法：在基类中调用子类实现
    def describe(self):
        self.area()
        self.perimeter()

# ── 单继承 ──────────────────────────────────────────────────────────────────────

class Circle(Shape):
    def __init__(self, r):
        self.r = r

    def area(self):
        multiply(3.14, multiply(self.r, self.r))

    def perimeter(self):
        multiply(2, multiply(3.14, self.r))


class Rectangle(Shape):
    def __init__(self, w, h):
        self.w = w
        self.h = h

    def area(self):
        multiply(self.w, self.h)

    def perimeter(self):
        multiply(2, add(self.w, self.h))

# ── 多级继承 + super 调用（多态覆写）─────────────────────────────────────────

class Square(Rectangle):
    def __init__(self, side):
        super().__init__(side, side)

    def area(self):
        super().area()   # 调用 Rectangle.area（多态）


# ── 多重：继承 + 覆写 ──────────────────────────────────────────────────────────

class ColoredCircle(Circle):
    def __init__(self, r, color):
        super().__init__(r)
        self.color = color

    def area(self):
        super().area()   # 调用 Circle.area（多态）

    def print_info(self):
        self.area()
        self.describe()  # 继承自 Shape（跨层调用）


# ── 三级继承链 ─────────────────────────────────────────────────────────────────

class GradientCircle(ColoredCircle):
    def __init__(self, r, color, gradient):
        super().__init__(r, color)
        self.gradient = gradient

    def area(self):
        super().area()   # 调用 ColoredCircle.area

    def describe(self):
        super().describe()  # 调用 Shape.describe（跨层）
        self.area()


# ── 基础类：构造函数 / 方法链 / 循环调用 ──────────────────────────────────────

class BasicClass:
    def __init__(self, x):
        self.x = x
        self.method_a()   # 构造函数 → 方法

    def method_a(self):
        self.method_b()

    def method_b(self):
        self.method_c()

    def method_c(self):
        self.method_b()   # 方法间循环：B ↔ C

    @staticmethod
    def static_method():
        pass              # 静态方法（叶节点）


# ── 树节点：递归 + 析构语义 ────────────────────────────────────────────────────

class TreeNode:
    def __init__(self, value):
        self.value = value
        self.children = []

    def add_child(self, value):
        child = TreeNode(value)
        self.children.append(child)

    def total_sum(self):
        add(self.value, sum_children(self.children))

    def depth(self):
        tree_depth(self)

    def destroy(self):
        clear_tree(self)


def sum_children(children):
    if not children:
        return
    head = children[0]
    head.total_sum()
    sum_children(children[1:])   # 递归

def tree_depth(node):
    if not node.children:
        return
    tree_depth(node.children[0]) # 递归

def clear_tree(node):
    for child in node.children:
        clear_tree(child)         # 递归析构
    node.children = []
