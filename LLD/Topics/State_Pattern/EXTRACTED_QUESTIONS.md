# State Pattern — Extracted Questions

> **10 questions** sourced from the LeetLens DB (`processed.extracted_questions`, snapshot 2026-05-31).
> Vertical: **LLD** · Bucket: `State_Pattern` · Bucket study-order rank in vertical: **9**.
> See [`../../../leetlens-import/STUDY-GUIDE.md`](../../../leetlens-import/STUDY-GUIDE.md) for the cross-vertical sequence.

## How to use this file

- Each row is **metadata only** — question text, difficulty, company, topic tags, LeetLens ID.
- The **Seq** column gives the recommended execution order WITHIN this bucket (Easy → Hard, then by LLM quality score).
- The **⚠️ also fits** annotation lists OTHER buckets the question could appear in (cross-cutting practice).
- When you're ready to author a walkthrough for a question, create a new file alongside this manifest (e.g. `Question_Name.md`) following the vertical's TEMPLATE-v2.md.

## Summary

- **Total:** 10
- **Difficulty mix:** Medium: 3 · Hard: 7
- **Top companies:** Google (4), Amazon (2), Uber (1), Netflix (1), DoorDash (1), Goldman Sachs (1)

## Questions

| Seq | Difficulty | Company | Question | Topics | LeetLens ID | Also fits |
|---:|---|---|---|---|---|---|
| 1 | Medium | Amazon | Design an order management system supporting order creation, status tracking (placed, confirmed, preparing, shipped, delivered, cancelled, returned), payment integration, refund processing, and order history with pagination. | Object-Oriented Design, State Pattern, Event Sourcing, Payment Integration | `6ea9c102` | `Event_Sourcing` · `Object_Oriented_Design` |
| 2 | Medium | Goldman Sachs | Design an ATM machine supporting cash withdrawal (multiple denominations), balance inquiry, mini statement, PIN change, fund transfer, and daily withdrawal limits. Handle concurrent access to the same account. | Object-Oriented Design, State Pattern, Chain of Responsibility, Concurrency | `a47f949b` | `Chain_of_Responsibility` · `Object_Oriented_Design` |
| 3 | Medium | Google | Design a traffic signal control system for a 4-way intersection supporting vehicle detection, pedestrian crossing, emergency vehicle priority override, and configurable timing patterns. | Object-Oriented Design, State Pattern, Observer Pattern, Finite State Machine | `091c200b` | `Object_Oriented_Design` · `Observer_Pattern` |
| 4 | Hard | Google | Design a state machine framework that supports state definition, transition rules, guards/conditions, entry/exit actions, hierarchical states, and event-driven transitions. Make it generic and reusable. | Object-Oriented Design, State Pattern, Generics, Framework Design | `286fb9b9` | `Object_Oriented_Design` · `Plugin_Architecture` |
| 5 | Hard | Google | Design a regex engine that supports literal characters, dot (any character), star (*), plus (+), question mark (?), character classes ([abc]), and grouping with parentheses. Implement using NFA construction and simulation. | Object-Oriented Design, NFA, State Machine, Parser, +1 | `651a9e3f` | `Object_Oriented_Design` |
| 6 | Hard | Netflix | Design a workflow engine supporting sequential and parallel task execution, conditional branching, error handling with compensation, task timeout, and workflow versioning. | Object-Oriented Design, State Pattern, Chain of Responsibility, Saga Pattern, +1 | `656dea03` | `Chain_of_Responsibility` · `LLD_DataStructures` · `Object_Oriented_Design` |
| 7 | Hard | Uber | Design a ride-sharing application at the class level with driver/rider registration, ride matching based on proximity, fare estimation, ride lifecycle management (request, match, pickup, trip, dropoff, payment), and rating system. | Object-Oriented Design, State Pattern, Strategy Pattern, Observer Pattern, +1 | `26102174` | `Object_Oriented_Design` · `Observer_Pattern` · `Strategy_Pattern` |
| 8 | Hard | DoorDash | Design a food delivery system like DoorDash at the class level with restaurant onboarding, menu management, order placement, delivery assignment based on proximity/availability, real-time order tracking, and review system. | Object-Oriented Design, State Pattern, Strategy Pattern, Observer Pattern, +1 | `8ee8211f` | `Object_Oriented_Design` · `Observer_Pattern` · `Strategy_Pattern` |
| 9 | Hard | Amazon | Design a movie ticket booking system like BookMyShow with theater/screen management, seat selection with real-time locking, showtime scheduling, pricing tiers, and booking confirmation with QR code generation. | Object-Oriented Design, State Pattern, Locking Mechanism, Seat Selection Algorithm | `3e21d773` | `Object_Oriented_Design` |
| 10 | Hard | Google | Design a chat bot framework supporting intent recognition, entity extraction, conversation state management, context tracking across turns, fallback handling, and integration with external APIs for fulfillment. | Object-Oriented Design, State Machine, Strategy Pattern, NLP, +1 | `76a80a75` | `Object_Oriented_Design` · `Plugin_Architecture` · `Strategy_Pattern` |

---

## Future scope (placeholder)

Once questions are reviewed, the next pass will create per-question walkthrough files in this directory following the vertical's `TEMPLATE-v2.md`. Track those additions in the parent topic's `LEARNING.md` if one exists.