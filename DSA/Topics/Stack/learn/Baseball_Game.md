# Baseball Game — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Baseball_Game.md`](../Baseball_Game.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/baseball-game/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. The lesson: **a stack is the natural data structure for "simulate operations that reference the most recent few elements."** Once you've internalized the stack-as-simulation pattern, you'll spot it in RPN evaluation, text editor backspace, and undo-stack problems. **Read [`Valid_Parentheses.md`](./Valid_Parentheses.md) first.**

**Map of this file (8 short sections):**

1. Read the problem
2. The pattern in the rules
3. Mapping rules to stack operations
4. Code
5. Trace it
6. Common pitfalls
7. The shape — stack-as-simulation
8. Cross-references

---

## 1. Read the problem

You're given a list of strings `ops` representing baseball-scoreboard operations. Each string is one of:

| Operation | Effect |
|---|---|
| an integer like `"5"` or `"-2"` | Record this as a new score. |
| `"+"` | Record a new score equal to the **sum of the two previous scores**. |
| `"D"` | Record a new score equal to **double the previous score**. |
| `"C"` | **Cancel** (remove) the most recent score. |

Return the **sum of all scores currently on the record** after processing all operations.

**Example:** `ops = ["5", "2", "C", "D", "+"]`.

```
"5": record 5.            scores: [5]
"2": record 2.            scores: [5, 2]
"C": cancel last (2).     scores: [5]
"D": double last (5→10). scores: [5, 10]
"+": last two sum (5+10=15). scores: [5, 10, 15]
```

Total: 5 + 10 + 15 = **30**.

Problem guarantees inputs are always legal (never `C` on empty list, never `D`/`+` without enough scores).

---

## 2. The pattern in the rules

Look at what each operation needs:

- **Integer:** add a new score (no reads).
- **`+`:** READ the last 2 scores; ADD a new score.
- **`D`:** READ the last 1 score; ADD a new score.
- **`C`:** REMOVE the last score.

Every operation that does anything (other than just push a literal) interacts with the **MOST RECENT** scores. None ever references "the 5th score" or "all scores so far." Only **the tail**.

> **Mini-refresher: when is a stack the right tool?**
>
> A stack (LIFO) is the right data structure when:
> - The next event interacts with the MOST RECENT element(s), AND
> - You may need to ADD to or REMOVE from the tail of a growing list.
>
> The operations available — push, pop, top, peek-second-from-top — match exactly the access patterns we need here.

A plain dynamic array (`std::vector`, Python `list`, JS `Array`) works perfectly as a stack since it has fast back-access.

---

## 3. Mapping rules to stack operations

Pseudocode:

```
stack = []
for op in ops:
    if op is an integer:
        stack.push(parseInt(op))
    elif op == "+":
        n = len(stack)
        stack.push(stack[n-1] + stack[n-2])
    elif op == "D":
        stack.push(2 * stack[n-1])
    elif op == "C":
        stack.pop()
return sum(stack)
```

> **Mini-refresher: parsing strings to ints.**
>
> The input is strings. Integers like `"5"` or `"-2"` need to be converted via the language's int-parse function:
> - C++: `stoi(op)` (or `stoll` for safety with multiplication).
> - Python: `int(op)`.
> - JavaScript: `parseInt(op, 10)` or `Number(op)`.
>
> **Order of checks matters:** check the three operation literals (`"+"`, `"D"`, `"C"`) FIRST, then treat anything else as an integer. Calling `stoi("+")` would throw — `"+"` isn't a valid integer.

For accessing the top two without popping, we can either use `stack[size-1]` and `stack[size-2]` directly (since these are vectors/arrays) or pop twice and push back. The first is cleaner.

---

## 4. Code

**C++:**

```cpp
int calPoints(vector<string>& ops) {
    vector<int> stack;
    for (const string& op : ops) {
        if (op == "+") {
            int n = stack.size();
            stack.push_back(stack[n - 1] + stack[n - 2]);
        } else if (op == "D") {
            stack.push_back(2 * stack.back());
        } else if (op == "C") {
            stack.pop_back();
        } else {
            stack.push_back(stoi(op));
        }
    }
    int sum = 0;
    for (int v : stack) sum += v;
    return sum;
}
```

Notice the **order of branches**: the three literal-operation strings are checked first. The `else` catches the integer case. Trying it the other way around would throw on `stoi("+")`.

**Python:**

```python
def calPoints(ops):
    stack = []
    for op in ops:
        if op == "+":
            stack.append(stack[-1] + stack[-2])
        elif op == "D":
            stack.append(2 * stack[-1])
        elif op == "C":
            stack.pop()
        else:
            stack.append(int(op))
    return sum(stack)
```

