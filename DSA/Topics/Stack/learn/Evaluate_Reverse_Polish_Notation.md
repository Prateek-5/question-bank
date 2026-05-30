# Evaluate Reverse Polish Notation — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Evaluate_Reverse_Polish_Notation.md`](../Evaluate_Reverse_Polish_Notation.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/evaluate-reverse-polish-notation/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/evaluate-reverse-polish-notation/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. The lesson: **postfix (RPN) notation EXISTS because of the stack**. The data structure isn't just convenient — RPN was DESIGNED so a stack evaluates it. Once you understand WHY operands sit on the stack and operators consume the top two, you've understood compiler theory's most-used data structure. **Read [`Baseball_Game.md`](./Baseball_Game.md) first** — same stack-as-simulation idea, just with arithmetic.

**Map of this file (10 short sections):**

1. Read the problem
2. What is Reverse Polish Notation, exactly?
3. Why does RPN exist?
4. Simulate by hand
5. The algorithm
6. Operand order — the non-commutative trap
7. Code
8. Trace a longer example
9. Common pitfalls
10. The shape — RPN, infix, and the shunting yard

---

## 1. Read the problem

You're given an array `tokens` of strings, where each token is either:

- An integer (possibly negative): e.g., `"3"`, `"-11"`.
- An operator: one of `"+"`, `"-"`, `"*"`, `"/"`.

The tokens form a valid **Reverse Polish Notation (RPN)** expression. Evaluate it.

Integer division **truncates toward zero** (so `6 / -4 = -1`, not `-2`). The problem guarantees the expression is well-formed and intermediate results fit in a signed 32-bit integer.

**Example:** `tokens = ["2", "1", "+", "3", "*"]` → evaluate `(2 + 1) * 3 = 9`.

---

## 2. What is Reverse Polish Notation, exactly?

In standard ("infix") notation: `3 + 4`. The operator sits BETWEEN its operands.

In RPN ("postfix"): `3 4 +`. The operator comes AFTER its operands.

| Infix | RPN |
|---|---|
| `3 + 4` | `3 4 +` |
| `(3 + 4) * 5` | `3 4 + 5 *` |
| `3 * (4 + 5)` | `3 4 5 + *` |
| `(1 + 2) * (3 + 4)` | `1 2 + 3 4 + *` |

> **Mini-refresher: how to read RPN.**
>
> Read left to right. Push numbers as you see them. When you see an operator, it operates on the MOST RECENT TWO NUMBERS, replacing them with the result.
>
> `3 4 +`: push 3, push 4, see `+` → pop 4, pop 3, compute 3+4=7, push 7. Result: 7.
>
> `1 2 + 3 4 + *`: 
> - Push 1, 2. See `+` → push 3 (= 1+2).
> - Push 3, 4. See `+` → push 7.
> - See `*` → push 21 (= 3*7).
>
> Result: 21.

Notice the rule is exactly **stack semantics**. The operator always consumes the TOP TWO operands and pushes back the result.

---

## 3. Why does RPN exist?

Infix is great for humans but **needs parentheses** to disambiguate, plus rules of precedence (× before +). A compiler or calculator must do real work to parse infix: track operator precedence, handle parens, etc.

RPN has **no parentheses** and **no precedence rules**. Reading order = evaluation order. This is why early calculators (HP RPN models) and the JVM, .NET CLR, and PostScript all use a stack-based execution model rooted in RPN.

> **Mini-refresher: postfix is "operator after operands."**
>
> | Form | Example | Notes |
> |---|---|---|
> | Infix | `3 + 4` | operator between; needs precedence + parens |
> | Prefix (Polish) | `+ 3 4` | operator before; readable with a stack from the right |
> | Postfix (RPN) | `3 4 +` | operator after; readable with a stack from the left |
>
> Postfix is what you GET when you convert infix using the **shunting-yard algorithm** (covered briefly at the end). It's also what you'd manually write to express a calculation as a sequence of stack instructions.

---

## 4. Simulate by hand

`tokens = ["2", "1", "+", "3", "*"]`:

```
stack = [].

"2": push 2.         stack = [2].
"1": push 1.         stack = [2, 1].
"+": pop 1, pop 2, push 1+2=3.  stack = [3].
"3": push 3.         stack = [3, 3].
"*": pop 3, pop 3, push 3*3=9.  stack = [9].

End. Top = 9. Return 9.
```

Always ends with exactly ONE number on the stack — the final answer.

---

## 5. The algorithm

