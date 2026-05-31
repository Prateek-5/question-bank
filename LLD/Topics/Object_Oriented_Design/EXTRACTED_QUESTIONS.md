# Object-Oriented Design — Extracted Questions

> **26 questions** sourced from the LeetLens DB (`processed.extracted_questions`, snapshot 2026-05-31).
> Vertical: **LLD** · Bucket: `Object_Oriented_Design` · Bucket study-order rank in vertical: **1**.
> See [`../../../leetlens-import/STUDY-GUIDE.md`](../../../leetlens-import/STUDY-GUIDE.md) for the cross-vertical sequence.

## How to use this file

- Each row is **metadata only** — question text, difficulty, company, topic tags, LeetLens ID.
- The **Seq** column gives the recommended execution order WITHIN this bucket (Easy → Hard, then by LLM quality score).
- The **⚠️ also fits** annotation lists OTHER buckets the question could appear in (cross-cutting practice).
- When you're ready to author a walkthrough for a question, create a new file alongside this manifest (e.g. `Question_Name.md`) following the vertical's TEMPLATE-v2.md.

## Summary

- **Total:** 26
- **Difficulty mix:** Medium: 12 · Hard: 14
- **Top companies:** Google (11), Amazon (5), Meta (3), Microsoft (2), Airbnb (1), Netflix (1), LinkedIn (1)

## Questions

