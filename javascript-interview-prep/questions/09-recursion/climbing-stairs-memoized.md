# Climbing stairs — recursive with memoization

> **Difficulty:** Foundation-Medium   |   **Time:** ~10 min   |   **Prereqs:** [trampoline-pattern.md](./trampoline-pattern.md)
>
> **Source:** LeetCode #70. Rosetta stone of DP.

---

## 1. Problem statement

`f(n) = f(n-1) + f(n-2)`. Three solutions: naive (exponential), memoized (O(n)), iterative O(1) space.

**Verification examples**

```js
climbStairs(2);                          // 2
climbStairs(3);                          // 3
climbStairs(10);                         // 89
climbStairs(45);                         // 1_836_311_903 (last that fits Number safely)
```

**Constraints**
- Naive: O(2^n) — useless past n≈30.
- Memo: O(n) time, O(n) space.
- Iterative: O(n) time, O(1) space.
- Same shape as Fibonacci.

---

## 2. Plain-English restatement

Number of ways to climb n stairs taking 1 or 2 at a time = Fibonacci. Three solutions in escalating sophistication.

---

## 3. Why this matters in interviews

Diagnostic: senior candidates volunteer naive → notice overlap → memo → iterative O(1). Tests recurrence recognition + DP progression.

---

## 4. Mental model

```
   f(n) = f(n-1) + f(n-2), f(1)=1, f(2)=2.
   
   Naive recursion: O(2^n).
     Each call branches twice; tree has 2^n leaves.
     Lots of repeated subproblems: f(2) recomputed many times.
   
   Top-down memo: O(n).
     Cache memo[n].
     First call computes; subsequent: lookup.
     Tree pruned to n unique subproblems.
   
   Bottom-up iterative: O(n) time, O(1) space.
     Build up: f(1), f(2), f(3) = f(2)+f(1), ...
     Only need last two values.
   
   Matrix exponentiation: O(log n).
     [[1,1],[1,0]]^n; rarely needed.
   
   Closed form (Binet): O(1) but float precision limits.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why is naive O(2^n)?
> 2. Stack depth for naive vs memo?
> 3. Can you do O(1) space?

---

## 6. Brute force — walked through

```js
function naive(n) {
  if (n <= 2) return n;
  return naive(n - 1) + naive(n - 2);   // recomputes constantly
}
// naive(40) takes seconds; naive(50) takes minutes.
```

---

## 7. The unlocking insight

> **Recurrence overlaps; memo or bottom-up turns exponential → linear. Only last two values needed.**

Three properties:

1. **Overlapping subproblems** → memo.
2. **Only `prev1, prev2`** needed → O(1) space.
3. **Fibonacci shape** — common pattern.

---

## 8. Solution (annotated)

```js
// 1. Naive (DO NOT submit)
function climbStairsNaive(n) {
  if (n <= 2) return n;
  return climbStairsNaive(n - 1) + climbStairsNaive(n - 2);                // step 1: O(2^n)
}

// 2. Top-down memoization
function climbStairsMemo(n, memo = new Map()) {
  if (n <= 2) return n;
  if (memo.has(n)) return memo.get(n);                                      // step 2: cache hit
  const result = climbStairsMemo(n - 1, memo) + climbStairsMemo(n - 2, memo);
  memo.set(n, result);                                                       // step 3: store
  return result;
}

// 3. Bottom-up O(1) space — production answer
function climbStairs(n) {
  if (n <= 2) return n;
  let prev2 = 1, prev1 = 2;
  for (let i = 3; i <= n; i++) {                                             // step 4: build up
    const curr = prev1 + prev2;
    prev2 = prev1;
    prev1 = curr;
  }
  return prev1;
}

// 4. Matrix exponentiation O(log n)
function climbStairsMatrix(n) {
  if (n <= 2) return n;
  function mul(a, b) {
    return [
      [a[0][0]*b[0][0] + a[0][1]*b[1][0], a[0][0]*b[0][1] + a[0][1]*b[1][1]],
      [a[1][0]*b[0][0] + a[1][1]*b[1][0], a[1][0]*b[0][1] + a[1][1]*b[1][1]],
    ];
  }
  function pow(m, p) {
    let result = [[1, 0], [0, 1]];
    while (p > 0) {
      if (p & 1) result = mul(result, m);
      m = mul(m, m);
      p >>= 1;
    }
    return result;
  }
  const m = pow([[1, 1], [1, 0]], n);
  return m[0][0];
}
```

**Try it yourself**

```js
climbStairs(1);                                                // 1
climbStairs(2);                                                // 2
climbStairs(3);                                                // 3
climbStairs(10);                                               // 89
climbStairs(45);                                               // 1_836_311_903

// Benchmark: naive vs memo
console.time('naive');
climbStairsNaive(35);     // ~ seconds
console.timeEnd('naive');

console.time('memo');
climbStairsMemo(1000);    // microseconds
console.timeEnd('memo');

