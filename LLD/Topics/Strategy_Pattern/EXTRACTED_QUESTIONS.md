# Strategy Pattern — Extracted Questions

> **17 questions** sourced from the LeetLens DB (`processed.extracted_questions`, snapshot 2026-05-31).
> Vertical: **LLD** · Bucket: `Strategy_Pattern` · Bucket study-order rank in vertical: **7**.
> See [`../../../leetlens-import/STUDY-GUIDE.md`](../../../leetlens-import/STUDY-GUIDE.md) for the cross-vertical sequence.

## How to use this file

- Each row is **metadata only** — question text, difficulty, company, topic tags, LeetLens ID.
- The **Seq** column gives the recommended execution order WITHIN this bucket (Easy → Hard, then by LLM quality score).
- The **⚠️ also fits** annotation lists OTHER buckets the question could appear in (cross-cutting practice).
- When you're ready to author a walkthrough for a question, create a new file alongside this manifest (e.g. `Question_Name.md`) following the vertical's TEMPLATE-v2.md.

## Summary

- **Total:** 17
- **Difficulty mix:** Medium: 10 · Hard: 7
- **Top companies:** Amazon (7), Google (2), Meta (2), Stripe (2), Netflix (2), Spotify (1), eBay (1)

## Questions

| Seq | Difficulty | Company | Question | Topics | LeetLens ID | Also fits |
|---:|---|---|---|---|---|---|
| 1 | Medium | Amazon | Design a notification service at the class level supporting multiple channels (email, SMS, push notification, in-app), template management, user preference handling, batching, and retry logic. | Object-Oriented Design, Strategy Pattern, Observer Pattern, Template Method, +1 | `3bf3ca90` | `Object_Oriented_Design` · `Observer_Pattern` · `Retry_Pattern` · `Template_Method` |
| 2 | Medium | Netflix | Design a feature toggle service at the class level supporting boolean flags, percentage rollouts, user segment targeting, mutual exclusion groups, and flag dependency management. Include an SDK for client integration. | Object-Oriented Design, Feature Flags, Strategy Pattern, Targeting Rules, +1 | `eee89a2c` | `Object_Oriented_Design` |
| 3 | Medium | Amazon | Design an online shopping cart with product catalog browsing, cart management (add/remove/update quantity), coupon/discount application, tax calculation, and checkout flow with order creation. | Object-Oriented Design, Strategy Pattern, Decorator Pattern, State Pattern | `3d164b11` | `Decorator_Pattern` · `Object_Oriented_Design` · `State_Pattern` |
| 4 | Medium | Amazon | Design a load testing framework at the class level supporting configurable user scenarios, ramp-up patterns, request rate control, response time measurement, percentile calculation (P50/P95/P99), and result reporting. | Object-Oriented Design, Load Testing, Strategy Pattern, Statistics, +2 | `c8510771` | `Object_Oriented_Design` |
| 5 | Medium | Amazon | Design a coupon/discount engine supporting percentage off, flat amount off, buy-one-get-one, tiered discounts, combinable vs exclusive coupons, and usage limits per user/global. Handle the discount stacking priority. | Object-Oriented Design, Strategy Pattern, Chain of Responsibility, Decorator Pattern, +1 | `e1b697b7` | `Chain_of_Responsibility` · `Decorator_Pattern` · `Object_Oriented_Design` · `Rule_Engine` |
| 6 | Medium | Amazon | Design a car rental system with vehicle fleet management, reservation booking with date ranges, customer profiles, pricing strategies (daily, weekly, per-mile), insurance options, and late return penalty calculation. | Object-Oriented Design, Strategy Pattern, State Pattern, Date Range | `fc5aeac8` | `Object_Oriented_Design` · `State_Pattern` |
| 7 | Medium | Amazon | Design a Battleship game supporting grid setup, ship placement with rotation, turn-based attack system, hit/miss tracking, ship sinking detection, and game end condition. Support both human and AI players. | Object-Oriented Design, Strategy Pattern, Grid Data Structure, Game Design, +1 | `836db4b6` | `Object_Oriented_Design` |
| 8 | Medium | Spotify | Design a media player application supporting multiple audio/video formats, playlist management, playback controls (play, pause, seek, speed), equalizer settings, and subtitle handling. | Object-Oriented Design, Strategy Pattern, State Pattern, Adapter Pattern, +1 | `81aa67a3` | `Object_Oriented_Design` · `State_Pattern` |
| 9 | Medium | Amazon | Design a deck of cards system that supports multiple card games (Poker, Blackjack, Rummy). Include deck shuffling, dealing, hand evaluation, and game-specific rule engines. | Object-Oriented Design, Strategy Pattern, Template Method Pattern, Enum Design | `0e9a55ef` | `Object_Oriented_Design` · `Template_Method` |
| 10 | Medium | Meta | Design a Tic-Tac-Toe game supporting a configurable N x N board, two players, win condition checking (row, column, diagonal), and draw detection. Extend it to support an AI opponent using minimax. | Object-Oriented Design, Minimax Algorithm, Strategy Pattern, Game Theory | `559033fe` | `Object_Oriented_Design` |
| 11 | Hard | Stripe | Design a payment processing system supporting multiple payment methods (credit card, debit card, UPI, wallet), transaction lifecycle management, refund handling, idempotency, and fraud detection hooks. | Object-Oriented Design, Strategy Pattern, State Pattern, Idempotency, +1 | `b66b6bd7` | `Object_Oriented_Design` · `State_Pattern` |
| 12 | Hard | Stripe | Design a rate limiter class supporting fixed window, sliding window, token bucket, and leaky bucket algorithms. It should be configurable per-client and support distributed usage with a shared store. | Object-Oriented Design, Strategy Pattern, Token Bucket, Sliding Window, +1 | `54f14e02` | `LLD_DataStructures` · `Object_Oriented_Design` |
| 13 | Hard | Google | Design a calendar application supporting event creation with recurrence rules (daily, weekly, monthly, custom), conflict detection, timezone handling, shared calendars, and event reminders. | Object-Oriented Design, Strategy Pattern, Iterator Pattern, Timezone Handling, +1 | `06a3090b` | `Iterator_Pattern` · `Object_Oriented_Design` |
| 14 | Hard | Meta | Design a social media feed system at the class level with post creation (text, image, video), like/comment/share actions, follow/unfollow, and a feed generation algorithm (chronological and ranked). | Object-Oriented Design, Strategy Pattern, Observer Pattern, Feed Ranking | `4c65863a` | `Object_Oriented_Design` · `Observer_Pattern` |
| 15 | Hard | Google | Design an airline reservation system with flight search, seat selection (economy, business, first class), booking with passenger details, cancellation policies, frequent flyer program, and overbooking management. | Object-Oriented Design, Strategy Pattern, State Pattern, Inventory Management, +1 | `f44a6d2c` | `Object_Oriented_Design` · `State_Pattern` |
| 16 | Hard | Netflix | Design a data validation and transformation pipeline (ETL at class level) that reads from multiple sources, applies configurable transformations, validates data against schemas, and writes to multiple sinks. Support error handling and dead letter output. | Object-Oriented Design, Pipeline Pattern, Strategy Pattern, Adapter Pattern, +1 | `71657d0f` | `Object_Oriented_Design` |
| 17 | Hard | eBay | Design an auction system supporting English (ascending), Dutch (descending), and sealed-bid auctions. Include bid validation, time-based auction closing, winner determination, and anti-sniping extensions. | Object-Oriented Design, Strategy Pattern, State Pattern, Template Method | `899ce857` | `Object_Oriented_Design` · `State_Pattern` · `Template_Method` |

---

## Future scope (placeholder)

Once questions are reviewed, the next pass will create per-question walkthrough files in this directory following the vertical's `TEMPLATE-v2.md`. Track those additions in the parent topic's `LEARNING.md` if one exists.