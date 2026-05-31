# Caching — Extracted Questions

> **34 questions** sourced from the LeetLens DB (`processed.extracted_questions`, snapshot 2026-05-31).
> Vertical: **HLD** · Bucket: `Caching` · Bucket study-order rank in vertical: **1**.
> See [`../../../leetlens-import/STUDY-GUIDE.md`](../../../leetlens-import/STUDY-GUIDE.md) for the cross-vertical sequence.

## How to use this file

- Each row is **metadata only** — question text, difficulty, company, topic tags, LeetLens ID.
- The **Seq** column gives the recommended execution order WITHIN this bucket (Easy → Hard, then by LLM quality score).
- The **⚠️ also fits** annotation lists OTHER buckets the question could appear in (cross-cutting practice).
- When you're ready to author a walkthrough for a question, create a new file alongside this manifest (e.g. `Question_Name.md`) following the vertical's TEMPLATE-v2.md.

## Summary

- **Total:** 34
- **Difficulty mix:** Medium: 16 · Hard: 18
- **Top companies:** Google (24), Meta (2), Amazon (2), Microsoft (1), Cloudflare (1), Netflix (1)

## Questions

| Seq | Difficulty | Company | Question | Topics | LeetLens ID | Also fits |
|---:|---|---|---|---|---|---|
| 1 | Medium | Microsoft | Design a package registry like npm or PyPI: package publishing with versioning, dependency resolution, download serving via CDN, vulnerability scanning, namespace management, and download analytics. | System Design, Package Registry, Dependency Resolution, CDN, +2 | `0c301e96` | `Distributed_Systems_General` · `Versioning_Schema` |
| 2 | Medium | Meta | Design a photo sharing service with image upload, processing (resize, compress, filter), storage, CDN distribution, photo albums, tagging, and privacy controls for billions of photos. | System Design, Image Processing, Object Storage, CDN, +2 | `5a31b0a6` | `Distributed_Systems_General` · `Image_Media_Processing` |
| 3 | Medium | Google | Design a System for Handling User Sessions with Redis Cluster and Replication and Transactions and Locks and Transactions and Transactions | Session Management, Redis | `093439bf` | `Session_Management` |
| 4 | Medium | Google | Design a Distributed Cache System | Distributed Systems, Cache Design | `2919d7fd` | `Distributed_Systems_General` |
| 5 | Medium | Google | Design a Distributed Cache System (part 1) | Distributed Systems, Cache Design | `2fa98e42` | `Distributed_Systems_General` |
| 6 | Medium | Google | Design a System for Handling User Sessions with Redis Cluster and Replication and Transactions and Locks | Session Management, Redis | `3347b6bb` | `Session_Management` |
| 7 | Medium | Google | Design a Distributed Cache System (part 1) | Distributed Systems, Cache Design | `6b1069df` | `Distributed_Systems_General` |
| 8 | Medium | Google | Design a System for Handling User Sessions with Redis Cluster and Replication and Transactions and Locks and Transactions and Transactions and Transactions and Transactions | Session Management, Redis | `6db19f6e` | `Session_Management` |
| 9 | Medium | Google | Two Team Matching Calls (not matched) | Distributed Systems, Redis | `7df0f584` | `Distributed_Systems_General` |
| 10 | Medium | Google | Design a Distributed Cache System (part 1) | Distributed Systems, Cache Design | `826dff5d` | `Distributed_Systems_General` |
| 11 | Medium | Google | Design a caching system for a web application | Cache Invalidation, Redis | `89079e80` | — |
| 12 | Medium | Google | Design a System for Handling User Sessions with Redis Cluster and Replication | Session Management, Redis | `9b0dae45` | `Session_Management` |
| 13 | Medium | Google | Two Team Matching Calls (matched) | Distributed Systems, Redis | `c1c7bb08` | `Distributed_Systems_General` |
| 14 | Medium | Google | Design an elevator | Distributed Systems, Redis | `cd99d98f` | `Distributed_Systems_General` |
| 15 | Medium | Google | Design a System for Handling User Sessions with Redis Cluster | Session Management, Redis | `f3b1e293` | `Session_Management` |
| 16 | Medium | Google | Design a Cache System for an E-commerce Platform | Caching, Distributed Systems | `f43b1266` | `Distributed_Systems_General` |
| 17 | Hard | Netflix | Design a video streaming platform like Netflix: video upload and transcoding pipeline, adaptive bitrate streaming (HLS/DASH), content delivery via CDN, recommendation engine, and viewing analytics at scale. | System Design, CDN, Video Transcoding, Adaptive Bitrate, +2 | `5f35e518` | `Distributed_Systems_General` · `Image_Media_Processing` · `Search_Recommendation` |
| 18 | Hard | Amazon | Design a distributed cache like Redis: in-memory key-value storage, data structures (strings, lists, sets, sorted sets, hashes), replication, cluster mode with hash slots, persistence (RDB/AOF), and pub/sub. | System Design, Distributed Cache, Consistent Hashing, Replication, +2 | `80864ae2` | `Consistent_Hashing` · `Data_Storage_Retrieval` · `Distributed_Systems_General` |
| 19 | Hard | Meta | Design a social graph service: friend/follow relationships, friend-of-friend queries, mutual friends computation, friend recommendations, and graph traversal at scale for 2B+ users. | System Design, Graph Database, Graph Traversal, Caching, +2 | `19b963ab` | `Distributed_Systems_General` |
| 20 | Hard | Amazon | Design a live streaming platform like Twitch: live video ingestion (RTMP), transcoding for multiple qualities, CDN distribution, real-time chat, viewer count tracking, and VOD recording. | System Design, Live Streaming, RTMP, Transcoding, +2 | `f169da81` | `Distributed_Systems_General` · `Messaging_StreamProcessing` |
| 21 | Hard | Cloudflare | Design a global-scale DNS system: hierarchical name resolution, caching at multiple levels, zone file management, DNSSEC for security, anycast routing for availability, and handling billions of queries per day. | System Design, DNS, Caching, Anycast, +2 | `3449071f` | `Distributed_Systems_General` |
| 22 | Hard | Google | Design a Distributed Cache System | Distributed Systems, Caching | `223ddc11` | `Distributed_Systems_General` |
| 23 | Hard | Google | Design a System for Handling User Sessions with Memcached | Session Management, Memcached | `445c1bab` | `Session_Management` |
| 24 | Hard | Google | Design a Distributed Cache System (part 1) | Distributed Systems, Caching | `6bca6ae8` | `Distributed_Systems_General` |
| 25 | Hard | Google | Design a System for Handling User Sessions with Redis Cluster and Replication and Transactions and Locks and Transactions and Transactions and Transactions | Session Management, Redis | `90d74042` | `Session_Management` |
| 26 | Hard | Google | Design a Distributed Cache System (part 2) | Distributed Systems, Caching | `934f5f1e` | `Distributed_Systems_General` |
| 27 | Hard | Google | Design Twitter | Distributed Systems, Redis | `96460cfd` | `Distributed_Systems_General` |
| 28 | Hard | Google | Design a System for Handling User Sessions with Redis Cluster and Replication and Transactions and Locks and Transactions | Session Management, Redis | `d50ee069` | `Session_Management` |
| 29 | Hard | Google | Design a distributed system for storing and retrieving data from multiple databases | Distributed Systems, Redis | `df1da748` | `Distributed_Systems_General` |
| 30 | Hard | Google | Design a System for Handling User Sessions with Redis Cluster and Replication and Transactions | Session Management, Redis | `ea9a5f2b` | `Session_Management` |
| 31 | Hard | Google | Design a distributed cache system for a large-scale e-commerce platform | Distributed Systems, Cache | `f41ff7ce` | `Distributed_Systems_General` |
| 32 | Hard | — | Design Twitter | Distributed Systems, Redis | `51ab82f3` | `Distributed_Systems_General` |
| 33 | Hard | — | Design LRU Cache | Distributed Systems, Redis | `9b966442` | `Distributed_Systems_General` |
| 34 | Hard | — | Design a distributed cache system | Distributed Systems, Cache | `b0ce2939` | `Distributed_Systems_General` |

---

## Future scope (placeholder)

Once questions are reviewed, the next pass will create per-question walkthrough files in this directory following the vertical's `TEMPLATE-v2.md`. Track those additions in the parent topic's `LEARNING.md` if one exists.