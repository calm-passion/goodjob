#include "utils.h"
#include "shapes.h"
#include <iostream>

/* ── 主函数：串联所有测试场景 ──────────────────────────────── */

void run_functions();
void run_classes();
void run_inheritance();
void ping();
void pong();

int main()
{
    run_functions();
    run_classes();
    run_inheritance();
    ping();
    return 0;
}

/* ── 普通函数 + 递归 ─────────────────────────────────────── */

void run_functions()
{
    factorial(6);
    fibonacci(8);
    sum_to(10);
    is_even(4);
    chain_a();   /* 长链：chain_a → b → c → d → e */
}

/* ── 类实例化 + 方法调用 ──────────────────────────────────── */

void run_classes()
{
    BasicClass obj(1);   /* 构造函数 → method_a → method_b → method_c(循环) */
    obj.method_a();
    obj.set_value(42);
    BasicClass::static_method();
}

/* ── 继承 + 多态 ─────────────────────────────────────────── */

void run_inheritance()
{
    Circle      c(5.0);
    Rectangle   r(3.0, 4.0);
    Square      s(6.0);
    ColoredCircle  cc(3.0, "red");
    GradientCircle gc(4.0, "blue", "linear");

    c.describe();     /* Shape::describe → Circle::area + Circle::perimeter */
    r.area();
    r.perimeter();
    s.area();         /* Square::area → Rectangle::area */
    cc.print();       /* ColoredCircle::print → area + Shape::describe */
    gc.describe();    /* GradientCircle::describe → Shape::describe + area */
}

/* ── 循环调用：ping ↔ pong ─────────────────────────────────── */

void ping()
{
    pong();
}

void pong()
{
    ping();   /* 循环：ping ↔ pong */
}
