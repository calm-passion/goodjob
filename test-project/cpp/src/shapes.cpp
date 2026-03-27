#include "shapes.h"
#include <cmath>

/* ── Shape ───────────────────────────────────────────────── */

void Shape::describe() const
{
    area();
    perimeter();
}

/* ── Circle ──────────────────────────────────────────────── */

Circle::Circle(double r) : m_r(r) {}

double Circle::area() const
{
    return M_PI * m_r * m_r;
}

double Circle::perimeter() const
{
    return 2.0 * M_PI * m_r;
}

/* ── Rectangle ───────────────────────────────────────────── */

Rectangle::Rectangle(double w, double h) : m_w(w), m_h(h) {}

double Rectangle::area() const
{
    return m_w * m_h;
}

double Rectangle::perimeter() const
{
    return 2.0 * (m_w + m_h);
}

/* ── Square ──────────────────────────────────────────────── */

Square::Square(double side) : Rectangle(side, side) {}

double Square::area() const
{
    return Rectangle::area();   /* 调用父类 */
}

/* ── ColoredCircle ───────────────────────────────────────── */

ColoredCircle::ColoredCircle(double r, const std::string& color)
    : Circle(r), m_color(color)
{}

double ColoredCircle::area() const
{
    return Circle::area();   /* 调用 Circle::area */
}

void ColoredCircle::print() const
{
    area();
    describe();   /* 继承自 Shape（跨层调用） */
}

/* ── GradientCircle ──────────────────────────────────────── */

GradientCircle::GradientCircle(double r, const std::string& color,
                                const std::string& gradient)
    : ColoredCircle(r, color), m_gradient(gradient)
{}

double GradientCircle::area() const
{
    return ColoredCircle::area();   /* 调用 ColoredCircle::area */
}

void GradientCircle::describe() const
{
    Shape::describe();   /* 跨层调用基类模板方法 */
    area();
}
