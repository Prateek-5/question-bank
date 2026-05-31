# Distributed Systems (general) — Extracted Questions

> **47 questions** sourced from the LeetLens DB (`processed.extracted_questions`, snapshot 2026-05-31).
> Vertical: **HLD** · Bucket: `Distributed_Systems_General` · Bucket study-order rank in vertical: **16**.
> See [`../../../leetlens-import/STUDY-GUIDE.md`](../../../leetlens-import/STUDY-GUIDE.md) for the cross-vertical sequence.

## How to use this file

- Each row is **metadata only** — question text, difficulty, company, topic tags, LeetLens ID.
- The **Seq** column gives the recommended execution order WITHIN this bucket (Easy → Hard, then by LLM quality score).
- The **⚠️ also fits** annotation lists OTHER buckets the question could appear in (cross-cutting practice).
- When you're ready to author a walkthrough for a question, create a new file alongside this manifest (e.g. `Question_Name.md`) following the vertical's TEMPLATE-v2.md.

## Summary

- **Total:** 47
- **Difficulty mix:** Medium: 9 · Hard: 38
- **Top companies:** Meta (24), Google (16), Amazon (2), Uber (2), Dropbox (1), Coinbase (1), Netflix (1)

## Questions

| Seq | Difficulty | Company | Question | Topics | LeetLens ID | Also fits |
|---:|---|---|---|---|---|---|
| 1 | Medium | Google | Design a CI/CD pipeline system: source code integration, build orchestration, test execution (unit, integration, e2e), artifact management, deployment strategies (blue-green, canary, rolling), and rollback. | System Design, CI/CD, Build System, Deployment Strategies, +2 | `00303b11` | — |
| 2 | Medium | Google | Design a Parking Lot System | Parking Lot, Distributed Systems | `1e09f0f3` | — |
| 3 | Medium | Google | Design a Distributed Queue System | Distributed Systems, Queue Design | `67059716` | — |
| 4 | Medium | Google | Design a parking lot system | Distributed Systems, Data Structure | `9ad70f71` | — |
| 5 | Medium | Google | Design a Distributed Queue System (part 1) | Distributed Systems, Queue Design | `b79b0bcf` | — |
| 6 | Medium | Google | Design a Parking Lot System | Distributed Systems, Scheduling | `c5fb0d9d` | — |
| 7 | Medium | Google | Design a System for Handling User Profile Management | User Profiles, Distributed Systems | `d1217d97` | — |
| 8 | Medium | Google | Design a Phone System | Distributed Systems, Scheduling | `edc6cbd8` | — |
| 9 | Medium | Google | Design a Distributed Queue System (part 1) | Distributed Systems, Queue Design | `fadc3e23` | — |
| 10 | Hard | Amazon | Design a serverless computing platform like AWS Lambda: function deployment, cold start optimization, auto-scaling to zero, request routing, execution isolation, concurrency management, and billing based on execution time. | System Design, Serverless, Cold Start, Isolation, +2 | `70c0d817` | — |
| 11 | Hard | Google | Design a container orchestration platform like Kubernetes: pod scheduling, service discovery, rolling deployments, auto-scaling (HPA/VPA), resource quotas, and health management. | System Design, Container Orchestration, Scheduling, Service Discovery, +2 | `1ce7c587` | — |
| 12 | Hard | Google | Design a warehouse-scale computer resource management system: compute allocation, job scheduling across thousands of machines, resource isolation (CPU, memory, disk), preemption policies, and cluster utilization optimization. | System Design, Resource Management, Job Scheduling, Resource Isolation, +2 | `24af2a4c` | — |
| 13 | Hard | Dropbox | Design Dropbox or Google Drive: file sync across devices, conflict resolution, chunked upload/download, deduplication, version history, sharing and permissions, and offline mode. | System Design, File Sync, Chunked Upload, Deduplication, +2 | `06c94073` | — |
| 14 | Hard | Google | Design a service mesh like Istio: sidecar proxy deployment, service discovery, traffic management (routing, retries, timeouts), mutual TLS, observability (metrics, tracing, logging), and canary deployments. | System Design, Service Mesh, Sidecar Pattern, mTLS, +2 | `5a07a73d` | — |
| 15 | Hard | Google | Design a distributed lock service: lock acquisition with TTL, reentrant locks, read-write locks, fencing tokens to prevent split-brain, and high-availability deployment using consensus protocol. | System Design, Distributed Locks, Consensus, Fencing Token, +2 | `77902039` | — |
| 16 | Hard | Amazon | Design a cloud-based backup and disaster recovery system: incremental backups, deduplication, encryption at rest and in transit, cross-region replication, point-in-time recovery, and RPO/RTO guarantee management. | System Design, Backup, Disaster Recovery, Deduplication, +2 | `6c3b46e4` | — |
| 17 | Hard | Google | Design a scalable email service like Gmail: email sending (SMTP), receiving, storage, search, spam filtering, label/folder management, and attachment handling for billions of emails. | System Design, Email, SMTP, Search Index, +2 | `0fe3d171` | — |
| 18 | Hard | Netflix | Design a secrets management system like Vault: secret storage with encryption at rest, access control policies, dynamic secret generation, secret rotation, audit logging, and high-availability deployment. | System Design, Secrets Management, Encryption, Access Control, +2 | `8d95fa7b` | — |
| 19 | Hard | Uber | Design a distributed cron/job scheduler like Airflow: DAG-based workflow definition, task scheduling with dependencies, distributed execution across workers, retry policies, monitoring, and backfill support. | System Design, DAG, Distributed Scheduling, Worker Pool, +2 | `8169fe4b` | — |
| 20 | Hard | Coinbase | Design a blockchain-based digital asset registry: transaction validation, consensus mechanism, smart contract execution, wallet management, and handling 10K+ transactions per second with finality guarantees. | System Design, Blockchain, Consensus, Smart Contracts, +2 | `14a955d4` | — |
| 21 | Hard | Uber | Design a distributed tracing system like Jaeger: trace context propagation, span collection, sampling strategies, trace storage, dependency graph visualization, and latency analysis. | System Design, Distributed Tracing, Context Propagation, Sampling, +2 | `84dbb960` | — |
| 22 | Hard | Google | Design a System for Handling User Feedback | Feedback, Distributed Systems | `9376c19c` | — |
| 23 | Hard | Google | Design a System for Handling API Errors | Error Handling, Distributed Systems | `d8fa4e17` | — |
| 24 | Hard | Meta | Design a system to optimize the performance of a large-scale online gaming platform | Online Gaming, Distributed Systems | `03c6da49` | — |
| 25 | Hard | Meta | Design a system to manage and optimize the performance of a large-scale social media platform | Social Media, Distributed Systems | `0ba76c02` | — |
| 26 | Hard | Meta | Design a system to optimize the performance of a large-scale data compression platform | Data Compression, Distributed Systems | `1564dcdd` | — |
| 27 | Hard | Meta | Design a system to manage and optimize the performance of a large-scale data anonymization platform for sensitive data with high accuracy | Data Anonymization, Distributed Systems | `17037a3f` | — |
| 28 | Hard | Meta | Design a system to manage and optimize the performance of a large-scale data anonymization platform for sensitive data with high accuracy, low latency, scalability, security, and compliance | Data Anonymization, Distributed Systems | `1965f9ed` | — |
| 29 | Hard | Meta | Design a distributed cache system with multiple data centers and high availability requirements | Distributed Systems, Cache | `2e51e3fb` | `Hashing_Sliding_Window` |
| 30 | Hard | Meta | Design a system to manage and optimize the performance of a large-scale data integration platform | Data Integration, Distributed Systems | `2edb3b93` | — |
| 31 | Hard | Meta | Design a system to optimize the performance of a large-scale data anonymization platform for sensitive data | Data Anonymization, Distributed Systems | `3594197f` | — |
| 32 | Hard | Meta | Design a system to manage and optimize the performance of a large-scale data encryption platform | Data Encryption, Distributed Systems | `46b8b296` | — |
| 33 | Hard | Meta | Design a system to detect and prevent SQL injection attacks in a web application | SQL Injection, Distributed Systems | `48852966` | — |
| 34 | Hard | Meta | Design a system to manage and optimize the performance of a large-scale data warehousing platform | Data Warehousing, Distributed Systems | `4c3d6a13` | — |
| 35 | Hard | Meta | Design a system to manage and optimize the performance of a large-scale IoT device network | IoT, Distributed Systems | `552e1812` | — |
| 36 | Hard | Meta | Design a system to manage and optimize the performance of a large-scale data analytics platform | Data Analytics, Distributed Systems | `59b7b122` | — |
| 37 | Hard | Meta | Design a system to optimize the performance of a large-scale data deduplication platform | Data Deduplication, Distributed Systems | `674eac8f` | — |
| 38 | Hard | Meta | Design a system to manage and optimize the performance of a large-scale data anonymization platform | Data Anonymization, Distributed Systems | `76206a74` | — |
| 39 | Hard | Meta | Design a system to optimize the performance of a large-scale data anonymization platform for sensitive data with high accuracy and low latency | Data Anonymization, Distributed Systems | `77437581` | — |
| 40 | Hard | Meta | Design a system to optimize the performance of a large-scale data anonymization platform for sensitive data with high accuracy, low latency, scalability, and security | Data Anonymization, Distributed Systems | `77fb9e67` | — |
| 41 | Hard | Meta | Design a system to optimize the performance of a large-scale data storage platform | Data Storage, Distributed Systems | `983c38a0` | — |
| 42 | Hard | Meta | Design a system to optimize the performance of a large-scale data anonymization platform for sensitive data with high accuracy, low latency, scalability, security, compliance, and auditing | Data Anonymization, Distributed Systems | `a4307530` | — |
| 43 | Hard | Meta | Design a system to optimize the performance of a large-scale e-commerce platform | E-commerce, Distributed Systems | `be972c39` | — |
| 44 | Hard | Meta | Design a system to optimize the performance of a large-scale cloud-based data processing platform | Cloud Computing, Distributed Systems | `c97fce8f` | — |
| 45 | Hard | Meta | Design a system to optimize the performance of a large-scale machine learning model training platform | Machine Learning, Distributed Systems | `d3595dae` | — |
| 46 | Hard | Meta | Design a system to manage and optimize the performance of a large-scale data anonymization platform for sensitive data with high accuracy, low latency, and scalability | Data Anonymization, Distributed Systems | `e6b79f55` | — |
| 47 | Hard | Meta | Design a system to manage and optimize the performance of a large-scale data anonymization platform for sensitive data with high accuracy, low latency, scalability, security, compliance, auditing, and data governance | Data Anonymization, Distributed Systems | `f5eeb401` | — |

---

## Future scope (placeholder)

Once questions are reviewed, the next pass will create per-question walkthrough files in this directory following the vertical's `TEMPLATE-v2.md`. Track those additions in the parent topic's `LEARNING.md` if one exists.