```
stack = []
for tok in tokens:
    if tok is an operator (+, -, *, /):
        b = stack.pop()                # second pushed (top of stack)
        a = stack.pop()                # first pushed
        stack.push(apply(a, op, b))    # NOTE: a op b, not b op a
    else:
        stack.push(parseInt(tok))
return stack.top()
```

The single most error-prone line: **which popped value is the left operand?** See section 6.

---

## 6. Operand order — the non-commutative trap

For `+` and `*`, order doesn't matter (commutative). For `-` and `/`, it MATTERS.

When you see `a b -` in RPN, the meaning is `a - b` (NOT `b - a`).

What's on the stack? `a` was pushed FIRST, then `b`. So when you pop, you get `b` (the top), then `a`.

```
b = stack.pop()        ← top, the most recent
a = stack.pop()        ← second-from-top, the older one
result = a - b         ← left operand first; subtract the more-recent from the older
```

**Common bug:** `a = pop(); b = pop(); result = a - b;` — this gives `b - a`, the WRONG answer.

> **Mini-refresher: stack LIFO order on pop.**
>
> If you pushed in order [a, b, c], then `pop()` returns c, next `pop()` returns b, next `pop()` returns a — the REVERSE of the push order.
>
> So to recover ORIGINAL ORDER of "a, b", pop twice and ASSIGN to "b, a" — same as reading right-to-left.

The same trap applies to `/`: `a b /` means `a / b`, not `b / a`.

---

## 7. Code

**C++:**

```cpp
int evalRPN(vector<string>& tokens) {
    stack<long long> st;
    for (const string& t : tokens) {
        if (t == "+" || t == "-" || t == "*" || t == "/") {
            long long b = st.top(); st.pop();           // top first
            long long a = st.top(); st.pop();           // then the lower one
            long long r;
            if (t == "+") r = a + b;
            else if (t == "-") r = a - b;
            else if (t == "*") r = a * b;
            else                r = a / b;              // truncates toward 0 in C++
            st.push(r);
        } else {
            st.push(stoll(t));                          // handles negative numbers like "-11"
        }
    }
    return (int)st.top();
}
```

Notes:
- `long long` for safety with multiplication. `(2³¹ - 1) * something` could overflow `int`.
- `stoll(t)` parses `"-11"` correctly. Don't roll your own digit parser.
- C++ `/` on integers truncates toward zero — matches the problem spec. Python's `//` rounds toward negative infinity (different!), so in Python use `int(a / b)` instead of `a // b`.

**Python:**

```python
def evalRPN(tokens):
    stack = []
    for t in tokens:
        if t in ("+", "-", "*", "/"):
            b = stack.pop()
            a = stack.pop()
            if t == "+": stack.append(a + b)
            elif t == "-": stack.append(a - b)
            elif t == "*": stack.append(a * b)
            else: stack.append(int(a / b))             # NOT a // b — needs trunc-toward-zero
        else:
            stack.append(int(t))
    return stack[-1]
```

> **Mini-refresher: Python integer division.**
>
> `7 // -2` in Python is **-4** (floor: rounds toward -∞).
> `int(7 / -2)` is **-3** (truncation toward 0).
>
> LeetCode wants truncation toward 0, matching C / C++ / Java. Use `int(a / b)`.

**JavaScript:**

```javascript
function evalRPN(tokens) {
    const stack = [];
    for (const t of tokens) {
        if (t === "+" || t === "-" || t === "*" || t === "/") {
            const b = stack.pop();
            const a = stack.pop();
            if (t === "+") stack.push(a + b);
            else if (t === "-") stack.push(a - b);
            else if (t === "*") stack.push(a * b);
            else stack.push(Math.trunc(a / b));        // truncation toward zero
        } else {
            stack.push(parseInt(t, 10));
        }
    }
    return stack[stack.length - 1];
}
```

`Math.trunc` because JS `/` is float division; truncation matches the spec.

---

## 8. Trace a longer example

`tokens = ["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]`:

```
"10":   stack = [10].
"6":    stack = [10, 6].
"9":    stack = [10, 6, 9].
"3":    stack = [10, 6, 9, 3].
"+":    b=3, a=9 → 9+3=12.    stack = [10, 6, 12].
"-11":  stack = [10, 6, 12, -11].
"*":    b=-11, a=12 → 12*(-11)=-132.  stack = [10, 6, -132].
"/":    b=-132, a=6 → 6/-132 = 0 (truncated toward 0).  stack = [10, 0].
"*":    b=0, a=10 → 10*0=0.   stack = [0].
"17":   stack = [0, 17].
"+":    b=17, a=0 → 17.       stack = [17].
"5":    stack = [17, 5].
"+":    b=5, a=17 → 22.       stack = [22].

Return 22.
```

