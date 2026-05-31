# LeetLens — HLD Questions (Categorized)

> **337 questions** from `processed.extracted_questions` (snapshot 2026-05-31).
> Buckets are listed in **pedagogical study order** — go top-down for a structured path.
> Within each bucket, questions are sorted Easy → Medium → Hard.
> Companion file: [`STUDY-GUIDE.md`](./STUDY-GUIDE.md) for the cross-category sequence.

## Bucket index (in study order)

| # | Bucket | Count | Difficulty mix | Layer |
|---|---|---:|---|---|
| 1 | [`Caching`](#caching) | 34 | Medium:16 · Hard:18 | Infra primitive — start here |
| 2 | [`Load Balancing`](#load_balancing) | 19 | Medium:5 · Hard:14 | Infra primitive |
| 3 | [`Consistent Hashing`](#consistent_hashing) | 2 | Hard:2 | Infra primitive |
| 4 | [`Rate Limiting`](#rate_limiting) | 20 | Medium:1 · Hard:19 | Infra pattern |
| 5 | [`Session Management & Auth`](#session_management) | 8 | Medium:2 · Hard:6 | Infra pattern |
| 6 | [`Messaging & Stream Processing`](#messaging_streamprocessing) | 34 | Medium:3 · Hard:31 | Infra pattern |
| 7 | [`Data Storage & Retrieval`](#data_storage_retrieval) | 24 | Medium:1 · Hard:23 | Infra pattern |
| 8 | [`URL Shortener`](#url_shortener) | 24 | Medium:1 · Hard:23 | Classic archetype |
| 9 | [`Search & Recommendation`](#search_recommendation) | 7 | Medium:2 · Hard:5 | Classic archetype |
| 10 | [`Geospatial Services`](#geospatial) | 1 | Medium:1 | Classic archetype |
| 11 | [`Payments & Inventory`](#payments_inventory) | 5 | Medium:1 · Hard:4 | Classic archetype |
| 12 | [`A/B Testing`](#ab_testing) | 2 | Medium:2 | Classic archetype |
| 13 | [`Image / Media Processing`](#image_media_processing) | 2 | Hard:2 | Classic archetype |
| 14 | [`Versioning & Schema`](#versioning_schema) | 1 | Medium:1 | Niche |
| 15 | [`HLD Algorithmic Foundations`](#hld_algorithmic_foundations) | 128 | Medium:57 · Hard:71 | Algo-heavy HLD |
| 16 | [`Distributed Systems (general)`](#distributed_systems_general) | 23 | Medium:9 · Hard:14 | Catch-all — review individually |
| 17 | [`Uncategorized`](#uncategorized) | 3 | Medium:2 · Hard:1 | Needs manual review |
| **Total** | | **337** | | |

---

## <a id="caching"></a>1. Caching — 34 questions

_Layer: **Infra primitive — start here**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Google | Session Management, Redis | Design a System for Handling User Sessions with Redis Cluster and Replication and Transactions and Locks and Transactions and Transactions ⚠️ also fits: `Session_Management` |
| 2 | Medium | Google | Distributed Systems, Cache Design | Design a Distributed Cache System ⚠️ also fits: `Distributed_Systems_General` |
| 3 | Medium | Google | Distributed Systems, Cache Design | Design a Distributed Cache System (part 1) ⚠️ also fits: `Distributed_Systems_General` |
| 4 | Medium | Google | Session Management, Redis | Design a System for Handling User Sessions with Redis Cluster and Replication and Transactions and Locks ⚠️ also fits: `Session_Management` |
| 5 | Medium | Google | Distributed Systems, Cache Design | Design a Distributed Cache System (part 1) ⚠️ also fits: `Distributed_Systems_General` |
| 6 | Medium | Google | Session Management, Redis | Design a System for Handling User Sessions with Redis Cluster and Replication and Transactions and Locks and Transactions and Transactions and Transactions and Transactions ⚠️ also fits: `Session_Management` |
| 7 | Medium | Google | Distributed Systems, Redis | Two Team Matching Calls (not matched) ⚠️ also fits: `Distributed_Systems_General` |
| 8 | Medium | Google | Distributed Systems, Cache Design | Design a Distributed Cache System (part 1) ⚠️ also fits: `Distributed_Systems_General` |
| 9 | Medium | Google | Cache Invalidation, Redis | Design a caching system for a web application |
| 10 | Medium | Google | Session Management, Redis | Design a System for Handling User Sessions with Redis Cluster and Replication ⚠️ also fits: `Session_Management` |
| 11 | Medium | Google | Distributed Systems, Redis | Two Team Matching Calls (matched) ⚠️ also fits: `Distributed_Systems_General` |
| 12 | Medium | Google | Distributed Systems, Redis | Design an elevator ⚠️ also fits: `Distributed_Systems_General` |
| 13 | Medium | Google | Session Management, Redis | Design a System for Handling User Sessions with Redis Cluster ⚠️ also fits: `Session_Management` |
| 14 | Medium | Google | Caching, Distributed Systems | Design a Cache System for an E-commerce Platform ⚠️ also fits: `Distributed_Systems_General` |
| 15 | Medium | Meta | System Design, Image Processing, Object Storage, CDN | Design a photo sharing service with image upload, processing (resize, compress, filter), storage, CDN distribution, photo albums, tagging, and privacy controls for billions of photos. ⚠️ also fits: `Distributed_Systems_General` · `Image_Media_Processing` |
| 16 | Medium | Microsoft | System Design, Package Registry, Dependency Resolution, CDN | Design a package registry like npm or PyPI: package publishing with versioning, dependency resolution, download serving via CDN, vulnerability scanning, namespace management, and download analytics. ⚠️ also fits: `Distributed_Systems_General` · `Versioning_Schema` |
| 17 | Hard | Amazon | System Design, Distributed Cache, Consistent Hashing, Replication | Design a distributed cache like Redis: in-memory key-value storage, data structures (strings, lists, sets, sorted sets, hashes), replication, cluster mode with hash slots, persistence (RDB/AOF), and pub/sub. ⚠️ also fits: `Consistent_Hashing` · `Data_Storage_Retrieval` · `Distributed_Systems_General` |
| 18 | Hard | Amazon | System Design, Live Streaming, RTMP, Transcoding | Design a live streaming platform like Twitch: live video ingestion (RTMP), transcoding for multiple qualities, CDN distribution, real-time chat, viewer count tracking, and VOD recording. ⚠️ also fits: `Distributed_Systems_General` · `Messaging_StreamProcessing` |
| 19 | Hard | Cloudflare | System Design, DNS, Caching, Anycast | Design a global-scale DNS system: hierarchical name resolution, caching at multiple levels, zone file management, DNSSEC for security, anycast routing for availability, and handling billions of queries per day. ⚠️ also fits: `Distributed_Systems_General` |
| 20 | Hard | Google | Distributed Systems, Caching | Design a Distributed Cache System ⚠️ also fits: `Distributed_Systems_General` |
| 21 | Hard | Google | Session Management, Memcached | Design a System for Handling User Sessions with Memcached ⚠️ also fits: `Session_Management` |
| 22 | Hard | Google | Distributed Systems, Caching | Design a Distributed Cache System (part 1) ⚠️ also fits: `Distributed_Systems_General` |
| 23 | Hard | Google | Session Management, Redis | Design a System for Handling User Sessions with Redis Cluster and Replication and Transactions and Locks and Transactions and Transactions and Transactions ⚠️ also fits: `Session_Management` |
| 24 | Hard | Google | Distributed Systems, Caching | Design a Distributed Cache System (part 2) ⚠️ also fits: `Distributed_Systems_General` |
| 25 | Hard | Google | Distributed Systems, Redis | Design Twitter ⚠️ also fits: `Distributed_Systems_General` |
| 26 | Hard | Google | Session Management, Redis | Design a System for Handling User Sessions with Redis Cluster and Replication and Transactions and Locks and Transactions ⚠️ also fits: `Session_Management` |
| 27 | Hard | Google | Distributed Systems, Redis | Design a distributed system for storing and retrieving data from multiple databases ⚠️ also fits: `Distributed_Systems_General` |
| 28 | Hard | Google | Session Management, Redis | Design a System for Handling User Sessions with Redis Cluster and Replication and Transactions ⚠️ also fits: `Session_Management` |
| 29 | Hard | Google | Distributed Systems, Cache | Design a distributed cache system for a large-scale e-commerce platform ⚠️ also fits: `Distributed_Systems_General` |
| 30 | Hard | Meta | System Design, Graph Database, Graph Traversal, Caching | Design a social graph service: friend/follow relationships, friend-of-friend queries, mutual friends computation, friend recommendations, and graph traversal at scale for 2B+ users. ⚠️ also fits: `Distributed_Systems_General` |
| 31 | Hard | Netflix | System Design, CDN, Video Transcoding, Adaptive Bitrate | Design a video streaming platform like Netflix: video upload and transcoding pipeline, adaptive bitrate streaming (HLS/DASH), content delivery via CDN, recommendation engine, and viewing analytics at scale. ⚠️ also fits: `Distributed_Systems_General` · `Image_Media_Processing` · `Search_Recommendation` |
| 32 | Hard | — | Distributed Systems, Redis | Design Twitter ⚠️ also fits: `Distributed_Systems_General` |
| 33 | Hard | — | Distributed Systems, Redis | Design LRU Cache ⚠️ also fits: `Distributed_Systems_General` |
| 34 | Hard | — | Distributed Systems, Cache | Design a distributed cache system ⚠️ also fits: `Distributed_Systems_General` |

## <a id="load_balancing"></a>2. Load Balancing — 19 questions

_Layer: **Infra primitive**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Amazon | System Design, Load Balancing, Health Checking, SSL Termination | Design a load balancer: L4 vs L7 load balancing, algorithm selection (round-robin, least connections, consistent hashing, weighted), health checking, session affinity, SSL termination, and auto-scaling integration. ⚠️ also fits: `Consistent_Hashing` · `Distributed_Systems_General` |
| 2 | Medium | Google | Dijkstra's Algorithm, Graph | Design a load balancer for a cloud-based application ⚠️ also fits: `HLD_Algorithmic_Foundations` |
| 3 | Medium | Google | Dijkstra's Algorithm, Graph | Design a load balancer for a cloud-based application ⚠️ also fits: `HLD_Algorithmic_Foundations` |
| 4 | Medium | Google | Load Balancing, Distributed Systems | Design a System for Handling High Traffic Websites ⚠️ also fits: `Distributed_Systems_General` |
| 5 | Medium | Google | Dijkstra's Algorithm, Graph | Design a load balancer for a cloud-based application ⚠️ also fits: `HLD_Algorithmic_Foundations` |
| 6 | Hard | Cloudflare | System Design, CDN, Caching, Load Balancing | Design a Content Delivery Network (CDN): edge server placement strategy, content caching and invalidation, origin shield, load balancing across PoPs, SSL termination, and DDoS protection. ⚠️ also fits: `Caching` · `Distributed_Systems_General` |
| 7 | Hard | Google | Load Balancing, Distributed Systems | Design a distributed system with load balancing and failover ⚠️ also fits: `Distributed_Systems_General` |
| 8 | Hard | Google | Load Balancing, Distributed Systems | Design a Load Balancer for a E-commerce Platform ⚠️ also fits: `Distributed_Systems_General` |
| 9 | Hard | Google | Cache Invalidation, Redis | Design a load balancing system for a cloud-based application ⚠️ also fits: `Caching` |
| 10 | Hard | Meta | Graph | Design a load balancer for a web application with high traffic ⚠️ also fits: `HLD_Algorithmic_Foundations` |
| 11 | Hard | Meta | Graph, Distributed Systems | Design a distributed system for storing and retrieving data with high availability, scalability, low latency, and high performance, using a combination of caching and load balancing ⚠️ also fits: `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` |
| 12 | Hard | Meta | Graph | Design a load balancing system for a web application with high traffic and low latency ⚠️ also fits: `HLD_Algorithmic_Foundations` |
| 13 | Hard | Meta | Graph, Distributed Systems | Design a distributed system for storing and retrieving data with high availability, scalability, and low latency, using a combination of caching and load balancing ⚠️ also fits: `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` |
| 14 | Hard | Meta | Graph | Design a load balancing system for a web application ⚠️ also fits: `HLD_Algorithmic_Foundations` |
| 15 | Hard | — | Distributed Systems, Hash Table, Load Balancing | Design a distributed hash table (DHT) with load balancing ⚠️ also fits: `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` |
| 16 | Hard | — | Distributed Systems, Hash Table, Data Compression, Data Encryption | Design a distributed hash table (DHT) with data compression and encryption, and load balancing ⚠️ also fits: `Data_Storage_Retrieval` · `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` · `Session_Management` |
| 17 | Hard | — | Graph, Distributed Systems | Design a load balancing system for a web application ⚠️ also fits: `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` |
| 18 | Hard | — | Distributed Systems, Hash Table, Data Deduplication, Data Encryption | Design a distributed hash table (DHT) with data deduplication and encryption, and load balancing ⚠️ also fits: `Data_Storage_Retrieval` · `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` · `Session_Management` |
| 19 | Hard | — | Distributed Systems, Hash Table, Data Anonymization, Data Encryption | Design a distributed hash table (DHT) with data anonymization and encryption, and load balancing ⚠️ also fits: `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` · `Session_Management` |

## <a id="consistent_hashing"></a>3. Consistent Hashing — 2 questions

_Layer: **Infra primitive**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Hard | Amazon | System Design, Consistent Hashing, Quorum, Vector Clocks | Design a distributed key-value store like DynamoDB: consistent hashing for partitioning, replication with tunable consistency (quorum reads/writes), vector clocks for conflict detection, gossip protocol for membership, a ⚠️ also fits: `Distributed_Systems_General` |
| 2 | Hard | Netflix | System Design, A/B Testing, Consistent Hashing, Statistics | Design a large-scale A/B testing platform: experiment creation, user bucketing with consistent hashing, multi-variate testing, interaction detection between experiments, statistical significance calculation, and guardrai ⚠️ also fits: `AB_Testing` · `Distributed_Systems_General` |

## <a id="rate_limiting"></a>4. Rate Limiting — 20 questions

_Layer: **Infra pattern**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Amazon | System Design, API Gateway, Rate Limiting, Circuit Breaker | Design an API gateway: request routing, authentication/authorization, rate limiting, request/response transformation, circuit breaking, load balancing, API versioning, and analytics/logging. ⚠️ also fits: `Distributed_Systems_General` · `Load_Balancing` · `Session_Management` |
| 2 | Hard | Amazon | Rate Limiting, Distributed Systems, Redis | Design a distributed rate limiter for an API gateway ⚠️ also fits: `Caching` · `Distributed_Systems_General` |
| 3 | Hard | Amazon | Rate Limiting, Distributed Systems, Redis | Design a distributed rate limiter for an API gateway ⚠️ also fits: `Caching` · `Distributed_Systems_General` |
| 4 | Hard | Amazon | System Design, Concurrency Control, Rate Limiting, Distributed Locks | Design a coupon distribution system for a flash sale: generate unique coupons, prevent double-claiming under extreme concurrency, enforce time-window validity, track redemption, and handle 100K+ claims per second. ⚠️ also fits: `Distributed_Systems_General` · `Payments_Inventory` |
| 5 | Hard | Amazon | Rate Limiting, Distributed Systems, Redis | Design a distributed rate limiter for an API gateway ⚠️ also fits: `Caching` · `Distributed_Systems_General` |
| 6 | Hard | Amazon | System Design, Message Queue, Rate Limiting, Template Engine | Design a notification system at scale: support push notifications, email, SMS, and in-app notifications with user preference management, templating, batching, rate limiting, and delivery tracking for 1B+ users. ⚠️ also fits: `Distributed_Systems_General` · `Messaging_StreamProcessing` |
| 7 | Hard | Amazon | Rate Limiting, Distributed Systems, Redis | Design a distributed rate limiter for an API gateway ⚠️ also fits: `Caching` · `Distributed_Systems_General` |
| 8 | Hard | Amazon | Rate Limiting, Distributed Systems, Redis | Design a distributed rate limiter for an API gateway ⚠️ also fits: `Caching` · `Distributed_Systems_General` |
| 9 | Hard | Cloudflare | System Design, Rate Limiting, Distributed Systems, Redis | Design a rate limiter at scale: support multiple algorithms (token bucket, sliding window), per-user and per-API limits, distributed rate limiting across multiple servers, and graceful degradation under load. ⚠️ also fits: `Caching` · `Consistent_Hashing` · `Distributed_Systems_General` |
| 10 | Hard | Google | Rate Limiting, Distributed Systems, Redis | Design a distributed rate limiter for an API gateway ⚠️ also fits: `Caching` · `Distributed_Systems_General` |
| 11 | Hard | Google | Rate Limiting, Distributed Systems, Redis | Design a distributed rate limiter for an API gateway ⚠️ also fits: `Caching` · `Distributed_Systems_General` |
| 12 | Hard | Google | System Design, Distributed Computing, URL Frontier, Bloom Filter | Design a web crawler that can crawl billions of pages: URL frontier management, politeness policies (robots.txt, rate limiting), duplicate detection, distributed crawling coordination, and handling dynamic JavaScript-ren ⚠️ also fits: `Distributed_Systems_General` |
| 13 | Hard | Google | Distributed Systems, Rate Limiting | Design Twitter ⚠️ also fits: `Distributed_Systems_General` |
| 14 | Hard | Google | Rate Limiting, Distributed Systems, Redis | Design a distributed rate limiter for an API gateway ⚠️ also fits: `Caching` · `Distributed_Systems_General` |
| 15 | Hard | Meta | Graph | Design a load balancer for a web application with high traffic and low latency, using a combination of caching and rate limiting ⚠️ also fits: `HLD_Algorithmic_Foundations` · `Load_Balancing` |
| 16 | Hard | Meta | Graph | Design a load balancing system for a web application with high traffic and low latency, using a combination of caching and rate limiting, and a time-based eviction policy ⚠️ also fits: `HLD_Algorithmic_Foundations` · `Load_Balancing` |
| 17 | Hard | Salesforce | System Design, Multi-tenancy, Data Isolation, Usage Billing | Design a multi-tenant SaaS platform: tenant onboarding, data isolation strategies, per-tenant customization, usage-based billing, tenant-level rate limiting, and noisy neighbor prevention. ⚠️ also fits: `Distributed_Systems_General` |
| 18 | Hard | Stripe | System Design, Webhooks, Retry Pattern, Message Queue | Design a webhook delivery system at scale: reliable webhook event delivery with retry and exponential backoff, signature verification for security, delivery status tracking, dead letter queue for failed webhooks, and rat ⚠️ also fits: `Distributed_Systems_General` · `Messaging_StreamProcessing` |
| 19 | Hard | — | Rate Limiting, Distributed Systems, Redis | Design a distributed rate limiter for an API gateway ⚠️ also fits: `Caching` · `Distributed_Systems_General` |
| 20 | Hard | — | Rate Limiting, Distributed Systems, Redis | Design a distributed rate limiter for an API gateway ⚠️ also fits: `Caching` · `Distributed_Systems_General` |

## <a id="session_management"></a>5. Session Management & Auth — 8 questions

_Layer: **Infra pattern**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Google | Session Management, Redis | Design a System for Handling User Sessions with Redis ⚠️ also fits: `Caching` |
| 2 | Medium | Google | Session Management, Distributed Systems | Design a System for Handling User Sessions ⚠️ also fits: `Distributed_Systems_General` |
| 3 | Hard | Google | Distributed Systems, Authentication | Design a distributed system to manage user authentication across multiple servers ⚠️ also fits: `Distributed_Systems_General` |
| 4 | Hard | Google | Distributed Systems, Session Management | Design a distributed system to manage user sessions across multiple servers ⚠️ also fits: `Distributed_Systems_General` |
| 5 | Hard | Google | Session Management, Cookies | Design a System for Handling User Sessions with Cookies |
| 6 | Hard | Google | Session Management, Redis | Design a System for Handling User Sessions with Redis Sentinel ⚠️ also fits: `Caching` |
| 7 | Hard | Google | Authentication, Distributed Systems | Design a System for Handling User Authentication ⚠️ also fits: `Distributed_Systems_General` |
| 8 | Hard | Google | System Design, Authentication, SSO, MFA | Design a global identity and authentication service: user registration, multi-factor authentication, single sign-on (SSO), OAuth provider, session management across devices, and account recovery at scale. ⚠️ also fits: `Distributed_Systems_General` |

## <a id="messaging_streamprocessing"></a>6. Messaging & Stream Processing — 34 questions

_Layer: **Infra pattern**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Amazon | System Design, Sorted Set, Caching, Sharding | Design a leaderboard system for a gaming platform: real-time score updates, top-K queries, rank queries for specific users, time-bounded leaderboards (daily/weekly/all-time), and handling millions of concurrent players. ⚠️ also fits: `Caching` · `Distributed_Systems_General` · `Search_Recommendation` |
| 2 | Medium | Google | Real-time Data, Distributed Systems | Design a System for Handling Real-time Data ⚠️ also fits: `Distributed_Systems_General` |
| 3 | Medium | Netflix | System Design, Configuration Management, Pub-Sub, Versioning | Design a distributed configuration management system: centralized config storage, versioning, environment-specific overrides, real-time propagation to services, rollback support, and audit logging. ⚠️ also fits: `Distributed_Systems_General` · `Versioning_Schema` |
| 4 | Hard | Amazon | System Design, Message Queue, Worker Pool, Retry Pattern | Design a distributed task queue like Celery or SQS: task submission, priority queuing, worker pool management, retry with backoff, dead letter queue, task result storage, and exactly-once processing guarantees. ⚠️ also fits: `Distributed_Systems_General` |
| 5 | Hard | Amazon | System Design, IoT, Time Series, MQTT | Design an IoT data platform: device registration and management, telemetry data ingestion at massive scale, time-series storage, real-time alerting rules, device shadow/twin, and OTA firmware updates. ⚠️ also fits: `Distributed_Systems_General` |
| 6 | Hard | Amplitude | System Design, Analytics, Event Collection, Stream Processing | Design an analytics event collection and processing system: client-side event SDK, event ingestion at scale, real-time and batch processing, funnel analysis, cohort analysis, and data warehouse integration. ⚠️ also fits: `Data_Storage_Retrieval` · `Distributed_Systems_General` |
| 7 | Hard | Datadog | System Design, Time Series Database, Stream Processing, Alerting | Design a metrics and monitoring system like Datadog: metric ingestion at high throughput, time-series storage, alerting with configurable thresholds, dashboarding, anomaly detection, and distributed tracing integration. ⚠️ also fits: `Distributed_Systems_General` |
| 8 | Hard | Goldman Sachs | System Design, Order Matching, Real-time Processing, Low Latency | Design a stock trading platform: real-time price feeds, order book management, order matching engine, portfolio tracking, risk management, and regulatory compliance reporting. Handle millisecond-level latency requirement ⚠️ also fits: `Distributed_Systems_General` |
| 9 | Hard | Google | System Design, Graph Algorithms, Geospatial Index, Tile Server | Design Google Maps: map tile rendering and serving, route calculation (shortest path, traffic-aware), real-time traffic data processing, place search, and turn-by-turn navigation at global scale. ⚠️ also fits: `Distributed_Systems_General` · `Geospatial` |
| 10 | Hard | Google | System Design, Security, URL Classification, Bloom Filter | Design a URL safety/phishing detection service: URL classification (safe, phishing, malware), real-time scanning, blocklist/allowlist management, browser extension integration, and handling billions of URL checks per day ⚠️ also fits: `Caching` · `Distributed_Systems_General` |
| 11 | Hard | Google | System Design, CRDT, Operational Transformation, WebSocket | Design a real-time collaborative document editor like Google Docs: concurrent editing, conflict resolution using Operational Transformation (OT) or CRDTs, cursor presence, version history, and offline editing support. ⚠️ also fits: `Distributed_Systems_General` |
| 12 | Hard | Google | System Design, Real-time Bidding, Ad Serving, Budget Pacing | Design a real-time bidding (RTB) ad serving platform: bid request processing within 100ms SLA, advertiser targeting, budget pacing, impression tracking, click attribution, and fraud filtering. ⚠️ also fits: `Distributed_Systems_General` |
| 13 | Hard | Google | Stream Processing, Distributed Systems | Design a real-time analytics system (e.g., web traffic monitoring) ⚠️ also fits: `Distributed_Systems_General` |
| 14 | Hard | Google | System Design, Collaboration, Block Editor, CRDT | Design a document collaboration platform like Notion: block-based content model, real-time collaboration, page hierarchy, database views (table, board, calendar), search, and permission management. ⚠️ also fits: `Distributed_Systems_General` · `Search_Recommendation` |
| 15 | Hard | Google | System Design, ML Serving, Model Registry, A/B Testing | Design an ML model serving platform: model versioning and registry, A/B testing between model versions, real-time inference with low latency, batch prediction, feature store integration, and model monitoring/drift detect ⚠️ also fits: `AB_Testing` · `Distributed_Systems_General` |
| 16 | Hard | Google | System Design, WebRTC, SFU, Adaptive Bitrate | Design a video conferencing system like Zoom: real-time audio/video streaming, screen sharing, virtual backgrounds, recording, breakout rooms, and handling network quality degradation with adaptive bitrate. ⚠️ also fits: `Distributed_Systems_General` · `Image_Media_Processing` |
| 17 | Hard | Google | Distributed Systems, Queue | Design a queue-based system for a real-time data processing pipeline ⚠️ also fits: `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` |
| 18 | Hard | Meta | System Design, Content Moderation, ML Classification, Human-in-the-Loop | Design a content moderation system: automated text/image/video classification, human review queues, appeal workflows, policy rule engine, and real-time content filtering at scale. ⚠️ also fits: `Distributed_Systems_General` |
| 19 | Hard | Meta | System Design, WebSocket, Message Queue, End-to-End Encryption | Design WhatsApp or a real-time messaging system supporting 1-on-1 and group messaging, end-to-end encryption, message delivery receipts (sent, delivered, read), offline message queuing, and media sharing. ⚠️ also fits: `Distributed_Systems_General` |
| 20 | Hard | Meta | System Design, Geospatial Index, GeoHash, Pub-Sub | Design a proximity service / nearby friends feature: real-time location updates from millions of users, geospatial indexing, configurable radius search, privacy controls, and battery-efficient location reporting. ⚠️ also fits: `Distributed_Systems_General` · `Geospatial` |
| 21 | Hard | Meta | System Design, Feed Generation, Ranking, Fan-out | Design a news feed system like Facebook: feed generation for 2B+ users, ranking algorithm, real-time updates, mixed content types (posts, ads, stories), and A/B testing of feed algorithms. ⚠️ also fits: `AB_Testing` · `Caching` · `Distributed_Systems_General` · `Search_Recommendation` |
| 22 | Hard | Meta | System Design, CDN, Object Storage, Feed Generation | Design Instagram: photo/video upload and processing, news feed generation, stories (24-hour ephemeral content), explore/discover, direct messaging, and handling 2B+ monthly active users. ⚠️ also fits: `Caching` · `Distributed_Systems_General` · `Image_Media_Processing` · `Search_Recommendation` |
| 23 | Hard | Microsoft | System Design, Cloud IDE, Container Orchestration, WebSocket | Design a cloud-based IDE like GitHub Codespaces: workspace provisioning, code editing with IntelliSense, terminal access, extension support, file synchronization, and dev environment as code (devcontainers). ⚠️ also fits: `Distributed_Systems_General` |
| 24 | Hard | Netflix | System Design, Log Aggregation, Stream Processing, Inverted Index | Design a distributed logging system like ELK Stack: log ingestion from thousands of servers, structured parsing, full-text search indexing, log aggregation, retention policies, and real-time log tailing. ⚠️ also fits: `Distributed_Systems_General` |
| 25 | Hard | Netflix | System Design, ETL, Stream Processing, Schema Evolution | Design a data pipeline / ETL system: data ingestion from multiple sources, transformation processing, schema evolution handling, exactly-once delivery, data quality validation, and lineage tracking. ⚠️ also fits: `Distributed_Systems_General` |
| 26 | Hard | Netflix | System Design, Recommendation Engine, Collaborative Filtering, Feature Store | Design a recommendation system: collaborative filtering, content-based filtering, hybrid approaches, feature store, real-time re-ranking, cold start handling, and A/B testing of recommendation algorithms. ⚠️ also fits: `AB_Testing` · `Distributed_Systems_General` · `Search_Recommendation` |
| 27 | Hard | Riot Games | System Design, Game Networking, Client Prediction, State Synchronization | Design a real-time multiplayer game backend: game state synchronization, client-side prediction, server reconciliation, lag compensation, matchmaking, and cheat detection. ⚠️ also fits: `Distributed_Systems_General` |
| 28 | Hard | Slack | System Design, WebSocket, Presence System, Search Index | Design a real-time chat system like Slack: channels, direct messages, threads, file sharing, presence indicators, message search, and workspace management supporting millions of concurrent connections. ⚠️ also fits: `Distributed_Systems_General` |
| 29 | Hard | Stripe | System Design, Fraud Detection, ML Serving, Rule Engine | Design a fraud detection system for e-commerce: real-time transaction scoring, rule engine, ML model serving, user behavior profiling, device fingerprinting, and alert/review workflow. ⚠️ also fits: `Distributed_Systems_General` |
| 30 | Hard | Uber | System Design, Geospatial Index, Real-time Matching, Surge Pricing | Design Uber or a ride-sharing platform: real-time driver/rider matching, ETA calculation, surge pricing, trip tracking, payment processing, and driver payout at scale across multiple cities. ⚠️ also fits: `Distributed_Systems_General` · `Geospatial` · `Payments_Inventory` |
| 31 | Hard | Uber | System Design, Matching Algorithm, Geospatial, Real-time Processing | Design a ride-sharing matching algorithm at scale: real-time supply-demand matching, batched matching for efficiency, driver-rider scoring, ETA estimation, and handling peak demand with surge pricing zones. ⚠️ also fits: `Distributed_Systems_General` · `Geospatial` |
| 32 | Hard | Uber | System Design, Geospatial Index, ETA Prediction, Real-time Tracking | Design a food delivery platform like Uber Eats at scale: restaurant discovery, menu management, order placement, real-time delivery tracking, ETA prediction, driver assignment optimization, and surge pricing. ⚠️ also fits: `Distributed_Systems_General` · `Geospatial` |
| 33 | Hard | Uber | System Design, Dynamic Pricing, Real-time Processing, Geospatial | Design a ride-sharing surge pricing system: real-time supply-demand calculation per zone, dynamic price multiplier, smooth price transitions, driver incentive balancing, and price transparency for riders. ⚠️ also fits: `Distributed_Systems_General` · `Geospatial` |
| 34 | Hard | Uber | System Design, Geofencing, Geospatial, Real-time Processing | Design a geofencing system for a delivery app: defining geo-boundaries, real-time device location tracking, entry/exit event detection, push notification triggering, and handling millions of concurrent location updates. ⚠️ also fits: `Distributed_Systems_General` · `Geospatial` |

## <a id="data_storage_retrieval"></a>7. Data Storage & Retrieval — 24 questions

_Layer: **Infra pattern**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Google | Data Storage, Distributed Systems | Design a System for Handling User Data ⚠️ also fits: `Distributed_Systems_General` |
| 2 | Hard | Amazon | System Design, Object Storage, Erasure Coding, Multi-part Upload | Design an object storage service like S3: bucket management, object CRUD with versioning, multi-part upload, storage classes (hot/warm/cold), cross-region replication, and lifecycle policies. ⚠️ also fits: `Distributed_Systems_General` |
| 3 | Hard | Google | Distributed Systems, Data Storage and Retrieval | Design a distributed system to manage user data storage and retrieval across multiple servers with high availability, scalability, and performance ⚠️ also fits: `Distributed_Systems_General` |
| 4 | Hard | Google | Distributed Systems, Data Processing and Retrieval | Design a distributed system to manage user data processing and retrieval across multiple servers with high availability, scalability, and performance ⚠️ also fits: `Distributed_Systems_General` |
| 5 | Hard | Google | Distributed Systems, Data Storage | Design a distributed system to manage user data across multiple servers ⚠️ also fits: `Distributed_Systems_General` |
| 6 | Hard | Google | Data Storage, Device Independence | Design a system for managing and optimizing data storage on multiple devices ⚠️ also fits: `Distributed_Systems_General` |
| 7 | Hard | Google | Distributed Systems, Data Storage and Retrieval | Design a distributed system to manage user data storage and retrieval across multiple servers with high availability ⚠️ also fits: `Distributed_Systems_General` |
| 8 | Hard | Google | System Design, Multi-Region, Active-Active, Replication | Design a multi-region, active-active database deployment: data replication across regions, conflict resolution, failover handling, read/write routing, consistency guarantees, and disaster recovery. ⚠️ also fits: `Distributed_Systems_General` |
| 9 | Hard | Google | Distributed Systems, Data Processing and Retrieval | Design a distributed system to manage user data processing and retrieval across multiple servers with high availability ⚠️ also fits: `Distributed_Systems_General` |
| 10 | Hard | Google | Data Retrieval, Device Independence | Design a system for managing and optimizing data retrieval on multiple devices (e.g. cloud, on-prem) ⚠️ also fits: `Distributed_Systems_General` |
| 11 | Hard | Google | Data Storage, Device Independence | Design a system for managing and optimizing data storage on multiple devices (e.g. cloud, on-prem) ⚠️ also fits: `Distributed_Systems_General` |
| 12 | Hard | Google | Distributed Systems, Data Storage | Design a distributed system to manage user data storage across multiple servers ⚠️ also fits: `Distributed_Systems_General` |
| 13 | Hard | Google | Distributed Systems, Data Processing and Retrieval | Design a distributed system to manage user data processing and retrieval across multiple servers with high availability and scalability ⚠️ also fits: `Distributed_Systems_General` |
| 14 | Hard | Google | Data Processing, Device Independence | Design a system for managing and optimizing data processing on multiple devices (e.g. cloud, on-prem) ⚠️ also fits: `Distributed_Systems_General` |
| 15 | Hard | Google | Distributed Systems, Data Processing | Design a distributed system to manage user data processing across multiple servers ⚠️ also fits: `Distributed_Systems_General` |
| 16 | Hard | Google | Data Processing, Device Independence | Design a system for managing and optimizing data processing on multiple devices ⚠️ also fits: `Distributed_Systems_General` |
| 17 | Hard | Google | Distributed Systems, Data Storage and Retrieval | Design a distributed system to manage user data storage and retrieval across multiple servers with high availability and scalability ⚠️ also fits: `Distributed_Systems_General` |
| 18 | Hard | Google | Data Retrieval, Device Independence | Design a system for managing and optimizing data retrieval on multiple devices ⚠️ also fits: `Distributed_Systems_General` |
| 19 | Hard | Google | Distributed Systems, Data Retrieval | Design a distributed system to manage user data retrieval across multiple servers ⚠️ also fits: `Distributed_Systems_General` |
| 20 | Hard | Google | Distributed Systems, Data Processing and Retrieval | Design a distributed system to manage user data processing and retrieval across multiple servers ⚠️ also fits: `Distributed_Systems_General` |
| 21 | Hard | Google | Distributed Systems, Data Storage and Retrieval | Design a distributed system to manage user data storage and retrieval across multiple servers with high availability, scalability, performance, and reliability ⚠️ also fits: `Distributed_Systems_General` |
| 22 | Hard | Google | Distributed Systems, Data Storage and Retrieval | Design a distributed system to manage user data storage and retrieval across multiple servers ⚠️ also fits: `Distributed_Systems_General` |
| 23 | Hard | Google | Data Processing, Distributed Systems | Design a System for Handling Large Datasets ⚠️ also fits: `Distributed_Systems_General` |
| 24 | Hard | Netflix | System Design, Data Lake, Schema-on-Read, Data Catalog | Design a data lake architecture: raw data ingestion from multiple sources, schema-on-read, data cataloging, query engine integration (Presto/Trino/Spark), access control, and data retention lifecycle management. ⚠️ also fits: `Distributed_Systems_General` |

## <a id="url_shortener"></a>8. URL Shortener — 24 questions

_Layer: **Classic archetype**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Google | System Design, Base62 Encoding, Caching, Analytics Pipeline | Design a URL shortener at scale (like bit.ly): short URL generation, redirection with low latency, click analytics (geographic, temporal, referrer), custom aliases, and link expiration handling billions of redirects per  ⚠️ also fits: `Caching` · `Consistent_Hashing` · `Distributed_Systems_General` |
| 2 | Hard | Google | URL Shortening, Distributed Systems | Design a URL Shortener at scale (part 1) ⚠️ also fits: `Distributed_Systems_General` |
| 3 | Hard | Google | URL Shortening, Distributed Systems | Design a URL Shortener at scale (part 3) ⚠️ also fits: `Distributed_Systems_General` |
| 4 | Hard | Google | URL Shortening, Distributed Systems | Design a URL Shortener at scale (part 1) ⚠️ also fits: `Distributed_Systems_General` |
| 5 | Hard | Google | URL Shortening, Distributed Systems | Design a URL Shortener at scale ⚠️ also fits: `Distributed_Systems_General` |
| 6 | Hard | Google | Graph, Distributed Systems | Design a URL shortener at scale ⚠️ also fits: `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` |
| 7 | Hard | Google | URL Shortening, Distributed Systems | Design a URL Shortener at scale ⚠️ also fits: `Distributed_Systems_General` |
| 8 | Hard | Google | Distributed Systems, Data Structure | Design a URL shortener at scale ⚠️ also fits: `Distributed_Systems_General` |
| 9 | Hard | Google | URL Shortening, Distributed Systems | Design a URL Shortener at scale (part 1) ⚠️ also fits: `Distributed_Systems_General` |
| 10 | Hard | Google | URL Shortening, Distributed Systems | Design a URL Shortener at scale (part 1) ⚠️ also fits: `Distributed_Systems_General` |
| 11 | Hard | Google | URL Shortening, Distributed Systems | Design a URL Shortener at scale (part 1) ⚠️ also fits: `Distributed_Systems_General` |
| 12 | Hard | Google | URL Shortening, Distributed Systems | Design a URL Shortener at scale ⚠️ also fits: `Distributed_Systems_General` |
| 13 | Hard | Google | URL Shortening, Distributed Systems | Design a URL Shortener at scale (part 3) ⚠️ also fits: `Distributed_Systems_General` |
| 14 | Hard | Google | URL Shortening, Distributed Systems | Design a URL Shortener at scale (part 1) ⚠️ also fits: `Distributed_Systems_General` |
| 15 | Hard | Google | URL Shortening, Distributed Systems | Design a URL Shortener at scale (part 2) ⚠️ also fits: `Distributed_Systems_General` |
| 16 | Hard | Google | URL Shortening, Distributed Systems | Design a URL Shortener at scale (part 1) ⚠️ also fits: `Distributed_Systems_General` |
| 17 | Hard | Google | URL Shortening, Distributed Systems | Design a URL Shortener at scale (part 2) ⚠️ also fits: `Distributed_Systems_General` |
| 18 | Hard | Meta | Graph, Cache, Rate Limiting | Design a URL shortener with caching and rate limiting ⚠️ also fits: `Caching` · `HLD_Algorithmic_Foundations` · `Rate_Limiting` |
| 19 | Hard | Meta | Graph, Distributed Systems | Design a URL shortener at scale ⚠️ also fits: `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` |
| 20 | Hard | Meta | URL Shortening, Distributed Systems | Design a URL shortener with support for redirects and caching ⚠️ also fits: `Distributed_Systems_General` |
| 21 | Hard | — | Graph Data Structure, URL Shortener | Design a URL shortener at scale |
| 22 | Hard | — | Distributed Systems, URL Hash | Design URL Shortener at scale ⚠️ also fits: `Distributed_Systems_General` |
| 23 | Hard | — | URL Shortening, Distributed Systems | Design a URL Shortener at scale ⚠️ also fits: `Distributed_Systems_General` |
| 24 | Hard | — | Graph, Distributed Systems | Design a URL shortener at scale ⚠️ also fits: `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` |

## <a id="search_recommendation"></a>9. Search & Recommendation — 7 questions

_Layer: **Classic archetype**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Google | System Design, Trie, Caching, Personalization | Design a search autocomplete system: prefix-based suggestion generation, personalized suggestions, trending queries, typo tolerance, and serving suggestions with sub-50ms latency at scale. ⚠️ also fits: `Caching` · `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` · `Messaging_StreamProcessing` |
| 2 | Medium | Google | Dijkstra's Algorithm, Graph | Design a search engine index for a large dataset ⚠️ also fits: `HLD_Algorithmic_Foundations` |
| 3 | Hard | Amazon | System Design, Microservices, Search, Inventory Management | Design Amazon e-commerce platform: product catalog, search with faceted filtering, shopping cart, order management, inventory tracking, payment processing, and recommendation engine for 300M+ products. ⚠️ also fits: `Distributed_Systems_General` · `Payments_Inventory` |
| 4 | Hard | Google | Search, Distributed Systems | Design a System for Handling User Search ⚠️ also fits: `Distributed_Systems_General` |
| 5 | Hard | Google | System Design, Inverted Index, PageRank, Web Crawler | Design Google Search: web crawling, indexing (inverted index), PageRank, query processing, spell correction, search result ranking, and serving results with sub-200ms latency at global scale. ⚠️ also fits: `Distributed_Systems_General` |
| 6 | Hard | Meta | System Design, Fan-out, Timeline Generation, Caching | Design Twitter/X at scale: support tweet creation, timelines (home and user), follow/unfollow, trending topics, and search. Handle 500M+ daily tweets with sub-second feed generation. ⚠️ also fits: `Caching` · `Distributed_Systems_General` · `Messaging_StreamProcessing` |
| 7 | Hard | Meta | System Design, Video Processing, Recommendation, Content Moderation | Design a short-form video platform like TikTok: video upload and processing, content recommendation feed (For You page), creator tools, live streaming, duets/stitches, and content moderation at scale. ⚠️ also fits: `Caching` · `Distributed_Systems_General` · `Image_Media_Processing` |

## <a id="geospatial"></a>10. Geospatial Services — 1 questions

_Layer: **Classic archetype**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Google | System Design, Geospatial Search, Review System, Spam Detection | Design a location-based social network like Yelp: business listings, user reviews with photos, star ratings, business search with filters (cuisine, price, distance), review spam detection, and business owner dashboard. ⚠️ also fits: `Distributed_Systems_General` · `Search_Recommendation` |

## <a id="payments_inventory"></a>11. Payments & Inventory — 5 questions

_Layer: **Classic archetype**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Booking.com | System Design, API Aggregation, Caching, Search | Design a hotel/flight booking aggregator like Kayak: aggregating prices from multiple providers, caching search results, handling stale prices, sorting/filtering, and booking redirect with affiliate tracking. ⚠️ also fits: `Caching` · `Distributed_Systems_General` · `Messaging_StreamProcessing` · `Search_Recommendation` |
| 2 | Hard | Amazon | System Design, Inventory Management, Concurrency Control, Queue | Design a ticket master-like event ticketing system: event creation, seat map management, ticket purchasing with seat selection, inventory management under high concurrency, waitlists, and resale marketplace. ⚠️ also fits: `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` |
| 3 | Hard | Google | Distributed Systems, Inventory Management | Design a distributed system to manage inventory levels across multiple warehouses ⚠️ also fits: `Distributed_Systems_General` |
| 4 | Hard | PayPal | System Design, Payment Processing, P2P Transfer, KYC | Design a digital wallet and peer-to-peer payment service like Venmo: account management, P2P transfers, bank linking, transaction feed, split payments, and regulatory compliance (KYC/AML). ⚠️ also fits: `Distributed_Systems_General` |
| 5 | Hard | Stripe | System Design, Payment Processing, Idempotency, PCI Compliance | Design a global payment system like Stripe: payment intent creation, multi-currency support, payment method abstraction, PCI compliance architecture, idempotent processing, refunds, disputes, and reconciliation. ⚠️ also fits: `Distributed_Systems_General` |

## <a id="ab_testing"></a>12. A/B Testing — 2 questions

_Layer: **Classic archetype**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Cloudflare | System Design, Caching, Edge Computing, Geolocation | Design a URL redirect service that handles vanity URLs, geographic-based redirects, A/B test routing, redirect chain detection, and analytics. Process 100K+ redirects per second with P99 latency under 10ms. ⚠️ also fits: `Caching` · `Distributed_Systems_General` |
| 2 | Medium | Meta | System Design, Feature Flags, A/B Testing, Targeting | Design a feature flag / experimentation platform: flag creation and targeting rules, percentage-based rollouts, A/B testing with statistical significance, kill switch, and flag lifecycle management. ⚠️ also fits: `Distributed_Systems_General` |

## <a id="image_media_processing"></a>13. Image / Media Processing — 2 questions

_Layer: **Classic archetype**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Hard | Meta | System Design, Image Processing, Video Processing, ML Classification | Design an image/video processing pipeline for a social media platform: upload handling, format conversion, thumbnail generation, content-aware resizing, NSFW detection, and serving optimized versions for different device ⚠️ also fits: `Caching` · `Distributed_Systems_General` |
| 2 | Hard | Spotify | System Design, Audio Streaming, Recommendation, Offline Sync | Design a music streaming service like Spotify: audio storage and delivery, playlist management, personalized daily mixes, collaborative playlists, offline sync, and royalty tracking/reporting. ⚠️ also fits: `Caching` · `Distributed_Systems_General` |

## <a id="versioning_schema"></a>14. Versioning & Schema — 1 questions

_Layer: **Niche**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Stripe | System Design, Database Migration, Schema Evolution, Zero Downtime | Design a database migration system: schema versioning, forward and rollback migrations, zero-downtime migration strategies (expand-contract), data migration for large tables, and migration state tracking. ⚠️ also fits: `Distributed_Systems_General` |

## <a id="hld_algorithmic_foundations"></a>15. HLD Algorithmic Foundations — 128 questions

_Layer: **Algo-heavy HLD**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Google | Heaps, Dynamic Programming | Design a Min Heap |
| 2 | Medium | Google | Heaps, Dynamic Programming | Design a Min Heap (part 1) |
| 3 | Medium | Google | Queues, Dynamic Programming | Design a Min Queue |
| 4 | Medium | Google | Queues, Dynamic Programming | Design a Min Queue (with support for enqueue and dequeue) with O(1) time complexity |
| 5 | Medium | Google | Stacks, Dynamic Programming | Design a Min Stack |
| 6 | Medium | Google | Stacks, Dynamic Programming | Design a Min Stack (with support for push and pop) in Python |
| 7 | Medium | Google | Heaps, Dynamic Programming | Design a Min Heap |
| 8 | Medium | Google | Deques, Dynamic Programming | Design a Min Deque (with support for enqueue and dequeue) with O(1) time complexity |
| 9 | Medium | Google | Graph, Linked List | Design a linked list with insert and delete operations (2-3 levels of nesting) (2-3 levels of nesting) |
| 10 | Medium | Google | Dijkstra's Algorithm, Graph | Design an elevator |
| 11 | Medium | Google | Queue, Distributed Systems | Design a queue with max size and min size ⚠️ also fits: `Distributed_Systems_General` |
| 12 | Medium | Google | Heaps, Dynamic Programming | Design a Min Heap (with support for insert and delete) in Python |
| 13 | Medium | Google | Heaps, Dynamic Programming | Design a Min Heap (part 1) |
| 14 | Medium | Google | Stacks, Dynamic Programming | Design a Min Stack (with support for push and pop) in C++ |
| 15 | Medium | Google | Heaps, Dynamic Programming | Design a Min Heap (part 1) |
| 16 | Medium | Google | Graph, Linked List | Design a linked list with insert and delete operations |
| 17 | Medium | Google | Heaps, Dynamic Programming | Design a Min Heap (part 2) |
| 18 | Medium | Google | Queues, Dynamic Programming | Design a Min Queue (with support for enqueue and dequeue) in Python |
| 19 | Medium | Google | Stacks, Dynamic Programming | Design a Min Stack |
| 20 | Medium | Google | Queues, Dynamic Programming | Design a Min Queue (part 1) |
| 21 | Medium | Google | Heaps, Dynamic Programming | Design a Min Heap |
| 22 | Medium | Google | Heaps, Dynamic Programming | Design a Min Heap (part 2) |
| 23 | Medium | Google | Graph, Linked List | Design a linked list with insert and delete operations (2-3 levels of nesting) |
| 24 | Medium | Google | Heaps, Dynamic Programming | Design a Min Heap (part 1) |
| 25 | Medium | Google | Graph, Linked List | Design a linked list with insert and delete operations (2-3 levels of nesting) (2-3 levels of nesting) |
| 26 | Medium | Google | Heaps, Dynamic Programming | Design a Min Heap (part 2) |
| 27 | Medium | Google | Queues, Dynamic Programming | Design a Min Queue (with support for enqueue and dequeue) in Java |
| 28 | Medium | Google | Stacks, Dynamic Programming | Design a Min Stack |
| 29 | Medium | Google | Graph, Linked List | Design a linked list with insert and delete operations (2-3 levels of nesting) (2-3 levels of nesting) |
| 30 | Medium | Google | Heaps, Dynamic Programming | Design a Min Heap (with support for insert and delete) in C++ |
| 31 | Medium | Google | Heaps, Dynamic Programming | Design a Min Heap (with support for insert and delete) in Java |
| 32 | Medium | Google | Queues, Dynamic Programming | Design a Min Queue (with support for enqueue and dequeue) in C++ |
| 33 | Medium | Google | Graph, Dijkstra's algorithm | Design an elevator |
| 34 | Medium | Google | Graph, Random Node | Design a linked list random node question |
| 35 | Medium | Google | Stacks, Dynamic Programming | Design a Min Stack (with support for push and pop) in Java |
| 36 | Medium | — | Graph, Dynamic Programming | Design a Min Disjoint Set Union (Union-Find) with Approximate Union by Rank and Path Compression |
| 37 | Medium | — | Heaps, Dynamic Programming | Design a Min Heap |
| 38 | Medium | — | Queue, Dynamic Programming | Design a Min Deque |
| 39 | Medium | — | Deques, Dynamic Programming | Design a Min Deque (with support for enqueue and dequeue) with O(log n) time complexity |
| 40 | Medium | — | Queues, Dynamic Programming | Design a Min Queue |
| 41 | Medium | — | Deques, Dynamic Programming | Design a Min Deque |
| 42 | Medium | — | Queues, Dynamic Programming | Design a Min Queue (with support for enqueue and dequeue) with O(log n) time complexity |
| 43 | Medium | — | Deques, Dynamic Programming | Design a Min Deque (with support for enqueue and dequeue) with O(1) time complexity |
| 44 | Medium | — | Queues, Dynamic Programming | Design a Min Queue (with support for enqueue and dequeue) with O(1) time complexity |
| 45 | Medium | — | Deques, Dynamic Programming | Design a Min Deque (with support for enqueue and dequeue) with O(log n) time complexity |
| 46 | Medium | — | Queues, Dynamic Programming | Design a Min Queue (with support for enqueue and dequeue) with O(1) time complexity |
| 47 | Medium | — | Graph, Dynamic Programming | Design a Min Disjoint Set Union (Union-Find) with Approximate Union by Rank, Path Compression, and Weak Key Hashing |
| 48 | Medium | — | Graph, Dynamic Programming | Design a Min Disjoint Set Union (Union-Find) with Union by Rank |
| 49 | Medium | — | Deques, Dynamic Programming | Design a Min Deque (with support for enqueue and dequeue) with O(1) time complexity |
| 50 | Medium | — | Deques, Dynamic Programming | Design a Min Deque (with support for enqueue and dequeue) with O(1) time complexity |
| 51 | Medium | — | Graph, Dynamic Programming | Design a Min Disjoint Set Union (Union-Find) with Path Compression |
| 52 | Medium | — | Stacks, Dynamic Programming | Design a Min Stack |
| 53 | Medium | — | Graph, Dynamic Programming | Design a Min Disjoint Set Union (Union-Find) |
| 54 | Medium | — | Queues, Dynamic Programming | Design a Min Queue (with support for enqueue and dequeue) with O(log n) time complexity |
| 55 | Medium | — | Graph, Dynamic Programming | Design a Min Disjoint Set Union (Union-Find) with Approximate Union by Rank, Path Compression, and Weak Key Hashing and Approximate Nearest Neighbor |
| 56 | Medium | — | Queues, Dynamic Programming | Design a Min Queue (with support for enqueue and dequeue) with O(1) time complexity |
| 57 | Medium | — | Graph, Dynamic Programming | Design a Min Disjoint Set Union (Union-Find) with Approximate Union by Rank |
| 58 | Hard | Google | Stacks, Dynamic Programming | Design a Min Stack (with support for push and pop) with O(1) time complexity |
| 59 | Hard | Google | Graph, Distributed Systems | Design a system for handling multiple concurrent requests to the same resource with complex queries ⚠️ also fits: `Distributed_Systems_General` |
| 60 | Hard | Google | Heaps, Dynamic Programming | Design a Min Heap (with support for insert and extract-min) with O(log n) time complexity |
| 61 | Hard | Google | Binary Search, Distributed Systems | Design a Min Binary Search Tree (Recursive with Iterative) ⚠️ also fits: `Distributed_Systems_General` |
| 62 | Hard | Google | Binary Search, Distributed Systems | Design a Min Binary Search Tree (Iterative with Recursion) ⚠️ also fits: `Distributed_Systems_General` |
| 63 | Hard | Google | Graph, Dijkstra | Design a parking lot system |
| 64 | Hard | Google | Stacks, Distributed Systems | Design a Min Priority Queue (Priority Queue) ⚠️ also fits: `Distributed_Systems_General` |
| 65 | Hard | Google | Binary Search, Distributed Systems | Design a Min Binary Search Tree (Iterative) ⚠️ also fits: `Distributed_Systems_General` |
| 66 | Hard | Google | Graph, Distributed Systems | Design a system for handling multiple concurrent requests to the same resource with complex queries and ensuring data consistency, using techniques like transactional updates, and caching ⚠️ also fits: `Distributed_Systems_General` |
| 67 | Hard | Google | Binary Search, Distributed Systems | Design a Min Binary Search Tree (Iterative with Memoization) ⚠️ also fits: `Distributed_Systems_General` |
| 68 | Hard | Google | Graph, Dijkstra | Design a graph algorithm for finding the shortest path |
| 69 | Hard | Google | Trie, Dynamic Programming | Design a Trie (with support for insert, search, and delete) in C++ |
| 70 | Hard | Google | Trie, Dynamic Programming | Design a Trie |
| 71 | Hard | Google | Trie, String Manipulation | Design a Trie with Vowel Removal (with support for insert and search) with O(n) time complexity |
| 72 | Hard | Google | Trie, Dynamic Programming | Design a Trie (with support for insert, search, and delete) in Java |
| 73 | Hard | Google | Deques, Dynamic Programming | Design a Min Deque (with support for push and pop) in C++ |
| 74 | Hard | Google | Deques, Dynamic Programming | Design a Min Deque (with support for push and pop) in Python |
| 75 | Hard | Google | Graph, Distributed Systems | Design a system for handling multiple concurrent requests to the same resource ⚠️ also fits: `Distributed_Systems_General` |
| 76 | Hard | Google | Graph, Distributed Systems | Design a system for handling multiple concurrent requests to the same resource with complex queries and ensuring data consistency, using techniques like transactional updates ⚠️ also fits: `Distributed_Systems_General` |
| 77 | Hard | Google | Binary Search, Distributed Systems | Design a Min Binary Search Tree (Iterative with Hashing and Iteration) ⚠️ also fits: `Distributed_Systems_General` |
| 78 | Hard | Google | Graph, Distributed Systems | Design a system for handling multiple concurrent requests to the same resource with complex queries and ensuring data consistency ⚠️ also fits: `Distributed_Systems_General` |
| 79 | Hard | Google | Stacks, Distributed Systems | Design a Min Priority Queue ⚠️ also fits: `Distributed_Systems_General` |
| 80 | Hard | Google | Binary Search, Distributed Systems | Design a Min Binary Search Tree (Iterative with Hashing and Memoization) ⚠️ also fits: `Distributed_Systems_General` |
| 81 | Hard | Google | Binary Search, Distributed Systems | Design a Min Binary Search Tree (Iterative with Hashing) ⚠️ also fits: `Distributed_Systems_General` |
| 82 | Hard | Google | Stacks, Distributed Systems | Design a Min Heap (Priority Queue) ⚠️ also fits: `Distributed_Systems_General` |
| 83 | Hard | Google | Trie, String Manipulation | Design a Trie with Vowel Removal |
| 84 | Hard | Google | Binary Search, Distributed Systems | Design a Min Binary Search Tree ⚠️ also fits: `Distributed_Systems_General` |
| 85 | Hard | Google | Deques, Dynamic Programming | Design a Min Deque (with support for push and pop) in Java |
| 86 | Hard | Google | Trie, Dynamic Programming | Design a Trie (with support for insert, search, and delete) in Python |
| 87 | Hard | Google | Graph, Distributed Systems | Design a system for handling multiple concurrent requests to the same resource with complex queries and caching ⚠️ also fits: `Distributed_Systems_General` |
| 88 | Hard | Google | Binary Search, Distributed Systems | Design a Min Binary Search Tree (Recursive) ⚠️ also fits: `Distributed_Systems_General` |
| 89 | Hard | Google | Binary Search, Distributed Systems | Design a Min Binary Search Tree (Iterative with Iteration) ⚠️ also fits: `Distributed_Systems_General` |
| 90 | Hard | Meta | Graph, Distributed Systems | Binary Tree Right Side View ⚠️ also fits: `Distributed_Systems_General` |
| 91 | Hard | Meta | Graph | Design a distributed system for storing and retrieving data |
| 92 | Hard | Meta | Graph | Design an elevator |
| 93 | Hard | Meta | Graph, Distributed Systems | Design a distributed system for storing and retrieving data with high availability and scalability ⚠️ also fits: `Distributed_Systems_General` |
| 94 | Hard | Meta | Graph, Distributed Systems | Design an elevator ⚠️ also fits: `Distributed_Systems_General` |
| 95 | Hard | Meta | Graph, Distributed Systems, Redis | Design a distributed system for storing and retrieving data with high availability and scalability, using Redis as the cache layer ⚠️ also fits: `Caching` · `Distributed_Systems_General` |
| 96 | Hard | Meta | Graph, Distributed Systems | Design a distributed system for storing and retrieving data with high availability ⚠️ also fits: `Distributed_Systems_General` |
| 97 | Hard | — | Graph, Distributed Systems | Design a system to manage user data anonymization auditing metrics ⚠️ also fits: `Distributed_Systems_General` |
| 98 | Hard | — | Binary Search, Dynamic Programming | Design a Min Binary Search Tree (BST) |
| 99 | Hard | — | Distributed Systems, Hash Table | Design a distributed hash table (DHT) ⚠️ also fits: `Distributed_Systems_General` |
| 100 | Hard | — | Distributed Systems, Hash Table, Data Replication | Design a distributed hash table (DHT) with data replication ⚠️ also fits: `Distributed_Systems_General` |
| 101 | Hard | — | Graph, Distributed Systems | Design a system to manage user data anonymization auditing ⚠️ also fits: `Distributed_Systems_General` |
| 102 | Hard | — | Distributed Systems, Hash Table, Data Deduplication | Design a distributed hash table (DHT) with data deduplication ⚠️ also fits: `Data_Storage_Retrieval` · `Distributed_Systems_General` |
| 103 | Hard | — | Graph, Distributed Systems | Design a system to manage user data anonymization security ⚠️ also fits: `Distributed_Systems_General` |
| 104 | Hard | — | Stacks, Dynamic Programming | Design a Min Stack (with support for push and pop) with O(1) time complexity |
| 105 | Hard | — | Distributed Systems, Hash Table, Data Compression | Design a distributed hash table (DHT) with data compression ⚠️ also fits: `Data_Storage_Retrieval` · `Distributed_Systems_General` |
| 106 | Hard | — | Graph, Distributed Systems | Design a system to manage user data validation ⚠️ also fits: `Distributed_Systems_General` |
| 107 | Hard | — | Distributed Systems, Hash Table, Data Deduplication, Data Encryption | Design a distributed hash table (DHT) with data deduplication and encryption ⚠️ also fits: `Data_Storage_Retrieval` · `Distributed_Systems_General` · `Session_Management` |
| 108 | Hard | — | String, Dynamic Programming | Longest Common Subsequence (LCS) |
| 109 | Hard | — | Graph, Distributed Systems | Design a system to manage user authentication ⚠️ also fits: `Distributed_Systems_General` |
| 110 | Hard | — | Graph, Distributed Systems | Design a system to manage user preferences ⚠️ also fits: `Distributed_Systems_General` |
| 111 | Hard | — | Distributed Systems, Hash Table, Cache | Design a distributed hash table (DHT) with caching ⚠️ also fits: `Caching` · `Distributed_Systems_General` |
| 112 | Hard | — | Distributed Systems, Hash Table, Data Anonymization | Design a distributed hash table (DHT) with data anonymization ⚠️ also fits: `Distributed_Systems_General` |
| 113 | Hard | — | Distributed Systems, Hash Table, Data Encryption | Design a distributed hash table (DHT) with data encryption ⚠️ also fits: `Distributed_Systems_General` · `Session_Management` |
| 114 | Hard | — | Graph, Distributed Systems | Design a system to manage user data encryption ⚠️ also fits: `Distributed_Systems_General` |
| 115 | Hard | — | Graph, Distributed Systems | Design a system to manage user data anonymization algorithms ⚠️ also fits: `Distributed_Systems_General` |
| 116 | Hard | — | Heaps, Dynamic Programming | Design a Min Heap (with support for insert and extractMin) with O(log n) time complexity |
| 117 | Hard | — | Distributed Systems, Queue | Design a distributed queue system ⚠️ also fits: `Distributed_Systems_General` |
| 118 | Hard | — | Graph, Distributed Systems | Design an elevator ⚠️ also fits: `Distributed_Systems_General` |
| 119 | Hard | — | Graph, Distributed Systems | Design a system to manage user sessions ⚠️ also fits: `Distributed_Systems_General` |
| 120 | Hard | — | Distributed Systems, Hash Table, Data Anonymization, Data Encryption | Design a distributed hash table (DHT) with data anonymization and encryption ⚠️ also fits: `Distributed_Systems_General` · `Session_Management` |
| 121 | Hard | — | Stacks, Dynamic Programming | Design a Min Stack (with support for push and pop) with O(1) time complexity |
| 122 | Hard | — | Graph, Distributed Systems | Design a system to manage user data anonymization ⚠️ also fits: `Distributed_Systems_General` |
| 123 | Hard | — | Heaps, Dynamic Programming | Design a Min Heap (with support for insert and extractMin) with O(log n) time complexity |
| 124 | Hard | — | Graph, Distributed Systems | Design a system to manage user data storage ⚠️ also fits: `Distributed_Systems_General` |
| 125 | Hard | — | Binary Search, Dynamic Programming | Design a Min Binary Search Tree (BST) with Range Sum Query |
| 126 | Hard | — | String, Dynamic Programming | Edit Distance (Minimum Number of Operations) |
| 127 | Hard | — | Stacks, Dynamic Programming | Design a Min Stack (with support for push and pop) with O(1) time complexity |
| 128 | Hard | — | Distributed Systems, Hash Table, Data Compression, Data Encryption | Design a distributed hash table (DHT) with data compression and encryption ⚠️ also fits: `Data_Storage_Retrieval` · `Distributed_Systems_General` · `Session_Management` |

## <a id="distributed_systems_general"></a>16. Distributed Systems (general) — 23 questions

_Layer: **Catch-all — review individually**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Google | System Design, CI/CD, Build System, Deployment Strategies | Design a CI/CD pipeline system: source code integration, build orchestration, test execution (unit, integration, e2e), artifact management, deployment strategies (blue-green, canary, rolling), and rollback. |
| 2 | Medium | Google | Parking Lot, Distributed Systems | Design a Parking Lot System |
| 3 | Medium | Google | Distributed Systems, Queue Design | Design a Distributed Queue System |
| 4 | Medium | Google | Distributed Systems, Data Structure | Design a parking lot system |
| 5 | Medium | Google | Distributed Systems, Queue Design | Design a Distributed Queue System (part 1) |
| 6 | Medium | Google | Distributed Systems, Scheduling | Design a Parking Lot System |
| 7 | Medium | Google | User Profiles, Distributed Systems | Design a System for Handling User Profile Management |
| 8 | Medium | Google | Distributed Systems, Scheduling | Design a Phone System |
| 9 | Medium | Google | Distributed Systems, Queue Design | Design a Distributed Queue System (part 1) |
| 10 | Hard | Amazon | System Design, Backup, Disaster Recovery, Deduplication | Design a cloud-based backup and disaster recovery system: incremental backups, deduplication, encryption at rest and in transit, cross-region replication, point-in-time recovery, and RPO/RTO guarantee management. |
| 11 | Hard | Amazon | System Design, Serverless, Cold Start, Isolation | Design a serverless computing platform like AWS Lambda: function deployment, cold start optimization, auto-scaling to zero, request routing, execution isolation, concurrency management, and billing based on execution tim |
| 12 | Hard | Coinbase | System Design, Blockchain, Consensus, Smart Contracts | Design a blockchain-based digital asset registry: transaction validation, consensus mechanism, smart contract execution, wallet management, and handling 10K+ transactions per second with finality guarantees. |
| 13 | Hard | Dropbox | System Design, File Sync, Chunked Upload, Deduplication | Design Dropbox or Google Drive: file sync across devices, conflict resolution, chunked upload/download, deduplication, version history, sharing and permissions, and offline mode. |
| 14 | Hard | Google | System Design, Email, SMTP, Search Index | Design a scalable email service like Gmail: email sending (SMTP), receiving, storage, search, spam filtering, label/folder management, and attachment handling for billions of emails. |
| 15 | Hard | Google | System Design, Container Orchestration, Scheduling, Service Discovery | Design a container orchestration platform like Kubernetes: pod scheduling, service discovery, rolling deployments, auto-scaling (HPA/VPA), resource quotas, and health management. |
| 16 | Hard | Google | System Design, Resource Management, Job Scheduling, Resource Isolation | Design a warehouse-scale computer resource management system: compute allocation, job scheduling across thousands of machines, resource isolation (CPU, memory, disk), preemption policies, and cluster utilization optimiza |
| 17 | Hard | Google | System Design, Service Mesh, Sidecar Pattern, mTLS | Design a service mesh like Istio: sidecar proxy deployment, service discovery, traffic management (routing, retries, timeouts), mutual TLS, observability (metrics, tracing, logging), and canary deployments. |
| 18 | Hard | Google | System Design, Distributed Locks, Consensus, Fencing Token | Design a distributed lock service: lock acquisition with TTL, reentrant locks, read-write locks, fencing tokens to prevent split-brain, and high-availability deployment using consensus protocol. |
| 19 | Hard | Google | Feedback, Distributed Systems | Design a System for Handling User Feedback |
| 20 | Hard | Google | Error Handling, Distributed Systems | Design a System for Handling API Errors |
| 21 | Hard | Netflix | System Design, Secrets Management, Encryption, Access Control | Design a secrets management system like Vault: secret storage with encryption at rest, access control policies, dynamic secret generation, secret rotation, audit logging, and high-availability deployment. |
| 22 | Hard | Uber | System Design, DAG, Distributed Scheduling, Worker Pool | Design a distributed cron/job scheduler like Airflow: DAG-based workflow definition, task scheduling with dependencies, distributed execution across workers, retry policies, monitoring, and backfill support. |
| 23 | Hard | Uber | System Design, Distributed Tracing, Context Propagation, Sampling | Design a distributed tracing system like Jaeger: trace context propagation, span collection, sampling strategies, trace storage, dependency graph visualization, and latency analysis. |

## <a id="uncategorized"></a>17. Uncategorized — 3 questions

_Layer: **Needs manual review**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | Google | Database Optimization, Query Optimization | Design a system for managing and optimizing database queries |
| 2 | Medium | — | String, Stack | Valid Parentheses |
| 3 | Hard | Google | Network Optimization, Traffic Management | Design a system for managing and optimizing network traffic |
