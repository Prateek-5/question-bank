# BFS with Bounded Concurrency (Web Crawl / Graph Walk)

## Source / Origin
- Classic web-crawler interview question.
- Asked at: Google, Cloudflare, Atlassian, Razorpay, Booking.
- Concept reference: `concepts/recursion.md`, sibling `async-pool.md`, `async-semaphore.md`.

## Why this question matters in interviews
"Crawl this site, but don't fire more than 10 fetches at once" is the canonical async-graph problem. Pure BFS uses a queue and processes one node at a time — too slow. Pure `Promise.all` on all neighbors — explodes when fanout is wide. The right answer combines a queue + visited set + semaphore. Senior bar: you reason about visited-state races, depth limit, cycle handling, error per node vs error per crawl.

## Concepts involved

### Syntax to lock in
```js
async function bfsConcurrent(startUrl, { concurrency = 10, maxDepth = 5, fetcher, getNeighbors }) {
  const visited = new Set([startUrl]);
  const queue = [{ url: startUrl, depth: 0 }];
  let active = 0;

  return new Promise((resolve, reject) => {
    const results = new Map();
    const errors = new Map();

    const tryDrain = () => {
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
        if (depth < maxDepth) {
          for (const nb of getNeighbors(data)) {
            if (!visited.has(nb)) {
              visited.add(nb);             // mark BEFORE enqueue — prevents duplicate enqueue
              queue.push({ url: nb, depth: depth + 1 });
            }
          }
        }
      } catch (err) {
        errors.set(url, err);
      } finally {
        active--;
        tryDrain();
      }
    };

    tryDrain();
  });
}
```

### Edge cases / interview traps
1. **Mark visited BEFORE enqueue, not after fetch.** If you mark after, two parallel fetches discover the same neighbor and both enqueue it.
2. **Cycles** — the visited set handles them; without it, BFS loops forever.
3. **Depth limit** — must check at the enqueue site, not the fetch site (otherwise you fetch a depth-N+1 node only to discard).
4. **Error policy.** One bad URL shouldn't kill the crawl. Capture per-URL errors.
5. **"Same canonical URL"** — `http://x.com/foo` vs `http://x.com/foo/` vs `http://x.com/foo?utm=...`. Canonicalize before adding to visited.
6. **Robots.txt + rate limit per-host** — production crawlers need a per-host semaphore on top of global concurrency.
7. **Memory** — visited set can be huge; for billion-page crawls use Bloom filter (false positives ok = "we might miss a page").
8. **Backpressure** — if `queue.length` grows unboundedly, you OOM. Bound the queue with a watermark.

## Mental Model

**BFS = a wave that expands one ring at a time**. With concurrency, the wave's "front" is the queue; the semaphore (`active < concurrency`) decides how many we process from the front simultaneously.

```
   start: A → enqueue
   tick 1: dequeue A, fetch A (active=1)
            A's neighbors: B, C, D  → mark visited; enqueue
   tick 2: drain queue while active<concurrency
            dequeue B (active=2); dequeue C (active=3); dequeue D (active=4)
            fetch B, C, D in parallel
   tick 3: B's neighbors: E, F  → enqueue
            C's neighbors: E (visited; skip), G
            D's neighbors: H
            queue = [E, F, G, H]
            ... continue draining as active<concurrency
```

## Why interviewers care

- **Async + graph algorithm** — twin signals in one question.
- **Race condition awareness** — mark-before-enqueue is the classic trap.
- **Production realism** — depth limit, error per node, canonicalization.

## Common beginner confusion

- **"Use `Promise.all` on each level."** Levels with one slow node stall the whole level. With semaphore-based draining, fast neighbors keep flowing.
- **"Recurse instead of queue."** Stack overflow on deep graphs; harder to bound concurrency.
- **"Use plain `for...of` with await."** That's sequential — concurrency = 1.
- **"Visited set is enough."** Not without canonicalization; same logical URL with different query strings causes loops.
- **"Mark visited after fetch."** Race — two fetches enqueue the same neighbor.

## Brute force approach

```js
async function crawl(url, depth, visited = new Set()) {
  if (visited.has(url) || depth > maxDepth) return;
  visited.add(url);
  const data = await fetch(url);
  for (const nb of neighbors(data)) await crawl(nb, depth + 1, visited);
}
```

DFS, sequential, slow. Hammers a single host (no concurrency control).

## Optimal approach

