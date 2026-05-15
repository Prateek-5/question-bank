# Recursion

## TL;DR
- Recursion = a function that calls itself, building a chain of pending frames on the call stack.
- V8 stack limit is **~10–15k frames** depending on local-var size (default ~984KB stack). Hit it → `RangeError: Maximum call stack size exceeded`.
- **JS does NOT implement Tail Call Optimization (TCO)** in any major engine despite ES2015 specifying it (Safari briefly did). Deep recursion → blow the stack.
- Convert deep recursion to: **iteration**, **explicit stack/queue**, or **trampolining** (return thunks, drive in a loop).
- Use **memoization** (Map/WeakMap) to turn exponential recursion (Fibonacci, overlapping subproblems) into polynomial.

## Why backend interviewers care
- Tree/graph traversal shows up everywhere: directory walks, JSON traversal, dependency graphs, permission trees, comment threads.
- DFS vs BFS choice, cycle detection, and memoization are core to many real backend tasks (resolver chains, GraphQL traversal).
- Stack overflow in prod from recursive deserialization or JSON walks is a common Node post-mortem item.

## Core mental model
Each recursive call pushes a stack frame holding the locals, return address, and `this`. When the base case returns, frames pop one by one. The depth × frame-size must fit within the V8 stack (~1MB by default, configurable via `--stack-size`).

```js
function fact(n) {
  if (n <= 1) return 1;
  return n * fact(n - 1);   // not a tail call: multiplication after return
}
```

Even if you rewrite as a *true* tail call (`return helper(n - 1, acc * n)`), V8 doesn't fold the frame. So **tail recursion in JS still overflows** on deep input.

**Two recursive patterns**:
1. **Linear recursion** — fact, sum, list traversal. Depth = n.
2. **Branching recursion** — tree DFS, fibonacci. Depth = tree height (log n if balanced) or n in pathological cases.

**Memoization** transforms exponential branching into linear:
```js
const memo = new Map();
function fib(n) {
  if (n < 2) return n;
  if (memo.has(n)) return memo.get(n);
  const v = fib(n - 1) + fib(n - 2);
  memo.set(n, v);
  return v;
}
```

**Iterative conversion** when depth is the bottleneck:
- Use an explicit `stack = [root]` array → DFS.
- Use a `queue` (array with shift, or a real Deque) → BFS.

**Trampolining** for tail-recursive algorithms:
```js
const trampoline = (fn) => (...args) => {
  let result = fn(...args);
  while (typeof result === "function") result = result();
  return result;
};
const sum = trampoline(function f(n, acc = 0) {
  return n === 0 ? acc : () => f(n - 1, acc + n);
});
sum(1e6); // works
```

## Syntax cheat sheet
```js
// Classic recursion
function fact(n) { return n <= 1 ? 1 : n * fact(n - 1); }

// Recursion with default acc
function sum(arr, i = 0) {
  return i === arr.length ? 0 : arr[i] + sum(arr, i + 1);
}

// Mutual recursion
const isEven = n => n === 0 ? true  : isOdd(n - 1);
const isOdd  = n => n === 0 ? false : isEven(n - 1);

// Tree DFS (recursive)
function dfs(node, visit) {
  visit(node);
  for (const child of node.children) dfs(child, visit);
}

// Tree DFS (iterative — stack)
function dfsIter(root, visit) {
  const stack = [root];
  while (stack.length) {
    const n = stack.pop();
    visit(n);
    for (let i = n.children.length - 1; i >= 0; i--) stack.push(n.children[i]);
  }
}

// Tree BFS (iterative — queue)
function bfs(root, visit) {
  const q = [root];
  while (q.length) {
    const n = q.shift();          // O(n) shift — use a real deque for large trees
    visit(n);
    q.push(...n.children);
  }
}

// JSON deep walk
function walk(value, fn, path = []) {
  fn(value, path);
  if (value && typeof value === "object") {
    for (const [k, v] of Object.entries(value)) walk(v, fn, [...path, k]);
  }
}

// Memoize a recursive fn (decorator style)
const memoize = (fn) => {
  const cache = new Map();
  return function rec(n) {
    if (cache.has(n)) return cache.get(n);
    const v = fn(rec, n);   // pass `rec` so internal calls hit cache
    cache.set(n, v);
    return v;
  };
};
const fib = memoize((self, n) => n < 2 ? n : self(n - 1) + self(n - 2));

// Trampoline
const trampoline = (fn) => (...a) => {
  let r = fn(...a);
  while (typeof r === "function") r = r();
  return r;
};

// Async recursion (careful with stack — usually fine because await breaks it up)
async function walkDir(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const e of entries) {
    if (e.isDirectory()) await walkDir(path.join(dir, e.name));
    else handle(path.join(dir, e.name));
  }
}

// Cycle detection
function hasCycle(graph, start) {
  const seen = new Set();
  function dfs(node) {
    if (seen.has(node)) return true;
    seen.add(node);
    return graph[node].some(dfs);
  }
  return dfs(start);
}
```

