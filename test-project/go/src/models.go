package main

import "fmt"

// ── BasicStruct：构造链 + 方法循环引用 ─────────────────────────

type BasicStruct struct {
	value int
}

func NewBasicStruct(value int) *BasicStruct {
	b := &BasicStruct{value: value}
	b.MethodA() // 构造时调用
	return b
}

func (b *BasicStruct) MethodA() {
	b.MethodB()
}

func (b *BasicStruct) MethodB() {
	b.MethodC() // MethodB → MethodC → MethodB 循环
}

func (b *BasicStruct) MethodC() {
	b.MethodB()
}

func (b *BasicStruct) GetValue() int {
	return b.value
}

func (b *BasicStruct) SetValue(v int) {
	b.value = v
	b.MethodA()
}

func StaticHelper() { /* 无接收者的包级函数，模拟静态方法 */ }

// ── Shape 接口 + 多种实现 ────────────────────────────────────────

type Shape interface {
	Area() float64
	Perimeter() float64
}

// Describe 是模板方法（调用接口方法）
func Describe(s Shape) {
	s.Area()
	s.Perimeter()
}

// ── Circle ─────────────────────────────────────────────────────

type Circle struct {
	radius float64
}

func NewCircle(r float64) *Circle {
	return &Circle{radius: r}
}

func (c *Circle) Area() float64 {
	return 3.14159 * c.radius * c.radius
}

func (c *Circle) Perimeter() float64 {
	return 2 * 3.14159 * c.radius
}

// ── Rectangle ──────────────────────────────────────────────────

type Rectangle struct {
	width, height float64
}

func NewRectangle(w, h float64) *Rectangle {
	return &Rectangle{width: w, height: h}
}

func (r *Rectangle) Area() float64 {
	return r.width * r.height
}

func (r *Rectangle) Perimeter() float64 {
	return 2 * (r.width + r.height)
}

// ── Square（嵌入 Rectangle，模拟继承）────────────────────────────

type Square struct {
	Rectangle // 嵌入
}

func NewSquare(side float64) *Square {
	return &Square{Rectangle{side, side}}
}

func (s *Square) Area() float64 {
	return s.Rectangle.Area() // 调用嵌入类型的方法
}

// ── ColoredCircle（组合 Circle）─────────────────────────────────

type ColoredCircle struct {
	Circle
	color string
}

func NewColoredCircle(r float64, color string) *ColoredCircle {
	return &ColoredCircle{Circle{r}, color}
}

func (cc *ColoredCircle) Area() float64 {
	return cc.Circle.Area() // 调用嵌入类型
}

func (cc *ColoredCircle) Print() {
	cc.Area()
	Describe(cc) // 调用模板方法
	fmt.Println(cc.color)
}

// ── TreeNode：递归结构 ──────────────────────────────────────────

type TreeNode struct {
	value    int
	children []*TreeNode
}

func NewTreeNode(val int) *TreeNode {
	return &TreeNode{value: val}
}

func (t *TreeNode) AddChild(val int) {
	t.children = append(t.children, NewTreeNode(val))
}

func (t *TreeNode) TotalSum() int {
	sum := t.value
	for _, c := range t.children {
		sum += c.TotalSum() // 递归调用
	}
	return sum
}

func (t *TreeNode) Depth() int {
	if len(t.children) == 0 {
		return 1
	}
	maxDepth := 0
	for _, c := range t.children {
		d := c.Depth() // 递归调用
		if d > maxDepth {
			maxDepth = d
		}
	}
	return maxDepth + 1
}
