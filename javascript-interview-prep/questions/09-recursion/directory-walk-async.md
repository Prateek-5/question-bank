# Async Directory Walker

## Source / Origin
- `node:fs/promises.readdir({withFileTypes:true, recursive:true})`; classic tool-building question.
- Asked at: Razorpay, Atlassian, Cloudflare (CLI/dev-tool shops).
- Concept reference: `concepts/recursion.md`, sibling `06-streams/file-line-reader-with-backpressure.md`.

## Why this question matters in interviews
"Walk this directory tree, return all files matching X." Tests async recursion, error handling for unreadable dirs, concurrency control. Senior bar: you use async iterators for streaming, bound concurrency, and skip symlink cycles.

## Concepts involved

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

### Edge cases / traps
1. **Permission errors** — `EACCES`/`EPERM`; decide skip-or-throw.
2. **Symlink loops** — track visited inodes (`fs.stat`) to avoid.
3. **Concurrency** — naive recursion is sequential per branch; with a worker pool, parallel readdir of subdirs is much faster on slow filesystems.
4. **Backpressure** — async generators handle it; pull-based.
5. **`recursive: true`** flag on `readdir` (Node 20+) — built-in, simpler.
6. **Hidden files** — `.git`, `.DS_Store`; document policy.
7. **Memory** — yielding is constant; collecting into array is O(n).
8. **`isFile` vs `isDirectory` vs `isSymbolicLink`** — three different checks.

## Mental Model

```
   walk(dir):
     readdir(dir) → entries
     for each entry:
       if dir → recurse walk(subdir)
       if file → yield path
   
   for await consumes:
     pull-based; readdir paused while consumer is busy
```

## Solution

```js
import { readdir, stat } from 'node:fs/promises';
import path from 'node:path';

async function* walk(root, {
  followSymlinks = false,
  filter = () => true,
  onError = (err, p) => { /* default: skip */ },
} = {}) {
  const seen = new Set();
  async function* recurse(dir) {
    let entries;
    try { entries = await readdir(dir, { withFileTypes: true }); }
    catch (e) { onError(e, dir); return; }
    for (const entry of entries) {
      const p = path.join(dir, entry.name);
      try {
        if (entry.isSymbolicLink()) {
          if (!followSymlinks) continue;
          const real = await stat(p);
          if (seen.has(real.ino)) continue;
          seen.add(real.ino);
          if (real.isDirectory()) yield* recurse(p);
          else if (real.isFile() && filter(p)) yield p;
        } else if (entry.isDirectory()) {
          yield* recurse(p);
        } else if (entry.isFile() && filter(p)) {
          yield p;
        }
      } catch (e) { onError(e, p); }
    }
  }
  yield* recurse(root);
}

// Usage
for await (const f of walk('/repo', { filter: f => f.endsWith('.js') })) {
  console.log(f);
}

// Concurrent walker (faster on slow filesystems)
async function walkConcurrent(root, { concurrency = 10, filter = () => true } = {}) {
  const results = [];
  const queue = [root];
  let active = 0;
  let idx = 0;
  await new Promise((resolve, reject) => {
    const drain = async () => {
      while (active < concurrency && idx < queue.length) {
        const dir = queue[idx++]; active++;
        readdir(dir, { withFileTypes: true })
          .then(entries => {
            for (const e of entries) {
              const p = path.join(dir, e.name);
              if (e.isDirectory()) queue.push(p);
              else if (e.isFile() && filter(p)) results.push(p);
            }
          })
          .catch(() => {})
          .finally(() => { active--; if (active === 0 && idx >= queue.length) resolve(); else drain(); });
      }
    };
    drain();
  });
  return results;
}

// Node 20+ shortcut
import { readdir } from 'node:fs/promises';
const files = await readdir('/repo', { recursive: true, withFileTypes: true });
// files is flat list of Dirent; filter as needed
```

## Dry run

```
/root
├── a.js
├── b/
│   ├── c.js
│   └── d.js
└── e.txt

walk('/root'):
  readdir → [a.js, b/, e.txt]
  yield '/root/a.js'
  recurse '/root/b':
    readdir → [c.js, d.js]
    yield '/root/b/c.js'
    yield '/root/b/d.js'
  yield '/root/e.txt'

consumer for await: receives 4 paths in order
```

## How to think aloud

> "Async generator: `walk(dir)` reads dir entries, recurses on subdirs, yields files. `for await` consumes pull-based — natural backpressure. Add: filter predicate, error handler (skip unreadable dirs), symlink loop detection via inode Set. For perf on slow FS, use bounded-concurrency variant — parallel readdir of subdirs. Node 20+ has `readdir({recursive:true})` built-in but doesn't expose backpressure."

## Important takeaways

- **Async generator** for streaming, backpressure-aware.
- **`for await` + `yield*`** for recursion.
- **Error policy** — `onError(err, path)` callback; default skip.
- **Symlink loops** — track inode Set.
- **Concurrency for perf** — bounded async pool of readdir calls.
- **Node 20+**: `readdir({recursive:true})` shortcut.

## Variants

- **Glob** — `fast-glob`, `globby` libraries.
- **`fdir`** — bundle of optimized walkers.
- **`fs.opendir`** — iterable handle, lower-level.
- **Watch mode** — `fs.watch` for incremental changes.

## Revision notes

```
walk(dir):
  async function* walk(dir):
    entries = await readdir(dir, {withFileTypes:true})
    for e of entries:
      p = path.join(dir, e.name)
      if e.isDirectory(): yield* walk(p)
      else if e.isFile(): yield p

for await (file of walk(root)): consume one at a time (pull-based)

OPTIONS:
  filter predicate
  onError (skip vs throw)
  followSymlinks + inode Set (loop detection)
  concurrency (bounded readdir pool)

Node 20+: readdir(path, {recursive:true, withFileTypes:true})

MEMORY: yielding constant; collecting → O(n)
```
