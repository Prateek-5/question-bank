# Sliding window helper

> **Difficulty:** Medium-Senior   |   **Time:** ~15 min   |   **Prereqs:** [find-runs.md](./find-runs.md), [move-zeros-in-place.md](./move-zeros-in-place.md)
>
> **Source:** Universal pattern. LeetCode tag. Every senior interview.

---

## 1. Problem statement

Implement the sliding-window template for both fixed-size and variable-size variants.

**Verification examples**

```js
// Fixed-size window — max sum of k consecutive
maxSumFixed([2, 1, 5, 1, 3, 2], 3);          // 9 (5+1+3)

// Variable-size — longest substring of distinct chars
longestDistinct('abcabcbb');                  // 3 ('abc')

// Variable-size — minimum size subarray sum >= target
minSubarraySum([2, 3, 1, 2, 4, 3], 7);       // 2 ([4, 3])
```

**Constraints**
- O(n) — each index visited at most O(1) times amortized.
- Fixed: precompute first window; slide by adding right, subtracting left.
- Variable: expand right; contract left while invariant violated.
- Maintain incremental state (sum / count / frequency map).

---

## 2. Plain-English restatement

Two pointers `left, right`. Expand right; if constraint violated, contract left until valid again. Track best answer. O(n) because each pointer moves only forward.

---

## 3. Why this matters in interviews

"Longest/shortest/max-something within constraint" → sliding window. Senior bar: produce template on demand, distinguish fixed vs variable, pick the right invariant.

---

## 4. Mental model

```
   Fixed-size window:
     sum = sum of first k.
     best = sum.
     for i = k..n-1:
       sum += arr[i] - arr[i-k]      ← slide; O(1)
       best = max(best, sum)
   
   Variable-size window template:
     left = 0
     for right = 0..n-1:
       include arr[right] in state
       while constraint violated:
         exclude arr[left] from state
         left++
       update best with (right - left + 1)
   
   Common invariants:
     - sum / running average
     - unique count (use Map<char, lastIndex> or Set)
     - frequency map (Map<value, count>)
     - max/min (use deque for O(1) max — monotonic queue)
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Difference between fixed and variable window?
> 2. Why is it O(n) not O(n²)?
> 3. When use Set vs Map for the state?

---

## 6. Brute force — walked through

```js
// O(n²) all substrings
function longestDistinctBrute(s) {
  let best = 0;
  for (let i = 0; i < s.length; i++) {
    const seen = new Set();
    for (let j = i; j < s.length; j++) {
      if (seen.has(s[j])) break;
      seen.add(s[j]);
    }
    best = Math.max(best, seen.size);
  }
  return best;
}
```

O(n²); sliding window does it in O(n).

---

## 7. The unlocking insight

> **Two pointers, both move only forward (O(n) total). Expand right; contract left while invalid. Maintain state incrementally.**

Three properties:

1. **Each pointer monotonic** — O(n) amortized.
2. **Incremental state update** — add/remove single element.
3. **Best updated** when window valid.

---

## 8. Solution (annotated)

```js
// Fixed-size: max sum of k consecutive
function maxSumFixed(arr, k) {
  if (arr.length < k) return null;                                        // step 1: guard
  let sum = 0;
  for (let i = 0; i < k; i++) sum += arr[i];                              // step 2: first window
  let best = sum;
  for (let i = k; i < arr.length; i++) {
    sum += arr[i] - arr[i - k];                                            // step 3: slide
    best = Math.max(best, sum);
  }
  return best;
}

// Variable: longest substring with no repeating chars
function longestDistinct(s) {
  const lastIdx = new Map();                                              // step 4: char → last index
  let left = 0, best = 0;
  for (let right = 0; right < s.length; right++) {
    if (lastIdx.has(s[right]) && lastIdx.get(s[right]) >= left) {
      left = lastIdx.get(s[right]) + 1;                                   // step 5: jump past dup
    }
    lastIdx.set(s[right], right);
    best = Math.max(best, right - left + 1);
  }
  return best;
}

// Variable: minimum subarray sum >= target
function minSubarraySum(arr, target) {
  let left = 0, sum = 0, best = Infinity;
  for (let right = 0; right < arr.length; right++) {
    sum += arr[right];                                                     // step 6: include right
    while (sum >= target) {                                                // step 7: shrink while valid
      best = Math.min(best, right - left + 1);
      sum -= arr[left];
      left++;
    }
  }
  return best === Infinity ? 0 : best;
}
```

**Try it yourself**

```js
maxSumFixed([2, 1, 5, 1, 3, 2], 3);                          // 9
maxSumFixed([1, 2], 3);                                       // null

longestDistinct('abcabcbb');                                  // 3
longestDistinct('bbbb');                                       // 1
longestDistinct('pwwkew');                                    // 3

minSubarraySum([2, 3, 1, 2, 4, 3], 7);                       // 2 ([4, 3])
minSubarraySum([1, 1, 1], 10);                                // 0 (impossible)

