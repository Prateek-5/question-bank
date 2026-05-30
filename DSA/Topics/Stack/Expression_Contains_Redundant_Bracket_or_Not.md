# Expression Contains Redundant Bracket or Not

**Problem Link:**
<a href="https://www.geeksforgeeks.org/expression-contains-redundant-bracket-not/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/expression-contains-redundant-bracket-not/</a>

**Topic:**
Stack

----------------------------------------

## Step 1: What Counts as Redundant?

An expression like `((a+b))` has a redundant outer pair of parentheses — removing them doesn't change the value. Same for `(a+b+(c))` — the inner `(c)` is redundant because `c` is already a single value.

Define: a pair of parentheses is **redundant** if there's **no operator** between them that requires grouping.

Examples of redundant:
- `((a+b))` — outer pair redundant.
- `(a)` — no operator inside.
- `(a+(b)+c)` — inner `(b)` redundant.

Examples of NOT redundant:
- `(a+b)*c` — parens group `a+b` against `*`; necessary.
- `a+(b*c)` — actually, this IS redundant because `*` has higher precedence than `+`, so the parens don't change meaning. But most problems don't analyze precedence; they consider any parens with an operator inside as non-redundant.

This problem: return true if the expression contains **any** redundant parens. Operators: `+ - * /`.

----------------------------------------

## Step 2: Characterize With a Stack

Intuition: when we hit a `)`, check what's inside since the matching `(`. If there's **no operator** between them, the parens are redundant.

Algorithm:
- Iterate the expression character by character.
- Push everything onto a stack.
- When we hit `)`, pop until we hit `(`. If we didn't pop any operator, these parens are redundant — return true.

----------------------------------------

## Step 3: Pseudocode

```
stack = empty

for ch in expression:
    if ch == ')':
        hasOperator = false
        while stack.top() != '(':
            top = stack.pop()
            if top is an operator (+, -, *, /):
                hasOperator = true
        stack.pop()   # pop the '('
        if not hasOperator: return true
    else:
        stack.push(ch)

return false
```

Each character pushed and popped once → O(n) time.

----------------------------------------

## Step 4: Trace on `((a+b))`

```
stack = [].

Push '(' → [(].
Push '(' → [(, (].
Push 'a' → [(, (, a].
Push '+' → [(, (, a, +].
Push 'b' → [(, (, a, +, b].

Encounter ')'. Pop until '(':
  Pop 'b'. Not operator.
  Pop '+'. Operator! hasOperator = true.
  Pop 'a'. Not operator.
  Next is '('. Stop inner loop. Pop '('.
hasOperator = true. Not redundant. Continue.

stack = [(].

Encounter ')'. Pop until '(':
  Pop '('. Wait, top is now '('. Inner loop doesn't execute.
  Pop the outer '('.
hasOperator = false. Redundant! Return true.
```

Correct: the outer `((a+b))` has redundant parens.

For `(a+b)` (no redundancy):
```
Push (, a, +, b.
Encounter ')'. Pop b, +, a, (. Found +. hasOperator = true. Not redundant.
End.
Return false.
```

✓

For `(a+(b))`:
```
Push (, a, +, (.
Push b.
Encounter ')'. Pop b, (. No operator. Redundant. Return true.
```

✓ Inner `(b)` is redundant.

----------------------------------------

## Step 5: Why the Stack Finds Redundancy Correctly

The stack holds the "prefix" of the expression not yet matched by a closing parenthesis. When a `)` arrives, everything between the current position and the most recent unmatched `(` is the content of the closing parenthesis group.

If that content has no operator, the group is a single expression (variable or nested group) wrapped in parens — redundant.

If it has an operator, the parens are performing meaningful grouping.

----------------------------------------

## Step 6: Name It

**Stack-based expression analysis.** Same pattern as Valid Parentheses, but with a semantic check instead of just balance.

Related:
- Expression evaluation (evaluate a fully parenthesized expression using two stacks).
- Simplify expression.
- Remove minimum parentheses to make valid.
- Shunting-yard for infix-to-postfix.

Whenever expression syntax needs nested analysis, a stack fits.

----------------------------------------

## Step 7: Complexity

Time: **O(n)**. Each character pushed and popped at most once.
Space: **O(n)** for the stack.

----------------------------------------

## Step 8: C++ Implementation

```cpp
bool hasRedundantBrackets(const string& expr) {
    stack<char> stk;

    for (char ch : expr) {
        if (ch == ')') {
            bool hasOp = false;
            while (!stk.empty() && stk.top() != '(') {
                char top = stk.top(); stk.pop();
                if (top == '+' || top == '-' || top == '*' || top == '/') {
                    hasOp = true;
                }
            }
            if (!stk.empty()) stk.pop();   // pop the '('
            if (!hasOp) return true;
        } else {
            stk.push(ch);
        }
    }

    return false;
}
```

10 lines. Two key observations:
- Track whether we popped any operator between `(` and `)`.
- If no operator was popped, those parens are redundant.

----------------------------------------

## Step 9: Follow-up Questions

- **Consider operator precedence to mark `a+(b*c)` as redundant.** Harder — needs a parser with precedence awareness.
- **Find the specific redundant bracket positions.** Augment the stack with position info.
- **Remove redundant brackets, returning the simplified expression.** Build an output string, skipping redundant parens.
- **Count redundant brackets.** Continue through the expression, tallying each occurrence.
- **Handle unary operators (`-a`).** Trickier; `(-a)` has no "operator between" in the binary sense but is still meaningful.
- **Mixed bracket types.** Extend to `[ ]` and `{ }` with the same principle.