**JavaScript:**

```javascript
function calPoints(ops) {
    const stack = [];
    for (const op of ops) {
        if (op === "+") {
            stack.push(stack[stack.length - 1] + stack[stack.length - 2]);
        } else if (op === "D") {
            stack.push(2 * stack[stack.length - 1]);
        } else if (op === "C") {
            stack.pop();
        } else {
            stack.push(parseInt(op, 10));
        }
    }
    return stack.reduce((a, b) => a + b, 0);
}
```

**Complexity:**
- Time: **O(n)** — each operation is O(1), and we do n operations plus a final O(stack-size) sum.
- Space: **O(n)** worst case for the stack.

---

## 5. Trace it

`ops = ["5", "-2", "4", "C", "D", "9", "+", "+"]`:

```
stack = [].

"5":   integer 5. push.       stack = [5].
"-2":  integer -2. push.      stack = [5, -2].
"4":   integer 4. push.       stack = [5, -2, 4].
"C":   pop.                    stack = [5, -2].
"D":   2 * back (-2) = -4. push.  stack = [5, -2, -4].
"9":   push.                   stack = [5, -2, -4, 9].
"+":   stack[3] + stack[2] = 9 + (-4) = 5. push.  stack = [5, -2, -4, 9, 5].
"+":   stack[4] + stack[3] = 5 + 9 = 14. push.    stack = [5, -2, -4, 9, 5, 14].

Sum: 5 + (-2) + (-4) + 9 + 5 + 14 = 27.
```

Notice how parsing `"-2"` as an integer must handle the leading minus sign — that's why we use `stoi`/`int()`, not naive digit-character extraction.

---

## 6. Common pitfalls

1. **Checking integer FIRST and operation strings later.** `stoi("+")` throws. Always check the three operation literals first, integer in the else.

2. **Treating `"+"` as a no-op or as "add to last."** Re-read the rules: `"+"` adds a NEW score equal to the SUM OF THE LAST TWO. The previous two stay.

3. **For `"D"`, multiplying the wrong score.** It's the most recent SCORE, not the most recent ANYTHING. (They're the same thing in this problem, but stay careful.)

4. **For `"C"`, removing the wrong score.** It removes the MOST RECENT score (top of stack), not the smallest, not the first.

5. **Forgetting to take the final SUM.** The answer isn't just the last score or the stack size — it's the TOTAL of all surviving scores.

6. **Worrying about edge cases the problem rules out.** The spec says operations are always legal — never `C` on empty stack, never `D`/`+` without enough scores. Don't add defensive checks. Trust the spec.

7. **Overflow.** Sums and doubles can grow. For safety in C++, you could use `long long`, but typical constraints keep things within `int`. Read the constraints.

---

## 7. The shape — stack-as-simulation

This is the canonical "stack as simulator" pattern. Anywhere you process a sequence of events where **each event modifies the tail of a state list**, a stack is the right tool.

| Problem | Events that modify the tail |
|---|---|
| **This problem** | record / cancel / double / sum |
| Evaluate Reverse Polish Notation | numbers push; operators pop 2, push result |
| Backspace String Compare | char appends; `#` pops |
| Text editor with undo (one level) | edits push; undo pops |
| Function call stack (in a compiler) | call pushes a frame; return pops it |
| Stack-based VM (e.g., JVM bytecode) | each opcode operates on the top of the operand stack |
| Browser back button | navigate pushes; back pops |

**Pattern to internalize:**

> "When a problem describes a SEQUENCE OF OPERATIONS where each modifies only the most recent few elements of an evolving list, use a stack. Each operation maps directly to push, pop, or peek."

The recognition cue: the rules of the problem read like instructions to a register-stack-machine. When you find yourself thinking "after this op, the tail of the list looks like X," you've already invented the stack.

---

> **Self-check — the question to ask next time.**
>
> When a problem hands you a sequence of operations to simulate, and each operation references only the MOST RECENT elements of a running list, ask:
>
> > **"Can I push integers and let operators pop and combine the top few? Use a stack as the simulator."**
>
> If yes, the code writes itself — branch per operation type, push or pop accordingly.

---

## 8. Cross-references

- **Reference card (post-mastery):** [`../Baseball_Game.md`](../Baseball_Game.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Valid_Parentheses.md`](./Valid_Parentheses.md), [`Min_Stack.md`](./Min_Stack.md) — stack basics.
  - Coming next: [`Evaluate_Reverse_Polish_Notation.md`](./Evaluate_Reverse_Polish_Notation.md) — the same simulation pattern with operators consuming operands.
