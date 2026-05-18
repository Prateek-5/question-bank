# MongoDB: Schema for chat — 1-1, group, broadcast

## Source / Origin
- WhatsApp / Slack / Discord-style chat modeling. Asked at every messaging-heavy product interview.
- Concept reference: `backend-data-prep/nosql/04-mongodb.md`.
- Related: `backend-data-prep/system-design/03-chat-system.md` (if extending to full design).

## Why this question matters in interviews
Chat is the **paradigmatic write-heavy, append-only, time-ordered workload**. The naive answer ("one document per conversation with embedded messages") fails at the 16 MB limit by day 3. The senior answer separates **conversations metadata** from **messages bucket-by-time**, with read patterns driving the indexes. Interviewers use this to test whether you understand growth, hot-doc rewrites, and the "messages per conversation" cardinality.

## Concepts involved

### Syntax to lock in

```javascript
// conversations: metadata about who is in the chat
{
  _id: ObjectId("CONV-1"),
  type: "group",                       // "dm" | "group" | "broadcast"
  participantIds: ["U-1","U-2","U-3"], // bounded for DM/group; nullable for broadcast
  title: "Backend channel",
  lastMessage: { _id, text, at, sender }, // denormalized for inbox list
  unreadCounts: { "U-1": 0, "U-2": 3 },   // optional, per-user
  createdAt: ISODate(...)
}

// messages: append-only, sharded by conversationId
{
  _id: ObjectId("MSG-1"),
  conversationId: ObjectId("CONV-1"),
  senderId: "U-2",
  text: "hello",
  attachments: [],
  reactions: [],
  createdAt: ISODate(...),
  editedAt: null,
  deletedAt: null
}

// receipts: per-user-per-message, side collection
{ userId: "U-1", conversationId: "CONV-1", lastReadMessageId: ObjectId("MSG-99"), at: ISODate(...) }
```

### Edge cases / interview traps

1. **Embedding messages in the conversation doc** — works for ~100 messages, dies at 16 MB. Always separate.
2. **Bucketing messages** — for very high volume conversations, group messages by hour/day into a bucket document (`{convId, bucket: "2026-05-17T12", msgs: [...]}`) to amortize per-message overhead. Trade-off: in-place updates on edits/deletes become awkward.
3. **Broadcast channels** with millions of recipients — do *not* store recipientIds in the conversation. Make recipient list implicit by topic subscription.
4. **Read receipts fan-out** — N participants × M messages = explosion. Store **lastReadMessageId per user**, not per message.
5. **Edits / deletes** — soft-delete with `deletedAt`; do not remove docs (audit, abuse review).
6. **Unread counts** — denormalized on the conversation, updated atomically with `$inc` on message send. Risky when participants are many; pick this only for small groups.
7. **DM dedup** — for 1-1, derive a deterministic `_id` from sorted user pair (`U-1|U-2`) so two clients can't create two DMs.
8. **Index on `{ conversationId: 1, createdAt: -1 }`** — the bread-and-butter index. Sort key supports infinite scroll backward.

## Mental Model

> Three collections, three jobs:
> - **conversations** = the room (who's in it, what's the last word).
> - **messages** = the transcript (append-only, time-ordered, partitioned by room).
> - **receipts** = "where each person is in the transcript."

```
   conversations  ──(1:N)──▶  messages   keyed by (convId, createdAt)
        │
        └──(per-user)──▶  receipts  (userId, convId) → lastReadMessageId

   Inbox list:    conversations.find({ participantIds: U }).sort({ "lastMessage.at": -1 })
   Open chat:     messages.find({ convId }).sort({ createdAt: -1 }).limit(50)
   Older pages:   add { createdAt: { $lt: cursor } }
   Mark read:     receipts.upsert({ userId, convId }, lastReadMessageId)
```

## Why interviewers care

- Tests **growth awareness** — you've thought beyond day-1 scale.
- Tests **access-pattern modeling** — inbox list vs message scroll vs receipts are different queries.
- Tests **fan-out reasoning** — when do you write N times, when do you read N times.

