# Find runs — consecutive same-value segments

> **Difficulty:** Foundation   |   **Time:** ~10 min   |   **Prereqs:** [move-zeros-in-place.md](./move-zeros-in-place.md)
>
> **Source:** Run-length encoding classic. LeetCode #443. Razorpay, Atlassian.

---

## 1. Problem statement

Return all maximal runs of consecutive equal values: `{value, start, length}`.

**Verification examples**

```js
findRuns([1, 1, 2, 2, 2, 3]);
// [{value:1, start:0, length:2}, {value:2, start:2, length:3}, {value:3, start:5, length:1}]

findRuns([]);                            // []
findRuns([5]);                           // [{value:5, start:0, length:1}]

// String compression — in-place
compress(['a','a','b','b','b','c']);     // returns 4; chars = ['a','2','b','3','c',...]
```

**Constraints**
- Linear single scan.
- Two-pointer: outer `i`, inner `j` advances while equal.
- String compression variant — in-place write index.

---

## 2. Plain-English restatement

Walk the array. For each run, advance an inner pointer while values match. Emit `{value, start, length}`. Move outer to end of run.

---

## 3. Why this matters in interviews

Two-pointer iteration with boundary care. String compression variant tests in-place writes. Senior bar: O(n) scan, no special-case for last run.

---

## 4. Mental model

```
   findRuns(arr):
     i = 0
     while i < n:
       j = i + 1
       while j < n && arr[j] === arr[i]:
         j++
       emit {value: arr[i], start: i, length: j - i}
       i = j
   
   No special-case for "last run" — naturally exits when i = n.
   
   String compression (in-place):
     write = 0; read = 0
     while read < n:
       c = chars[read]
       count = 0
       while read < n && chars[read] === c:
         read++; count++
       chars[write++] = c
       if count > 1:
         for digit of String(count): chars[write++] = digit
     return write   ← new "length"
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why doesn't the last run need a special case?
> 2. How do you handle count > 9 in string compression?
> 3. What if values are objects?

---

## 6. Brute force — walked through

```js
// Build groups via reduce — works but allocates
arr.reduce((acc, v, i) => {
  const last = acc[acc.length - 1];
  if (last && last.value === v) last.length++;
  else acc.push({ value: v, start: i, length: 1 });
  return acc;
}, []);
```

O(n) time; clean but extra allocation per item.

---

## 7. The unlocking insight

> **Two-pointer: outer `i` to start of run, inner `j` advances while `arr[j] === arr[i]`. Emit `{value, start: i, length: j-i}`, then `i = j`.**

Three properties:

1. **Outer/inner pointers** — no nested loops; total O(n).
2. **No last-run special case** — `i = j` exits naturally.
3. **String compression** — in-place via write index.

---

## 8. Solution (annotated)

```js
function findRuns(arr) {
  const out = [];
  let i = 0;
  while (i < arr.length) {                                                // step 1: outer
    let j = i + 1;
    while (j < arr.length && arr[j] === arr[i]) j++;                     // step 2: inner advance
    out.push({ value: arr[i], start: i, length: j - i });                 // step 3: emit
    i = j;                                                                // step 4: skip run
  }
  return out;
}

// String compression in-place (LeetCode #443)
function compress(chars) {
  let write = 0, read = 0;
  while (read < chars.length) {
    const c = chars[read];
    let count = 0;
    while (read < chars.length && chars[read] === c) {                   // step 5: count run
      read++;
      count++;
    }
    chars[write++] = c;
    if (count > 1) {                                                       // step 6: digits if >1
      for (const d of String(count)) chars[write++] = d;
    }
  }
  return write;                                                            // step 7: new length
}
```

**Try it yourself**

```js
findRuns([1, 1, 2, 2, 2, 3]);
// [{value:1, start:0, length:2}, {value:2, start:2, length:3}, {value:3, start:5, length:1}]

findRuns(['a', 'a', 'b']);
// [{value:'a', start:0, length:2}, {value:'b', start:2, length:1}]

findRuns([]);                                                 // []
findRuns([1, 2, 3]);                                          // 3 single-item runs