// Reusable helper (LeetCode #76 style)
function minWindowContains(s, needCounts) {
  const have = new Map();
  let satisfied = 0, required = needCounts.size;
  let left = 0, bestLen = Infinity, bestStart = 0;
  for (let right = 0; right < s.length; right++) {
    const c = s[right];
    if (needCounts.has(c)) {
      have.set(c, (have.get(c) || 0) + 1);
      if (have.get(c) === needCounts.get(c)) satisfied++;
    }
    while (satisfied === required) {
      if (right - left + 1 < bestLen) {
        bestLen = right - left + 1;
        bestStart = left;
      }
      const lc = s[left];
      if (needCounts.has(lc)) {
        have.set(lc, have.get(lc) - 1);
        if (have.get(lc) < needCounts.get(lc)) satisfied--;
      }
      left++;
    }
  }
  return bestLen === Infinity ? '' : s.slice(bestStart, bestStart + bestLen);
}
```

---

## 9. Step-by-step dry run

```
longestDistinct('abcabcbb'):
  left=0, best=0, lastIdx={}.
  right=0 'a': not seen. set a→0. best=max(0, 1)=1.
  right=1 'b': not seen. set b→1. best=2.
  right=2 'c': not seen. set c→2. best=3.
  right=3 'a': lastIdx['a']=0 ≥ left=0. left = 0+1 = 1. set a→3. best=max(3, 3)=3.
  right=4 'b': lastIdx['b']=1 ≥ left=1. left = 2. set b→4. best=3.
  right=5 'c': lastIdx['c']=2 ≥ left=2. left = 3. set c→5. best=3.
  right=6 'b': lastIdx['b']=4 ≥ left=3. left = 5. set b→6. best=3.
  right=7 'b': lastIdx['b']=6 ≥ left=5. left = 7. set b→7. best=max(3, 1)=3.
  
  Return 3.

minSubarraySum([2,3,1,2,4,3], 7):
  left=0, sum=0, best=∞.
  r=0: sum=2. 2<7.
  r=1: sum=5. 5<7.
  r=2: sum=6. <7.
  r=3: sum=8. ≥7.
    best=min(∞, 4)=4. sum-=arr[0]=2 → 6. left=1.
    6<7 → exit while.
  r=4: sum=10. ≥7.
    best=min(4, 4)=4. sum-=3 → 7. left=2.
    7≥7: best=min(4, 3)=3. sum-=1 → 6. left=3.
    6<7 → exit.
  r=5: sum=9.
    best=min(3, 3)=3. sum-=2 → 7. left=4.
    7≥7: best=min(3, 2)=2. sum-=4 → 3. left=5.
    3<7 → exit.
  Return 2.
```

---

## 10. Common confusion + traps

1. **Nested loop, not sliding** — O(n²).
2. **left not monotonic** — must only increase.
3. **State not incremental** — recomputing per window is O(n × n) → O(n²).
4. **`if` vs `while`** to shrink — `while` until valid.
5. **Off-by-one** — window size `right - left + 1`.
6. **Fixed-size needs `arr.length >= k`** check.
7. **Reset state across runs** — closures may leak.

---

## 11. Senior follow-ups & variants

### Variant 1 — Min window substring (LeetCode #76)
Need frequency map; track "satisfied" count.

### Variant 2 — Monotonic deque
Window max/min in O(n) using deque.

### Variant 3 — Sliding window median
Two heaps; O(n log k).

### Variant 4 — At most K distinct
Variable window with `Map<char, count>` size.

### Variant 5 — Exactly K — at most K minus at most K-1.

---

## 12. How to think aloud

> "Sliding window collapses 'longest/shortest/max-something with constraint' problems from O(n²) to O(n). Two pointers `left, right`, both move only forward — total work bounded by `2n` operations. Expand right; while constraint violated, contract left. Update best when valid. Fixed-size variant: precompute first window's state, then slide by adding `arr[right]` and subtracting `arr[right-k]` — O(1) per step. Variable variant: include arr[right] in incremental state, while invariant violated remove arr[left] and increment left. State varies by problem: running sum, frequency Map, last-index Map, monotonic deque (window max). LeetCode #76 'minimum window substring' uses frequency Map + 'satisfied' counter. Trap: nested loop without monotonic pointers (still O(n²)); recomputing state per window; `if` vs `while` for shrink (must shrink until valid)."

---

## 13. 60-second revision

> - **Two pointers, both monotonic** → O(n).
> - **Fixed:** add right + subtract left-k.
> - **Variable:** expand right; while invalid contract left.
> - **State incremental:** sum, freq Map, lastIdx Map.
> - **Window size:** `right - left + 1`.
> - **Update best when window valid.**
> - **Monotonic deque** for window max/min in O(n).
> - **Trap:** non-monotonic; `if` vs `while`; state recomputed.

---

**Related:** [find-runs.md](./find-runs.md) · [move-zeros-in-place.md](./move-zeros-in-place.md) · [`08-maps-sets/two-sum-map.md`](../08-maps-sets/two-sum-map.md) · [`08-maps-sets/first-non-repeating-char.md`](../08-maps-sets/first-non-repeating-char.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
