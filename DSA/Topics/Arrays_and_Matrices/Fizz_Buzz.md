# Fizz Buzz

**Problem Link:**
https://leetcode.com/problems/fizz-buzz/

**Topic:**
Arrays & Matrices

----------------------------------------

## Step 1: The Rules

For each integer from 1 to n:
- If divisible by **both 3 and 5**: output `"FizzBuzz"`.
- Else if divisible by **3**: output `"Fizz"`.
- Else if divisible by **5**: output `"Buzz"`.
- Else: output the number as a string.

Return the list.

Example: n = 5.
- 1: "1"
- 2: "2"
- 3: "Fizz"
- 4: "4"
- 5: "Buzz"

Output: `["1", "2", "Fizz", "4", "Buzz"]`.

----------------------------------------

## Step 2: Direct Check in Order

The rules have a priority: check 15 (3 AND 5) first, then 3, then 5, else number.

Divisible by both 3 and 5 ⇔ divisible by 15. We check that case first.

```
for i in 1..n:
    if i % 15 == 0:
        append "FizzBuzz"
    elif i % 3 == 0:
        append "Fizz"
    elif i % 5 == 0:
        append "Buzz"
    else:
        append str(i)
```

Order matters: if we checked `% 3 == 0` first, we'd label 15 as "Fizz" — wrong.

Alternative: check `i % 3 == 0 and i % 5 == 0` instead of `i % 15 == 0`. Equivalent.

----------------------------------------

## Step 3: Alternative — Concatenate

A more "programming-style" version avoids nested if-else:

```
for i in 1..n:
    s = ""
    if i % 3 == 0: s += "Fizz"
    if i % 5 == 0: s += "Buzz"
    if s == "": s = str(i)
    append s
```

Build the string incrementally. If neither condition hits, default to the number string. This handles 15 naturally: both conditions fire, giving "FizzBuzz".

This version extends cleanly to more rules (e.g., also print "Fuzz" for multiples of 7).

----------------------------------------

## Step 4: Trace for n = 15

```
1: not div 3 or 5. "1".
2: "2".
3: div 3. "Fizz".
4: "4".
5: div 5. "Buzz".
6: div 3. "Fizz".
7: "7".
8: "8".
9: div 3. "Fizz".
10: div 5. "Buzz".
11: "11".
12: div 3. "Fizz".
13: "13".
14: "14".
15: div 15. "FizzBuzz".
```

Correct.

----------------------------------------

## Step 5: Why It's a Classic Interview Warm-Up

Fizz Buzz is legendary as a simple interview filter. It tests:
- Basic loop and modular arithmetic.
- Correct conditional order.
- String manipulation.

It's been the subject of memes ("if you can't solve FizzBuzz, you can't code"), but truthfully, clean implementations show attention to detail.

----------------------------------------

## Step 6: Complexity

Time: **O(n)** — one iteration per number.
Space: **O(n)** for the result list.

----------------------------------------

## Step 7: C++ Implementation

**Straightforward if-else:**

```cpp
vector<string> fizzBuzz(int n) {
    vector<string> result;
    result.reserve(n);
    for (int i = 1; i <= n; ++i) {
        if (i % 15 == 0) result.push_back("FizzBuzz");
        else if (i % 3 == 0) result.push_back("Fizz");
        else if (i % 5 == 0) result.push_back("Buzz");
        else result.push_back(to_string(i));
    }
    return result;
}
```

Direct and readable.

**Concatenation style:**

```cpp
vector<string> fizzBuzz(int n) {
    vector<string> result;
    result.reserve(n);
    for (int i = 1; i <= n; ++i) {
        string s;
        if (i % 3 == 0) s += "Fizz";
        if (i % 5 == 0) s += "Buzz";
        if (s.empty()) s = to_string(i);
        result.push_back(s);
    }
    return result;
}
```

Either works. The concat version is more extensible; the if-else is more immediate.

----------------------------------------

## Step 8: Follow-up Questions

- **Custom rules: "Fuzz" for 7, "Bizz" for 11.** Concat-style extends naturally.
- **Cumulative version (just append concatenated strings).** Adjust accordingly.
- **Multi-threaded FizzBuzz.** A classic concurrency exercise — 4 threads coordinating output.
- **FizzBuzz via lookup / pattern.** The pattern of outputs repeats every 15. Precompute one period, replicate.
- **Avoid modulo entirely.** Use counters that reset to 0 at 3 and 5 cycles. Micro-optimization, not usually useful.
- **Generalize to any two divisors m and k.** Straightforward parameterization.
