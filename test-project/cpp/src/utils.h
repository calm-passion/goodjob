#pragma once

/* 工具函数 */
long factorial(int n);
long fibonacci(int n);
int sum_to(int n);
bool is_even(int n);
bool is_odd(int n);

void chain_a();
void chain_b();
void chain_c();
void chain_d();
void chain_e();

/* ── BasicClass：构造链 + 方法循环引用 ──────────────────────── */
class BasicClass {
public:
    explicit BasicClass(int value);
    void method_a();
    void method_b();
    void method_c();   // method_b ↔ method_c 循环
    int  get_value() const;
    void set_value(int v);
    static void static_method();

private:
    int m_value;
};