## Edge cases & interview traps
1. **No TCO in V8** — even properly written tail-recursive code overflows on deep input.
2. **Default stack ~1MB** → ~10k frames for typical locals; `node --stack-size=N` (KB) can raise it.
3. **Async recursion does NOT use the JS call stack** between `await` points — each suspension resets the stack. Safe for deep walks.
4. **`Promise.all` recursion** can blow up memory by holding all pending promises — chunk with promise pool.
5. **`Array.prototype.shift()` is O(n)** — BFS with array as queue is O(n²); use a linked list or `denque` for big graphs.
6. **DFS recursive on cyclic graphs hangs** — always use a `Set` of visited nodes.
7. **Order of DFS visit**: pre-order vs post-order matters for dependency resolution (topological sort = post-order DFS).
8. **`JSON.stringify` is recursive internally** — large nested objects can throw `RangeError`.
9. **Recursive `clone` without cycle detection** infinite-loops on `obj.self = obj`.
10. **Memoization with object args** needs a serializer or `WeakMap` (only for single object arg).
11. **`for...in` walks the prototype chain** — recursive object walks should use `Object.keys`/`Object.entries` or `Reflect.ownKeys`.
12. **Tail-call form (return f(...))** still costs a frame in V8 — no magic.
13. **Recursive functions named in expressions** can self-reference even if outer name reassigned: `const x = function rec(){ rec(); };`.
14. **Mutual recursion ordering** with `const` arrow functions and TDZ — use function declarations or assign before use.
15. **`Array.flat(Infinity)` is recursive internally** — beware on deep arrays.
    ```js
    // A pathologically deep array: [[[[[[...]]]]]] can RangeError on flat(Infinity).
    let a = [1]; for (let i = 0; i < 20000; i++) a = [a]; // a.flat(Infinity) may throw.
    ```

## Interview worked examples

### Example 1 — Fibonacci (naive → memo → iterative)
**Asked as:** "Implement Fibonacci. Optimize."

I'd say: "Naive recursion is O(2ⁿ) — same subproblems recomputed. Memoization caches by `n`, dropping it to O(n) time, O(n) space. Iterative is O(n) time, O(1) space — typically what you ship."

```js
// O(2^n) — exponential
const fib = (n) => n < 2 ? n : fib(n-1) + fib(n-2);

// Memoized — O(n)
const fibMemo = (() => {
  const m = new Map();
  return function f(n) {
    if (n < 2) return n;
    if (m.has(n)) return m.get(n);
    const v = f(n-1) + f(n-2);
    m.set(n, v); return v;
  };
})();

// Iterative — O(n), O(1)
function fibIter(n) {
  let [a, b] = [0, 1];
  for (let i = 0; i < n; i++) [a, b] = [b, a + b];
  return a;
}
```

**What the interviewer is testing:** Spotting overlapping subproblems; converting recursion to iteration.
**Sharp follow-up they often ask:** "What's the stack depth of the naive version for n=40?" → 40 levels — fine; for n=10000, blow stack (no TCO).

