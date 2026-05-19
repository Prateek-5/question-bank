# Async directory walker

> **Difficulty:** Medium-Senior   |   **Time:** ~12 min   |   **Prereqs:** [`06-streams/async-iterator-pagination.md`](../06-streams/async-iterator-pagination.md), [`06-streams/callback-api-to-async-iterator.md`](../06-streams/callback-api-to-async-iterator.md)
>
> **Source:** Node `fs/promises`. Razorpay, Atlassian, Cloudflare.

---

## 1. Problem statement

Walk a directory tree async; yield files. Handle perms, symlink cycles, large trees.

**Verification examples**

```js
import { readdir } from 'node:fs/promises';
import path from 'node:path';

async function* walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(p);
    else yield p;
  }
}

for await (const file of walk('/some/dir')) {
  console.log(file);
}
```

**Constraints**
- `async function*` for lazy streaming.
- Skip perm errors (decide policy).
- Track symlink cycles via inode set.
- Optional concurrency for parallel readdir.

---

## 2. Plain-English restatement

`yield*` delegates to a recursive walk. Yields each file as discovered. Caller pulls one at a time.

---

## 3. Why this matters in interviews

Tests async generator + recursion + error handling + concurrency awareness.

---

## 4. Mental model

```
   async function* walk(dir):
     entries = await readdir(dir, {withFileTypes: true})
     for entry of entries:
       p = path.join(dir, entry.name)
       if entry.isDirectory():
         yield* walk(p)             ← delegate recursion
       else:
         yield p                     ← yield file
   
   Symlink cycle:
     /a/b → /a (loop).
     Track visited via fs.stat → inode.
     Skip already-visited.
   
   Concurrency:
     Naive: sequential readdir per dir.
     Concurrent: kick off readdirs in parallel; bound with semaphore.
     Memory: bounded by depth × concurrency.
   
   Backpressure: async iter is pull-based.
     Caller decides pace.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. How does `yield*` simplify recursion?
> 2. Why does symlink loop matter?
> 3. Sequential vs concurrent tradeoff?

---

## 6. Brute force — walked through

```js
// Sync collection — uses sync API, blocks event loop
const fs = require('node:fs');
function walkSync(dir, out = []) {
  for (const name of fs.readdirSync(dir, {withFileTypes: true})) {
    const p = path.join(dir, name.name);
    if (name.isDirectory()) walkSync(p, out);
    else out.push(p);
  }
  return out;
}
```

Sync blocks event loop on large trees. Bad in production.

---

## 7. The unlocking insight

> **`async function*` with `yield*` for recursion. Pull-based; caller paces. Track symlinks via inode set. Concurrency optional for speed.**

Three properties:

1. **`async function*` + `yield*`** for clean recursion.
2. **Pull-based** backpressure.
3. **Symlink cycles** via inode set.

---

## 8. Solution (annotated)

```js
import { readdir, stat } from 'node:fs/promises';
import path from 'node:path';

// Basic — sequential
async function* walk(dir) {
  let entries;
  try {
    entries = await readdir(dir, { withFileTypes: true });                  // step 1: read entries
  } catch (err) {
    if (err.code === 'EACCES' || err.code === 'EPERM') return;             // step 2: skip perm
    throw err;
  }
  for (const entry of entries) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      yield* walk(p);                                                      // step 3: delegate
    } else if (entry.isFile()) {
      yield p;
    }
    // skip symlinks/sockets/etc by default
  }
}

// With symlink cycle detection
async function* walkSafe(dir, visited = new Set()) {
  const s = await stat(dir);
  if (visited.has(s.ino)) return;                                          // step 4: cycle
  visited.add(s.ino);

  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) yield* walkSafe(p, visited);
    else if (entry.isFile()) yield p;
    // symlinks: follow via lstat to detect, then recurse with stat
  }
}

// Concurrent readdir with semaphore
async function* walkConcurrent(dir, { concurrency = 8 } = {}) {
  const queue = [dir];
  let active = 0;
  const pending = [];

  while (queue.length || active > 0) {
    while (queue.length && active < concurrency) {
      const d = queue.shift();
      active++;
      pending.push(
        readdir(d, { withFileTypes: true })
          .then((entries) => ({ d, entries }))
          .finally(() => active--)
      );
    }
    const { d, entries } = await Promise.race(pending);                    // step 5: race
    pending.splice(pending.indexOf(/* matching */), 1);
    for (const entry of entries) {
      const p = path.join(d, entry.name);
      if (entry.isDirectory()) queue.push(p);
      else if (entry.isFile()) yield p;
    }
  }
}

// Node 20+ built-in
import { readdir as readdirNew } from 'node:fs/promises';
const all = await readdirNew('/dir', { recursive: true });                // step 6: native
```

**Try it yourself**

```js
// Find all .js files
for await (const f of walk('/path')) {
  if (f.endsWith('.js')) console.log(f);
}

