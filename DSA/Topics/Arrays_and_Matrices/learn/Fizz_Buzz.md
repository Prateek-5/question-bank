# Fizz Buzz — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Fizz_Buzz.md`](../Fizz_Buzz.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/fizz-buzz/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/fizz-buzz/</a>

---

## How to use this file

Paced for someone seeing the problem for the first time. Reading time: ~8 minutes. There is no algorithmic trick here — it's pure rule-checking — but the problem teaches three things you'll need forever: **the `%` (modulo) operator**, **the relationship "divisible by 3 AND 5 = divisible by 15"**, and **the discipline of checking the most-specific rule FIRST**.

**Map of this file (9 short sections):**

1. Read the problem
2. What "divisible" means + the modulo operator
3. The naive trap: rule order matters
4. The if-else-cascade approach
5. Trace it
6. An alternative: the build-the-string approach
7. Code
8. Common pitfalls
9. The shape — where "specific-first" rules apply later

---

## 1. Read the problem

For each integer from `1` to `n`, build a string according to these rules:

- If the number is **divisible by both 3 and 5**, the string is `"FizzBuzz"`.
- Else if **divisible by 3**, the string is `"Fizz"`.
- Else if **divisible by 5**, the string is `"Buzz"`.
- Else, the string is the number itself (as a string).

Return all `n` strings in order, as an array.

Example for `n = 5`:

```
i = 1:  not divisible by 3 or 5     →  "1"
i = 2:  not divisible by 3 or 5     →  "2"
i = 3:  divisible by 3              →  "Fizz"
i = 4:  not divisible by 3 or 5     →  "4"
i = 5:  divisible by 5              →  "Buzz"
```

Output: `["1", "2", "Fizz", "4", "Buzz"]`.

---

## 2. What "divisible" means + the modulo operator

> **Mini-refresher: divisibility and the `%` operator.**
>
> A whole number `a` is **divisible by** `b` (where `b ≠ 0`) if dividing `a` by `b` leaves no remainder. Equivalently: `b` evenly fits into `a` some whole number of times.
>
> Examples: 15 is divisible by 3 (because `15 ÷ 3 = 5` exactly). 16 is not (because `16 ÷ 3 = 5` remainder `1`).
>
> Most programming languages have a **modulo** (remainder) operator `%`:
>
> ```
> 15 % 3 = 0     ← 15 is divisible by 3
> 16 % 3 = 1     ← 16 is NOT divisible by 3 (remainder 1)
> 10 % 5 = 0     ← 10 is divisible by 5
> 10 % 3 = 1     ← 10 is NOT divisible by 3 (remainder 1)
> 15 % 5 = 0     ← 15 is divisible by 5
> ```
>
> So **"`a` is divisible by `b`"** is checked in code as **`a % b == 0`**.

That's the only operator we need for this problem.

---

## 3. The naive trap: rule order matters

Imagine you write the rules in this order, top-to-bottom:

```
if i % 3 == 0:          output "Fizz"
else if i % 5 == 0:     output "Buzz"
else if i % 3 == 0 and i % 5 == 0:  output "FizzBuzz"
else:                   output the number
```

What happens at `i = 15`?

- `15 % 3 == 0` is true → output `"Fizz"`.
- We never reach the "FizzBuzz" branch.

**Wrong.** The rule "divisible by both 3 AND 5" can never fire because every number divisible by both is also divisible by 3, which catches it first.

**The fix:** check the **most-specific** rule FIRST. "Divisible by both 3 and 5" is more specific than "divisible by 3 alone," so it must come earlier in the if-else cascade:

```
if i % 3 == 0 and i % 5 == 0:    output "FizzBuzz"
else if i % 3 == 0:              output "Fizz"
else if i % 5 == 0:              output "Buzz"
else:                            output the number
```

Now `i = 15` hits the first branch and produces `"FizzBuzz"` as intended.

> **Mini-refresher: "divisible by both 3 and 5" = "divisible by 15."**
>
> A number is divisible by 3 means 3 fits in it exactly. Divisible by 5 means 5 fits in it exactly. Divisible by **both** means both 3 and 5 fit in it — i.e., 15 (which equals 3 × 5) fits in it.
>
> So the two conditions are equivalent:
> ```
> i % 3 == 0 AND i % 5 == 0     ⇔     i % 15 == 0
> ```
>
> Either form works. `i % 15 == 0` is one slightly faster check; the longer form is more transparent.

---

## 4. The if-else-cascade approach

The straightforward implementation:

```
result = empty array
for i in 1..n:
    if i % 15 == 0:
        result.append("FizzBuzz")
    else if i % 3 == 0:
        result.append("Fizz")
    else if i % 5 == 0:
        result.append("Buzz")
    else:
        result.append(string(i))
return result
```

Each iteration falls through the cascade until one rule matches. By placing the most-specific rule first, we guarantee correctness.

---

## 5. Trace it

For `n = 15`, let me run through every iteration:

```
i=1:   1 % 15 ≠ 0.  1 % 3 ≠ 0.  1 % 5 ≠ 0.  →  "1"
i=2:                                          →  "2"
i=3:   3 % 15 ≠ 0.  3 % 3 == 0.               →  "Fizz"
i=4:                                          →  "4"
i=5:   5 % 15 ≠ 0.  5 % 3 ≠ 0.  5 % 5 == 0.   →  "Buzz"
i=6:   6 % 15 ≠ 0.  6 % 3 == 0.               →  "Fizz"
i=7:                                          →  "7"
i=8:                                          →  "8"
i=9:   9 % 3 == 0.                            →  "Fizz"
i=10:  10 % 5 == 0.                           →  "Buzz"
i=11:                                         →  "11"
i=12:  12 % 3 == 0.                           →  "Fizz"
i=13:                                         →  "13"
i=14:                                         →  "14"
i=15:  15 % 15 == 0.                          →  "FizzBuzz"
```

