# Rate Limiting — Extracted Questions

> **20 questions** sourced from the LeetLens DB (`processed.extracted_questions`, snapshot 2026-05-31).
> Vertical: **HLD** · Bucket: `Rate_Limiting` · Bucket study-order rank in vertical: **4**.
> See [`../../../leetlens-import/STUDY-GUIDE.md`](../../../leetlens-import/STUDY-GUIDE.md) for the cross-vertical sequence.

## How to use this file

- Each row is **metadata only** — question text, difficulty, company, topic tags, LeetLens ID.
- The **Seq** column gives the recommended execution order WITHIN this bucket (Easy → Hard, then by LLM quality score).
- The **⚠️ also fits** annotation lists OTHER buckets the question could appear in (cross-cutting practice).
- When you're ready to author a walkthrough for a question, create a new file alongside this manifest (e.g. `Question_Name.md`) following the vertical's TEMPLATE-v2.md.

## Summary

- **Total:** 20
- **Difficulty mix:** Medium: 1 · Hard: 19
- **Top companies:** Amazon (8), Google (5), Meta (2), Stripe (1), Cloudflare (1), Salesforce (1)

## Questions

| Seq | Difficulty | Company | Question | Topics | LeetLens ID | Also fits |
|---:|---|---|---|---|---|---|
| 1 | Medium | Amazon | Design an API gateway: request routing, authentication/authorization, rate limiting, request/response transformation, circuit breaking, load balancing, API versioning, and analytics/logging. | System Design, API Gateway, Rate Limiting, Circuit Breaker, +2 | `2763c522` | `Distributed_Systems_General` · `Load_Balancing` · `Session_Management` |
| 2 | Hard | Cloudflare | Design a rate limiter at scale: support multiple algorithms (token bucket, sliding window), per-user and per-API limits, distributed rate limiting across multiple servers, and graceful degradation under load. | System Design, Rate Limiting, Distributed Systems, Redis, +2 | `53b0478f` | `Caching` · `Consistent_Hashing` · `Distributed_Systems_General` |
| 3 | Hard | Google | Design a web crawler that can crawl billions of pages: URL frontier management, politeness policies (robots.txt, rate limiting), duplicate detection, distributed crawling coordination, and handling dynamic JavaScript-rendered pages. | System Design, Distributed Computing, URL Frontier, Bloom Filter, +2 | `693f7004` | `Distributed_Systems_General` |
| 4 | Hard | Salesforce | Design a multi-tenant SaaS platform: tenant onboarding, data isolation strategies, per-tenant customization, usage-based billing, tenant-level rate limiting, and noisy neighbor prevention. | System Design, Multi-tenancy, Data Isolation, Usage Billing, +2 | `e5648dc6` | `Distributed_Systems_General` |
| 5 | Hard | Stripe | Design a webhook delivery system at scale: reliable webhook event delivery with retry and exponential backoff, signature verification for security, delivery status tracking, dead letter queue for failed webhooks, and rate limiting per endpoint. | System Design, Webhooks, Retry Pattern, Message Queue, +2 | `0599c47f` | `Distributed_Systems_General` · `Messaging_StreamProcessing` |
| 6 | Hard | Amazon | Design a notification system at scale: support push notifications, email, SMS, and in-app notifications with user preference management, templating, batching, rate limiting, and delivery tracking for 1B+ users. | System Design, Message Queue, Rate Limiting, Template Engine, +2 | `734c7217` | `Distributed_Systems_General` · `Messaging_StreamProcessing` |
| 7 | Hard | Amazon | Design a coupon distribution system for a flash sale: generate unique coupons, prevent double-claiming under extreme concurrency, enforce time-window validity, track redemption, and handle 100K+ claims per second. | System Design, Concurrency Control, Rate Limiting, Distributed Locks, +1 | `4433cfbc` | `Distributed_Systems_General` · `Payments_Inventory` |
| 8 | Hard | Amazon | Design a distributed rate limiter for an API gateway | Rate Limiting, Distributed Systems, Redis | `0383ea4b` | `Caching` · `Distributed_Systems_General` |
| 9 | Hard | Amazon | Design a distributed rate limiter for an API gateway | Rate Limiting, Distributed Systems, Redis | `3f2c506c` | `Caching` · `Distributed_Systems_General` |
| 10 | Hard | Amazon | Design a distributed rate limiter for an API gateway | Rate Limiting, Distributed Systems, Redis | `5611cc14` | `Caching` · `Distributed_Systems_General` |
| 11 | Hard | Amazon | Design a distributed rate limiter for an API gateway | Rate Limiting, Distributed Systems, Redis | `cd6b4861` | `Caching` · `Distributed_Systems_General` |
| 12 | Hard | Amazon | Design a distributed rate limiter for an API gateway | Rate Limiting, Distributed Systems, Redis | `e21ea57d` | `Caching` · `Distributed_Systems_General` |
| 13 | Hard | Google | Design a distributed rate limiter for an API gateway | Rate Limiting, Distributed Systems, Redis | `037278ef` | `Caching` · `Distributed_Systems_General` |
| 14 | Hard | Google | Design a distributed rate limiter for an API gateway | Rate Limiting, Distributed Systems, Redis | `15c5ff34` | `Caching` · `Distributed_Systems_General` |
| 15 | Hard | Google | Design Twitter | Distributed Systems, Rate Limiting | `7d8c4bee` | `Distributed_Systems_General` |
| 16 | Hard | Google | Design a distributed rate limiter for an API gateway | Rate Limiting, Distributed Systems, Redis | `e1c4a3d8` | `Caching` · `Distributed_Systems_General` |
| 17 | Hard | Meta | Design a load balancer for a web application with high traffic and low latency, using a combination of caching and rate limiting | Graph | `1954ebb8` | `HLD_Algorithmic_Foundations` · `Load_Balancing` |
| 18 | Hard | Meta | Design a load balancing system for a web application with high traffic and low latency, using a combination of caching and rate limiting, and a time-based eviction policy | Graph | `4b81d853` | `HLD_Algorithmic_Foundations` · `Load_Balancing` |
| 19 | Hard | — | Design a distributed rate limiter for an API gateway | Rate Limiting, Distributed Systems, Redis | `2fe621b2` | `Caching` · `Distributed_Systems_General` |
| 20 | Hard | — | Design a distributed rate limiter for an API gateway | Rate Limiting, Distributed Systems, Redis | `fed3fcc7` | `Caching` · `Distributed_Systems_General` |

---

## Future scope (placeholder)

Once questions are reviewed, the next pass will create per-question walkthrough files in this directory following the vertical's `TEMPLATE-v2.md`. Track those additions in the parent topic's `LEARNING.md` if one exists.