Queue + visited set + semaphore-style concurrency gate. Mark visited before enqueue. Process in parallel up to `concurrency`. Collect results and errors as maps keyed by URL.

## Solution (JavaScript)

```js
async function bfsConcurrent(startUrl, {
  concurrency = 10,
  maxDepth = 5,
  fetcher,                      // async (url) => data
  getNeighbors,                 // (data) => string[]
  canonicalize = (u) => u,
  signal,
} = {}) {
  const start = canonicalize(startUrl);
  const visited = new Set([start]);
  const queue = [{ url: start, depth: 0 }];
  let active = 0;
  const results = new Map();
  const errors = new Map();
  return new Promise((resolve, reject) => {
    let cancelled = false;
    if (signal) signal.addEventListener('abort', () => { cancelled = true; resolve({ results, errors, aborted: true }); }, { once: true });

    const drain = () => {
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
        if (depth < maxDepth) {
          for (const raw of getNeighbors(data)) {
            const nb = canonicalize(raw);
            if (!visited.has(nb)) {
              visited.add(nb);
              queue.push({ url: nb, depth: depth + 1 });
            }
          }
        }
      } catch (err) {
        errors.set(url, err);
      } finally {
        active--;
        drain();
      }
    };
    drain();
  });
}

// Usage
const { results, errors } = await bfsConcurrent('https://example.com', {
  concurrency: 10,
  maxDepth: 3,
  fetcher: (u) => fetch(u).then(r => r.text()),
  getNeighbors: (html) => Array.from(html.matchAll(/href="([^"]+)"/g)).map(m => m[1]),
  canonicalize: (u) => new URL(u).origin + new URL(u).pathname,
});
```

## Step-by-step dry run

Graph: A → {B, C, D}; B → {E, F}; C → {E, G}; D → {H}. `concurrency=2, maxDepth=3`.

```
t=0   queue=[A]; drain → process A (active=1)
                  drain: active<2 but queue empty → stop
t=0+f A done → results[A]=...; neighbors B,C,D → mark visited; queue=[B,C,D]
      active--; drain → process B (active=1), process C (active=2)
                       queue=[D]
t=...  B done → neighbors E,F → mark; queue=[D,E,F]
       active--; drain → process D (active=2); queue=[E,F]
t=...  C done → neighbors E (visited, skip), G → mark G; queue=[E,F,G]
       active--; drain → process E (active=2); queue=[F,G]
t=...  ...continues until queue empty AND active=0 → resolve
```

Concurrency capped at 2. No duplicate fetches even with shared neighbor E.

## How to think aloud in the interview

> "BFS with a queue and visited set. Mark visited BEFORE enqueue — that's the race trap. A gate function drains the queue up to `concurrency` parallel. Each task in `finally` decrements active and calls drain again, so as soon as one finishes a new one starts. Errors go into a per-URL map; the crawl continues. For production: per-host rate limit on top, robots.txt respect, canonicalize URLs, bloom filter visited for billion-scale. AbortSignal threading for graceful stop."

## Important takeaways

- **Visited.add BEFORE queue.push.** Non-negotiable.
- **Drain on every completion.** Keeps active count near `concurrency`.
- **Canonicalize URLs.** Else infinite-loop on `?utm=...` variants.
- **Per-host semaphore** layered on global concurrency for production.
- **Errors per-node, not per-crawl.**

## Variants

- **Per-host concurrency** — a Map<host, Semaphore>; each fetch acquires from both global and per-host.
- **DFS variant** — depth-first walks; same shape, queue → stack.
- **Async-iterator emitter** — yield results as they arrive instead of collecting into a Map.
- **Bloom filter visited** — for billion-page crawls; tolerate ~0.01% missed pages.
- **Frontier persistence** — for crawls that span hours, persist queue/visited to disk so a crash resumes.

## Revision notes

```
bfsConcurrent(start, concurrency, maxDepth, fetcher, neighbors):
  visited = Set([start]); queue = [{start, 0}]; active = 0
  drain():
    while active < concurrency and queue.length:
      task = queue.shift(); active++; process(task)
    if active==0 and queue.empty → resolve
  process(url, depth):
    try fetch; for each nb: if !visited: visited.add(nb); queue.push
    catch errors[url] = err
    finally active--; drain()
  
  mark visited BEFORE enqueue (race fix)
  canonicalize URLs
  per-host semaphore in production
  Bloom filter visited at billion scale
```
