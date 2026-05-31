# Data-Structure Implementations — Extracted Questions

> **60 questions** sourced from the LeetLens DB (`processed.extracted_questions`, snapshot 2026-05-31).
> Vertical: **LLD** · Bucket: `LLD_DataStructures` · Bucket study-order rank in vertical: **3**.
> See [`../../../leetlens-import/STUDY-GUIDE.md`](../../../leetlens-import/STUDY-GUIDE.md) for the cross-vertical sequence.

## How to use this file

- Each row is **metadata only** — question text, difficulty, company, topic tags, LeetLens ID.
- The **Seq** column gives the recommended execution order WITHIN this bucket (Easy → Hard, then by LLM quality score).
- The **⚠️ also fits** annotation lists OTHER buckets the question could appear in (cross-cutting practice).
- When you're ready to author a walkthrough for a question, create a new file alongside this manifest (e.g. `Question_Name.md`) following the vertical's TEMPLATE-v2.md.

## Summary

- **Total:** 60
- **Difficulty mix:** Medium: 50 · Hard: 10
- **Top companies:** Google (54), Microsoft (2), Amazon (2), LinkedIn (1), Cloudflare (1)

## Questions

| Seq | Difficulty | Company | Question | Topics | LeetLens ID | Also fits |
|---:|---|---|---|---|---|---|
| 1 | Medium | Amazon | Design an LRU Cache with O(1) get and put operations, configurable capacity, and eviction callback support. Implement it using a doubly linked list and hash map. | Object-Oriented Design, Hash Map, Doubly Linked List, Cache Eviction | `209dd444` | `Object_Oriented_Design` |
| 2 | Medium | Microsoft | Design a URL shortener service at the class level: URL encoding/decoding, custom alias support, expiration handling, click analytics tracking, and collision resolution. | Object-Oriented Design, Hashing, Base62 Encoding, Repository Pattern | `11f81600` | `Object_Oriented_Design` · `Repository_Pattern` |
| 3 | Medium | Google | Design a cache with least recently used (LRU) eviction policy | Cache, LRU | `05be2a6c` | — |
| 4 | Medium | Google | Design LRU Cache | Cache, LRU | `06202864` | — |
| 5 | Medium | Google | Design a Min Deque with Synchronization (Java) | Stack, Min Heap | `0686742e` | — |
| 6 | Medium | Google | Design a Min Stack with Support for Push and Pop Operations (with time complexity O(1)) | Stack, Data Structure | `1870eebc` | — |
| 7 | Medium | Google | Design a Min Queue with Support for Enqueue and Dequeue Operations (with time complexity O(1)) | Queue, Data Structure | `1dd575b1` | — |
| 8 | Medium | Google | Design a Min Priority Queue | Stack, Min Heap | `285b2b8c` | — |
| 9 | Medium | Google | Design a Min Deque with Support for Enqueue and Dequeue Operations (with time complexity O(1)) | Deque, Data Structure | `4d4a6f7c` | — |
| 10 | Medium | Google | Design a Min Deque with Support for Enqueue and Dequeue Operations (with time complexity O(log n)) | Deque, Data Structure | `516144b7` | — |
| 11 | Medium | Google | Design a Min Deque with Support for Enqueue and Dequeue Operations (with time complexity O(log n)) | Deque, Data Structure | `58806287` | — |
| 12 | Medium | Google | Design a Min Deque with Support for Enqueue and Dequeue Operations (with time complexity O(log n)) | Deque, Data Structure | `5db91d52` | — |
| 13 | Medium | Google | Design a Min Queue with Synchronization (Python) | Stack, Min Heap | `5df160b7` | — |
| 14 | Medium | Google | Design a Min Deque with Synchronization (Python) | Stack, Min Heap | `615544fd` | — |
| 15 | Medium | Google | Design LRU Cache | Cache, Data Structures | `637f8cc8` | — |
| 16 | Medium | Google | Design a Min Queue with Support for Enqueue and Dequeue Operations (with time complexity O(log n)) | Queue, Data Structure | `70de70f2` | — |
| 17 | Medium | Google | Design a Min Deque | Deque, Data Structure | `71f12ed8` | — |
| 18 | Medium | Google | Design LRU Cache | Cache, Data Structure | `73a6246b` | — |
| 19 | Medium | Google | Design a Min Queue with Synchronization (C#) | Stack, Min Heap | `7e5f30b0` | — |
| 20 | Medium | Google | Design a Min Heap | Heap, Data Structure | `8085fcd4` | — |
| 21 | Medium | Google | Design a Min Deque with Support for Enqueue and Dequeue Operations (with time complexity O(1)) | Deque, Data Structure | `8b0847d2` | — |
| 22 | Medium | Google | Design a Min Heap with Support for Push and Pop Operations (with time complexity O(log n)) | Heap, Data Structure | `8b30639b` | — |
| 23 | Medium | Google | Design a Min Heap with Support for Push and Pop Operations | Heap, Data Structure | `963f1d2e` | — |
| 24 | Medium | Google | Design a Min Deque | Stack, Min Heap | `9c952b0d` | — |
| 25 | Medium | Google | Design a Min Deque with Synchronization (C++) | Stack, Min Heap | `9d528deb` | — |
| 26 | Medium | Google | Design a Min Heap with Support for Push and Pop Operations (with time complexity O(log n)) | Heap, Data Structure | `9f245a07` | — |
| 27 | Medium | Google | Design a Min Queue with Synchronization (C++) | Stack, Min Heap | `a36eebfc` | — |
| 28 | Medium | Google | Design a Min Stack with Synchronization | Stack, Min Heap | `a83e956b` | — |
| 29 | Medium | Google | Design a Min Queue | Stack, Min Heap | `a992b322` | — |
| 30 | Medium | Google | Design a Min Queue with Support for Enqueue and Dequeue Operations | Queue, Data Structure | `b1ebd004` | — |
| 31 | Medium | Google | Design a Min Queue with Synchronization | Stack, Min Heap | `bce5ed06` | — |
| 32 | Medium | Google | Design a Min Stack with Support for Push and Pop Operations (with time complexity O(log n)) | Stack, Data Structure | `c076926f` | — |
| 33 | Medium | Google | Design a Min Deque with Support for Enqueue and Dequeue Operations | Deque, Data Structure | `c5298675` | — |
| 34 | Medium | Google | Design a Min Deque with Synchronization (C#) | Stack, Min Heap | `c8b8abf8` | — |
| 35 | Medium | Google | Design a Min Stack with Support for Push and Pop Operations | Stack, Data Structure | `ce1bd353` | — |
| 36 | Medium | Google | Design a Min Queue | Queue, Data Structure | `d75190bd` | — |
| 37 | Medium | Google | Design a Min Deque with Synchronization | Stack, Min Heap | `d9aae3b9` | — |
| 38 | Medium | Google | Design a Min Stack with Support for Push and Pop Operations (with time complexity O(log n)) | Stack, Data Structure | `da8d915f` | — |
| 39 | Medium | Google | Design a Min Priority Queue with Synchronization (C++) | Stack, Min Heap | `dae35c02` | — |
| 40 | Medium | Google | Design a Min Stack | Stack, Min Heap | `dd2a9f70` | — |
| 41 | Medium | Google | Design a Min Queue with Support for Enqueue and Dequeue Operations (with time complexity O(1)) | Queue, Data Structure | `de734d7e` | — |
| 42 | Medium | Google | Design a Min Queue with Support for Enqueue and Dequeue Operations (with time complexity O(log n)) | Queue, Data Structure | `e0517ca8` | — |
| 43 | Medium | Google | Design a Min Priority Queue with Synchronization (Java) | Stack, Min Heap | `e55e28db` | — |
| 44 | Medium | Google | Design a Min Queue with Synchronization (Java) | Stack, Min Heap | `e809888d` | — |
| 45 | Medium | Google | Design a Min Queue with Support for Enqueue and Dequeue Operations (with time complexity O(log n)) | Queue, Data Structure | `e8fabd22` | — |
| 46 | Medium | Google | Design a Min Priority Queue with Synchronization (Python) | Stack, Min Heap | `eb055329` | — |
| 47 | Medium | Google | Design a Min Priority Queue with Synchronization (C#) | Stack, Min Heap | `ef23ef62` | — |
| 48 | Medium | Google | Design a Min Queue with Support for Enqueue and Dequeue Operations (with time complexity O(log n)) | Queue, Data Structure | `f752043b` | — |
| 49 | Medium | Google | Design a Min Deque with Support for Enqueue and Dequeue Operations (with time complexity O(log n)) | Deque, Data Structure | `f79385cc` | — |
| 50 | Medium | Google | Design a Min Stack | Stack, Data Structure | `fdeec4a2` | — |
| 51 | Hard | Cloudflare | Design an API rate limiter middleware that supports per-user, per-endpoint, and global rate limits using sliding window counters. Include rate limit headers in responses and support distributed deployment. | Object-Oriented Design, Sliding Window, Middleware Pattern, Decorator Pattern | `36d2b952` | `Decorator_Pattern` · `Object_Oriented_Design` |
| 52 | Hard | Microsoft | Design a version control system (simplified Git) supporting init, add, commit, branch, checkout, merge, diff, and log operations. Model the object store (blobs, trees, commits) and reference management. | Object-Oriented Design, Tree Data Structure, DAG, Content-Addressable Storage, +1 | `d043ce7e` | `Object_Oriented_Design` |
| 53 | Hard | Amazon | Design a task scheduler that supports one-time and recurring tasks, priority-based execution, task dependencies (DAG), cancellation, and retry with exponential backoff. | Object-Oriented Design, Priority Queue, DAG, Observer Pattern, +1 | `24907f7a` | `Object_Oriented_Design` · `Observer_Pattern` · `Retry_Pattern` |
| 54 | Hard | Google | Design a type-ahead suggestion system at the class level: trie-based prefix matching, suggestion ranking by frequency/recency/personalization, fuzzy matching for typos, and memory-efficient trie representations (compressed trie, ternary search trie). | Object-Oriented Design, Trie, Compressed Trie, Fuzzy Matching, +1 | `a7f9a4d1` | `Object_Oriented_Design` |
| 55 | Hard | LinkedIn | Design a cron job scheduler that parses cron expressions, schedules jobs at specified intervals, handles missed executions, supports job dependencies, and provides execution history and alerting. | Object-Oriented Design, Cron Parser, Priority Queue, DAG, +1 | `202aae2a` | `Object_Oriented_Design` |
| 56 | Hard | Google | Design a distributed queue for a microservices architecture | Graph, Dijkstra's Algorithm | `218c434f` | — |
| 57 | Hard | Google | Design a distributed queue for a microservices architecture | Graph, Dijkstra's Algorithm | `57391323` | — |
| 58 | Hard | Google | Design a system for handling duplicate keys in a database | Graph, Hash Map | `af8a8dfa` | — |
| 59 | Hard | Google | Design a distributed queue for a microservices architecture | Graph, Dijkstra's Algorithm | `bf931b9a` | — |
| 60 | Hard | Google | Design a load balancing system for a web application | Graph, Dijkstra's Algorithm | `c09ce3de` | — |

---

## Future scope (placeholder)

Once questions are reviewed, the next pass will create per-question walkthrough files in this directory following the vertical's `TEMPLATE-v2.md`. Track those additions in the parent topic's `LEARNING.md` if one exists.