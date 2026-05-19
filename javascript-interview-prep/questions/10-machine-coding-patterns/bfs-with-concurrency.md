# BFS with Bounded Concurrency — async graph walk

> **Difficulty:** Senior   |   **Time:** ~25 min   |   **Prereqs:** [async-pool.md](./async-pool.md), [`09-recursion/bfs-dfs-iterative.md`](../09-recursion/bfs-dfs-iterative.md)
>
> **Source:** Web crawler classic. Google, Cloudflare, Atlassian, Razorpay, Booking.

---

## 1. Problem statement

**Signature**
```ts
function bfsConcurrent(startUrl: string, opts: {
  concurrency?: number;
  maxDepth?: number;
  fetcher: (url) => Promise<any>;
  getNeighbors: (data) => string[];
  canonicalize?: (url) => string;
  signal?: AbortSignal;
}): Promise<{ results: Map<string, any>; errors: Map<string, Error> }>;
```

**Input / Output examples**

| Setup (concurrency=10, maxDepth=3)                    | Behaviour                                              |
|--------------------------------------------------------|---------------------------------------------------------|
| Graph: A→{B,C,D}; B→{E,F}; C→{E,G}; D→{H}              | each visited once; E not fetched twice                 |
| One URL throws                                          | error recorded; crawl continues                        |
| Cycle A→B→A                                             | visited set prevents infinite loop                     |
| Depth limit reached                                      | leaf URLs fetched; their neighbors skipped             |
| `signal.abort()`                                        | running tasks drain; resolves with `aborted: true`     |

**Constraints**
- Visited set + queue + bounded concurrency.
- **Mark visited BEFORE enqueue** (race fix).
- Depth check at enqueue site (not fetch site).
- Errors per node, not per crawl.
- Canonicalize URLs (deduplicate `?utm=...` variants).

---

## 2. Plain-English restatement

Crawl a graph (web pages, social network, dependency tree) breadth-first but with at most N concurrent fetches. Pure BFS one-at-a-time is too slow; `Promise.all` on all neighbors explodes on wide fanout. The right answer: queue + visited set + concurrency gate that drains as workers complete.

---

## 3. Why this matters in interviews

The canonical async-graph problem. Probes async + graph algorithm + race-condition awareness (mark-before-enqueue is the classic trap) + production realism (depth limit, error policy, canonicalization).

---

## 4. Mental model

```
   concurrency=2, maxDepth=3, graph A→{B,C,D}; B→{E,F}; C→{E,G}; D→{H}

   t=0   queue=[A]; drain → process A (active=1); queue empty → stop draining
   t=0   A done → neighbors=B,C,D → mark visited; queue=[B,C,D]
         active=0; drain → process B, process C (active=2). queue=[D]
   ...  B done → neighbors=E,F → mark; queue=[D,E,F]
         drain → process D (active=2); queue=[E,F]
   ...  C done → neighbors=E (visited, skip), G → mark G; queue=[E,F,G]
         drain → process E (active=2); queue=[F,G]
   ...  process F, then G, then H. Each fetch ≤ depth limit.

   Two key tricks:
   1. mark visited BEFORE enqueue (or two parallel fetches dup-enqueue same neighbor)
   2. drain on every completion (keeps active near `concurrency`)
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why mark visited BEFORE enqueue, not after fetch?
> 2. What's wrong with `Promise.all` on each BFS level?
> 3. Why canonicalize URLs?

---

## 6. Brute force — walked through

### Wrong attempt 1: sequential BFS
`for...of` with `await`. Concurrency = 1. Slow.

### Wrong attempt 2: `Promise.all` on each level
Levels with one slow node stall whole level. Semaphore-style drain keeps fast nodes flowing.

### Wrong attempt 3: mark visited AFTER fetch
Two parallel fetches discover same neighbor → both enqueue → duplicate work. Mark BEFORE enqueue.

### Wrong attempt 4: no canonicalization
`http://x.com/page` and `http://x.com/page?utm=campaign` look distinct → infinite loop on tracking params.

---

## 7. The unlocking insight

> **Queue + visited Set + concurrency gate. On each `process` completion: decrement active, call `drain` again — keeps active count near `concurrency`. Mark visited BEFORE enqueue to prevent race-duplicates. Errors per-URL in a Map; crawl continues.**

Three properties:

1. **Mark-before-enqueue** — race fix.
2. **Drain-on-completion** — keeps the conveyor full.
3. **Per-URL errors** — one bad node doesn't kill the crawl.

---

## 8. Solution (annotated)

```js
async function bfsConcurrent(startUrl, {
  concurrency = 10,
  maxDepth = 5,
  fetcher,
  getNeighbors,
  canonicalize = (u) => u,
  signal,
} = {}) {
  const start = canonicalize(startUrl);
  const visited = new Set([start]);                                  // step 1: race-protected
  const queue = [{ url: start, depth: 0 }];
  let active = 0;
  const results = new Map();
  const errors = new Map();

  return new Promise((resolve) => {
    let cancelled = false;
    if (signal) signal.addEventListener('abort', () => {
      cancelled = true;
      resolve({ results, errors, aborted: true });
    }, { once: true });

    const drain = () => {                                             // step 2: keep conveyor full
      if (cancelled) return;
      while (active < concurrency && queue.length > 0) {
        const { url, depth } = queue.shift();
        active++;
        process(url, depth);
      }
      if (active === 0 && queue.length === 0) resolve({ results, errors });
    };

    const process = async (url, depth) => {
      try {
        const data = await fetcher(url);
        results.set(url, data);
        if (depth < maxDepth) {                                        // step 3: depth check at enqueue
          for (const raw of getNeighbors(data)) {
            const nb = canonicalize(raw);                              // step 4: canonicalize
            if (!visited.has(nb)) {
              visited.add(nb);                                          // step 5: MARK BEFORE enqueue
              queue.push({ url: nb, depth: depth + 1 });
            }
          }
        }
      } catch (err) {
        errors.set(url, err);                                           // step 6: per-URL error
      } finally {
        active--;
        drain();                                                         // step 7: re-drain
      }
    };

    drain();
  });
}
```