### Example 2 — Deep clone with cycle detection via WeakMap
**Asked as:** "Write `deepClone(obj)` that handles cycles."

I'd say: "Recursively copy properties, but use a WeakMap to track originals → clones. Before recursing into an object, check the map — if seen, return the existing clone. This handles `a.self = a` and shared subgraph correctly."

```js
function deepClone(x, seen = new WeakMap()) {
  if (x === null || typeof x !== "object") return x;
  if (seen.has(x)) return seen.get(x);
  const out = Array.isArray(x) ? [] : {};
  seen.set(x, out);
  for (const k of Object.keys(x)) out[k] = deepClone(x[k], seen);
  return out;
}
const a = { x: 1 }; a.self = a;
deepClone(a);                    // works, no infinite loop
```

**What the interviewer is testing:** Cycle detection via auxiliary map; awareness that naive recursion infinite-loops on cycles.
**Sharp follow-up they often ask:** "Handle Dates, RegExps, Maps, Sets." → branch by `instanceof`; reconstruct with appropriate constructors before recursing into contents.

### Example 3 — Flatten an arbitrarily-nested array
**Asked as:** "Flatten `[1, [2, [3, [4]]]]` to `[1,2,3,4]` without `flat`."

I'd say: "Reduce: for each element, if it's an array, recurse and concat the result; otherwise concat the element. Recursion depth = array nesting depth — fine for normal inputs."

```js
function flatten(arr) {
  return arr.reduce(
    (acc, x) => acc.concat(Array.isArray(x) ? flatten(x) : x),
    [],
  );
}
flatten([1, [2, [3, [4]]]]); // [1, 2, 3, 4]
```

**What the interviewer is testing:** Recursion + reduce composition.
**Sharp follow-up they often ask:** "Iterative version?" → Use a stack, push children in reverse order when you see an array; pop and append otherwise.

### Example 4 — Tree DFS: recursive AND iterative
**Asked as:** "Visit every node of an n-ary tree in DFS order. Show both versions."

I'd say: "Recursive DFS is one-liner — visit, then recurse on each child. Iterative uses an explicit stack to avoid V8 stack overflow on deep trees. To preserve left-to-right order, push children in reverse."

```js
// Recursive
function dfs(node, visit) {
  visit(node);
  for (const c of node.children) dfs(c, visit);
}

// Iterative — safe for deep trees
function dfsIter(root, visit) {
  const stack = [root];
  while (stack.length) {
    const n = stack.pop();
    visit(n);
    for (let i = n.children.length - 1; i >= 0; i--) {
      stack.push(n.children[i]);
    }
  }
}
```

**What the interviewer is testing:** Recursion → iteration conversion using an explicit stack.
**Sharp follow-up they often ask:** "Convert to BFS." → swap stack for queue (`shift`/`push`, ideally a real deque) and remove the reverse-loop.

### Example 5 — Generate all valid parentheses
**Asked as:** "Generate all valid combinations of `n` pairs of parentheses."

I'd say: "Classic backtracking. Track open and close counts. Add `(` if open < n; add `)` if close < open. When length is 2n, push the result. Recursion depth is 2n — fine."

```js
function generateParens(n) {
  const out = [];
  function back(cur, open, close) {
    if (cur.length === 2 * n) { out.push(cur); return; }
    if (open  < n)     back(cur + "(", open + 1, close);
    if (close < open)  back(cur + ")", open,     close + 1);
  }
  back("", 0, 0);
  return out;
}
generateParens(3);
// ["((()))","(()())","(())()","()(())","()()()"]
```

**What the interviewer is testing:** Backtracking template; pruning invalid branches early.
**Sharp follow-up they often ask:** "Time complexity?" → Catalan number Cₙ — roughly 4ⁿ / n^1.5.

### Example 6 — Permutations
**Asked as:** "Return all permutations of an array of distinct integers."

I'd say: "Backtracking with a 'used' flag per index — pick an unused element, recurse, then mark unused on the way back (undo). Result count is n!; depth is n."