The stack expands as numbers arrive, shrinks as operators consume two and push one. Net effect of each operator: stack shrinks by 1. At the end: exactly one number, the answer.

Sanity: the equivalent infix is `((10 * ((6 + (9 + 3)) / -11)) + 17) + 5` — but you don't need to reconstruct it. The RPN evaluation just works.

---

## 9. Common pitfalls

1. **Wrong operand order for `-` and `/`.** This is THE bug. Pop into `b` first, then into `a`. Compute `a - b`, not `b - a`. (Section 6.)

2. **Using `//` in Python for division.** Floor division rounds toward -∞, but the problem wants truncation toward 0. Use `int(a / b)` instead.

3. **Using `int` in C++ where intermediate values might overflow.** A product of two values near `INT_MAX / 2` overflows. Use `long long`. (Or check the constraints — the problem may guarantee `int` suffices, in which case it's a non-issue.)

4. **Naïve digit parsing that mishandles `"-11"`.** Use the language's int-parse function. `stoi`, `int()`, `parseInt(...,10)`.

5. **Forgetting to push the OPERATOR RESULT.** Some candidates pop the two operands, compute, and then... return early or discard. The result must go BACK on the stack so subsequent operators can use it.

6. **Checking integer-ness FIRST in the branch order.** Same trap as Baseball_Game — try `stoi("+")` and you crash. Check the four operator literals first.

7. **Assuming infix-style precedence.** RPN HAS NO PRECEDENCE. The order in the token list IS the order of evaluation. Don't sort, don't reorder.

8. **Returning the wrong thing at the end.** Return `stack.top()`, not `stack` or `stack.size()`.

9. **Treating "/" as float division.** In C++ and most languages with int division, that's what `/` already does. In JS, `/` is float division — you must explicitly truncate.

---

## 10. The shape — RPN, infix, and the shunting yard

The pattern this problem teaches generalizes in two big directions:

**Direction 1: stack-based evaluation in general.**

The same stack works for ANY postfix expression — boolean operations, set operations, vector operations. Whenever you encode an expression as "operands, then their combiner," a stack evaluates it.

| Problem | Token meaning |
|---|---|
| **This problem** | int + arith op |
| RPN with floats | float + arith op |
| Boolean RPN | bool + AND/OR/NOT |
| Stack-VM bytecode (JVM, .NET) | each instruction reads or writes the operand stack |
| PostScript / Forth | the language is RPN at the source level |
| Database query plans (executed bottom-up) | each plan node consumes its children's outputs from a stack |

**Direction 2: converting infix to postfix — the shunting yard.**

If a problem gives you INFIX (e.g., `(2 + 3) * 5`) and asks you to evaluate, you have two paths:

1. **Direct two-stack evaluation:** one stack for values, one for operators with precedence.
2. **Convert to RPN first, then evaluate as we did.**

Edsger Dijkstra's **shunting-yard algorithm** is the standard infix-to-postfix converter, also stack-based. (Out of scope for this problem, but mentioned for completeness.)

**Pattern to internalize:**

> "RPN evaluates with a stack because each operator consumes the most-recent few operands, and stacks give O(1) access to 'most recent.' This is what postfix was designed for."

When you spot postfix in any problem (boolean DAG topological order, expression rendering, calculator), reach for the stack.

---

> **Self-check — the question to ask next time.**
>
> When you face expression evaluation where operators come AFTER their operands (or could be transformed into that form), ask:
>
> > **"Can I push operands onto a stack, and let each operator pop and combine the top two? Then I get O(n) evaluation with no parens, no precedence parsing."**
>
> If yes, the postfix-evaluation pattern handles it.

---

## Cross-references

- **Reference card (post-mastery):** [`../Evaluate_Reverse_Polish_Notation.md`](../Evaluate_Reverse_Polish_Notation.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Valid_Parentheses.md`](./Valid_Parentheses.md), [`Baseball_Game.md`](./Baseball_Game.md) — earlier stack problems.
  - [`Min_Stack.md`](./Min_Stack.md) — stack with extra metadata.
  - Coming next: Expression_Contains_Redundant_Bracket_or_Not — uses stack to detect redundant parens in infix.
  - Coming later: monotonic-stack family (Daily_Temperatures, Next_Greater_Element_I, Largest_Rectangle_in_Histogram).