**Try it yourself**

```js
const ac = new AbortController();

const { results, errors } = await bfsConcurrent('https://example.com', {
  concurrency: 10,
  maxDepth: 3,
  fetcher: (u) => fetch(u).then((r) => r.text()),
  getNeighbors: (html) => Array.from(html.matchAll(/href="([^"]+)"/g)).map((m) => m[1]),
  canonicalize: (u) => {
    const x = new URL(u);
    return x.origin + x.pathname;                                     // strip query for dedup
  },
  signal: ac.signal,
});

setTimeout(() => ac.abort(), 30_000);                                  // 30s budget
```

---

## 9. Step-by-step dry run

```
Graph A→{B,C,D}; B→{E,F}; C→{E,G}; D→{H}. concurrency=2.

t=0    queue=[A]; drain → process A (active=1). queue empty.
       drain: 2nd iteration → active<2 but queue empty → no spawn.

t=0+ε  A done → neighbors B,C,D → mark visited; queue=[B,C,D].
       active=0. drain → process B (active=1), process C (active=2). queue=[D].

t=80   B done → neighbors E,F → mark; queue=[D,E,F].
       active=1. drain → process D (active=2). queue=[E,F].

t=100  C done → neighbors E (visited! skip), G → mark G; queue=[D-still-active waiting, E, F, G]
       wait, D is still active. Let me redo: D was started so queue=[E,F,G].
       active=1 (D still running). drain → process E (active=2). queue=[F,G].

...continues until queue empty and active=0 → resolve.

Concurrency cap respected; E fetched ONCE despite being a neighbor of both B and C.
```

---

## 10. Common confusion + traps

1. **Mark visited AFTER fetch** — race; duplicates enqueued.
2. **`Promise.all` per level** — stragglers stall.
3. **No canonicalization** — infinite-loop on tracking params.
4. **Plain `for await`** — sequential; concurrency=1.
5. **Recursive crawl** — stack overflow on deep graphs; can't bound concurrency.
6. **Depth check at fetch site** — wastes a fetch for depth N+1.
7. **No per-host limit** — hammers a single host. Add per-host semaphore in production.

---

## 11. Senior follow-ups & variants

### Variant 1 — Per-host concurrency
`Map<host, Semaphore>`; each fetch acquires from BOTH global and per-host.

### Variant 2 — DFS variant
Same shape; queue → stack. (But careful — async DFS doesn't have BFS's "shortest path" property.)

### Variant 3 — Async-iterator emitter
Yield results as they arrive instead of collecting into Map. Streams huge crawls.

### Variant 4 — Bloom filter visited
For billion-page crawls; tolerate ~0.01% missed pages.

### Variant 5 — Frontier persistence
For crawls that span hours, persist queue/visited to disk so a crash resumes.

### Variant 6 — Robots.txt + rate limit per-host
Production crawlers respect robots.txt and add per-host token bucket.

---

## 12. How to think aloud

> "BFS with a queue and visited set, bounded by concurrency. `process(url, depth)`: fetch, record result, mark neighbors visited BEFORE enqueue (race fix), enqueue with depth+1 if under limit. In `finally`: decrement active, call `drain()` again — keeps conveyor full. Errors per-URL in a Map; crawl continues. For production: per-host semaphore on top of global, robots.txt, canonicalize URLs (strip tracking params), Bloom filter visited at billion-scale, AbortSignal for budget cap. Trap: mark visited after fetch (race); no canonicalization (infinite loop on `?utm=`); `Promise.all` per level (stragglers); plain `for await` (concurrency=1)."

---

## 13. 60-second revision

> - **Queue + visited Set + concurrency gate.**
> - **Mark visited BEFORE enqueue** (race fix).
> - **Drain on every `finally`** — keeps active count near concurrency.
> - **Canonicalize URLs** — strip tracking params.
> - **Depth check at enqueue site** (not fetch).
> - **Errors per-URL** in Map; crawl continues.
> - **Production:** per-host semaphore, robots.txt, Bloom filter visited, AbortSignal budget.
> - **Variants:** DFS, async-iterator emitter, frontier persistence.
> - **Trap:** mark-after-fetch race; no canonicalization; `Promise.all` per level; sequential await.

---

**Related:** [async-pool.md](./async-pool.md) · [async-semaphore.md](./async-semaphore.md) · [`09-recursion/bfs-dfs-iterative.md`](../09-recursion/bfs-dfs-iterative.md) · [rate-limiter-token-bucket.md](./rate-limiter-token-bucket.md)

**Concept primer:** [`concepts/recursion.md`](../../concepts/recursion.md)