## Common beginner confusion

- "Embed messages in the conversation." 16 MB doc limit kills it.
- "Store unread count as `messages.count() - lastReadIndex`." Slow at scale; denormalize as a counter or compute from receipts.
- "Use a separate collection per conversation." Explodes collection count; index overhead per collection kills you.
- "Strong consistency for inbox preview." It's fine for the preview to lag by a few hundred ms — Mongo's secondary reads or eventual consistency on `lastMessage` is OK.

## Brute force approach

One document per conversation, messages embedded as an array. Atomic `$push`. Works for 50 messages, breaks at scale. Don't.

## Optimal approach

Three collections:
1. `conversations` — small, queried by `participantIds`.
2. `messages` — append-only, indexed `{ conversationId: 1, createdAt: -1 }`. For very heavy convs, bucket by hour.
3. `receipts` — `(userId, convId)` unique; updated on read.

Broadcast channels: drop `participantIds`; use a separate `subscriptions(userId, channelId)` collection.

## Solution (Mongo shell)

```javascript
// === Indexes ===
db.conversations.createIndex({ participantIds: 1, "lastMessage.at": -1 });
db.conversations.createIndex({ type: 1 });
db.messages.createIndex({ conversationId: 1, createdAt: -1 });
db.messages.createIndex({ senderId: 1, createdAt: -1 });
db.receipts.createIndex({ userId: 1, conversationId: 1 }, { unique: true });
db.subscriptions.createIndex({ userId: 1, channelId: 1 }, { unique: true });

// === DM deterministic _id ===
function dmId(u1, u2) {
  const [a, b] = [u1, u2].sort();
  return `dm:${a}|${b}`;
}

db.conversations.updateOne(
  { _id: dmId("U-1", "U-2") },
  { $setOnInsert: { type: "dm", participantIds: ["U-1","U-2"], createdAt: new Date() } },
  { upsert: true }
);

// === Send message ===
const msg = {
  _id: new ObjectId(),
  conversationId: ObjectId("CONV-1"),
  senderId: "U-2",
  text: "hello",
  createdAt: new Date()
};
db.messages.insertOne(msg);
db.conversations.updateOne(
  { _id: msg.conversationId },
  {
    $set: { lastMessage: { _id: msg._id, text: msg.text, at: msg.createdAt, sender: msg.senderId } },
    $inc: { "unreadCounts.U-1": 1, "unreadCounts.U-3": 1 }   // skip sender
  }
);

// === Inbox list for user U-1 ===
db.conversations.find({ participantIds: "U-1" })
                .sort({ "lastMessage.at": -1 })
                .limit(50);

// === Scroll messages (newest first, paginate by createdAt cursor) ===
db.messages.find({ conversationId: ObjectId("CONV-1"), createdAt: { $lt: cursor } })
           .sort({ createdAt: -1 }).limit(50);

// === Mark read ===
db.receipts.updateOne(
  { userId: "U-1", conversationId: ObjectId("CONV-1") },
  { $set: { lastReadMessageId: ObjectId("MSG-99"), at: new Date() } },
  { upsert: true }
);
db.conversations.updateOne(
  { _id: ObjectId("CONV-1") },
  { $set: { "unreadCounts.U-1": 0 } }
);

// === Broadcast: subscribe-publish ===
db.subscriptions.insertOne({ userId: "U-1", channelId: "ch-news" });
db.messages.insertOne({ conversationId: "ch-news", senderId: "system", text: "announcement", createdAt: new Date() });
// Recipients are discovered via subscriptions, not stored on the conversation.
```

### Bucketed messages variant (super-high-volume)

```javascript
// One bucket per (convId, hour)
{
  _id: { convId: "CONV-1", bucket: "2026-05-17T12" },
  msgs: [ { _id, senderId, text, createdAt }, ... ],
  count: 87,
  closedAt: null
}
db.messageBuckets.updateOne(
  { _id: { convId: "CONV-1", bucket: hourBucket(now) }, count: { $lt: 500 } },
  { $push: { msgs: msg }, $inc: { count: 1 }, $setOnInsert: { closedAt: null } },
  { upsert: true }
);
// When count hits 500 (or hour rolls), open a new bucket.
```