Output: `["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz", "11", "Fizz", "13", "14", "FizzBuzz"]`. ✓

Notice `i = 15` correctly produced `"FizzBuzz"` because it hit the first branch — the most-specific one.

---

## 6. An alternative: the build-the-string approach

Some engineers prefer this style:

```
for i in 1..n:
    s = ""
    if i % 3 == 0: s += "Fizz"
    if i % 5 == 0: s += "Buzz"
    if s == "":    s = string(i)
    result.append(s)
```

Walk through `i = 15`:

- Start `s = ""`.
- `15 % 3 == 0` → `s = "Fizz"`.
- `15 % 5 == 0` → `s = "Fizz" + "Buzz" = "FizzBuzz"`.
- `s != ""`, so no number fallback.
- Append `"FizzBuzz"`. ✓

And `i = 4`:

- `s = ""`.
- `4 % 3 ≠ 0`. No append.
- `4 % 5 ≠ 0`. No append.
- `s == ""` → set `s = "4"`.
- Append `"4"`. ✓

This style is appealing because **it extends gracefully if more rules are added later** — e.g., a "Bizz for 7" rule just becomes one more `if i % 7 == 0: s += "Bizz"` line. The if-else cascade would need its branches restructured.

For the standard problem statement, both styles are equally correct. Pick whichever feels clearer.

---

## 7. Code

C++ — if-else cascade:

```cpp
vector<string> fizzBuzz(int n) {
    vector<string> result;
    result.reserve(n);                            // pre-allocate for speed
    for (int i = 1; i <= n; i++) {
        if (i % 15 == 0)         result.push_back("FizzBuzz");
        else if (i % 3 == 0)     result.push_back("Fizz");
        else if (i % 5 == 0)     result.push_back("Buzz");
        else                     result.push_back(to_string(i));
    }
    return result;
}
```

C++ — concat style:

```cpp
vector<string> fizzBuzz(int n) {
    vector<string> result;
    result.reserve(n);
    for (int i = 1; i <= n; i++) {
        string s;
        if (i % 3 == 0) s += "Fizz";
        if (i % 5 == 0) s += "Buzz";
        if (s.empty()) s = to_string(i);
        result.push_back(s);
    }
    return result;
}
```

Python — concat style:

```python
def fizzBuzz(n):
    result = []
    for i in range(1, n + 1):
        s = ""
        if i % 3 == 0: s += "Fizz"
        if i % 5 == 0: s += "Buzz"
        if not s:      s = str(i)
        result.append(s)
    return result
```

---

## 8. Common pitfalls

1. **Putting the most-specific rule LAST.** Already covered in section 3. `i = 15` produces `"Fizz"` instead of `"FizzBuzz"`. Always check `i % 15 == 0` (or `i % 3 == 0 AND i % 5 == 0`) FIRST.

2. **Off-by-one on the loop.** The problem says 1 to n **inclusive**. That's `for i in 1..n` (or `for (i = 1; i <= n; i++)`). Common error: starting at 0 or stopping at `n - 1`. Re-read the spec.

3. **Returning numbers, not strings.** The output is an array of strings. Forgetting `to_string(i)` (or `str(i)`) for the non-FizzBuzz cases is a type error in strongly-typed languages.

4. **Performance worry (none here).** Some candidates over-think this and try to "avoid `%` for speed." That's micro-optimization for a problem the judge will run in milliseconds. Don't bother.

5. **Not pre-allocating the result vector.** In C++, calling `result.reserve(n)` before pushing into a vector avoids repeated reallocations. Tiny gain on this problem, but a good habit for hotter loops later.

---

## 9. The shape — where "specific-first" rules apply later

The lesson from this problem isn't `%`. It's **rule order matters when rules overlap**. Many later problems hide a similar trap:

| Where you'll see "specific-first" again | What overlaps |
|---|---|
| **This problem** (FizzBuzz) | "divisible by 3 AND 5" overlaps "divisible by 3" |
| Parsing tokens (lexer, JSON, regex) | Keywords like `"if"` overlap identifier rule `"[a-z]+"` — check keywords first |
| Routing rules in web frameworks | More-specific URL patterns must come before catch-all `/*` |
| Switch-case fall-through | Specific case before `default` |
| Exception handlers | More-specific exception class before parent class (`FileNotFoundError` before `IOError`) |
| Code-style linter rules | Stricter rule must override looser rule if both match |

Pattern to internalize: **when checking which of several rules a thing matches, list rules from most-specific to most-general.** The general rule is the safety net that catches whatever the specific rules didn't.

---

> **Self-check — the question to ask next time.**
>
> When you face a problem of the form **"check each item against multiple rules and produce an output based on which rule(s) it matches,"** before writing the if-else cascade, ask:
>
> > **"If two rules can match the same input, which is more specific? Is it listed FIRST?"**
>
> If you can't immediately answer that, you have an ordering bug waiting to happen.

---

## Cross-references

- **Reference card (post-mastery):** [`../Fizz_Buzz.md`](../Fizz_Buzz.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:** [`Concatenation_of_Array.md`](./Concatenation_of_Array.md) (other trivial warm-up)
