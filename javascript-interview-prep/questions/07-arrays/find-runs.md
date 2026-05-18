# Find Runs (Consecutive Same-Value Segments)

## Source / Origin
- "Run-length encoding" classic; LeetCode 443 "String Compression."
- Asked at: Razorpay, Atlassian.
- Concept reference: `concepts/arrays.md`.

## Why this question matters in interviews
"Find all consecutive runs of equal/qualifying values." Tests two-pointer iteration and care with boundaries. Senior bar: you produce a clean linear scan and discuss in-place compression for the string variant.

## Concepts involved

```js
function findRuns(arr) {
  const out = [];
  let i = 0;
  while (i < arr.length) {
    let j = i + 1;
    while (j < arr.length && arr[j] === arr[i]) j++;
    out.push({ value: arr[i], start: i, length: j - i });
    i = j;
  }
  return out;
}

// String compression — in-place "aabbbc" → "a2b3c"
function compress(chars) {
  let write = 0, read = 0;
  while (read < chars.length) {
    let count = 0;
    const c = chars[read];
    while (read < chars.length && chars[read] === c) { read++; count++; }
    chars[write++] = c;
    if (count > 1) for (const d of String(count)) chars[write++] = d;
  }
  return write;
}
```

### Edge cases / traps
1. **Single-element runs** — emit with length 1.
2. **Empty array** — return [].
3. **All same** — one run of length n.
4. **In-place compression** must write before it overtakes read; happens naturally because runs of length 1 don't grow.
5. **Predicate-based runs** — generalize `===` to a predicate `(prev, curr) => boolean`.
6. **Streaming variant** — emit runs as found rather than collecting all.

## Mental Model

```
   arr = [1, 1, 2, 3, 3, 3, 1]
          ←┐ ↓ ↓ ←─┐ ↓
   runs:   [1,2]  [2,1]  [3,3]  [1,1]
            (val=1,start=0,len=2)
            (val=2,start=2,len=1)
            (val=3,start=3,len=3)
            (val=1,start=6,len=1)
```

## Solution

```js
// Basic
function findRuns(arr, eq = (a, b) => a === b) {
  const out = [];
  let i = 0;
  while (i < arr.length) {
    let j = i + 1;
    while (j < arr.length && eq(arr[j], arr[i])) j++;
    out.push({ value: arr[i], start: i, length: j - i });
    i = j;
  }
  return out;
}

// Streaming async generator
async function* runsAsync(iter, eq = (a, b) => a === b) {
  let curr = null, start = 0, len = 0, i = 0;
  for await (const x of iter) {
    if (len === 0) { curr = x; start = i; len = 1; }
    else if (eq(x, curr)) { len++; }
    else { yield { value: curr, start, length: len }; curr = x; start = i; len = 1; }
    i++;
  }
  if (len > 0) yield { value: curr, start, length: len };
}

// Predicate-based: find runs where each item satisfies a predicate
function findRunsBy(arr, pred) {
  const out = [];
  let start = -1;
  for (let i = 0; i <= arr.length; i++) {
    if (i < arr.length && pred(arr[i])) {
      if (start === -1) start = i;
    } else if (start !== -1) {
      out.push({ start, length: i - start });
      start = -1;
    }
  }
  return out;
}

// Longest run
function longestRun(arr, eq = (a, b) => a === b) {
  let bestLen = 0, bestStart = 0, bestVal = arr[0];
  let i = 0;
  while (i < arr.length) {
    let j = i + 1;
    while (j < arr.length && eq(arr[j], arr[i])) j++;
    if (j - i > bestLen) { bestLen = j - i; bestStart = i; bestVal = arr[i]; }
    i = j;
  }
  return { value: bestVal, start: bestStart, length: bestLen };
}
```

## Dry run

`arr=[1,1,2,3,3,3,1]`:

```
i=0; j=1; arr[1]==arr[0]; j=2; arr[2]!=arr[0] → push {val:1,start:0,len:2}; i=2
i=2; j=3; arr[3]!=arr[2] → push {val:2,start:2,len:1}; i=3
i=3; j=4; arr[4]==arr[3]; j=5; arr[5]==arr[3]; j=6; arr[6]!=arr[3] → push {val:3,start:3,len:3}; i=6
i=6; j=7; out of bounds → push {val:1,start:6,len:1}; i=7
done
```

## How to think aloud

> "Two pointers: `i` is the run start, `j` walks forward while equal. Push `{value, start, length: j-i}`, set `i = j`, repeat. Generalize equality to a predicate for use cases like 'runs of positive numbers.' For streaming input, async generator with carry-over state. For in-place string compression, write pointer can never overtake read pointer because runs of length 1 don't grow."

## Important takeaways

- **Two-pointer linear scan.** `i` is start, `j` walks while equal.
- **Predicate** generalizes equality.
- **In-place string compression** is safe because writes don't outpace reads.
- **Longest-run** is a one-line variant.
- **Streaming async** for unbounded input.

## Variants

- **RLE encode/decode** — value+count pairs.
- **Longest "good" substring** — predicate-based, two-pointer.
- **Boyer-Moore majority** — different but related family.
- **Sparse representation** of long-run arrays.

## Revision notes

```
findRuns(arr):
  i=0
  while i<n:
    j = i+1
    while j<n && arr[j]==arr[i]: j++
    push {value:arr[i], start:i, length:j-i}
    i = j

generalize:
  eq predicate
  pred-based (filter-runs)
  longest-run (track best)
  streaming (async generator)

USES:
  RLE encoding
  string compression (in-place)
  finding flat sections in data
```