## Step-by-step dry run

```
t=0  U-2 sends "hello" in CONV-1 (group of 3)
     → insert into messages
     → conversations: set lastMessage, $inc unreadCounts for U-1, U-3
t=2  U-1 opens app → inbox list query returns conversations sorted by lastMessage.at
     unreadCounts.U-1 = 1   → red badge
t=3  U-1 opens CONV-1 → messages.find({convId}).sort(-1).limit(50)
t=4  Client marks read up to MSG-99 → upsert receipts; set unreadCounts.U-1 = 0
t=10 U-3 (offline) comes online → still sees unread = 1 until they open & mark read

Broadcast variant:
t=0  Channel "ch-news" insert message (no participantIds resolution needed).
t=1  Push worker queries subscriptions(channelId="ch-news") → fan-out push
t=2  Each subscriber's inbox shows the channel as unread when they sync.
```

## How to think aloud in the interview

> "Three collections, not one. The conversation doc is small metadata; messages live in their own append-only collection partitioned logically by conversationId. Embedding messages dies at 16 MB. I'll index messages on `{conversationId: 1, createdAt: -1}` to support scroll-back pagination by cursor.
>
> For DMs I derive a deterministic `_id` from the sorted user pair — that's how I dedup. For groups, `participantIds` is a bounded array on the conversation; I can find a user's inbox via a multikey index on it.
>
> Broadcast channels are different: millions of recipients, so I drop `participantIds` and use a `subscriptions` collection. Recipient resolution is a fan-out pass at delivery time, not a stored array.
>
> Read receipts are per-user, not per-message-per-user. I store `lastReadMessageId` in a `receipts` collection and a denormalized `unreadCounts` on the conversation for small groups. For very large groups I'd drop the denormalized counts and compute on read.
>
> If a single conversation grows to millions of messages I'd bucket into hour-sized arrays to amortize per-doc overhead, accepting the cost of slightly more complex edit/delete logic."

## Important takeaways

- **Separate conversations, messages, receipts.** Three collections, three jobs.
- **Index `{conversationId, createdAt: -1}`.** The single index that powers scroll.
- **DM dedup by deterministic _id** from sorted user pair.
- **Broadcast ≠ group.** Drop participantIds; use subscriptions collection.
- **Read receipts = lastReadMessageId per user**, not per-message rows.
- **Bucket only when a single conversation overwhelms per-doc overhead.**

## Variants

1. **Threaded replies (Slack-style)** — add `parentMessageId` to message; index `{conversationId, parentMessageId, createdAt}`.
2. **Reactions** — embed `reactions: [{ emoji, userId }]` on the message; bounded.
3. **Typing indicators** — ephemeral; do not persist; push via WebSocket.
4. **Message search** — separate index (Atlas Search or Elasticsearch); Mongo text indexes don't scale to billion messages.
5. **End-to-end encryption** — body is ciphertext; metadata (sender, timestamps) still in plaintext.
6. **Delete-for-everyone** — soft-delete with `deletedAt`, project as "this message was deleted" at render.
7. **Sharded messages** — shard by `{conversationId: hashed}` for horizontal scale.

## Revision notes

> **chat schema — 60s recap**
> - 3 collections: `conversations` (metadata), `messages` (append-only), `receipts` (per-user position).
> - Index: `{conversationId: 1, createdAt: -1}` on messages — the scroll workhorse.
> - DM: deterministic `_id = "dm:" + sorted(u1, u2)`.
> - Group: `participantIds` bounded array on conversation, multikey index.
> - Broadcast: drop participantIds, use subscriptions collection, fan-out at delivery.
> - Unread: lastReadMessageId in receipts + optional denormalized counter on conversation (small groups only).
> - Don't embed messages in conversation — 16 MB death.
> - Bucket by hour only for extreme single-conv volume.
