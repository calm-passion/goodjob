#include "utils.h"
#include <cstdio>

/* ── 递归函数 ─────────────────────────────────────────────── */

long factorial(int n)
{
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

long fibonacci(int n)
{
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

/* ── 普通函数 ─────────────────────────────────────────────── */

int sum_to(int n)
{
    int total = 0;
    for (int i = 1; i <= n; i++) total += i;
    return total;
}

/* ── 互相递归 ────────────────────────────────────────────── */

bool is_even(int n)
{
    if (n == 0) return true;
    return is_odd(n - 1);
}

bool is_odd(int n)
{
    if (n == 0) return false;
    return is_even(n - 1);
}

/* ── 长链调用 ────────────────────────────────────────────── */

void chain_e() { /* 叶节点 */ }
void chain_d() { chain_e(); }
void chain_c() { chain_d(); }
void chain_b() { chain_c(); }
void chain_a() { chain_b(); }

/* ── BasicClass 实现 ─────────────────────────────────────── */

BasicClass::BasicClass(int value) : m_value(value)
{
    method_a();
}

void BasicClass::method_a()
{
    method_b();
}

void BasicClass::method_b()
{
    method_c();   /* method_b → method_c → method_b 循环 */
}

void BasicClass::method_c()
{
    method_b();
}

int BasicClass::get_value() const
{
    return m_value;
}

void BasicClass::set_value(int v)
{
    m_value = v;
    method_a();
}

void BasicClass::static_method()
{
    /* 叶节点 */
}
