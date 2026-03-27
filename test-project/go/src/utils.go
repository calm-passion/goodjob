package main

// ── 递归函数 ─────────────────────────────────────────────────

func factorial(n int) int {
	if n <= 1 {
		return 1
	}
	return n * factorial(n-1) // 自递归
}

func fibonacci(n int) int {
	if n <= 1 {
		return n
	}
	return fibonacci(n-1) + fibonacci(n-2) // 自递归
}

// ── 普通函数 ─────────────────────────────────────────────────

func sumTo(n int) int {
	total := 0
	for i := 1; i <= n; i++ {
		total += i
	}
	return total
}

// ── 互相递归 ─────────────────────────────────────────────────

func isEven(n int) bool {
	if n == 0 {
		return true
	}
	return isOdd(n - 1)
}

func isOdd(n int) bool {
	if n == 0 {
		return false
	}
	return isEven(n - 1)
}

// ── 长链调用：chainA → B → C → D → E ──────────────────────

func chainE() { /* 叶节点 */ }
func chainD() { chainE() }
func chainC() { chainD() }
func chainB() { chainC() }
func chainA() { chainB() }
