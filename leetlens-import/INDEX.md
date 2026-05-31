# LeetLens Import — Index

> Snapshot of `processed.extracted_questions` in the LeetLens Postgres DB (snapshot date: **2026-05-31**).
> 905 LLM-extracted interview questions; this folder categorizes the **785 DSA + LLD + HLD** rows by primary topic.
> The remaining 120 — System Design (79), Behavioral (38), Other (3) — are not bucketed here.

## Read this first

**Start with [`STUDY-GUIDE.md`](./STUDY-GUIDE.md)** — that's the student-facing 12-week sequence with rationale. The per-category files below are catalogues you reference once you know what week you're in.

## Files in this folder

| File | Purpose |
|---|---|
| [`STUDY-GUIDE.md`](./STUDY-GUIDE.md) | **Master file** — 12-week sequenced study plan across DSA/LLD/HLD, with rationale |
| [`DSA-questions.md`](./DSA-questions.md) | 302 DSA questions, bucketed in pedagogical order, Easy→Hard within each bucket |
| [`LLD-questions.md`](./LLD-questions.md) | 146 LLD questions, bucketed by design pattern with study-order layering |
| [`HLD-questions.md`](./HLD-questions.md) | 337 HLD questions, bucketed by system-design archetype |
| [`overlaps.md`](./overlaps.md) | 476 questions (60.6%) that fit MORE THAN ONE bucket — flagged for double-duty practice |
| [`categorization-method.md`](./categorization-method.md) | The bucketing algorithm, caveats, and how to re-run |

## High-level counts

| Category | Total | Easy | Medium | Hard |
|---|---:|---:|---:|---:|
| DSA | 302 | 79 | 134 | 89 |
| LLD | 146 | 0 | 96 | 50 |
| HLD | 337 | 0 | 104 | 233 |
| **Sum** | **785** | **79** | **234** | **372** |

> Note: no Easy LLD or HLD questions exist in the dataset. Those verticals are inherently open-ended design questions.

## Bucket distribution per category

### DSA — 302 questions, 13 buckets

| # | Bucket | Count | % |
|---|---|---:|---:|
| 1 | `JS_Coding_(out_of_DSA_scope)` | 56 | 18.5% |
| 2 | `Hashing_Sliding_Window` | 55 | 18.2% |
| 3 | `Arrays_and_Matrices` | 43 | 14.2% |
| 4 | `Searching_Binary_Search` | 42 | 13.9% |
| 5 | `Graph_BFS_DFS_Dijkstra_DSU` | 42 | 13.9% |
| 6 | `Distributed_Systems_(out_of_DSA_scope)` | 24 | 7.9% |
| 7 | `Stack` | 11 | 3.6% |
| 8 | `Heap_Priority_Queue` | 8 | 2.6% |
| 9 | `Trie_Bit_Manipulation_Trie` | 5 | 1.7% |
| 10 | `Uncategorized` | 5 | 1.7% |
| 11 | `Trees_Binary_Trees` | 4 | 1.3% |
| 12 | `Linked_List` | 4 | 1.3% |
| 13 | `Queues_Deque_Monotonic_Queue` | 3 | 1.0% |

### LLD — 146 questions, 19 buckets

| # | Bucket | Count | % |
|---|---|---:|---:|
| 1 | `LLD_DataStructures` | 60 | 41.1% |
| 2 | `Object_Oriented_Design` | 26 | 17.8% |
| 3 | `Strategy_Pattern` | 17 | 11.6% |
| 4 | `Observer_Pattern` | 12 | 8.2% |
| 5 | `State_Pattern` | 10 | 6.8% |
| 6 | `Command_Pattern` | 3 | 2.1% |
| 7 | `Retry_Pattern` | 3 | 2.1% |
| 8 | `Plugin_Architecture` | 2 | 1.4% |
| 9 | `Rule_Engine` | 2 | 1.4% |
| 10 | `Composite_Pattern` | 2 | 1.4% |
| 11-19 | (eight 1-count buckets) | 8 | 5.5% |

### HLD — 337 questions, 17 buckets (refined via text override)

| # | Bucket | Count | % |
|---|---|---:|---:|
| 1 | `HLD_Algorithmic_Foundations` | 128 | 38.0% |
| 2 | `Messaging_StreamProcessing` | 34 | 10.1% |
| 3 | `Caching` | 34 | 10.1% |
| 4 | `URL_Shortener` | 24 | 7.1% |
| 5 | `Data_Storage_Retrieval` | 24 | 7.1% |
| 6 | `Distributed_Systems_General` | 23 | 6.8% |
| 7 | `Rate_Limiting` | 20 | 5.9% |
| 8 | `Load_Balancing` | 19 | 5.6% |
| 9 | `Session_Management` | 8 | 2.4% |
| 10 | `Search_Recommendation` | 7 | 2.1% |
| 11 | `Payments_Inventory` | 5 | 1.5% |
| 12 | `Uncategorized` | 3 | 0.9% |
| 13 | `Consistent_Hashing` | 2 | 0.6% |
| 14 | `AB_Testing` | 2 | 0.6% |
| 15 | `Image_Media_Processing` | 2 | 0.6% |
| 16 | `Versioning_Schema` | 1 | 0.3% |
| 17 | `Geospatial` | 1 | 0.3% |

## Overlap statistics

**476 questions (60.6%) fit more than one bucket.** This is by design — interview questions are multi-faceted. See [`overlaps.md`](./overlaps.md) for the full cross-bucket map.

| Category | Overlap-flagged | % of category |
|---|---:|---:|
| DSA | 166 | 55.0% |
| LLD | 80 | 54.8% |
| HLD | 230 | 68.3% |

HLD has the highest overlap rate because system-design questions inherently combine primitives (e.g. "URL shortener + caching + rate limiting" is one question).
