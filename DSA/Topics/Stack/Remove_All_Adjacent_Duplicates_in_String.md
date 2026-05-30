# Remove All Adjacent Duplicates in String

**Problem Link:**
<a href="https://leetcode.com/problems/remove-all-adjacent-duplicates-in-string/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/remove-all-adjacent-duplicates-in-string/</a>

**Topic:**
Stack

----------------------------------------

## Step 1: What Are We Doing?

Given a string of lowercase letters, repeatedly remove any two **adjacent equal** characters. Keep doing this until no such pair remains. Return whatever's left.

Example: `s = "abbaca"`.

Let me apply the rule by hand:
- `"abbaca"` — see the `bb`. Remove → `"aaca"`.
- `"aaca"` — see the `aa` at the start. Remove → `"ca"`.
- `"ca"` — no adjacent duplicates. Stop.

Answer: `"ca"`.

Another: `"azxxzy"`:
- `"azxxzy"` — `xx` → `"azzy"`.
- `"azzy"` — `zz` → `"ay"`.

Answer: `"ay"`.

One more: `"aaaa"`:
- `"aaaa"` — `aa` (first pair) → `"aa"` — `aa` → `""`.

Answer: `""`.

----------------------------------------

## Step 2: Brute Force Thinking

Naïvely: repeatedly scan the string looking for any adjacent duplicate, remove it, restart.

```
while True:
    found = False
    for i in range(len(s) - 1):
        if s[i] == s[i+1]:
            s = s[:i] + s[i+2:]
            found = True
            break
    if not found: break
```

Each scan is O(n), and in the worst case we do n/2 scans (if n/2 pairs get removed). Total O(n²). For large inputs, too slow.

But there's a bigger issue: after each removal, new adjacent duplicates might appear. Like in `"abbaca"`, removing the `bb` exposed `aa`. So we can't just mark pairs in one pass — removing one pair can create another.

This "cascading removals" behavior is a classic hint for a **stack**.

----------------------------------------

## Step 3: Think of the String as Being Built Left to Right

Imagine I'm typing out the resulting string one character at a time, reading from the input. Each time I type a character, I can compare it with the character just before it. If they're equal, I've created an adjacent duplicate — I should erase both.

Specifically:
- If the new character equals the last character I've placed, erase the last and don't place the new.
- Otherwise, place the new character.

That "last character placed" is always the top of a growing sequence. Popping the top when a new duplicate comes in is exactly stack behavior.

```
for each char c in s:
    if stack not empty and stack.top() == c:
        stack.pop()
    else:
        stack.push(c)
return string(stack, bottom to top)
```

Beautiful and linear.

----------------------------------------

## Step 4: Why This Catches Cascades

The key insight: when we pop the top, whatever was *below* the top becomes the new top. If the new incoming character matches *that* (which was just exposed), we pop again on the next iteration (actually wait — we already consumed this incoming char by popping; the *next* incoming char might match the newly exposed top).

Let me trace carefully on `"abbaca"`.

```
i=0, c='a': stack empty. Push. stack = [a].
i=1, c='b': top='a' != 'b'. Push. stack = [a, b].
i=2, c='b': top='b' == 'b'. Pop. stack = [a].
i=3, c='a': top='a' == 'a'. Pop. stack = [].
i=4, c='c': stack empty. Push. stack = [c].
i=5, c='a': top='c' != 'a'. Push. stack = [c, a].
```

Result: "ca". ✓

Look at steps 2 and 3. When `b` arrived at i=2, it matched the top `b` and we popped. That exposed `a` as the new top. Then at i=3, another `a` came in — matched the exposed `a` — we popped. The cascade was handled naturally by the stack.

The scan sees each character exactly once. Each character is pushed at most once and popped at most once. So total work is **O(n)**.

----------------------------------------

## Step 5: Implementation Choice — Use a String as the Stack

In C++, a `std::string` is perfect as a stack: `push_back` adds to the end (top), `back()` peeks, `pop_back()` removes. Plus, at the end we don't need to reverse anything — the string is already in correct order (bottom to top = start to end).

```cpp
string result;
for (char c : s) {
    if (!result.empty() && result.back() == c) result.pop_back();
    else result.push_back(c);
}
return result;
```

No explicit stack container needed. Clean.

----------------------------------------

## Step 6: Edge Cases

- **Empty input:** loop doesn't run; return `""`.
- **No duplicates at all:** every char is pushed, none popped; return the original string.
- **All same characters even length:** every other char cancels; return `""`.
- **All same characters odd length:** everything cancels except one; return one char.

All handled naturally by the same logic.

----------------------------------------

## Step 7: Name What We Used

The pattern is **stack-based cancellation** — process a stream one element at a time; when a new element "cancels" the top (by some rule), pop; otherwise push. Same shape solves:
- Valid Parentheses (opens and their matching closes cancel).
- Basic Calculator (numbers push, operators pop and combine).
- Asteroid Collision (right-moving asteroids on the stack, left-moving ones can cancel).
- Remove K Adjacent Duplicates (generalization of this problem).

----------------------------------------

## Step 8: Complexity

Time: **O(n)**. Each character pushed at most once and popped at most once.
Space: **O(n)** for the result in the worst case (when nothing cancels).

Compare to the O(n²) naive: we avoid the rescanning by maintaining enough state (the stack) to react immediately to each incoming character.

----------------------------------------

## Step 9: C++ Implementation

```cpp
string removeDuplicates(string s) {
    string result;
    for (char c : s) {
        if (!result.empty() && result.back() == c) {
            result.pop_back();
        } else {
            result.push_back(c);
        }
    }
    return result;
}
```

Short, direct, and fast. The "is the new char equal to the last placed one?" check handles everything.

----------------------------------------

## Step 10: Follow-up Questions

- **Remove All Adjacent Duplicates II (remove when `k` consecutive equal chars appear).** Use a stack of `(char, count)` pairs. When a new char matches the top's char, increment count; when count hits k, pop. When it doesn't match, push a new entry.
- **Remove all adjacent duplicates, but allow re-insertion.** Different problem — would need more complex state.
- **Find the final length without constructing the string.** Same algorithm, but just track the stack size; don't store characters.
- **Given a stream (too big to buffer), output the result as it stabilizes.** Same idea — but "stable" output lags behind the stream (a char's permanence depends on future input).
- **Remove duplicates with a custom "cancel rule" (e.g., any vowel cancels any other vowel).** Generalize the match check.
