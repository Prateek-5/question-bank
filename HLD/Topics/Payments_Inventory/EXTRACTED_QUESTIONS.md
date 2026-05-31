# Payments & Inventory — Extracted Questions

> **5 questions** sourced from the LeetLens DB (`processed.extracted_questions`, snapshot 2026-05-31).
> Vertical: **HLD** · Bucket: `Payments_Inventory` · Bucket study-order rank in vertical: **11**.
> See [`../../../leetlens-import/STUDY-GUIDE.md`](../../../leetlens-import/STUDY-GUIDE.md) for the cross-vertical sequence.

## How to use this file

- Each row is **metadata only** — question text, difficulty, company, topic tags, LeetLens ID.
- The **Seq** column gives the recommended execution order WITHIN this bucket (Easy → Hard, then by LLM quality score).
- The **⚠️ also fits** annotation lists OTHER buckets the question could appear in (cross-cutting practice).
- When you're ready to author a walkthrough for a question, create a new file alongside this manifest (e.g. `Question_Name.md`) following the vertical's TEMPLATE-v2.md.

## Summary

- **Total:** 5
- **Difficulty mix:** Medium: 1 · Hard: 4
- **Top companies:** Booking.com (1), Google (1), Amazon (1), Stripe (1), PayPal (1)

## Questions

| Seq | Difficulty | Company | Question | Topics | LeetLens ID | Also fits |
|---:|---|---|---|---|---|---|
| 1 | Medium | Booking.com | Design a hotel/flight booking aggregator like Kayak: aggregating prices from multiple providers, caching search results, handling stale prices, sorting/filtering, and booking redirect with affiliate tracking. | System Design, API Aggregation, Caching, Search, +2 | `169bf7eb` | `Caching` · `Distributed_Systems_General` · `Messaging_StreamProcessing` · `Search_Recommendation` |
| 2 | Hard | Stripe | Design a global payment system like Stripe: payment intent creation, multi-currency support, payment method abstraction, PCI compliance architecture, idempotent processing, refunds, disputes, and reconciliation. | System Design, Payment Processing, Idempotency, PCI Compliance, +2 | `68238411` | `Distributed_Systems_General` |
| 3 | Hard | PayPal | Design a digital wallet and peer-to-peer payment service like Venmo: account management, P2P transfers, bank linking, transaction feed, split payments, and regulatory compliance (KYC/AML). | System Design, Payment Processing, P2P Transfer, KYC, +2 | `d19ff407` | `Distributed_Systems_General` |
| 4 | Hard | Amazon | Design a ticket master-like event ticketing system: event creation, seat map management, ticket purchasing with seat selection, inventory management under high concurrency, waitlists, and resale marketplace. | System Design, Inventory Management, Concurrency Control, Queue, +2 | `63072e5f` | `Distributed_Systems_General` · `HLD_Algorithmic_Foundations` |
| 5 | Hard | Google | Design a distributed system to manage inventory levels across multiple warehouses | Distributed Systems, Inventory Management | `47abdad7` | `Distributed_Systems_General` |

---

## Future scope (placeholder)

Once questions are reviewed, the next pass will create per-question walkthrough files in this directory following the vertical's `TEMPLATE-v2.md`. Track those additions in the parent topic's `LEARNING.md` if one exists.