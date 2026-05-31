# High-Level Design — Vertical Overview

> Net-new vertical seeded from the LeetLens DB. **361 questions** across **17 buckets**.
> Snapshot: 2026-05-31. See [`../leetlens-import/STUDY-GUIDE.md`](../leetlens-import/STUDY-GUIDE.md) for the cross-vertical study sequence.

## Structure

```
HLD/
├── LEARNING.md            (you are here)
├── TEMPLATE-v2.md         (HLD walkthrough template — capacity-first, diagram-required)
└── Topics/
    └── <Bucket>/
        ├── EXTRACTED_QUESTIONS.md   (metadata manifest from LeetLens)
        └── <Question>.md            (author later, following TEMPLATE-v2.md)
```

## Buckets in study order

| # | Bucket | Count | Difficulty mix |
|---|---|---:|---|
| 1 | [`Caching`](./Topics/Caching/EXTRACTED_QUESTIONS.md) | 34 | Medium:16 · Hard:18 |
| 2 | [`Load Balancing`](./Topics/Load_Balancing/EXTRACTED_QUESTIONS.md) | 19 | Medium:5 · Hard:14 |
| 3 | [`Consistent Hashing`](./Topics/Consistent_Hashing/EXTRACTED_QUESTIONS.md) | 2 | Hard:2 |
| 4 | [`Rate Limiting`](./Topics/Rate_Limiting/EXTRACTED_QUESTIONS.md) | 20 | Medium:1 · Hard:19 |
| 5 | [`Session Management & Auth`](./Topics/Session_Management/EXTRACTED_QUESTIONS.md) | 8 | Medium:2 · Hard:6 |
| 6 | [`Messaging & Stream Processing`](./Topics/Messaging_StreamProcessing/EXTRACTED_QUESTIONS.md) | 34 | Medium:3 · Hard:31 |
| 7 | [`Data Storage & Retrieval`](./Topics/Data_Storage_Retrieval/EXTRACTED_QUESTIONS.md) | 24 | Medium:1 · Hard:23 |
| 8 | [`URL Shortener`](./Topics/URL_Shortener/EXTRACTED_QUESTIONS.md) | 24 | Medium:1 · Hard:23 |
| 9 | [`Search & Recommendation`](./Topics/Search_Recommendation/EXTRACTED_QUESTIONS.md) | 7 | Medium:2 · Hard:5 |
| 10 | [`Geospatial Services`](./Topics/Geospatial/EXTRACTED_QUESTIONS.md) | 1 | Medium:1 |
| 11 | [`Payments & Inventory`](./Topics/Payments_Inventory/EXTRACTED_QUESTIONS.md) | 5 | Medium:1 · Hard:4 |
| 12 | [`A/B Testing`](./Topics/AB_Testing/EXTRACTED_QUESTIONS.md) | 2 | Medium:2 |
| 13 | [`Image / Media Processing`](./Topics/Image_Media_Processing/EXTRACTED_QUESTIONS.md) | 2 | Hard:2 |
| 14 | [`Versioning & Schema`](./Topics/Versioning_Schema/EXTRACTED_QUESTIONS.md) | 1 | Medium:1 |
| 15 | [`HLD Algorithmic Foundations`](./Topics/HLD_Algorithmic_Foundations/EXTRACTED_QUESTIONS.md) | 128 | Medium:57 · Hard:71 |
| 16 | [`Distributed Systems (general)`](./Topics/Distributed_Systems_General/EXTRACTED_QUESTIONS.md) | 47 | Medium:9 · Hard:38 |
| — | [`Uncategorized`](./EXTRACTED_UNCATEGORIZED.md) | 3 | — |
| **Total** | | **361** | |

## TEMPLATE-v2.md status

✅ **[`./TEMPLATE-v2.md`](./TEMPLATE-v2.md) is live** — full HLD walkthrough template covering 16 required sections (clarifying questions → capacity estimation → data model → architecture diagram → component deep-dives → bottleneck analysis → failure modes → scaling story → tradeoffs). Two non-negotiables: capacity numbers and architecture diagrams (via excalidraw).

## Canonical sample walkthrough

✅ **[`./Topics/URL_Shortener/URL_Shortener_Design.md`](./Topics/URL_Shortener/URL_Shortener_Design.md)** — first complete v2 HLD walkthrough following the template. Read-heavy KV-store archetype with hot-key mitigation + asynchronous analytics. Includes sibling excalidraw files:

- [`./Topics/URL_Shortener/URL_Shortener_Design.architecture.excalidraw`](./Topics/URL_Shortener/URL_Shortener_Design.architecture.excalidraw) — full system architecture (open in [excalidraw.com](https://excalidraw.com))
- [`./Topics/URL_Shortener/URL_Shortener_Design.sequence.excalidraw`](./Topics/URL_Shortener/URL_Shortener_Design.sequence.excalidraw) — redirect path with cache HIT / MISS scenarios

## Future scope

The vertical is now READY for systematic authoring. Next steps:

1. Review the URL Shortener sample for depth / numbers / tradeoff calibration. Fine-tune the template based on what works.
2. Pick the next bucket. Recommendations: `Caching` (34 Qs, foundational) or `Rate_Limiting` (20 Qs, infra primitive) — both unlock many subsequent archetypes.
3. Author per-question walkthroughs alongside their bucket's `EXTRACTED_QUESTIONS.md`, following the template + URL Shortener exemplar.
4. As walkthroughs land, update each bucket's `EXTRACTED_QUESTIONS.md` to mark covered LeetLens IDs.