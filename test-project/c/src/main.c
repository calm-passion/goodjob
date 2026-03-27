#include "utils.h"
#include <stdio.h>

/* ── 主函数：串联所有测试场景 ───────────────────────────────── */

void run_functions(void);
void run_recursion(void);
void ping(void);
void pong(void);

int main(void)
{
    run_functions();
    run_recursion();
    ping();
    return 0;
}

/* ── 普通函数调用 ────────────────────────────────────────────── */

void run_functions(void)
{
    sum_to(10);
    is_even(4);
    chain_a();   /* 长链：chain_a → b → c → d → e */
}

/* ── 递归测试 ─────────────────────────────────────────────────── */

void run_recursion(void)
{
    factorial(6);    /* 自递归 */
    fibonacci(8);    /* 自递归 */
}

/* ── 循环调用：ping ↔ pong ────────────────────────────────────── */

void ping(void)
{
    pong();
}

void pong(void)
{
    ping();   /* 循环：ping ↔ pong */
}
