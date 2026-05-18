# Sliding Window Helper

## Source / Origin
- Standard algorithmic pattern; LeetCode tag.
- Asked at: every senior interview (substring, sub-array problems).
- Concept reference: `concepts/arrays.md`.

## Why this question matters in interviews
Many "longest/shortest/max-something within constraint X" problems collapse to a sliding window: two pointers, expand right, contract left when constraint violated. Senior bar: you produce the template on demand, distinguish fixed-size vs variable-size windows, and pick the right invariant to maintain (sum, count, character frequency, etc.).

## Concepts involved

### Syntax to lock in
```js
// Variable-size window template
function maxLengthSubstring(s, isValid) {
  let left = 0, best = 0;
  // any state needed to test validity
  for (let right = 0; right < s.length; right++) {
    // include s[right]
    while (!isValid(/* state */)) {
      // exclude s[left]
      left++;
    }
    best = Math.max(best, right - left + 1);
  }
  return best;
}

// Fixed-size window template
function maxSumFixed(arr, k) {
  let sum = 0;
  for (let i = 0; i < k; i++) sum += arr[i];
  let best = sum;
  for (let i = k; i < arr.length; i++) {
    sum += arr[i] - arr[i - k];      // slide
    best = Math.max(best, sum);
  }
  return best;
}
```

### Edge cases / traps
1. **Boundary inclusivity**: `right - left + 1` is the window size when both ends are inclusive.
2. **Invariant maintenance** — choose ONE invariant to maintain and shrink the window when it breaks.
3. **Hash map of counts** — common state for "longest substring with k distinct chars."
4. **Reset vs slide** — fixed-size always slides one position; variable-size shrinks as needed.
5. **`left` only moves forward** — total work is O(n) amortized (right and left each move at most n times).
6. **Empty input** — return 0 or undefined explicitly.
7. **Negative numbers** — fixed-window sum works; max subarray with negatives is Kadane's (different pattern).
8. **At-most vs exactly** — "exactly K distinct" = "at-most K" minus "at-most K-1."

## Mental Model

```
   [a b c d e f g h i]
       ↑       ↑
      left    right

   expand:  right → ; update state
   shrink:  left  → ; update state; until invariant restored
   record:  window size or window sum

   each step: O(1) work
   total:    O(n) — left advances at most n times across the whole run
```

## Why interviewers care

- **Pattern recognition** — many problems are sliding-window in disguise.
- **Amortization reasoning** — explaining why it's O(n) not O(n²).
- **State design** — picking the right invariant.

## Common confusion

- **"Two-pointer = sliding window."** Sliding window IS a two-pointer pattern, but two-pointer also includes opposite-ends-converge (e.g., two-sum sorted).
- **"Window must always grow."** No — fixed-size slides one-at-a-time; variable-size can shrink.
- **"O(n²) because nested loop."** The inner `while` only advances `left`; left moves at most n total → amortized O(n).
- **"Need to revisit elements."** Don't — both pointers only go forward.

## Brute force

`O(n²)` or `O(n³)`: nested loops over all subarrays.

## Optimal approach

Two pointers moving in one direction. Maintain invariant via a hashmap of counts, running sum, or similar.

## Solution

