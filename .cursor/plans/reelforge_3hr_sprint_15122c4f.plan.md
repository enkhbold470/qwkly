---
name: ReelForge 3hr Sprint
overview: "Split team: backend owner ships Flask + Railtracks pipeline (Senso → script → kie Suno → DALL-E → FFmpeg 9:16) with streaming progress and a stable HTTP contract; frontend friend wires Next.js/assistant-ui to that API. **No Docker for now**—run locally (or on a VM) with **uvicorn** + Flask via WSGI→ASGI bridge; `ffmpeg` on host PATH. Unkey can guard the public edge (friend) or the backend directly."
todos:
  - id: python-main
    content: "Backend: Flask in main.py — SSE/streaming (e.g. Response + generator), Railtracks nodes (Senso, OpenAI, Suno, DALL-E, FFmpeg)"
    status: completed
  - id: ffmpeg-pipeline
    content: "Backend: 9:16 slideshow + timed captions + audio merge; test with ffmpeg locally"
    status: completed
  - id: api-contract
    content: "Document contract for friend: POST /generate topic, event types, final video URL or path; CORS if cross-origin"
    status: completed
  - id: unkey-backend
    content: "Optional: verify Unkey in Flask (Authorization header / before_request) if friend calls Python directly; else friend handles Unkey on Next route"
    status: completed
  - id: run-uvicorn
    content: "Backend: run with uvicorn (Flask WSGI via asgiref WsgiToAsgi); document command + port; no Docker for now; ffmpeg on PATH"
    status: completed
  - id: frontend-friend
    content: "[Friend] Next.js + assistant-ui — chat, stream SSE to UI, proxy or call backend URL"
    status: completed
isProject: false
---

# ReelForge implementation plan

## Team split


| Owner      | Scope                                                                                                                                                                                                                                                                                                  |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **You**    | Backend core: `main.py` (**Flask**), Railtracks pipeline, Senso / OpenAI / kie / DALL-E integrations, FFmpeg assembly, streaming progress events, **serve with uvicorn** (no Docker for now), API contract doc for the frontend. i created folder called core, just use core folder as backend i guess |
| **Friend** | Next.js UI: `assistant-ui`, topic input, consuming your stream (SSE or NDJSON), optional Next.js route that proxies to your backend + **Unkey** on the public edge if that fits their setup.                                                                                                           |


The [rules/coding-style.md](rules/coding-style.md) *"one main.py"* rule applies to **your** Python service; the frontend lives in a separate app (your repo may only contain `api/` or root `main.py` + `requirements` + `Dockerfile`).

## Target architecture

```mermaid
flowchart LR
  User[User] --> Chat[Next.js friend]
  Chat -->|SSE POST generate| Py[Flask main.py]
  Py --> Senso[Senso.ai]
  Py --> OAI[OpenAI]
  Py --> Kie[kie Suno]
  Py --> FF[FFmpeg]
  FF --> Mp4[video result]
  Py --> Chat
  Chat -.->|optional| Unkey[Unkey at edge]
```



## Backend contract (for your friend)

Define and stick to one pattern so UI work is parallel:

- **Endpoint:** e.g. `POST /generate` with JSON `{ "topic": "string" }`.
- **Response:** **SSE** (`text/event-stream`) with named events, e.g. `research`, `script`, `music`, `visuals`, `render`, `done`, `error` — each payload JSON with step-specific fields (context snippet, lines array, audio URL optional, image URLs, final `video_url` or relative path).
- **CORS:** If the Next app is on another origin in dev/prod, enable CORS on Flask (`flask-cors` or manual `Access-Control-`* on the app) for the friend’s origins.
- **Auth:** Either friend forwards `Authorization: Bearer <unkey>` and you validate with Unkey SDK, or friend validates only at Next and calls your service on a private network / shared secret—pick one and document it.

## FFmpeg / “beat-synced” reality check

1. Download images + audio to temp (`/tmp` on DO).
2. Slideshow: concat or xfade; **duration per image** = `audio_duration / n_lines` (or fixed cap) to match track length.
3. Captions: SRT/ASS or timed `drawtext` per segment—not a single static string.
4. Runtime: **ffmpeg binary** must exist in the container/image (`ffmpeg-python` is a wrapper).

## API integrations (backend)


| Service      | Backend action                                                                                 |
| ------------ | ---------------------------------------------------------------------------------------------- |
| **Senso.ai** | `senso_search(topic) -> str` for script context                                                |
| **OpenAI**   | `OPENAI_API_KEY`: chat for script + DALL-E 3 per line                                          |
| **kie Suno** | Poll until MP3 URL; use duration for FFmpeg                                                    |
| **Unkey**    | Validate on Flask **or** only on Next—avoid double confusion; one place is enough for the demo |


## Sprint mapping (rebalanced)

**You (backend)**

- Flask + Railtracks nodes end-to-end; structured streaming events (SSE via `Response` + stream generator or chunked).
- FFmpeg 9:16 output; expose final asset (signed URL, static mount, or base64 for tiny demos—keep clips short).
- Dockerfile + DO for Python + ffmpeg; env template (`OPENAI_API_KEY`, Senso, kie keys, etc.).

**Friend (frontend)**

- Next.js + assistant-ui wired to your `POST /generate` stream.
- Optional: Next `/api/generate` proxy + Unkey middleware.

**Together**

- Integration test: topic → streamed steps → playable MP4 in UI.

## Repo layout (suggested)

- **Your repo / folder:** `main.py` (or `api/main.py`), `requirements.txt` or `pyproject.toml`, `Dockerfile`, `.env.example`, short `API.md` for your friend.
- **Friend’s repo:** Next.js app; `NEXT_PUBLIC_REELFORGE_API_URL` or server-side `REELFORGE_BACKEND_URL`.

## Risks (3-hour window)

- **Railtracks:** Confirm package name and `agent_node` API from official docs/examples.
- **Timeouts:** Long-running pipeline → use a **long-lived** Python service on DO, not a 10s serverless function.
- **Senso/kie latency:** Streaming events keep the UI responsive.

## Optional

- Strict single-file *everything* including HTML would mean no Next.js—not your split; friend owns UI.