| Seq | Difficulty | Company | Question | Topics | LeetLens ID | Also fits |
|---:|---|---|---|---|---|---|
| 1 | Medium | Airbnb | Design a hotel booking system supporting room types (single, double, suite), date-range availability checks, booking confirmation, cancellation with refund policy, and loyalty points tracking. | Object-Oriented Design, Strategy Pattern, State Pattern, Date Range Handling | `1a33510b` | `State_Pattern` · `Strategy_Pattern` |
| 2 | Medium | Google | Design a hash map from scratch with support for generic key-value types, dynamic resizing, collision handling via chaining and open addressing, and custom hash function injection. | Object-Oriented Design, Hash Table, Collision Resolution, Generics, +1 | `61f8ffd6` | — |
| 3 | Medium | Google | Design a parking lot system with multiple floors, different vehicle types (motorcycle, car, bus), and payment processing. Include entry/exit gates, ticket generation, and hourly rate calculation. | Object-Oriented Design, SOLID Principles, Design Patterns, State Pattern | `79e56e70` | `SOLID_Principles` · `State_Pattern` |
| 4 | Medium | Amazon | Design a vending machine that supports multiple product types, coin/bill payment, change dispensing, inventory management, and an admin restocking interface. Handle edge cases like insufficient funds and out-of-stock items. | Object-Oriented Design, State Pattern, Strategy Pattern, Finite State Machine | `35f48d74` | `State_Pattern` · `Strategy_Pattern` |
| 5 | Medium | Amazon | Design an e-book reader application: book library management, pagination/scrolling modes, bookmarks, highlights with notes, font/theme customization, reading progress sync across devices, and dictionary lookup. | Object-Oriented Design, Observer Pattern, Strategy Pattern, Memento Pattern, +1 | `ae67f2a1` | `Memento_Pattern` · `Observer_Pattern` · `Strategy_Pattern` |
| 6 | Medium | Meta | Design a form validation library supporting field-level and form-level validation, async validators (e.g., checking username availability), dependent field validation, custom error messages, and validation groups. | Object-Oriented Design, Validation, Strategy Pattern, Composite Pattern, +1 | `b241d346` | `Composite_Pattern` · `Strategy_Pattern` |
| 7 | Medium | Amazon | Design the Snake game with a grid-based board, growing snake on food consumption, collision detection with walls and self, score tracking, and increasing speed levels. | Object-Oriented Design, Game Loop, Queue Data Structure, Collision Detection | `0e539e70` | — |
| 8 | Medium | Microsoft | Design a healthcare appointment scheduling system with doctor availability management, patient booking, appointment types (in-person, telehealth), waiting room queue, automated reminders, and cancellation with rebooking. | Object-Oriented Design, Scheduling, Observer Pattern, State Pattern, +1 | `7e9c706f` | `Observer_Pattern` · `State_Pattern` |
| 9 | Medium | Google | Design a library management system supporting book cataloging, member registration, book checkout/return, fine calculation, reservation queues, and search by title/author/ISBN. | Object-Oriented Design, Observer Pattern, Repository Pattern, SOLID Principles | `07aafc72` | `Observer_Pattern` · `Repository_Pattern` · `SOLID_Principles` |
| 10 | Medium | Google | Design a parking lot system | Graph, Dynamic Programming | `27ccd102` | `LLD_DataStructures` |
| 11 | Medium | Google | Design a parking lot system | Graph, Dijkstra's algorithm | `35c1c690` | `LLD_DataStructures` |
| 12 | Medium | — | Design a parking lot system | Graph | `003b8a08` | `LLD_DataStructures` |
| 13 | Hard | Google | Design a garbage collector for a managed language runtime. Support mark-and-sweep, reference counting, generational collection, and support for finalizers. Handle root set identification and object graph traversal. | Object-Oriented Design, Garbage Collection, Mark and Sweep, Generational GC, +1 | `ca76b12b` | — |
| 14 | Hard | Amazon | Design a key-value store with support for get, put, delete, TTL-based expiration, persistence to disk (append-only log), and compaction. Model the storage engine classes. | Object-Oriented Design, LSM Tree, Append-Only Log, Compaction, +1 | `3938ba62` | — |
| 15 | Hard | Google | Design a search engine at the class level with inverted index construction, TF-IDF scoring, boolean query support (AND, OR, NOT), phrase queries, and result pagination. Support incremental index updates. | Object-Oriented Design, Inverted Index, TF-IDF, Boolean Query, +1 | `3e0ec584` | — |
| 16 | Hard | LinkedIn | Design a message broker at the class level supporting topics, queues, message persistence, consumer groups, message acknowledgment, and dead letter queue. Include message ordering guarantees within a partition. | Object-Oriented Design, Message Broker, Consumer Groups, Partitioning, +1 | `ca493e32` | — |
| 17 | Hard | Amazon | Design a thread pool executor with configurable core and max pool size, task queue with bounded capacity, rejection policies (abort, discard, caller-runs), and graceful shutdown. | Object-Oriented Design, Concurrency, Thread Pool, Strategy Pattern, +1 | `0f1f9a6b` | `Strategy_Pattern` |
| 18 | Hard | Google | Design a JSON parser from scratch that handles objects, arrays, strings, numbers, booleans, and null values. Support nested structures and provide meaningful error messages for malformed input. | Object-Oriented Design, Recursive Descent Parser, Tokenizer, Visitor Pattern | `4f2321d3` | — |
| 19 | Hard | Microsoft | Design an elevator system for a 40-floor building with multiple elevators, handling peak traffic, priority requests, and maintenance mode. Define the scheduling algorithm for optimal wait times. | Object-Oriented Design, Strategy Pattern, State Machine, Scheduling Algorithms | `26d997db` | `State_Pattern` · `Strategy_Pattern` |
| 20 | Hard | Netflix | Design a connection pool manager supporting configurable min/max connections, connection health checking, idle timeout eviction, fair queuing for waiting clients, and graceful shutdown. | Object-Oriented Design, Object Pool Pattern, Concurrency, Resource Management | `492b4d0f` | — |
| 21 | Hard | Google | Design a Sudoku solver and validator. Model the board, implement constraint propagation, backtracking search, and provide efficient validation for rows, columns, and 3x3 boxes. Support puzzle generation with unique solutions. | Object-Oriented Design, Backtracking, Constraint Propagation, Puzzle Generation | `0092c47c` | — |
| 22 | Hard | Google | Design a parking lot system | Cache, Data Structures | `1add2b13` | `LLD_DataStructures` |
| 23 | Hard | Google | Design a parking lot system | Graph, Dynamic Programming | `8dadfd62` | `LLD_DataStructures` |
| 24 | Hard | Meta | Design a parking lot system for a city with a large number of cars and trucks | Parking Lot, Distributed Systems | `13fdf6de` | `LLD_DataStructures` |
| 25 | Hard | Meta | Design a parking lot system | Graph, Distributed Systems | `25c8b4c1` | `LLD_DataStructures` |
| 26 | Hard | — | Design a parking lot system | Graph Data Structure, Parking Lot | `1d37fd6c` | — |

---

## Future scope (placeholder)

Once questions are reviewed, the next pass will create per-question walkthrough files in this directory following the vertical's `TEMPLATE-v2.md`. Track those additions in the parent topic's `LEARNING.md` if one exists.