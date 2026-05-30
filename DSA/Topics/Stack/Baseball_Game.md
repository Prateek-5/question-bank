# Baseball Game

**Problem Link:**
<a href="https://leetcode.com/problems/baseball-game/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/baseball-game/</a>

**Topic:**
Stack

----------------------------------------

## Step 1: Parse the Rules

You have a list of operations on a running scoreboard. Each operation is one of:
- **An integer `x`**: record `x` as a new score.
- **`"+"`**: record a new score equal to the sum of the **two previous** scores.
- **`"D"`**: record a new score equal to **double** the previous score.
- **`"C"`**: **cancel** (remove) the most recent score.

Return the **sum of all scores** on the record at the end.

Example: `ops = ["5", "2", "C", "D", "+"]`.

Process:
- "5": record 5. List: [5].
- "2": record 2. List: [5, 2].
- "C": cancel last (2). List: [5].
- "D": double last (5 → 10). List: [5, 10].
- "+": sum of last two (5 + 10 = 15). List: [5, 10, 15].

Final sum: 5 + 10 + 15 = **30**.

----------------------------------------

## Step 2: Which Data Structure Fits?

Each operation references "the last few" records:
- C removes the last.
- D doubles the last (reads it).
- + sums the last two (reads them, then adds a new one).

"Last" operations on a sequence that grows and shrinks — that's a **stack**.

Specifically, we need LIFO: push (for numbers, D, +), pop (for C), peek (for D), peek-top-2 (for +).

A plain `std::vector<int>` works as a stack — `push_back`, `pop_back`, `back()`, access `[size-2]`.

----------------------------------------

## Step 3: Algorithm

```
stack = []
for op in ops:
    if op is a number: stack.push(parseInt(op))
    elif op == "+": stack.push(stack[size-1] + stack[size-2])
    elif op == "D": stack.push(2 * stack[size-1])
    elif op == "C": stack.pop()
return sum(stack)
```

Straight interpretation of the rules.

----------------------------------------

## Step 4: Trace on `["5", "-2", "4", "C", "D", "9", "+", "+"]`

```
"5": stack = [5].
"-2": stack = [5, -2].
"4": stack = [5, -2, 4].
"C": pop 4. stack = [5, -2].
"D": 2 * -2 = -4. stack = [5, -2, -4].
"9": stack = [5, -2, -4, 9].
"+": 9 + (-4) = 5. stack = [5, -2, -4, 9, 5].
"+": 5 + 9 = 14. stack = [5, -2, -4, 9, 5, 14].
```

Sum: 5 + (-2) + (-4) + 9 + 5 + 14 = **27**.

----------------------------------------

## Step 5: Parsing Integers

In C++, tokens are strings. Distinguish operation strings ("+", "D", "C") from integer strings. Integers may be negative (like "-2"), so parsing needs to handle the sign.

`stoi(op)` parses a signed integer. But we need to recognize "+", which starts with '+' — `stoi("+")` would error. So check for the three operation literals first, then fall back to stoi.

----------------------------------------

## Step 6: Name It

**Stack-based simulation** of a sequence-modifying operation stream. Same pattern solves:
- RPN Evaluation (different operators).
- Text editor backspace simulation.
- Function call stacks.
- Undo/redo with one level.

Whenever operations mutate the tail of a sequence based on its last few elements, stack is the natural fit.

----------------------------------------

## Step 7: Complexity

Time: **O(n)** — each operation is O(1).
Space: O(n) for the stack in the worst case.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int calPoints(vector<string>& ops) {
    vector<int> stack;
    for (const string& op : ops) {
        if (op == "+") {
            int n = stack.size();
            stack.push_back(stack[n-1] + stack[n-2]);
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

Seven lines of real logic. Problem solved.

Edge cases per the problem: always legal (we never pop empty, never "D"/"+" with insufficient scores). We don't need defensive checks.

----------------------------------------

## Step 9: Follow-up Questions

- **Support more operations (say, multiply by k).** Add more branches.
- **Undo a single C.** Uh oh — C doesn't track what it removed. Need a redo stack.
- **Multiple-level undo-redo.** Use two stacks.
- **What if operations can reference any past score, not just last few?** Need an indexable structure + memoization.
- **Parse more complex tokens (decimals, expressions).** Upgrade the parsing step.
- **Stream operations (read one at a time, return running sum).** Same algorithm, maintain running sum.
