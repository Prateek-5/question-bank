# Observer Pattern — Extracted Questions

> **12 questions** sourced from the LeetLens DB (`processed.extracted_questions`, snapshot 2026-05-31).
> Vertical: **LLD** · Bucket: `Observer_Pattern` · Bucket study-order rank in vertical: **8**.
> See [`../../../leetlens-import/STUDY-GUIDE.md`](../../../leetlens-import/STUDY-GUIDE.md) for the cross-vertical sequence.

## How to use this file

- Each row is **metadata only** — question text, difficulty, company, topic tags, LeetLens ID.
- The **Seq** column gives the recommended execution order WITHIN this bucket (Easy → Hard, then by LLM quality score).
- The **⚠️ also fits** annotation lists OTHER buckets the question could appear in (cross-cutting practice).
- When you're ready to author a walkthrough for a question, create a new file alongside this manifest (e.g. `Question_Name.md`) following the vertical's TEMPLATE-v2.md.

## Summary

- **Total:** 12
- **Difficulty mix:** Medium: 9 · Hard: 3
- **Top companies:** Google (5), Netflix (2), Riot Games (1), Uber (1), Amazon (1), Microsoft (1), eBay (1)

## Questions

| Seq | Difficulty | Company | Question | Topics | LeetLens ID | Also fits |
|---:|---|---|---|---|---|---|
| 1 | Medium | Netflix | Design a configuration hot-reload system for a running application. Support file-based and remote config sources, change detection, validation before applying, rollback on error, and notifying dependent components of changes. | Object-Oriented Design, Observer Pattern, Strategy Pattern, Hot Reload, +1 | `3cdf1fec` | `Object_Oriented_Design` · `Strategy_Pattern` |
| 2 | Medium | Google | Design an email client at the class level supporting compose, send, receive, folder management (inbox, sent, drafts, trash, custom), search, attachments, and email threading/conversation view. | Object-Oriented Design, Observer Pattern, Composite Pattern, Search | `22994584` | `Composite_Pattern` · `Object_Oriented_Design` |
| 3 | Medium | Microsoft | Design a stack overflow-like Q&A platform at the class level with question posting, answering, voting (upvote/downvote), accepted answer marking, tagging, reputation system, and badge awarding. | Object-Oriented Design, Observer Pattern, Strategy Pattern, Reputation System | `7bbb166b` | `Object_Oriented_Design` · `Strategy_Pattern` |
| 4 | Medium | eBay | Design an online auction countdown timer system with bid extension on last-minute bids, synchronized time across clients, server-authoritative time, and handling clock drift between client and server. | Object-Oriented Design, Time Synchronization, Observer Pattern, Real-time | `f4449453` | `Object_Oriented_Design` |
| 5 | Medium | Amazon | Design an inventory management system for a warehouse with product tracking, stock level alerts, batch operations, multi-warehouse transfer, and barcode/SKU management. | Object-Oriented Design, Observer Pattern, Repository Pattern, Event Sourcing | `41926aaa` | `Event_Sourcing` · `Object_Oriented_Design` · `Repository_Pattern` |
| 6 | Medium | Google | Design a meeting room scheduler for an office building. Support room search by capacity and amenities, booking with conflict detection, recurring meetings, and integration with calendar notifications. | Object-Oriented Design, Interval Scheduling, Observer Pattern, Builder Pattern | `10ca67e4` | `Builder_Pattern` · `Object_Oriented_Design` |
| 7 | Medium | Riot Games | Design a multi-player online game lobby system supporting room creation, player matchmaking by skill level, ready-check mechanism, in-lobby chat, and game session initialization. | Object-Oriented Design, Matchmaking, Observer Pattern, State Pattern | `184c31e9` | `Object_Oriented_Design` · `State_Pattern` |
| 8 | Medium | Google | Explain the Observer pattern vs Pub/Sub pattern with concrete examples. When would you use each? What are the coupling implications? Implement both and discuss memory leak risks with event listeners. | Design Patterns, Observer Pattern, Pub/Sub, Coupling, +1 | `14083dd8` | `Object_Oriented_Design` |
| 9 | Medium | Uber | Design a restaurant reservation system with table management, time-slot booking, party size matching, waitlist management, and cancellation with notification. | Object-Oriented Design, Observer Pattern, State Pattern, Scheduling | `211bb357` | `Object_Oriented_Design` · `State_Pattern` |
| 10 | Hard | Google | Design a spreadsheet application supporting cell value and formula input, formula evaluation with cell references (A1, B2), circular dependency detection, and auto-recalculation on cell updates. | Object-Oriented Design, Observer Pattern, Topological Sort, Expression Parsing, +1 | `7dfb37e6` | `LLD_DataStructures` · `Object_Oriented_Design` |
| 11 | Hard | Google | Design a publish-subscribe messaging system with topic-based routing, durable subscriptions, message ordering guarantees, acknowledgment, and dead letter queue support. | Object-Oriented Design, Observer Pattern, Message Queue, Pub-Sub, +1 | `09c3e938` | `Object_Oriented_Design` |
| 12 | Hard | Netflix | Design an event-driven architecture framework with event bus, event sourcing, handlers, middleware chain, and dead letter queue. Support sync and async event processing. | Object-Oriented Design, Event Sourcing, Mediator Pattern, Chain of Responsibility, +1 | `28f2ca4d` | `Chain_of_Responsibility` · `Event_Sourcing` · `Object_Oriented_Design` |

---

## Future scope (placeholder)

Once questions are reviewed, the next pass will create per-question walkthrough files in this directory following the vertical's `TEMPLATE-v2.md`. Track those additions in the parent topic's `LEARNING.md` if one exists.