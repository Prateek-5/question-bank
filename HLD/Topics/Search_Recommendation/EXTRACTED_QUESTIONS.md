# Search & Recommendation — Extracted Questions

> **7 questions** sourced from the LeetLens DB (`processed.extracted_questions`, snapshot 2026-05-31).
> Vertical: **HLD** · Bucket: `Search_Recommendation` · Bucket study-order rank in vertical: **9**.
> See [`../../../leetlens-import/STUDY-GUIDE.md`](../../../leetlens-import/STUDY-GUIDE.md) for the cross-vertical sequence.

## How to use this file

- Each row is **metadata only** — question text, difficulty, company, topic tags, LeetLens ID.
- The **Seq** column gives the recommended execution order WITHIN this bucket (Easy → Hard, then by LLM quality score).
- The **⚠️ also fits** annotation lists OTHER buckets the question could appear in (cross-cutting practice).
- When you're ready to author a walkthrough for a question, create a new file alongside this manifest (e.g. `Question_Name.md`) following the vertical's TEMPLATE-v2.md.

## Summary

- **Total:** 7
- **Difficulty mix:** Medium: 2 · Hard: 5
- **Top companies:** Google (4), Meta (2), Amazon (1)

## Questions

| Seq | Difficulty | Company | Question | Topics | LeetLens ID | Also fits |
|---:|---|---|---|---|---|---|
| 1 | Medium | Google | Design a search autocomplete system: prefix-based suggestion generation, personalized suggestions, trending queries, typo tolerance, and serving suggestions with sub-50ms latency at scale. | System Design, Trie, Caching, Personalization, +2 | `26d233af` | `Caching` · `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` · `Messaging_StreamProcessing` |
| 2 | Medium | Google | Design a search engine index for a large dataset | Dijkstra's Algorithm, Graph | `e9c0a06d` | `HLD_Algorithmic_Foundations` |
| 3 | Hard | Google | Design Google Search: web crawling, indexing (inverted index), PageRank, query processing, spell correction, search result ranking, and serving results with sub-200ms latency at global scale. | System Design, Inverted Index, PageRank, Web Crawler, +2 | `847490f1` | `Distributed_Systems_General` |
| 4 | Hard | Amazon | Design Amazon e-commerce platform: product catalog, search with faceted filtering, shopping cart, order management, inventory tracking, payment processing, and recommendation engine for 300M+ products. | System Design, Microservices, Search, Inventory Management, +2 | `703faa8c` | `Distributed_Systems_General` · `Payments_Inventory` |
| 5 | Hard | Meta | Design Twitter/X at scale: support tweet creation, timelines (home and user), follow/unfollow, trending topics, and search. Handle 500M+ daily tweets with sub-second feed generation. | System Design, Fan-out, Timeline Generation, Caching, +2 | `45323261` | `Caching` · `Distributed_Systems_General` · `Messaging_StreamProcessing` |
| 6 | Hard | Meta | Design a short-form video platform like TikTok: video upload and processing, content recommendation feed (For You page), creator tools, live streaming, duets/stitches, and content moderation at scale. | System Design, Video Processing, Recommendation, Content Moderation, +2 | `780b171a` | `Caching` · `Distributed_Systems_General` · `Image_Media_Processing` |
| 7 | Hard | Google | Design a System for Handling User Search | Search, Distributed Systems | `4cf970df` | `Distributed_Systems_General` |

---

## Future scope (placeholder)

Once questions are reviewed, the next pass will create per-question walkthrough files in this directory following the vertical's `TEMPLATE-v2.md`. Track those additions in the parent topic's `LEARNING.md` if one exists.