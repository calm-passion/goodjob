#pragma once
#include <string>

/* ── 抽象基类 ─────────────────────────────────────────────── */
class Shape {
public:
    virtual ~Shape() = default;
    virtual double area() const = 0;
    virtual double perimeter() const = 0;
    void describe() const;   /* 模板方法：调用 area() + perimeter() */
};

/* ── 单继承 ───────────────────────────────────────────────── */
class Circle : public Shape {
public:
    explicit Circle(double r);
    double area() const override;
    double perimeter() const override;
private:
    double m_r;
};

class Rectangle : public Shape {
public:
    Rectangle(double w, double h);
    double area() const override;
    double perimeter() const override;
private:
    double m_w, m_h;
};

/* ── 多级继承 ─────────────────────────────────────────────── */
class Square : public Rectangle {
public:
    explicit Square(double side);
    double area() const override;   /* 调用 Rectangle::area */
};

/* ── 接口 ─────────────────────────────────────────────────── */
class Printable {
public:
    virtual void print() const = 0;
    virtual ~Printable() = default;
};

/* ── 多重继承 ─────────────────────────────────────────────── */
class ColoredCircle : public Circle, public Printable {
public:
    ColoredCircle(double r, const std::string& color);
    double area() const override;   /* 调用 Circle::area */
    void print() const override;
private:
    std::string m_color;
};

/* ── 三级继承 ─────────────────────────────────────────────── */
class GradientCircle : public ColoredCircle {
public:
    GradientCircle(double r, const std::string& color, const std::string& gradient);
    double area() const override;     /* 调用 ColoredCircle::area */
    void describe() const;            /* 调用 Shape::describe + area */
private:
    std::string m_gradient;
};