console.time('iter');
climbStairs(1_000_000);   // ms (Number precision limits past ~45 though)
console.timeEnd('iter');

// BigInt for huge n
function climbStairsBigInt(n) {
  if (n <= 2) return BigInt(n);
  let prev2 = 1n, prev1 = 2n;
  for (let i = 3; i <= n; i++) {
    const curr = prev1 + prev2;
    prev2 = prev1; prev1 = curr;
  }
  return prev1;
}

// Variant: 3-step variants (1, 2, or 3 steps)
function climbStairs3Step(n) {
  if (n <= 2) return n;
  if (n === 3) return 4;
  let a = 1, b = 2, c = 4;
  for (let i = 4; i <= n; i++) {
    const next = a + b + c;
    a = b; b = c; c = next;
  }
  return c;
}
```

---

## 9. Step-by-step dry run

```
climbStairsNaive(5):
  f(5) = f(4) + f(3)
       = [f(3)+f(2)] + [f(2)+f(1)]
       = [(f(2)+f(1))+f(2)] + [f(2)+f(1)]
       = [(2+1)+2] + [2+1]
       = 5 + 3 = 8.

Tree of calls:
              f(5)
             /    \
           f(4)    f(3)
          /    \   /  \
         f(3) f(2) f(2) f(1)
         / \
       f(2) f(1)
  
  f(2) computed 3 times, f(1) computed 2 times.
  Exponential repetition.

climbStairsMemo(5):
  memo = {}.
  f(5) → memo miss. Need f(4) + f(3).
  f(4) → memo miss. Need f(3) + f(2).
  f(3) → memo miss. Need f(2) + f(1) = 2 + 1 = 3. memo.set(3, 3).
  f(2) → 2.
  Back to f(4): 3 + 2 = 5. memo.set(4, 5).
  Back to f(5): f(3) hit memo → 3. 5 + 3 = 8.
  
  Each f(k) computed once. O(n) total.

climbStairs(5) iterative:
  prev2=1, prev1=2.
  i=3: curr=3. prev2=2, prev1=3.
  i=4: curr=5. prev2=3, prev1=5.
  i=5: curr=8. prev2=5, prev1=8.
  return 8.
```

---

## 10. Common confusion + traps

1. **Submit naive** — TLE at n>30.
2. **`memo` default arg shared** — `memo = {}` per call creates new (correct); `memo = []` likewise; closure-captured Map can leak across calls.
3. **`memo[n] !== undefined`** vs `memo.has(n)` — works for Map.
4. **No `n <= 0` guard** — `0` returns 0; clarify spec.
5. **Number precision past n=45** — switch to BigInt.
6. **Stack depth** for naive ~n; memo still uses stack.
7. **Closed-form (Binet)** — float precision unreliable.

---

## 11. Senior follow-ups & variants

### Variant 1 — 3-step (1, 2, or 3)
Three-rolling-vars.

### Variant 2 — K-step
Generalized; rolling window of k.

### Variant 3 — Cost climbing (LeetCode #746)
Add per-step cost; minimize.

### Variant 4 — Path count in grid
Same recurrence, 2D.

### Variant 5 — Matrix exp O(log n)
Theoretical; rarely needed.

---

## 12. How to think aloud

> "Climbing stairs is `f(n) = f(n-1) + f(n-2)` with `f(1)=1, f(2)=2` — same shape as Fibonacci. Three solutions in escalating sophistication: (1) naive recursion `f(n) = f(n-1) + f(n-2)` — O(2^n) because the same subproblems are recomputed exponentially; takes seconds at n=30, hours at n=40, never finishes at n=50. (2) Top-down memoization — wrap with a Map cache; first call computes, subsequent return cached → O(n) time + O(n) space + O(n) stack. (3) Bottom-up iterative — only last two values needed (`prev1`, `prev2`); roll them forward; O(n) time, O(1) space. This is the production answer. Number precision limits past n≈45 — switch to BigInt for arbitrary precision. Matrix exponentiation gives O(log n) but is theoretical; rarely needed. Variants: 3-step (1, 2, or 3 steps — 3 rolling vars); cost climbing (LeetCode #746 — minimize cost); 2D path count. Senior signal: volunteer naive, recognize overlap, walk through to O(1) space."

---

## 13. 60-second revision

> - **`f(n) = f(n-1) + f(n-2)`**, Fibonacci shape.
> - **Naive O(2^n)** — useless past n=30.
> - **Memo O(n)** time + space.
> - **Iterative O(1) space** — production.
> - **`prev1, prev2` roll forward.**
> - **BigInt** for n > 45.
> - **Matrix exp** O(log n) theoretical.
> - **3-step / k-step** generalize.
> - **Trap:** naive submit; precision past n=45.

---

**Related:** [trampoline-pattern.md](./trampoline-pattern.md) · [iterative-from-recursive.md](./iterative-from-recursive.md) · [`10-machine-coding-patterns/memoize.md`](../10-machine-coding-patterns/memoize.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