```js
// 1. Longest substring without repeating characters
function lengthOfLongestSubstring(s) {
  const seen = new Map();
  let left = 0, best = 0;
  for (let right = 0; right < s.length; right++) {
    const c = s[right];
    if (seen.has(c) && seen.get(c) >= left) left = seen.get(c) + 1;
    seen.set(c, right);
    best = Math.max(best, right - left + 1);
  }
  return best;
}

// 2. Longest substring with at most K distinct characters
function lengthOfLongestSubstringKDistinct(s, k) {
  const count = new Map();
  let left = 0, best = 0;
  for (let right = 0; right < s.length; right++) {
    count.set(s[right], (count.get(s[right]) || 0) + 1);
    while (count.size > k) {
      const lc = s[left];
      count.set(lc, count.get(lc) - 1);
      if (count.get(lc) === 0) count.delete(lc);
      left++;
    }
    best = Math.max(best, right - left + 1);
  }
  return best;
}

// 3. Minimum window substring
function minWindow(s, t) {
  const need = new Map();
  for (const c of t) need.set(c, (need.get(c) || 0) + 1);
  let missing = t.length;
  let left = 0, bestLen = Infinity, bestStart = 0;
  for (let right = 0; right < s.length; right++) {
    if (need.has(s[right])) {
      if (need.get(s[right]) > 0) missing--;
      need.set(s[right], need.get(s[right]) - 1);
    }
    while (missing === 0) {
      if (right - left + 1 < bestLen) { bestLen = right - left + 1; bestStart = left; }
      if (need.has(s[left])) {
        need.set(s[left], need.get(s[left]) + 1);
        if (need.get(s[left]) > 0) missing++;
      }
      left++;
    }
  }
  return bestLen === Infinity ? '' : s.slice(bestStart, bestStart + bestLen);
}

// 4. Max sum of subarray of size K (fixed window)
function maxSumK(arr, k) {
  let sum = 0;
  for (let i = 0; i < k; i++) sum += arr[i];
  let best = sum;
  for (let i = k; i < arr.length; i++) {
    sum += arr[i] - arr[i - k];
    best = Math.max(best, sum);
  }
  return best;
}

// 5. Sliding window maximum (monotonic deque)
function maxSlidingWindow(arr, k) {
  const deque = [];
  const out = [];
  for (let i = 0; i < arr.length; i++) {
    if (deque[0] <= i - k) deque.shift();
    while (deque.length && arr[deque[deque.length - 1]] < arr[i]) deque.pop();
    deque.push(i);
    if (i >= k - 1) out.push(arr[deque[0]]);
  }
  return out;
}
```

## Dry run

`lengthOfLongestSubstring("abcabcbb")`:

```
right=0 s[0]='a' seen={}     left=0 best=1  set seen[a]=0
right=1 s[1]='b' seen={a:0}  left=0 best=2  set seen[b]=1
right=2 s[2]='c' seen={a:0,b:1} left=0 best=3  set seen[c]=2
right=3 s[3]='a' seen has 'a' at 0 ≥ left → left=1; set seen[a]=3; best=3
right=4 s[4]='b' seen has 'b' at 1 ≥ left → left=2; set seen[b]=4; best=3
right=5 s[5]='c' seen has 'c' at 2 ≥ left → left=3; set seen[c]=5; best=3
right=6 s[6]='b' seen has 'b' at 4 ≥ left → left=5; set seen[b]=6; best=3
right=7 s[7]='b' seen has 'b' at 6 ≥ left → left=7; set seen[b]=7; best=3
return 3
```

## How to think aloud

> "Sliding window: two pointers `left` and `right`, both moving forward. Expand right; if invariant breaks, advance left until restored. Record best on each iteration. Total O(n) amortized because each pointer moves at most n times. For 'at most K distinct,' the invariant is `map.size <= k`. For 'minimum window containing T,' the invariant is 'all chars in T covered.' For fixed-size, it's a one-add-one-remove slide each step. Sliding-window maximum needs a monotonic deque to retrieve the max in O(1)."

## Important takeaways

- **Two pointers**, both moving forward.
- **Amortized O(n)** — each pointer moves at most n.
- **Invariant** chosen from problem: count, distinct chars, sum, frequency match.
- **Fixed-size**: one-add-one-remove slide.
- **Variable-size**: expand right, shrink left when invariant breaks.
- **Monotonic deque** for window-min/max in O(1) per step.

## Variants

- **Sliding window over stream** — async iterator + bounded buffer.
- **2D sliding window** — submatrix sums.
- **Window of fixed *sum* not size** — like rate limiter.
- **Two-pointer (opposite-ends)** — different but related family.

## Revision notes

```
Sliding Window:
  let left=0, best=0
  for right in 0..n:
    include arr[right] (update state)
    while !isValid(state):
      exclude arr[left]; left++
    best = max(best, right-left+1)

Fixed-size:
  one-add-one-remove slide

Variable-size:
  expand right, shrink left when invariant breaks

AMORTIZED O(n) — left moves at most n times
state: hashmap of counts, running sum, distinct count

Variants:
  longest no-repeat
  at most K distinct
  exactly K = at-most-K minus at-most-(K-1)
  min window substring
  max in window: monotonic deque
```
