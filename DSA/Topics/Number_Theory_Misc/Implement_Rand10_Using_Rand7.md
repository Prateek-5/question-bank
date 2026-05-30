# Implement Rand10() Using Rand7()

**Problem Link:**
<a href="https://leetcode.com/problems/implement-rand10-using-rand7/description/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/implement-rand10-using-rand7/description/</a>

**Topic:**
Number Theory / Misc (also randomization)

----------------------------------------

## Step 1: What's Given

`rand7()` is a black-box function returning a **uniformly random integer in {1, 2, 3, 4, 5, 6, 7}**.

Build `rand10()` that returns a uniformly random integer in {1, 2, ..., 10}, using only `rand7()` internally.

Minimize the expected number of `rand7()` calls.

----------------------------------------

## Step 2: First Instinct — Scale Up

Can we just do `(rand7() - 1) * 10 / 7 + 1`? No — that's not uniform. Some values in {1..10} appear more often than others due to non-divisibility.

Similarly, `rand7() + rand7()` gives a distribution peaked at 8 (not uniform on {2..14}).

Uniform-from-biased sources require care.

----------------------------------------

## Step 3: The Core Technique — Rejection Sampling

Key idea: generate a value uniformly over some larger set that's a multiple of 10, then map into {1..10}.

Two rand7() calls give 7 × 7 = **49 equally likely outcomes** when we pair them. Enumerate: `value = (rand7() - 1) * 7 + rand7()`, producing uniform 1..49.

49 isn't a multiple of 10, but 40 is. Use rejection sampling:
- If `value ≤ 40`: return `((value - 1) % 10) + 1`.
- If `value > 40`: reject and try again.

This gives uniform {1..10} because within the accepted range 1..40, each of the 10 possible return values corresponds to exactly 4 pre-images. Uniformity preserved.

----------------------------------------

## Step 4: Why Rejection Works

When we reject, we retry from scratch. The distribution of the accepted outcome is uniform over the accepted set (1..40), and our mapping (value mod 10) is a balanced 4-to-1 function onto {1..10}. So each result in {1..10} has probability 4/40 = 1/10.

Rejection doesn't bias the output — it just extends the expected runtime.

----------------------------------------

## Step 5: Algorithm

```
def rand10():
    while True:
        a = rand7()
        b = rand7()
        value = (a - 1) * 7 + b   # uniform 1..49
        if value <= 40:
            return ((value - 1) % 10) + 1
        # else retry
```

Each iteration makes 2 `rand7()` calls. Probability of acceptance = 40/49.

Expected iterations = 1 / (40/49) = 49/40 ≈ 1.225.

Expected `rand7()` calls per `rand10()` = 2 × 1.225 = **2.45**.

----------------------------------------

## Step 6: Can We Do Better? (Optimization via Reusing Rejected Values)

When value ∈ {41..49}, we rejected 9 possible values — that's uniform over 9 outcomes. We can use them:
- Map 41..49 to 1..9 by subtracting 40.
- Now generate another rand7() and form a 9 × 7 = **63 uniform outcomes**, take mod 60, etc.

This cascades: squeeze every bit of entropy from rejects. Reduces expected calls to ~2.2.

The simple version (2.45) is usually enough for interviews.

----------------------------------------

## Step 7: Trace

Imagine rand7() returns: 3, 5. Then value = (3-1)*7 + 5 = 19. 19 ≤ 40, accept. Result = ((19-1) % 10) + 1 = 8 + 1 = **9**.

Another run: rand7() returns 6, 5. value = (6-1)*7 + 5 = 40. Accept. Result = ((40-1) % 10) + 1 = 9 + 1 = **10**.

Another: rand7() returns 7, 6. value = (7-1)*7 + 6 = 48. 48 > 40, reject. Retry.

----------------------------------------

## Step 8: Why Multiplication by (7 - 1)?

We use `(rand7() - 1) * 7 + rand7()`:
- `rand7() - 1` gives 0..6 (7 choices) — the "high digit" in base 7.
- Second `rand7()` gives 1..7 — the "low digit."
- Their combination gives 49 distinct pairs, mapping 1-to-1 onto 1..49.

Think of this as **base-7 composition**: we're building a 2-digit base-7 number plus 1. Guarantees uniformity when both rand7()s are independent.

----------------------------------------

## Step 9: Name It

**Rejection sampling from a larger uniform space.** Universal technique:
- Generate uniform on {1..M} where M > N and M is a multiple of N.
- Accept with probability ≤ M' / M where M' is the largest multiple of N ≤ M.
- Reject otherwise.

Related problems:
- rand_m from rand_n where gcd logic matters.
- Random point in a unit disk (sample in square, reject outside).
- Shuffle algorithms using biased sources.

The key insight: **you can't scale a random variable, but you can reject samples**.

----------------------------------------

## Step 10: Complexity

Expected time: **O(1)** per rand10() — ~2.45 rand7() calls on average.
Worst case: unbounded (probabilistic). In practice, the chance of many retries is astronomically small.

Space: O(1).

----------------------------------------

## Step 11: C++ Implementation

```cpp
int rand10() {
    while (true) {
        int a = rand7();   // 1..7
        int b = rand7();   // 1..7
        int value = (a - 1) * 7 + b;   // 1..49
        if (value <= 40) {
            return ((value - 1) % 10) + 1;
        }
    }
}
```

The `while (true)` with a probabilistic `return` is idiomatic for rejection sampling.

## Step 12: Optimized C++ (Reuse Rejects)

```cpp
int rand10() {
    while (true) {
        int a = rand7(), b = rand7();
        int v1 = (a - 1) * 7 + b;
        if (v1 <= 40) return ((v1 - 1) % 10) + 1;

        // v1 in 41..49 → subtract 40 to get 1..9
        int c = rand7();
        int v2 = (v1 - 41) * 7 + c;   // 1..63
        if (v2 <= 60) return ((v2 - 1) % 10) + 1;

        // v2 in 61..63 → subtract 60 to get 1..3
        int d = rand7();
        int v3 = (v2 - 61) * 7 + d;   // 1..21
        if (v3 <= 20) return ((v3 - 1) % 10) + 1;
        // Else start over with 3 rand7() calls spent but no result.
    }
}
```

Each cascade reduces the rejection probability further.

----------------------------------------

## Step 13: Follow-up Questions

- **rand_n from rand_m where n > m.** Combine more calls: k calls give m^k outcomes. Pick the largest multiple of n ≤ m^k.
- **rand_n from rand_m where gcd(m, n) > 1.** Possible but more complex to derive; similar rejection principle.
- **Without rejection (deterministic bounded time).** Impossible in general — some bias is inevitable when sampling from a non-divisible source.
- **Use bits from rand7().** rand7() has ~log2(7) ≈ 2.807 bits of entropy each. For rand10() (log2 10 ≈ 3.32), we need ~1.18 rand7() calls' worth of bits — so ~2 calls is near-optimal.
- **Expected number of calls for large n.** Approaches log2(n) / log2(m) for rand_n from rand_m.
- **Why not (rand7() + rand7()) % 10 + 1?** That's biased — sums are not uniform.
