# Load Balancing — Extracted Questions

> **19 questions** sourced from the LeetLens DB (`processed.extracted_questions`, snapshot 2026-05-31).
> Vertical: **HLD** · Bucket: `Load_Balancing` · Bucket study-order rank in vertical: **2**.
> See [`../../../leetlens-import/STUDY-GUIDE.md`](../../../leetlens-import/STUDY-GUIDE.md) for the cross-vertical sequence.

## How to use this file

- Each row is **metadata only** — question text, difficulty, company, topic tags, LeetLens ID.
- The **Seq** column gives the recommended execution order WITHIN this bucket (Easy → Hard, then by LLM quality score).
- The **⚠️ also fits** annotation lists OTHER buckets the question could appear in (cross-cutting practice).
- When you're ready to author a walkthrough for a question, create a new file alongside this manifest (e.g. `Question_Name.md`) following the vertical's TEMPLATE-v2.md.

## Summary

- **Total:** 19
- **Difficulty mix:** Medium: 5 · Hard: 14
- **Top companies:** Google (7), Meta (5), Cloudflare (1), Amazon (1)

## Questions

| Seq | Difficulty | Company | Question | Topics | LeetLens ID | Also fits |
|---:|---|---|---|---|---|---|
| 1 | Medium | Amazon | Design a load balancer: L4 vs L7 load balancing, algorithm selection (round-robin, least connections, consistent hashing, weighted), health checking, session affinity, SSL termination, and auto-scaling integration. | System Design, Load Balancing, Health Checking, SSL Termination, +2 | `55fc3419` | `Consistent_Hashing` · `Distributed_Systems_General` |
| 2 | Medium | Google | Design a load balancer for a cloud-based application | Dijkstra's Algorithm, Graph | `664b1680` | `HLD_Algorithmic_Foundations` |
| 3 | Medium | Google | Design a load balancer for a cloud-based application | Dijkstra's Algorithm, Graph | `860d7edb` | `HLD_Algorithmic_Foundations` |
| 4 | Medium | Google | Design a System for Handling High Traffic Websites | Load Balancing, Distributed Systems | `e59cd89a` | `Distributed_Systems_General` |
| 5 | Medium | Google | Design a load balancer for a cloud-based application | Dijkstra's Algorithm, Graph | `ebf02671` | `HLD_Algorithmic_Foundations` |
| 6 | Hard | Cloudflare | Design a Content Delivery Network (CDN): edge server placement strategy, content caching and invalidation, origin shield, load balancing across PoPs, SSL termination, and DDoS protection. | System Design, CDN, Caching, Load Balancing, +2 | `0b94d7e9` | `Caching` · `Distributed_Systems_General` |
| 7 | Hard | Google | Design a distributed system with load balancing and failover | Load Balancing, Distributed Systems | `078489c4` | `Distributed_Systems_General` |
| 8 | Hard | Google | Design a Load Balancer for a E-commerce Platform | Load Balancing, Distributed Systems | `11a0ae72` | `Distributed_Systems_General` |
| 9 | Hard | Google | Design a load balancing system for a cloud-based application | Cache Invalidation, Redis | `8f5421f4` | `Caching` |
| 10 | Hard | Meta | Design a load balancer for a web application with high traffic | Graph | `1da29d4d` | `HLD_Algorithmic_Foundations` |
| 11 | Hard | Meta | Design a distributed system for storing and retrieving data with high availability, scalability, low latency, and high performance, using a combination of caching and load balancing | Graph, Distributed Systems | `2c72d0d0` | `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` |
| 12 | Hard | Meta | Design a load balancing system for a web application with high traffic and low latency | Graph | `6898831e` | `HLD_Algorithmic_Foundations` |
| 13 | Hard | Meta | Design a distributed system for storing and retrieving data with high availability, scalability, and low latency, using a combination of caching and load balancing | Graph, Distributed Systems | `95d4c469` | `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` |
| 14 | Hard | Meta | Design a load balancing system for a web application | Graph | `e2be0df3` | `HLD_Algorithmic_Foundations` |
| 15 | Hard | — | Design a distributed hash table (DHT) with load balancing | Distributed Systems, Hash Table, Load Balancing | `6813c37a` | `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` |
| 16 | Hard | — | Design a distributed hash table (DHT) with data compression and encryption, and load balancing | Distributed Systems, Hash Table, Data Compression, Data Encryption, +1 | `6b7b7a12` | `Data_Storage_Retrieval` · `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` · `Session_Management` |
| 17 | Hard | — | Design a load balancing system for a web application | Graph, Distributed Systems | `b5560568` | `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` |
| 18 | Hard | — | Design a distributed hash table (DHT) with data deduplication and encryption, and load balancing | Distributed Systems, Hash Table, Data Deduplication, Data Encryption, +1 | `bcc7d82e` | `Data_Storage_Retrieval` · `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` · `Session_Management` |
| 19 | Hard | — | Design a distributed hash table (DHT) with data anonymization and encryption, and load balancing | Distributed Systems, Hash Table, Data Anonymization, Data Encryption, +1 | `c269a972` | `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` · `Session_Management` |

---

## Future scope (placeholder)

Once questions are reviewed, the next pass will create per-question walkthrough files in this directory following the vertical's `TEMPLATE-v2.md`. Track those additions in the parent topic's `LEARNING.md` if one exists.