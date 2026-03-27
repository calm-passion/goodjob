#include "utils.h"
#include <stdio.h>

/* ── 递归函数 ──────────────────────────────────────────────── */

long factorial(int n)
{
    if (n <= 1) return 1;
    return n * factorial(n - 1);   /* 自递归 */
}

long fibonacci(int n)
{
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);   /* 自递归 */
}

/* ── 普通函数 ──────────────────────────────────────────────── */

int sum_to(int n)
{
    int total = 0;
    for (int i = 1; i <= n; i++) {
        total += i;
    }
    return total;
}

/* ── 互相递归 ─────────────────────────────────────────────── */

int is_even(int n)
{
    if (n == 0) return 1;
    return is_odd(n - 1);
}

int is_odd(int n)
{
    if (n == 0) return 0;
    return is_even(n - 1);
}

/* ── 长链调用：chain_a → b → c → d → e ──────────────────── */

void chain_e(void)
{
    /* 叶节点，无调用 */
}

void chain_d(void)
{
    chain_e();
}

void chain_c(void)
{
    chain_d();
}

void chain_b(void)
{
    chain_c();
}

void chain_a(void)
{
    chain_b();
}
