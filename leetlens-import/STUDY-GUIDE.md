# LeetLens Study Guide — A Sequenced Path Through 785 Interview Questions

> **Audience:** a candidate preparing for engineering interviews who wants a structured, prerequisite-respecting path through this question set — not a random shuffle.
> **Source data:** `processed.extracted_questions` in the LeetLens Postgres DB (snapshot **2026-05-31**), 905 LLM-extracted real-interview questions. This guide covers the **785 DSA + LLD + HLD** rows; the remaining 120 (System Design freeform, Behavioral, Other) are out of scope.
> **How this guide differs from the per-category files:** [`DSA-questions.md`](./DSA-questions.md), [`LLD-questions.md`](./LLD-questions.md), [`HLD-questions.md`](./HLD-questions.md) catalogue questions WITHIN each vertical. This file orchestrates them ACROSS verticals — what to study first, what depends on what, and how to budget your time.

---

## 1. The big picture — what's in the dataset

| Vertical | Questions | Easy | Medium | Hard | What it tests |
|---|---:|---:|---:|---:|---|
| **DSA** | 302 | 79 | 134 | 89 | Algorithmic problem-solving — arrays → graphs → DP |
| **LLD** | 146 | 0 | 96 | 50 | OOD + design patterns — "design a parking lot / rate limiter / chess game" |
| **HLD** | 337 | 0 | 104 | 233 | System architecture — "design Twitter / Uber / a URL shortener" |
| **Sum** | **785** | **79** | **234** | **372** | |

Two structural facts worth holding in your head:

1. **There are no Easy LLD or HLD questions.** Every LLD and HLD interview question in this set is Medium or Hard — these are inherently open-ended design questions, not coding puzzles.
2. **HLD is Hard-heavy** (69% Hard). Treat HLD like senior-bar prep — you'll spend longer per question than DSA.

---

## 2. Three pillars, three different study mentalities

| Vertical | Study mentality | Pace | Tooling |
|---|---|---|---|
| **DSA** | Speed-and-pattern recognition — solve 300 patterns until they feel familiar | 2–4 questions/day | Whiteboard, IDE, [`bosscode-dsa-notes`](../DSA/) for reference cards |
| **LLD** | "Can I draw this class diagram and defend the patterns I picked?" — quality over quantity | 1 question/day; spend 60–90 min | Pen + paper class diagrams, then code skeleton |
| **HLD** | "Can I sketch a 3-layer architecture and reason about the bottlenecks?" — depth and tradeoffs | 1 question per 2 days; spend 90+ min | Whiteboard sketches, capacity-estimation cheatsheet |

**Do not try to study all three in parallel.** Sequence them.

---

## 3. The 12-week study sequence (recommended)

The plan below is calibrated for a candidate who can put in **~10 hours/week**. Scale weeks up/down for your own bandwidth.

### Weeks 1–6 — DSA foundation (302 questions)

DSA must come first because LLD and HLD both LEAN on DS&A primitives. You can't intelligently say "I'd use a heap with TTL eviction here" until you've internalized what a heap is.

| Week | Buckets | Target Qs | Why this order |
|---|---|---:|---|
| 1 | Arrays_and_Matrices · Prefix Sum / Kadane | 30 | The cheapest possible warmup — most questions are Easy. Builds index-thinking. |
| 2 | Hashing_Sliding_Window · Two_Pointers | 40 | Hash map = the #1 interview tool. Sliding window builds on it. |
| 3 | Searching_Binary_Search · Stack · Queues | 35 | Pattern problems. Easy → Hard within each. |
| 4 | Linked_List · Trees_Binary_Trees · BST | 15 | Hierarchical thinking. Smaller bucket sizes; go deep instead of wide. |
| 5 | Heap_Priority_Queue · Trie · Sorting/D&C · Greedy | 15 | Specialized DS. Treat each pattern as "learn the invariant, then 3 problems." |
| 6 | Graph_BFS_DFS_Dijkstra_DSU · Dynamic_Programming · Backtracking | 40 | The "advanced" core. DO NOT skip — these are interview-decisive. |

