# Climbing Stairs

**Problem Link:**
<a href="https://leetcode.com/problems/climbing-stairs/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/climbing-stairs/</a>

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Understand the Problem (Beginner Friendly)

There's a staircase with `n` steps. At each move you can climb either 1 step or 2 steps. You want to count **how many distinct ways** there are to reach the top.

Before trying any algorithm, let's just think about what "a way" means. A "way" is a sequence of moves. For `n = 3`, a sequence like `1 + 1 + 1` is one way. `1 + 2` is another. `2 + 1` is a third. We're not minimizing anything, we're not asking for the fastest path — we're counting sequences.

That's the entire problem. No tricks hidden in the phrasing. Our job is: given `n`, return the count of distinct step-sequences whose sum is `n` where each step is 1 or 2.

----------------------------------------

## Step 2: Let's Just Try Small Cases

When a counting problem looks abstract, the best move is to stop thinking about algorithms and start **counting by hand** for tiny inputs. The answer often reveals itself before we write a single line of code.

**n = 1:** Only one way — take a single 1-step. Count = **1**.

**n = 2:** Two ways — `1+1`, or `2`. Count = **2**.

**n = 3:** Let me list them carefully.
- `1+1+1`
- `1+2`
- `2+1`

That's three. Count = **3**.

**n = 4:** Let me be really careful here.
- `1+1+1+1`
- `1+1+2`
- `1+2+1`
- `2+1+1`
- `2+2`

Count = **5**.

**n = 5:** Same drill.
- `1+1+1+1+1`
- `1+1+1+2`, `1+1+2+1`, `1+2+1+1`, `2+1+1+1` — that's four.
- `1+2+2`, `2+1+2`, `2+2+1` — three.

Total = 1 + 4 + 3 = **8**.

So the sequence we've computed is: `1, 2, 3, 5, 8, ...`

Pause and look at that sequence.

----------------------------------------

## Step 3: What Do We Notice?

Stare at `1, 2, 3, 5, 8` for a moment.

- `3 = 2 + 1`
- `5 = 3 + 2`
- `8 = 5 + 3`

Each number is the sum of the two before it. That's a recurrence staring us in the face:

```
ways(n) = ways(n-1) + ways(n-2)
```

Now — and this is the important part — **why** should this be true? Patterns are nice, but we want to *understand* the pattern, not just observe it. Otherwise we'd never trust it for larger `n`.

Here's the reasoning: suppose you're standing at step `n`. How did you get there? Two options, no more, no less:

1. Your very last move was a **1-step**, meaning you were previously at step `n-1`.
2. Your very last move was a **2-step**, meaning you were previously at step `n-2`.

Those two options don't overlap (the last move is different in each) and together they cover every possible way to have arrived at step `n`. So the total number of ways to be at step `n` equals the number of ways to be at step `n-1` (and then take a 1-step) plus the number of ways to be at step `n-2` (and then take a 2-step).

That's the derivation. The pattern isn't a coincidence — it comes directly from "how did I take my last step?".

----------------------------------------

## Step 4: Naming What We've Found

Now we can name it: the sequence `1, 2, 3, 5, 8, 13, ...` is the **Fibonacci sequence** (shifted by one position from the usual mathematical definition). And the recurrence `f(n) = f(n-1) + f(n-2)` is the textbook definition of **Dynamic Programming**: the answer at state `n` depends only on a few smaller states.

But notice — we didn't *start* with "this is DP" or "this is Fibonacci". We started by listing small cases, saw the pattern, and reasoned *why* it must be true. The name came last, and it barely matters. What matters is the recurrence.

----------------------------------------

## Step 5: From Recurrence to Code

We have `f(n) = f(n-1) + f(n-2)` with `f(1) = 1` and `f(2) = 2`. The most natural first attempt is recursion:

```cpp
int ways(int n) {
    if (n == 1) return 1;
    if (n == 2) return 2;
    return ways(n-1) + ways(n-2);
}
```

This works for small `n`, but let's think about what it does for `n = 5`:

- `ways(5)` calls `ways(4)` and `ways(3)`.
- `ways(4)` calls `ways(3)` and `ways(2)`.
- `ways(3)` gets called **twice** — once from `ways(5)`, once from `ways(4)`.

And for `n = 40`, `ways(3)` is called billions of times. The recursion re-solves the same subproblems exponentially. Any beginner writing this would watch their program hang and think "something's wrong with my computer".

The fix is almost silly: **remember** each answer the first time we compute it. That's memoization. Or, even simpler — since we only ever need the previous two values, we don't need an array at all. Just two variables, rolling forward.

```cpp
int climbStairs(int n) {
    if (n <= 2) return n;
    int a = 1, b = 2;               // a = ways(1), b = ways(2)
    for (int i = 3; i <= n; ++i) {
        int c = a + b;              // ways(i) = ways(i-1) + ways(i-2)
        a = b;
        b = c;
    }
    return b;
}
```

----------------------------------------

## Step 6: Dry Run for n = 5

Let me trace this to make sure it's right.

```
Start: a = 1 (ways(1)), b = 2 (ways(2))

i = 3: c = 1 + 2 = 3. Shift: a = 2, b = 3.
i = 4: c = 2 + 3 = 5. Shift: a = 3, b = 5.
i = 5: c = 3 + 5 = 8. Shift: a = 5, b = 8.

Return b = 8.
```

Compare to our hand-count for `n = 5`: we found 8 sequences. They match. That's our validation.

----------------------------------------

## Step 7: Complexity

Time: we loop from 3 to n, doing O(1) work per iteration. That's **O(n)**.

Space: we use three integer variables. That's **O(1)**.

The recursive version with memoization would be O(n) time and O(n) space. The rolling-variable version trims space to constant because we only need the last two values.

A math-olympiad trick: since we're computing Fibonacci numbers, we can actually do this in O(log n) using matrix exponentiation. For `n ≤ 10^18`, that matters. For typical interview constraints, O(n) is fine.

----------------------------------------

## Step 8: Follow-up Questions

- **What if the allowed step sizes are {1, 2, 3}?** The recurrence becomes `f(n) = f(n-1) + f(n-2) + f(n-3)`. Same derivation, one extra term.
- **What if each step has a cost and you want the minimum cost to reach the top?** That's Min Cost Climbing Stairs — same structure, but replace "add" with "min of + cost".
- **What if some steps are broken and can't be used?** Set `f(broken) = 0`; the recurrence handles the rest.
- **What if you can take up to `k` steps?** `f(n) = f(n-1) + f(n-2) + ... + f(n-k)`, which is a sliding-window sum — O(n) with a running total.
- **n up to 10^18?** Matrix exponentiation of the Fibonacci transition `[[1,1],[1,0]]` in O(log n).
