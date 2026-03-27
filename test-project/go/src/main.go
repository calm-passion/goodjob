package main

// ── 主函数：串联所有测试场景 ──────────────────────────────────

func main() {
	runFunctions()
	runStructs()
	runShapes()
	runTree()
	ping()
}

// ── 普通函数 + 递归 ───────────────────────────────────────────

func runFunctions() {
	factorial(6)
	fibonacci(8)
	sumTo(10)
	isEven(4)
	chainA() // 长链：chainA → B → C → D → E
}

// ── 结构体实例化 + 方法调用 ───────────────────────────────────

func runStructs() {
	obj := NewBasicStruct(1) // 构造 → MethodA → MethodB → MethodC(循环)
	obj.MethodA()
	obj.SetValue(42)
	StaticHelper()
}

// ── 接口 + 多态 ───────────────────────────────────────────────

func runShapes() {
	c := NewCircle(5.0)
	r := NewRectangle(3.0, 4.0)
	s := NewSquare(6.0)
	cc := NewColoredCircle(3.0, "red")

	Describe(c)    // Shape.Describe → Circle.Area + Circle.Perimeter
	r.Area()
	r.Perimeter()
	s.Area()       // Square.Area → Rectangle.Area
	cc.Print()     // ColoredCircle.Print → area + Describe
}

// ── 树形结构：递归 ────────────────────────────────────────────

func runTree() {
	root := NewTreeNode(10)
	root.AddChild(5)
	root.AddChild(7)
	root.TotalSum() // 递归
	root.Depth()    // 递归
}

// ── 循环调用：ping ↔ pong ─────────────────────────────────────

func ping() {
	pong()
}

func pong() {
	ping() // 循环：ping ↔ pong
}