// Count files
let count = 0;
for await (const _ of walk('/path')) count++;

// Bounded memory (yield, don't collect)
const stream = walk('/path');
const first10 = [];
for await (const f of stream) {
  first10.push(f);
  if (first10.length === 10) break;     // stop early
}

// Combine with predicate
async function* walkFiltered(dir, pred) {
  for await (const f of walk(dir)) {
    if (pred(f)) yield f;
  }
}

// Production: handle errors per dir
async function* walkRobust(dir) {
  try {
    for await (const f of walk(dir)) yield f;
  } catch (err) {
    console.warn(`Error in ${dir}:`, err.code);
  }
}
```

---

## 9. Step-by-step dry run

```
walk('/a'):
  readdir('/a') → ['b', 'file1.txt'] (b is dir).
  entry 'b': isDirectory → yield* walk('/a/b'):
    readdir('/a/b') → ['file2.txt'].
    entry 'file2.txt': isFile → yield '/a/b/file2.txt'.
  entry 'file1.txt': isFile → yield '/a/file1.txt'.

Consumer for await:
  Pull → /a/b/file2.txt.
  Pull → /a/file1.txt.
  Pull → done.

Symlink loop:
  /a/symlink → /a.
  Without cycle detection: walk('/a') → walk('/a/symlink/...') → walk('/a/symlink/symlink/...') → infinite.
  
  With cycle: stat(/a/symlink) has inode of /a. visited.has → return.

Concurrent vs sequential:
  Tree with 100 dirs, 10ms readdir each.
  Sequential: 1000ms.
  Concurrent (8): ~125ms.
  Benefit grows with depth × breadth.

  Memory:
    Sequential: O(depth) (one path in stack).
    Concurrent: O(concurrency × depth).
```

---

## 10. Common confusion + traps

1. **`readdirSync`** blocks event loop.
2. **No perm error skip** — entire walk aborts.
3. **No cycle detection** — infinite on symlinks.
4. **`shift()` for queue** — O(n); use circular buffer or arr.length linear scan.
5. **Concurrent without bounds** — open file descriptor explosion.
6. **Native `{recursive: true}` Node 20+** — preferred for simple use.
7. **`isSymbolicLink`** — handle explicitly.

---

## 11. Senior follow-ups & variants

### Variant 1 — Node 20+ `readdir({recursive: true})`
Native; eager array.

### Variant 2 — Filter predicate
Compose with async generator.

### Variant 3 — Parallel with worker pool
Distribute readdir across workers.

### Variant 4 — Glob matching
Use `picomatch` or `minimatch` for patterns.

### Variant 5 — Path collection vs stream
Stream avoids OOM on huge trees.

---

## 12. How to think aloud

> "Async directory walker is the canonical async-generator + recursion problem. `async function* walk(dir)`: read entries via `await readdir(dir, {withFileTypes: true})`, iterate; if directory, `yield* walk(p)` (delegate recursion); if file, `yield p`. Pull-based — caller paces via `for await`. Handle EACCES/EPERM by skipping the dir (or throwing — define policy). Symlink cycles: track visited inodes via `fs.stat(dir).ino` in a Set; skip revisited. Concurrency: naive recursion is sequential per branch; for I/O-bound walks on slow filesystems (network, S3 prefixes), kick off multiple `readdir`s in parallel via a semaphore — bounded by `concurrency` parameter. Memory: sequential is O(depth); concurrent is O(concurrency × depth). Node 20+ has native `readdir(dir, {recursive: true})` — eager array; great for simple cases but not lazy. Variants: filter predicate (compose generators), worker-pool parallel, glob matching (picomatch). Trap: readdirSync (blocks); no perm error skip (entire walk aborts); no cycle detection (infinite on symlink loops); fd explosion without concurrency bounds."

---

## 13. 60-second revision

> - **`async function*` + `yield*`** clean recursion.
> - **Pull-based** backpressure.
> - **Catch EACCES/EPERM** — skip or throw policy.
> - **Symlink cycles** — inode Set.
> - **Concurrency** via bounded semaphore.
> - **Node 20+ `{recursive: true}`** native eager.
> - **Stream over collect** for huge trees.
> - **Trap:** sync API blocks; no cycle/perm handling; fd explosion.

---

**Related:** [`06-streams/async-iterator-pagination.md`](../06-streams/async-iterator-pagination.md) · [`06-streams/file-line-reader-with-backpressure.md`](../06-streams/file-line-reader-with-backpressure.md) · [tree-bfs-dfs.md](./tree-bfs-dfs.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md), [`concepts/streams.md`](../../concepts/streams.md)