```js
function permutations(nums) {
  const out = [], used = new Array(nums.length).fill(false), cur = [];
  function back() {
    if (cur.length === nums.length) { out.push([...cur]); return; }
    for (let i = 0; i < nums.length; i++) {
      if (used[i]) continue;
      used[i] = true; cur.push(nums[i]);
      back();
      cur.pop(); used[i] = false;        // undo
    }
  }
  back();
  return out;
}
permutations([1, 2, 3]);
// [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]
```

**What the interviewer is testing:** Backtracking with explicit undo (the "make-undo" pattern).
**Sharp follow-up they often ask:** "What if input has duplicates?" → sort first; inside loop, skip `if (i > 0 && nums[i] === nums[i-1] && !used[i-1]) continue;`.

## Common machine-coding patterns
- **DFS iterative with stack** — when used: avoid stack overflow on deep trees. Sketch above.
- **BFS with proper queue** — when used: shortest path, level-order. Use a real deque for perf.
- **Memoized recursive (Fibonacci, edit distance, coin change)** — sketch above.
- **Trampoline for tail-recursive** — when used: deep linear recursion you can't convert easily. Sketch above.
- **Directory walker (async)** —
  ```js
  async function* walk(dir) {
    for (const d of await fs.readdir(dir, { withFileTypes: true })) {
      const p = path.join(dir, d.name);
      if (d.isDirectory()) yield* walk(p);
      else yield p;
    }
  }
  ```
- **Deep clone with cycle detection** —
  ```js
  function clone(x, seen = new WeakMap()) {
    if (x === null || typeof x !== "object") return x;
    if (seen.has(x)) return seen.get(x);
    const out = Array.isArray(x) ? [] : {};
    seen.set(x, out);
    for (const k of Object.keys(x)) out[k] = clone(x[k], seen);
    return out;
  }
  ```
- **Topological sort (post-order DFS)** —
  ```js
  function topo(graph) {
    const order = [], seen = new Set();
    function visit(n) {
      if (seen.has(n)) return;
      seen.add(n);
      for (const m of graph[n] || []) visit(m);
      order.push(n);
    }
    Object.keys(graph).forEach(visit);
    return order.reverse();
  }
  ```

## Backend-specific notes
Directory walks, dependency-graph resolution, GraphQL field resolvers, permission tree checks — all recursive. In Node, prefer **async generators** for streaming traversal (constant memory) over collecting everything into an array.

For deeply nested user JSON (webhooks, third-party APIs), defensive depth-limiting prevents DoS by malicious payloads:
```js
function walk(x, depth = 0) {
  if (depth > 100) throw new Error("too deep");
  // ...
}
```

For graph algorithms with cycles (build dependency, microservice traces), always carry a `Set` of visited nodes. For high-fan-out trees, prefer iterative with explicit stack to avoid V8 stack limits — Node default 1MB gives roughly 10k frames for trivial functions.

## 60-second revision (day-before)
```text
┌──────────────────────────────────────────────────────────┐
│ RECURSION — DAY-BEFORE CRAM                              │
├──────────────────────────────────────────────────────────┤
│ • V8 stack ~1MB → ~10k frames; no TCO in any major JS    │
│ • Convert deep recursion → iteration with explicit stack │
│ • Trampoline: return () => f(...) until non-fn result    │
│ • DFS iterative: stack.push(...); pop, push children     │
│ • BFS iterative: queue.shift() — O(n²) array → deque     │
│ • Always visited Set on graphs (cycles)                  │
│ • Topological sort = post-order DFS reversed             │
│ • Memoize w/ Map (primitive keys) or WeakMap (obj key)   │
│ • async recursion safe — await resets sync stack         │
│ • clone with WeakMap to handle cycles                    │
│ • for...in walks prototype; use Object.keys/entries      │
│ • node --stack-size=N (KB) bumps limit                   │
│ • depth-limit user JSON to prevent DoS                   │
│ • async generators for streaming dir walks               │
│ • mutual recursion → function decls, not const arrows    │
└──────────────────────────────────────────────────────────┘
```
