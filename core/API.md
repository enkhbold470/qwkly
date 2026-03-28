# ReelForge core HTTP API

Base URL: your deployed host or `http://127.0.0.1:8000` in development.

## `POST /generate`

Starts the reel pipeline and streams **Server-Sent Events** (`text/event-stream`).

**Request body (JSON)**

| Field   | Type   | Required | Description        |
| ------- | ------ | -------- | ------------------ |
| `topic` | string | yes      | Theme for the reel |

**Headers**

- `Content-Type: application/json`
- If `UNKEY_VERIFY=true` on the server: `Authorization: Bearer <your-unkey-api-key>`

**SSE events**

Each message has an `event:` line and a JSON `data:` line.

| Event      | When | Payload (JSON) |
| ---------- | ---- | --------------- |
| `research` | start / done | `{ "status": "started", "topic" }` or `{ "status": "done", "context" }` |
| `script`   | start / done | `{ "status": "started" }` or `{ "status": "done", "lines": string[] }` |
| `music`    | start / done | `{ "status": "started" }` or `{ "status": "done", "audio_url" }` |
| `visuals`  | start / done | `{ "status": "started", "count" }` or `{ "status": "done", "paths": string[] }` (filenames only) |
| `render`   | start | `{ "status": "started" }` |
| `done`     | end | `{ "video_url", "filename" }` — `video_url` is absolute if `Host` is available |
| `error`    | failure | `{ "message": string }` |

**Example (curl)**

```bash
curl -N -H "Content-Type: application/json" \
  -d '{"topic":"morning routine tips"}' \
  http://127.0.0.1:8000/generate
```

**Frontend integration**

- Use `EventSource` only for GET; for POST+SSE use `fetch` with `ReadableStream` or libraries that parse SSE from a POST body (e.g. assistant-ui adapters often use `fetch` + split on `\n\n`).
- Point your Next.js app at `REELFORGE_BACKEND_URL` (e.g. `http://127.0.0.1:8000`).

## `GET /health`

Returns `{ "ok": true, "service": "reelforge-core" }`.

## `GET /videos/<filename>`

Serves a finished MP4 from server `output/` (filename from `done` event).

---

## Run locally (uvicorn)

From the `core` directory, with a virtualenv and `ffmpeg` on `PATH`:

```bash
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)   # or use direnv
uvicorn main:asgi_app --host 0.0.0.0 --port 8000
```

Requires: Python 3.10+, `ffmpeg` + `ffprobe` installed system-wide. For kie Suno music, **`KIE_SUNO_MODEL`** defaults to **`V4`** (affordable entry tier); see `.env.example`.
