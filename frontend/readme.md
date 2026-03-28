# qwkly frontend (Next.js)

This folder is for the **Next.js + assistant-ui** app. The backend lives in `../core/` and exposes `POST /generate` with **SSE** — see [`../core/API.md`](../core/API.md).

**Integration checklist**

1. Set `QWKLY_BACKEND_URL` (server) or `NEXT_PUBLIC_QWKLY_API_URL` (browser) to the Flask/uvicorn base URL.
2. On `POST /generate`, read the response body as a stream and parse `event:` / `data:` frames (not browser `EventSource`, which is GET-only).
3. Optional: protect your Next route with Unkey; if the backend has `UNKEY_VERIFY=true`, forward `Authorization: Bearer <key>` to the core API.