**Bucket-count truth:** Arrays_and_Matrices (43) + Hashing_Sliding_Window (55) + Searching_Binary_Search (42) = 140 questions, **46% of the DSA set**. That's deliberate — interviewers ask these the most. Don't rush past them to feel "advanced."

**JS_Coding_(56) and Distributed_Systems_(24) overflow buckets** — These got mis-tagged as DSA by the LLM. Treat them as separate study targets after the core DSA work:
- JS_Coding overflow → fold into your JS prep (this repo's `javascript-interview-prep/`)
- Distributed_Systems overflow → defer until HLD week 11–12

### Weeks 7–9 — LLD (146 questions)

LLD interviews are pattern-discrimination exercises: "Should I use Strategy or State here? Why?" You learn this by seeing the patterns side-by-side, not by drilling 50 Strategy questions in isolation.

| Week | Buckets | Target Qs | Why this order |
|---|---|---:|---|
| 7 | **Foundation:** Object_Oriented_Design · SOLID_Principles · LLD_DataStructures | 25 | Implement core data structures as proper classes first (LRU cache, observable list, undo stack). Forces you to use OOD primitives. |
| 8 | **Behavioral patterns:** Strategy · Observer · State · Command · Chain of Responsibility · Template Method · Iterator · Memento | 45 | These are 67% of named-pattern LLD questions. Spend two days on Strategy + State (the most confused pair). |
| 9 | **Structural + architectural:** Decorator · Composite · Repository · Interceptor · Plugin Architecture · DI · Event Sourcing · Rule Engine · Retry/Circuit Breaker · Singleton · Factory · Builder | 20 | Each pattern: 1 question, paper class diagram, verbal explanation of "when NOT to use." |

**The 60 `LLD_DataStructures` questions** are mostly "implement a stack/queue/cache with constraint X." Knock these out early in week 7 — they bridge DSA → LLD because the underlying DS is familiar.

**Pattern-discrimination drill (do this at end of week 8):** for each behavioral-pattern question, ask: "Could I have used a different pattern?" → if yes, write 3 sentences on why the chosen one is better. This is what senior interviewers probe.

### Weeks 10–12 — HLD (337 questions)

HLD is breadth-first AND depth-first at the same time. Strategy: pick **one archetype per study session** and go DEEP rather than touching 5 archetypes superficially.

| Week | Buckets | Target Qs | Why this order |
|---|---|---:|---|
| 10 | **Infra primitives:** Caching · Load_Balancing · Rate_Limiting · Consistent_Hashing | 75 | The Lego bricks of every HLD answer. You'll reuse them in week 11–12. |
| 11 | **Communication & storage:** Messaging_StreamProcessing · Data_Storage_Retrieval · Session_Management | 66 | Once you know caching/LB, layer on Kafka/pubsub/auth. |
| 12 | **Classic archetypes:** URL_Shortener · Search_Recommendation · Geospatial · Payments_Inventory · Image_Media_Processing · AB_Testing | 41 | The "design X" questions. Each is a synthesis of primitives + storage choices. |

**The 128 `HLD_Algorithmic_Foundations` bucket** is the leftovers — HLD questions tagged Graph/DP/Heap-heavy. Sprinkle 2–3 of these into every HLD week as "warm-up algo-heavy HLD problems." They're not a distinct study unit; they're peppered through the others.

**The 23 `Distributed_Systems_General` bucket** is genuinely catch-all. Use it as a vocabulary check: "can I define consensus / quorum / saga / CRDT?" If yes, move on; if no, pick 2–3 questions to deep-read.

---

## 4. The bucket → study-target table (quick reference)

This table maps every bucket to:

- **layer** (foundation / pattern / advanced)
- **typical interview question form** (so you recognize the bucket when you see one)
- **count + difficulty mix** (so you know what's coming)

### DSA buckets

| # | Bucket | Layer | Count | E·M·H | Typical question form |
|---|---|---|---:|---|---|
| 1 | Arrays_and_Matrices | Foundation | 43 | 33·9·1 | "Manipulate this array in place" / "Find the missing element" |
| 2 | Hashing_Sliding_Window | Foundation | 55 | 22·26·7 | "Longest substring with K distinct chars" / "Top K elements" |
| 3 | Two_Pointers | Pattern | (folded under #2 in topics) | — | "Pair with sum K" / "Container with most water" |
| 4 | Searching_Binary_Search | Pattern | 42 | 9·25·8 | "Find in rotated sorted array" / "Binary search on the answer" |
| 5 | Stack | Linear DS | 11 | 5·6·0 | "Valid parentheses" / "Next greater element" |
| 6 | Queues_Deque_Monotonic_Queue | Linear DS | 3 | 0·3·0 | "Sliding window maximum" |
| 7 | Linked_List | Linear DS | 4 | 3·1·0 | "Reverse a linked list" / "Detect cycle" |
| 8 | Trees_Binary_Trees | Hierarchical | 4 | 1·1·2 | "BT inorder traversal" / "Path sum" |
| 9 | Trie_Bit_Manipulation_Trie | Specialized | 5 | 0·0·5 | "Prefix search" / "XOR of two arrays" |
| 10 | Heap_Priority_Queue | Specialized | 8 | 0·8·0 | "Top K" / "Merge K sorted lists" |
| 11 | Graph_BFS_DFS_Dijkstra_DSU | Advanced | 42 | 1·29·12 | "Shortest path" / "Number of islands" / "Course schedule" |
| 12 | JS_Coding_(overflow) | Out-of-scope | 56 | 1·26·29 | "Implement Promise.all" / "Debounce" / "React hooks internals" |
| 13 | Distributed_Systems_(overflow) | Out-of-scope | 24 | 0·0·24 | Belongs in HLD, mis-tagged here |

### LLD buckets

| # | Bucket | Layer | Count | M·H | Typical question form |
|---|---|---|---:|---|---|
| 1 | Object_Oriented_Design | Foundation | 26 | 12·14 | "Design Parking Lot / ATM / Elevator" |
| 2 | LLD_DataStructures | Foundation | 60 | 50·10 | "Design LRU cache" / "Implement min stack" |
| 3 | SOLID_Principles | Foundation | 1 | 1·0 | "How does your design follow SOLID?" |
| 4 | Strategy_Pattern | Behavioral | 17 | 10·7 | "Payment strategies" / "Sorting strategies" |
| 5 | Observer_Pattern | Behavioral | 12 | 9·3 | "Notification system" / "Stock price subscribers" |
| 6 | State_Pattern | Behavioral | 10 | 3·7 | "Order/ticket state machine" / "Document workflow" |
| 7 | Command_Pattern | Behavioral | 3 | 1·2 | "Undo/redo" / "Macro recorder" |
| 8 | Chain_of_Responsibility | Behavioral | 1 | 1·0 | "Middleware chain" |
| 9 | Template_Method | Behavioral | 1 | 1·0 | "Algorithm skeleton with overridable steps" |
| 10 | Iterator_Pattern | Behavioral | 1 | 1·0 | "Custom iterator over tree" |
| 11 | Decorator_Pattern | Structural | 1 | 0·1 | "Pizza topping decorators" / "Stream wrappers" |
| 12 | Composite_Pattern | Structural | 2 | 0·2 | "File system tree" |
| 13 | Factory_Pattern | Creational | 1 | 1·0 | "Vehicle factory" |
| 14 | Builder_Pattern | Creational | 1 | 1·0 | "Pizza builder" / "Query builder" |
| 15 | Dependency_Injection | Architectural | 1 | 0·1 | "DI container" |
| 16 | Interceptor_Pattern | Architectural | 1 | 1·0 | "Middleware interceptor" |
| 17 | Plugin_Architecture | Architectural | 2 | 0·2 | "Extensible plugin system" |
| 18 | Repository_Pattern | Architectural | (rare) | — | "Repository over DB" |
| 19 | Event_Sourcing | Architectural | (rare) | — | "CQRS / event-sourced ledger" |
| 20 | Rule_Engine | Architectural | 2 | 1·1 | "RBAC" / "Promotion-rules engine" |
| 21 | Retry_Pattern | Resilience | 3 | 3·0 | "Retry with backoff" / "Circuit breaker" |

### HLD buckets

| # | Bucket | Layer | Count | M·H | Typical question form |
|---|---|---|---:|---|---|
| 1 | Caching | Infra primitive | 34 | 16·18 | "Design distributed cache" / "Cache invalidation" |
| 2 | Load_Balancing | Infra primitive | 19 | 5·14 | "Design L4/L7 load balancer" |
| 3 | Rate_Limiting | Infra pattern | 20 | 1·19 | "Distributed rate limiter" / "Token bucket" |
| 4 | Consistent_Hashing | Infra primitive | 2 | 0·2 | "Sharded cache with consistent hashing" |
| 5 | Session_Management | Infra pattern | 8 | 2·6 | "Auth/SSO/JWT" |
| 6 | Messaging_StreamProcessing | Infra pattern | 34 | 3·31 | "Notification system" / "Kafka-based pipeline" / "Chat" |
| 7 | Data_Storage_Retrieval | Infra pattern | 24 | 1·23 | "Time-series DB" / "Analytics pipeline" / "Distributed file storage" |
| 8 | URL_Shortener | Classic archetype | 24 | 1·23 | "Design TinyURL / bit.ly" |
| 9 | Search_Recommendation | Classic archetype | 7 | 2·5 | "Typeahead" / "Feed ranking" |
| 10 | Geospatial | Classic archetype | 1 | 1·0 | "Design Uber" / "Nearby places" |
| 11 | Payments_Inventory | Classic archetype | 5 | 1·4 | "Booking" / "Inventory" / "Checkout" |
| 12 | AB_Testing | Classic archetype | 2 | 2·0 | "Design experimentation platform" |
| 13 | Image_Media_Processing | Classic archetype | 2 | 0·2 | "YouTube / Netflix / Instagram" |
| 14 | Versioning_Schema | Niche | 1 | 1·0 | "Schema migration / versioned API" |
| 15 | HLD_Algorithmic_Foundations | Algo-heavy HLD | 128 | 57·71 | Algorithmic depth required inside a HLD question |
| 16 | Distributed_Systems_General | Catch-all | 23 | 9·14 | "Distributed lock / consensus / CRDT" |

---

## 5. How to approach an individual question (per category)

### For a DSA question

1. **Read twice, restate in your own words.** Catch the trick before it catches you.
2. **Brute force first.** Always. State complexity. Even if obvious.
3. **State the pivot as a question.** "What if I sorted first?" "What if I tracked the count by bit?"
4. **Derive the optimal.** Prove correctness on the small example with pen-paper.
5. **Code it.** Then trace it on the example. Don't skip the trace.
6. **Edge cases:** empty input, single element, all duplicates, negatives, overflow.
7. **Cross-reference with this repo's DSA walkthroughs** at `DSA/Topics/<X>/learn/` — every walkthrough follows the same structure.

### For an LLD question

1. **Clarify scope FIRST.** "Single-machine or distributed? Read-heavy or write-heavy? How many users?" Don't draw a class before you've nailed scope.
2. **Identify the entities** (nouns). Class candidates.
3. **Identify the operations** (verbs). Method candidates.
4. **Identify the variability points.** "What changes if requirements change?" These are where you reach for design patterns.
5. **Draw the class diagram on paper.** Methods + relationships. Two-way arrows are usually wrong.
6. **Defend each pattern choice.** "I used Strategy here because the sorting algo varies per use-case." If you can't defend it, drop it.
7. **Code the SKELETON.** Interfaces + 1–2 concrete classes. Not the whole thing.
8. **Discuss extensibility.** "If we added requirement X, here's where it'd plug in."

### For an HLD question

1. **Clarify scope, REQUEST SCALE NUMBERS.** "What's the QPS target? Read:write ratio? Latency SLO?" If they don't give numbers, propose reasonable ones aloud.
2. **Sketch the data model.** Tables + columns + access patterns. This drives DB choice.
3. **Sketch the architecture in 3 layers:** client → API/edge → service → DB. Add cache + queue + LB.
4. **Identify the bottlenecks.** Read amplification? Hot keys? Cross-region writes?
5. **Propose ONE solution per bottleneck.** Don't list 5 options for each; pick one and defend.
6. **Discuss failure modes.** "If this Redis node dies, what happens?" "If the queue backs up, do we drop or buffer?"
7. **Add scale numbers to the diagram.** "3000 RPS at peak" / "10TB storage" — anchors the discussion.

---

## 6. Cross-vertical question overlap

**60.6% of questions** (476/785) carry SECONDARY-bucket tags — meaning they exercise multiple concepts. The full list is in [`overlaps.md`](./overlaps.md). Highlights:

| Pattern | Where you see it |
|---|---|
| Caching ↔ Distributed Systems ↔ Consistent Hashing | Many HLD questions combine all three |
| Strategy ↔ State (most-confused LLD pair) | 80%+ of State questions also fit Strategy. Use the confusion as a learning opportunity. |
| Graph ↔ DP ↔ Hashing | These three appear together in 30+ algorithmically-deep HLD questions |
| URL Shortener ↔ Caching ↔ Rate Limiting | The canonical "design 3 systems in one" question |

**Practical use:** when planning a study week, **prefer overlap questions** — they give you double-duty practice. The `⚠️ also fits:` annotation on each question row in the per-category files flags these.

---

## 7. Where to write your answers

Don't just READ these questions — practice the WRITING.

| Vertical | Where to write |
|---|---|
| DSA | This repo's `DSA/Topics/<X>/learn/<Problem>.md` template — see [`DSA/TEMPLATE-v2.md`](../DSA/TEMPLATE-v2.md) |
| LLD | (No template yet in this repo — see open question in `categorization-method.md`) |
| HLD | This repo's `backend-data-prep/questions/<topic>/<name>.md` — see existing examples in `backend-data-prep/` |

The repo's `CONTRIBUTING-v2.md` explains the writing rules.

---

## 8. Quick reality check — what success looks like

After this 12-week sequence:

- **DSA:** you can write a passing solution to a fresh medium-hard problem in 25 minutes, including pen-paper trace.
- **LLD:** you can draw a defensible class diagram for any "design X" question in 15 minutes, naming 1–2 patterns explicitly.
- **HLD:** you can sketch a 3-tier architecture for a system you've never designed before in 30 minutes, including capacity estimates and identified bottlenecks.

If you can't do these YET — that's expected. The 785 questions are the path.

---

## 9. Files in this folder

| File | Purpose |
|---|---|
| [`STUDY-GUIDE.md`](./STUDY-GUIDE.md) | (you are here) — the consolidated sequence |
| [`DSA-questions.md`](./DSA-questions.md) | 302 DSA questions, bucketed in study order |
| [`LLD-questions.md`](./LLD-questions.md) | 146 LLD questions, bucketed by design pattern |
| [`HLD-questions.md`](./HLD-questions.md) | 337 HLD questions, bucketed by system-design archetype |
| [`overlaps.md`](./overlaps.md) | The 476 questions that fit more than one bucket |
| [`categorization-method.md`](./categorization-method.md) | How the bucketing was done + how to re-run |
| [`INDEX.md`](./INDEX.md) | Quick summary tables (no narrative) |

---

## 10. Open questions / where to expand

Things this guide does NOT yet do — flag if you want them tackled:

1. **Per-question depth annotations** (e.g., "this URL_Shortener question goes 3 layers deeper than typical — budget 90 min instead of 60"). Currently every question is treated as a single unit.
2. **Importing into the main repo** — these are still in `leetlens-import/` as a categorization layer. Whether/how to fold the actual question text into `backend-data-prep/` or a new `LLD/` vertical is an open call.
3. **Behavioral + System Design freeform questions** (the 120 we didn't bucket) — separate scheme needed.
4. **Per-question "study order" within a bucket** — currently sorted by difficulty, but two Medium questions in the same bucket may have very different optimal orderings.
