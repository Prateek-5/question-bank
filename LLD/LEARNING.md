# Low-Level Design — Vertical Overview

> Net-new vertical seeded from the LeetLens DB. **146 questions** across **19 buckets**.
> Snapshot: 2026-05-31. See [`../leetlens-import/STUDY-GUIDE.md`](../leetlens-import/STUDY-GUIDE.md) for the cross-vertical study sequence.

## Structure

```
LLD/
├── LEARNING.md            (you are here)
├── TEMPLATE-v2.md         (LLD walkthrough template — pattern-discrimination focus)
└── Topics/
    └── <Bucket>/
        ├── EXTRACTED_QUESTIONS.md   (metadata manifest from LeetLens)
        └── <Question>.md            (author later, following TEMPLATE-v2.md)
```

## Buckets in study order

| # | Bucket | Count | Difficulty mix |
|---|---|---:|---|
| 1 | [`Object-Oriented Design`](./Topics/Object_Oriented_Design/EXTRACTED_QUESTIONS.md) | 26 | Medium:12 · Hard:14 |
| 2 | [`SOLID Principles`](./Topics/SOLID_Principles/EXTRACTED_QUESTIONS.md) | 1 | Medium:1 |
| 3 | [`Data-Structure Implementations`](./Topics/LLD_DataStructures/EXTRACTED_QUESTIONS.md) | 60 | Medium:50 · Hard:10 |
| 4 | [`Factory Pattern`](./Topics/Factory_Pattern/EXTRACTED_QUESTIONS.md) | 1 | Medium:1 |
| 5 | [`Builder Pattern`](./Topics/Builder_Pattern/EXTRACTED_QUESTIONS.md) | 1 | Medium:1 |
| 6 | [`Strategy Pattern`](./Topics/Strategy_Pattern/EXTRACTED_QUESTIONS.md) | 17 | Medium:10 · Hard:7 |
| 7 | [`Observer Pattern`](./Topics/Observer_Pattern/EXTRACTED_QUESTIONS.md) | 12 | Medium:9 · Hard:3 |
| 8 | [`State Pattern`](./Topics/State_Pattern/EXTRACTED_QUESTIONS.md) | 10 | Medium:3 · Hard:7 |
| 9 | [`Command Pattern`](./Topics/Command_Pattern/EXTRACTED_QUESTIONS.md) | 3 | Medium:1 · Hard:2 |
| 10 | [`Chain of Responsibility`](./Topics/Chain_of_Responsibility/EXTRACTED_QUESTIONS.md) | 1 | Medium:1 |
| 11 | [`Template Method`](./Topics/Template_Method/EXTRACTED_QUESTIONS.md) | 1 | Medium:1 |
| 12 | [`Iterator Pattern`](./Topics/Iterator_Pattern/EXTRACTED_QUESTIONS.md) | 1 | Medium:1 |
| 13 | [`Decorator Pattern`](./Topics/Decorator_Pattern/EXTRACTED_QUESTIONS.md) | 1 | Hard:1 |
| 14 | [`Composite Pattern`](./Topics/Composite_Pattern/EXTRACTED_QUESTIONS.md) | 2 | Hard:2 |
| 15 | [`Interceptor Pattern`](./Topics/Interceptor_Pattern/EXTRACTED_QUESTIONS.md) | 1 | Medium:1 |
| 16 | [`Plugin Architecture`](./Topics/Plugin_Architecture/EXTRACTED_QUESTIONS.md) | 2 | Hard:2 |
| 17 | [`Dependency Injection`](./Topics/Dependency_Injection/EXTRACTED_QUESTIONS.md) | 1 | Hard:1 |
| 18 | [`Rule Engine / RBAC`](./Topics/Rule_Engine/EXTRACTED_QUESTIONS.md) | 2 | Medium:1 · Hard:1 |
| 19 | [`Retry / Circuit Breaker`](./Topics/Retry_Pattern/EXTRACTED_QUESTIONS.md) | 3 | Medium:3 |
| **Total** | | **146** | |

## TEMPLATE-v2.md status

✅ **[`./TEMPLATE-v2.md`](./TEMPLATE-v2.md) is live** — full LLD walkthrough template covering 14 required sections (clarifying questions → entity/verb extraction → variability points → pattern choice → UML diagram → skeleton code → sequence diagram → extensibility → anti-patterns → self-check). Pattern-discrimination cheatsheets and excalidraw diagram conventions are documented inline.

## Canonical sample walkthrough

✅ **[`./Topics/Object_Oriented_Design/Parking_Lot.md`](./Topics/Object_Oriented_Design/Parking_Lot.md)** — first complete v2 LLD walkthrough following the template. Uses Strategy + State + Factory patterns. Includes sibling excalidraw files:

- [`./Topics/Object_Oriented_Design/Parking_Lot.class-diagram.excalidraw`](./Topics/Object_Oriented_Design/Parking_Lot.class-diagram.excalidraw) — UML class diagram (open in [excalidraw.com](https://excalidraw.com))
- [`./Topics/Object_Oriented_Design/Parking_Lot.sequence.excalidraw`](./Topics/Object_Oriented_Design/Parking_Lot.sequence.excalidraw) — sequence diagram for the park → pay → exit flow

## Future scope

The vertical is now READY for systematic authoring. Next steps:

1. Review the Parking Lot sample for tone / depth / pattern. Fine-tune the template based on what works or doesn't.
2. Pick the next bucket. Recommendations: start with `Strategy_Pattern` (17 Qs, most common in interviews) or `Observer_Pattern` (12 Qs, high-impact).
3. Author per-question walkthroughs alongside their bucket's `EXTRACTED_QUESTIONS.md`, following the template + Parking Lot exemplar.
4. As walkthroughs land, update each bucket's `EXTRACTED_QUESTIONS.md` to mark covered LeetLens IDs.