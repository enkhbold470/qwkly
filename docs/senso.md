# Quickstart


This quickstart walks through the core loop every agent integration follows: **ingest knowledge → wait for indexing → query it**. By the end, your agent can answer questions grounded in your organisation's verified documents instead of its training data.

## What you're building

An agent that can answer *"What is the refund policy?"* using your actual policy document — not a hallucinated guess. The pattern is the same whether you're building a support bot, an internal copilot, or a customer-facing agent.

## Prerequisites

- A Senso API key (create one on the [API Keys](/api-keys) page)
- A source document (we'll use a policy file — swap in any `.txt`, `.pdf`, `.md`, or `.docx`)

```bash
export SENSO_KEY="YOUR_API_KEY"
```

---

## Step 1 — Ingest a source document

Before your agent can answer questions, it needs verified knowledge to search against. Ingestion is a two-step presigned-URL flow: request an upload URL, then PUT the file directly to S3.

```python
import hashlib, os, requests

KEY  = os.environ["SENSO_KEY"]
BASE = "https://apiv2.senso.ai/api/v1"
HEADERS = {"X-API-Key": KEY, "Content-Type": "application/json"}

file_bytes = open("refund-policy.txt", "rb").read()

resp = requests.post(f"{BASE}/org/kb/upload", headers=HEADERS, json={
    "files": [{
        "filename":         "refund-policy.txt",
        "file_size_bytes":  len(file_bytes),
        "content_type":     "text/plain",
        "content_hash_md5": hashlib.md5(file_bytes).hexdigest(),
    }]
})
result     = resp.json()["results"][0]
content_id = result["content_id"]
upload_url = result["upload_url"]
print(f"Content ID: {content_id}")
```

```bash
curl -X POST "https://apiv2.senso.ai/api/v1/org/kb/upload" \
  -H "X-API-Key: $SENSO_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      {
        "filename": "refund-policy.txt",
        "file_size_bytes": 204,
        "content_type": "text/plain",
        "content_hash_md5": "a3f2b8c9e1d04567890abcdef1234567"
      }
    ]
  }'
```

`status: "upload_pending"` means the file was accepted. Now PUT the raw file to the presigned URL — no API key needed, the URL is pre-authenticated:

```python
requests.put(upload_url, data=file_bytes)
print("Uploaded — processing started")
```

```bash
curl -X PUT "https://s3.amazonaws.com/..." \
  --upload-file refund-policy.txt
```

A background worker parses the file, splits it into chunks, generates vector embeddings, and indexes them into your org's knowledge base.

## Step 2 — Wait for indexing

Before your agent can search, the document needs to finish processing. **KB uploads** must be polled via **`GET /org/kb/nodes/{node_id}`** (use `node_id` from the upload response if present; otherwise the id returned for the file). Do **not** use `GET /org/content/{id}` for KB-ingested files — the API returns *“Knowledge base content must be accessed through KB node endpoints”*.

Poll until `processing_status` (or `status`) is `"complete"` / `"completed"`:

```python
import time

node_id = result.get("node_id") or content_id  # from Step 1 `result`
while True:
    item = requests.get(
        f"{BASE}/org/kb/nodes/{node_id}",
        headers={"X-API-Key": KEY},
    ).json()
    status = item.get("processing_status") or item.get("status") or ""
    print(f"Status: {status}")
    if status in ("complete", "completed"):
        break
    time.sleep(1)

print("Knowledge indexed — ready for agent queries")
```

```bash
curl "https://apiv2.senso.ai/api/v1/org/kb/nodes/e5f6a7b8-..." \
  -H "X-API-Key: $SENSO_KEY"
```

Text files complete in a few seconds. Large PDFs can take up to a minute.

## Step 3 — Agent queries the knowledge base

Now your agent can search the verified knowledge. Three search modes, same request — pick the one that fits your agent's architecture:

### Full search — agent gets an answer + sources

Use `POST /org/search` when your agent should relay a ready-made, grounded answer to the user:

```python
search = requests.post(f"{BASE}/org/search", headers=HEADERS, json={
    "query":       "What is the refund policy?",
    "max_results": 3,
}).json()

# The agent uses this answer — it's grounded in verified knowledge
print(f"Answer: {search['answer']}")

# Sources for citations
for r in search["results"]:
    print(f"  [{r['score']:.2f}] {r['title']}: {r['chunk_text'][:80]}...")
```

```bash
curl -X POST "https://apiv2.senso.ai/api/v1/org/search" \
  -H "X-API-Key: $SENSO_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the refund policy?",
    "max_results": 3
  }'
```

Response:

```json
{
  "query": "What is the refund policy?",
  "answer": "Customers may request a full refund within 30 days of purchase...",
  "results": [
    {
      "content_id": "e5f6a7b8-...",
      "version_id": "c9d0e1f2-...",
      "chunk_index": 0,
      "chunk_text": "Refund Policy: Customers may request a full refund within 30 days...",
      "score": 0.96,
      "title": "refund-policy.txt",
      "vector_id": "vec_abc"
    }
  ],
  "total_results": 1,
  "max_results": 3,
  "processing_time_ms": 380
}
```

### Context search — agent assembles its own response

Use `POST /org/search/context` when your agent has its own LLM and wants raw chunks as context. No AI answer generated — just the verified source material:

```python
context = requests.post(f"{BASE}/org/search/context", headers=HEADERS, json={
    "query": "What is the refund policy?",
    "max_results": 5,
}).json()

# Feed these chunks into your agent's LLM as grounded context
for r in context["results"]:
    print(f"  [{r['score']:.2f}] {r['chunk_text'][:100]}...")
```

```bash
curl -X POST "https://apiv2.senso.ai/api/v1/org/search/context" \
  -H "X-API-Key: $SENSO_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the refund policy?", "max_results": 5}'
```

### Content search — agent finds relevant documents

Use `POST /org/search/content` when your agent just needs to know *which documents* are relevant — returns deduplicated content IDs and titles:

```python
docs = requests.post(f"{BASE}/org/search/content", headers=HEADERS, json={
    "query": "refund policy",
}).json()

for c in docs["contents"]:
    print(f"  {c['content_id']}: {c['title']}")
```

```bash
curl -X POST "https://apiv2.senso.ai/api/v1/org/search/content" \
  -H "X-API-Key: $SENSO_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "refund policy"}'
```

---

## Which search mode should your agent use?

| Your agent needs | Use | Why |
|-----------------|-----|-----|
| A ready-made answer to show the user | `POST /org/search` | Returns an AI answer grounded in verified sources — agent can relay directly |
| Raw context to feed its own LLM | `POST /org/search/context` | Returns chunks without an answer — agent controls the final response |
| To know which documents are relevant | `POST /org/search/content` | Returns document IDs and titles — for routing, filtering, or retrieval |

---

## Full script

The complete ingest-and-search loop in one script. This is the pattern your agent integration will follow:

```python
import hashlib, os, time, requests

KEY = os.environ["SENSO_KEY"]
BASE = "https://apiv2.senso.ai/api/v1"
HEADERS = {"X-API-Key": KEY, "Content-Type": "application/json"}

# ── Ingest: give the agent verified knowledge ──────────────
file_path = "refund-policy.txt"
file_bytes = open(file_path, "rb").read()

resp = requests.post(f"{BASE}/org/kb/upload", headers=HEADERS, json={
    "files": [{
        "filename": file_path,
        "file_size_bytes": len(file_bytes),
        "content_type": "text/plain",
        "content_hash_md5": hashlib.md5(file_bytes).hexdigest(),
    }]
})
result = resp.json()["results"][0]
content_id = result["content_id"]

requests.put(result["upload_url"], data=file_bytes)
print(f"Ingesting {file_path}...")

# ── Wait for indexing (KB node endpoint) ─────────────────
node_id = result.get("node_id") or content_id
while True:
    item = requests.get(
        f"{BASE}/org/kb/nodes/{node_id}",
        headers={"X-API-Key": KEY},
    ).json()
    st = item.get("processing_status") or item.get("status") or ""
    if st in ("complete", "completed"):
        break
    time.sleep(1)
print("Knowledge indexed.")

# ── Agent query: grounded in verified knowledge ────────────
search = requests.post(f"{BASE}/org/search", headers=HEADERS, json={
    "query": "What is the refund policy?",
    "max_results": 3,
}).json()

print(f"\nAgent answer: {search['answer']}")
print(f"\nSources:")
for r in search["results"]:
    print(f"  [{r['score']:.2f}] {r['title']}: {r['chunk_text'][:80]}...")
```

## What's next

**Organize your knowledge base**

Create folders, move documents, and control which API keys can see what. Read [Knowledge Base](/docs/knowledge-base).

**Core Concepts**

Understand ingestion, search, and content generation in depth. Read [Core concepts](/docs/concepts).

**Need content generation?**

Set up your [Brand Kit](/docs/brand-kit) (2 minutes) and create a [Content Type](/docs/content-types) (2 minutes), then call `POST /org/content-generation/sample`.

**Using an AI coding tool (Claude Code, Cursor, etc.)?**

Install the CLI — your agent can call senso commands directly from its tool loop. See [Senso CLI](/docs/senso-for-agents).

**Just exploring the API?**

Browse the full [API Reference](/api-reference) for every endpoint with request/response schemas.




# Authentication


All Senso API calls are secured with **organisation-scoped API keys**. Send the key in the `X-API-Key` header on every request.

```
X-API-Key: YOUR_API_KEY
```

No OAuth flows, no token refresh — just the one header.

## Getting an API key

You can create and manage API keys directly from the [API Keys](/api-keys) page. Keys are scoped to your organisation — create a separate key for each environment or integration. You can also restrict which parts of your knowledge base a key can access — see [Permissions](/docs/permissions) for details.

## Using the key

```python
import os, requests

KEY  = os.environ["SENSO_KEY"]
BASE = "https://apiv2.senso.ai/api/v1"
HEADERS = {"X-API-Key": KEY, "Content-Type": "application/json"}

resp = requests.post(f"{BASE}/org/search", headers=HEADERS, json={
    "query": "How do I refinance?"
})
print(resp.json())
```

```bash
curl -X POST "https://apiv2.senso.ai/api/v1/org/search" \
  -H "X-API-Key: $SENSO_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I refinance?"}'
```

## Security tips

- Store keys in environment variables or a secret manager
- Never embed keys in browser or mobile apps
- Use separate keys for test and production
- Delete keys you no longer need

## Troubleshooting

**401 Unauthorized** — The key is missing or malformed. Check the header name and value.

**402 Payment Required** — Insufficient credits or spend limit reached.

**404 Not Found** — Resource doesn't exist or doesn't belong to your org.

## Next steps

- [Permissions](/docs/permissions) — Understand user roles and API key scopes
- [Quickstart](/docs/hello-world) — Make your first API call
- [API Reference](/api-reference) — Browse all endpoints