// With custom equality
function findRunsBy(arr, eq) {
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

// Run-length encoding (RLE)
function rle(arr) {
  return findRuns(arr).map(r => [r.value, r.length]);
}

// String compression
const c = ['a','a','b','b','b','c'];
const len = compress(c);
console.log(c.slice(0, len));                                 // ['a','2','b','3','c']
```

---

## 9. Step-by-step dry run

```
findRuns([1,1,2,2,2,3]):
  i=0:
    j=1: arr[1]=1 === arr[0]=1 → j=2.
    j=2: arr[2]=2 !== 1 → stop.
    emit {1, 0, 2}. i=2.
  i=2:
    j=3: arr[3]=2 === 2 → j=4.
    j=4: arr[4]=2 === 2 → j=5.
    j=5: arr[5]=3 !== 2 → stop.
    emit {2, 2, 3}. i=5.
  i=5:
    j=6 ≥ 6 → stop.
    emit {3, 5, 1}. i=6.
  i=6 = n → loop exit.

compress(['a','a','b','b','b','c']):
  read=0: c='a'. while equal: read=1, count=1; read=2, count=2; arr[2]='b' stop.
    chars[0]='a' (already). count=2>1: chars[1]='2'. write=2.
  read=2: c='b'. while equal: read=3 count=1; read=4 count=2; read=5 count=3; stop.
    chars[2]='b'. count=3>1: chars[3]='3'. write=4.
  read=5: c='c'. while equal: read=6 count=1; stop.
    chars[4]='c'. count=1 → no digits. write=5.
  return 5.
  
Final chars: ['a','2','b','3','c','c']. First 5 are the answer.
```

---

## 10. Common confusion + traps

1. **Special-case last run** — unnecessary; natural exit.
2. **`count > 1`** for digit emission — single char compresses to itself.
3. **Multi-digit counts** — write each digit; `String(10)` = '10' → 2 chars.
4. **Object equality** — `===` reference; need custom eq.
5. **Nested loops O(n²)** — total work is O(n) because `i = j`.
6. **Float NaN** — `NaN !== NaN`; handle via Object.is or skip.
7. **String compression returns length** — array longer than meaningful prefix.

---

## 11. Senior follow-ups & variants

### Variant 1 — Custom equality
Pass `eq` function for objects.

### Variant 2 — RLE / decode
`runs.flatMap(r => Array(r.length).fill(r.value))`.

### Variant 3 — Find longest run
Track max during scan.

### Variant 4 — Find runs matching predicate
`{value satisfying p}` runs.

### Variant 5 — Streaming runs (generator)
Yield runs lazily for large inputs.

---

## 12. How to think aloud

> "Find-runs is the canonical two-pointer scan with boundary care. Outer pointer `i` to start of each run; inner pointer `j` advances while `arr[j] === arr[i]`. Emit `{value, start: i, length: j - i}`, then `i = j` to skip the run. No special-case for the last run — when `i = n`, the outer while exits naturally. Total work O(n) — inner advances are amortized; each index visited once. String compression (LeetCode #443): same algorithm but in-place. Maintain `write` index; write the char and, if count > 1, write each digit of the count (multi-digit handling — `count = 10` writes '1','0'). Return new length. Variants: custom equality (objects via `eq` callback); RLE decode is inverse; longest run tracks max during scan; streaming yields lazily for large inputs. Trap: special-case last run (unnecessary); count > 1 missed (single chars become 'a1'); multi-digit (forget loop over String(count)); object equality (=== is ref)."

---

## 13. 60-second revision

> - **Two pointers:** outer `i` at run start, inner `j` advances while equal.
> - **Emit `{value, start: i, length: j-i}`; `i = j`.**
> - **No last-run special case** — natural exit.
> - **O(n) total** — amortized.
> - **String compression:** in-place write; `count > 1` writes digits.
> - **Multi-digit counts** — loop over `String(count)`.
> - **Custom eq** for objects.
> - **Trap:** special-case last; count==1 emit '1'; multi-digit miss.

---

**Related:** [move-zeros-in-place.md](./move-zeros-in-place.md) · [sliding-window-helper.md](./sliding-window-helper.md) · [polyfill-reduce.md](./polyfill-reduce.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
