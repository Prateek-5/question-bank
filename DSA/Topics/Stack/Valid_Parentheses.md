# Valid Parentheses

**Problem Link:**
https://leetcode.com/problems/valid-parentheses/

**Topic:**
Stack

----------------------------------------

## Step 1: What's Being Asked

You get a string made only of bracket characters: `(`, `)`, `[`, `]`, `{`, `}`. Return `true` if the string is "balanced" — every opener has a matching closer of the same type, and brackets close in the correct order.

Valid: `()`, `()[]{}`, `{[()]}`.
Invalid: `(]` (wrong type), `([)]` (wrong order), `(` (unclosed).

That's the entire task. No arithmetic, no counts to return — just a yes/no.

----------------------------------------

## Step 2: What Makes a String Valid? Think Physically.

Let's forget algorithms and just ask: how would a human check this?

Take `{[()]}`. I'd read left-to-right. I see `{`, then `[`, then `(`. So far, the *most recent unclosed* bracket is `(`. Next character is `)` — yes, that closes my most recent `(`. Now the most recent unclosed is `[`. Next is `]` — closes it. Now the most recent unclosed is `{`. Next is `}` — closes it. Everything closed. Valid.

What about `([)]`? I see `(`, then `[`. Most recent unclosed is `[`. Next is `)` — but that doesn't match `[`. Invalid right there.

So the key observation is: **the next closer must match the most recently opened bracket**. That's the rule. We only ever care about the most recent opener that hasn't been closed yet.

----------------------------------------

## Step 3: What Data Structure Behaves Like "Most Recent"?

I need to track openers as I encounter them, and when a closer appears, I need the most recent opener. When that opener is matched, I throw it away and now the *second most recent* becomes the most recent.

That's a last-in, first-out structure. The last opener I pushed should be the first one I pop when I see a closer.

It's the behavior of a **stack**. And this is where the idea reveals itself — we didn't reach for a stack because "bracket problems use stacks" as a rote rule. We reached for it because the *rule of the problem* (most recent unclosed opener matters) maps exactly to stack semantics.

----------------------------------------

## Step 4: The Algorithm Drops Out

Now the code almost writes itself.

- If the current char is an opener (`(`, `[`, `{`), push it onto the stack.
- If it's a closer:
  - If the stack is empty, there's no opener to match — return false.
  - Otherwise pop the top and check that it matches the closer. If not, return false.
- After processing all characters, the stack must be empty (otherwise some openers were never closed).

----------------------------------------

## Step 5: Let's Trace `{[()]}`

```
Start:  stack = []
'{':    push '{'              stack = ['{']
'[':    push '['              stack = ['{', '[']
'(':    push '('              stack = ['{', '[', '(']
')':    pop '(', matches ')'? yes. stack = ['{', '[']
']':    pop '[', matches ']'? yes. stack = ['{']
'}':    pop '{', matches '}'? yes. stack = []
end:    stack empty → valid
```

Now let's trace a failing case, `([)]`:

```
Start:  stack = []
'(':    push '('              stack = ['(']
'[':    push '['              stack = ['(', '[']
')':    pop '[', matches ')'? NO. return false
```

Notice how the stack caught the ordering bug. When `)` arrived, the most recent unclosed was `[`, not `(`. That's exactly the mismatch we want to detect.

----------------------------------------

## Step 6: Edge Cases Worth Thinking About

A beginner's first pass often forgets a few of these. Let me list them:

- **Empty string.** Trivially valid — zero brackets are all matched. Our loop never runs and the stack is empty. Correct by accident, but worth confirming.
- **Only closers, like `)))`.** First pop attempt on empty stack → return false. Good.
- **Only openers, like `(((`.** Loop finishes with a non-empty stack → return false. Good.
- **Odd length.** Can never be valid (every bracket needs a partner). We could short-circuit, but the algorithm catches it anyway when the stack is non-empty at the end.

----------------------------------------

## Step 7: Complexity

Time: one pass, O(1) per character. **O(n)**.
Space: in the worst case (all openers), the stack holds all `n` characters. **O(n)**.

You can't do better on time — you have to look at every character. You can't do better on space in the worst case either — `(((...(((` genuinely requires tracking `n/2` openers.

----------------------------------------

## Step 8: C++ Implementation

```cpp
bool isValid(string s) {
    stack<char> st;
    for (char c : s) {
        if (c == '(' || c == '[' || c == '{') {
            st.push(c);
        } else {
            // c is a closer
            if (st.empty()) return false;
            char top = st.top(); st.pop();
            if ((c == ')' && top != '(') ||
                (c == ']' && top != '[') ||
                (c == '}' && top != '{')) {
                return false;
            }
        }
    }
    return st.empty();
}
```

Two small style notes: I kept the match condition inline rather than using a `unordered_map<char,char>` because the three-way check is short enough to read. For more bracket types, a map would pay off. And I check `st.empty()` before popping — calling `top()` on an empty `std::stack` is undefined behavior, so never skip that check.

----------------------------------------

## Step 9: Follow-up Questions

- **Longest valid parentheses substring.** Now we track *positions*. When a `)` closes an opener, the valid span extends back to (at least) the closer's match. Classic stack-of-indices problem.
- **Minimum edits (add/remove) to make a string valid.** Count unmatched closers during the pass, and unmatched openers left in the stack at the end. Sum is the answer.
- **Nested-depth calculation.** At each `(` push and track current depth as the stack size; answer is the max depth observed.
- **Check balance in a stream (you can only see each character once, can't rescan).** Same algorithm — the stack handles streaming naturally.
- **If there were more bracket types (say 10), would this still work?** Yes, but refactor the match check into a small lookup table.
