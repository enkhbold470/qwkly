# qwkly core HTTP API

Base URL: your deployed host or `http://127.0.0.1:8000` in development.

## Postman

Import **`postman/qwkly.postman_collection.json`** (File → Import). Optionally import **`postman/qwkly.local.postman_environment.json`** and select environment **qwkly local**.

- **Health** — quick JSON check.
- **Generate reel** — body is JSON `{ "topic": "..." }`; response is **SSE** (see raw body). Enable the **Authorization** header if `UNKEY_VERIFY=true`.
- **Download video** — set `videoFilename` from the `done` event’s `filename`.

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
| `tts`      | start / done | `{ "status": "started" }` or `{ "status": "done", "skipped": bool }` — OpenAI TTS voiceover (skipped if `TTS_ENABLED=false`) |
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
- Point your Next.js app at `QWKLY_BACKEND_URL` (e.g. `http://127.0.0.1:8000`).

## `GET /health`

Returns `{ "ok": true, "service": "qwkly-core" }`.

## `GET /videos/<filename>`

Serves a finished MP4 from server `output/` (filename from `done` event).

## Rendered video (defaults)

Assembly uses FFmpeg: **one image every `SLIDE_DURATION_SEC` seconds** (default **3**), **up to `MAX_VIDEO_DURATION_SEC` total** (default **30**). If there are more images than fit, the rest are omitted. **Suno** is mixed under **TTS** with `TTS_MUSIC_VOLUME` / `TTS_VOICE_VOLUME` (defaults: quieter bed, louder voice).

---

## Run locally (uvicorn)

From the `core` directory, with a virtualenv and `ffmpeg` on `PATH`:

```bash
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)   # or use direnv
uvicorn main:asgi_app --host 0.0.0.0 --port 8000
```

Requires: Python 3.10+, `ffmpeg` + `ffprobe` installed system-wide. The script step uses the OpenAI **Responses** API with **`OPENAI_TEXT_MODEL`** (default **`gpt-5.4-2026-03-05`**). For kie Suno music, **`KIE_SUNO_MODEL`** defaults to **`V4`** (affordable entry tier); see `.env.example`.
