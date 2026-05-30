# Evaluate Reverse Polish Notation

**Problem Link:**
<a href="https://leetcode.com/problems/evaluate-reverse-polish-notation/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/evaluate-reverse-polish-notation/</a>

**Topic:**
Stack

----------------------------------------

## Step 1: What Is RPN?

Reverse Polish Notation is a way of writing arithmetic without any parentheses. Instead of `3 + 4`, you write `3 4 +`. Instead of `(3 + 4) * 5`, you write `3 4 + 5 *`.

The rule: operators appear **after** their operands. When you see an operator, it applies to the **two most recent** numbers.

Given a list of RPN tokens (like `["2", "1", "+", "3", "*"]`), compute the result.

`["2", "1", "+", "3", "*"]` reads as: compute `2 + 1 = 3`, then multiply by 3 → `9`.

----------------------------------------

## Step 2: Let Me Simulate By Hand

Take a slightly bigger example: `["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]`.

Standard math translation: `(10 * ((6 + (9 + 3)) / (-11))) + 17 + 5`. But let's not peek ahead — the whole point of RPN is to go left-to-right.

Reading left-to-right, what should happen at each token?

- `"10"` — a number. Remember it.
- `"6"` — another number. Remember it.
- `"9"` — remember.
- `"3"` — remember.
- `"+"` — combine the two most recent numbers: 9 and 3. Result 12. Forget the two, remember 12.
- `"-11"` — remember.
- `"*"` — combine the two most recent: 12 and -11. Result: -132. Remember that.
- `"/"` — combine the two most recent: 6 and -132. Result: 6 / -132 = 0 (integer division rounds toward zero).

Wait, let me be careful about operand order. When we see `"/"`, the two most recent are stored in the order they were added. For `a b /`, the meaning is `a / b` (the first-added is the dividend, the second the divisor). So here the first-added is 6, second is -132 — we compute `6 / -132`.

Hmm actually wait. Let me re-check which came first. We remembered 6 first, then later 12, then -132. So when `"/"` fires, the two most recent are -132 (last in) and 12 is no longer there... Let me re-trace more carefully.

OK this is getting complicated by hand. Let me formalize the rule.

----------------------------------------

## Step 3: The Rule Is Exactly Like a Stack

Numbers go onto a pile (last-in on top). When an operator arrives, it consumes the **top two numbers**, performs the operation, and pushes the result back.

Operand order: when you see `a b <op>`, the first-pushed is `a`, second-pushed is `b`. When we pop, we get `b` first (since it's on top), then `a`. So the computation is `a <op> b`, not `b <op> a`.

In code:
```
b = stack.pop()
a = stack.pop()
result = a OP b
stack.push(result)
```

That's critical. The order matters for non-commutative operators like `-` and `/`.

----------------------------------------

## Step 4: Retrace More Carefully

`["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]`

```
"10"   stack: [10]
"6"    stack: [10, 6]
"9"    stack: [10, 6, 9]
"3"    stack: [10, 6, 9, 3]
"+"    b=3, a=9, 9+3=12.  stack: [10, 6, 12]
"-11"  stack: [10, 6, 12, -11]
"*"    b=-11, a=12, 12*(-11)=-132. stack: [10, 6, -132]
"/"    b=-132, a=6, 6/(-132)=0 (integer div toward zero). stack: [10, 0]
"*"    b=0, a=10, 10*0=0. stack: [0]
"17"   stack: [0, 17]
"+"    b=17, a=0, 0+17=17. stack: [17]
"5"    stack: [17, 5]
"+"    b=5, a=17, 17+5=22. stack: [22]
```

Answer: **22**.

Notice how the stack shrinks each time an operator fires, and grows each time a number arrives. At the very end, there should be exactly one value on the stack — the answer. If there's more than one, the input was malformed.

----------------------------------------

## Step 5: Why the Stack Is Natural

Think about how RPN matches evaluation order. Operators apply to the most recent two operands. "Most recent" is LIFO — the defining property of a stack. So the stack isn't a clever choice; it's the *definition* of how RPN works. No other structure would be simpler.

Put another way: RPN is unambiguous *because* of this mechanic. There's never any question about "which operands does this operator apply to" — it's always the last two on the stack.

----------------------------------------

## Step 6: Translating to Code

```cpp
int evalRPN(vector<string>& tokens) {
    stack<long long> st;
    for (auto& t : tokens) {
        if (t == "+" || t == "-" || t == "*" || t == "/") {
            long long b = st.top(); st.pop();
            long long a = st.top(); st.pop();
            long long r;
            if (t == "+") r = a + b;
            else if (t == "-") r = a - b;
            else if (t == "*") r = a * b;
            else                r = a / b;    // integer division
            st.push(r);
        } else {
            st.push(stoll(t));
        }
    }
    return (int)st.top();
}
```

A few implementation choices:
- `long long` to avoid overflow on intermediate multiplications. If the problem constraints say all values fit in 32 bits, you can downgrade.
- `stoll` converts string to `long long`. It handles negative numbers like `"-11"` correctly (unlike just parsing digits naively).
- I use a chain of `if/else if` for the four operators. You could use a `switch` or a lookup map; doesn't matter at this scale.

----------------------------------------

## Step 7: Edge Cases

- **Single number input** like `["42"]`. No operator fires; stack ends with just `42`. Return 42. ✓
- **Negative operands.** `"-11"` is a valid number token. `stoll` handles it.
- **Division rounding.** C++ `/` on integers rounds toward zero, which matches the problem spec. (Be aware: Python's `//` rounds toward negative infinity — different semantics.)
- **Division by zero.** Not specified in the problem; typically inputs are guaranteed valid. Add a guard if in doubt.

----------------------------------------

## Step 8: Complexity

Time: we visit each token exactly once; each stack op is O(1). **O(n)** where n is the number of tokens.
Space: the stack holds at most the number of numbers seen before the next operator — at most O(n) in pathological inputs like `[1, 1, 1, +, +]` vs. short on well-balanced RPNs. Worst case **O(n)**.

----------------------------------------

## Step 9: Follow-up Questions

- **Parse and evaluate an infix expression (standard math notation).** Two-stack approach (values + operators) with operator precedence, or convert to RPN first via the shunting-yard algorithm.
- **Support more operators (exponent, modulo, unary minus).** Add cases. Unary minus is tricky in RPN — usually handled by requiring the token to be a signed number.
- **Mixed int/float arithmetic.** Store a variant or use doubles throughout.
- **Evaluate an RPN stream (tokens arrive over time).** Same algorithm — works incrementally.
- **Generate RPN from an infix expression.** Shunting-yard. Output has exactly the token order our stack evaluator expects.
