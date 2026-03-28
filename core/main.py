"""
ReelForge backend: Flask + Railtracks-style tool nodes, SSE progress, FFmpeg 9:16 assembly.
Run: uvicorn main:asgi_app --app-dir /path/to/core --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Generator

import httpx
import railtracks as rt
from asgiref.wsgi import WsgiToAsgi
from dotenv import load_dotenv
from flask import Flask, Response, has_request_context, request, send_from_directory
from flask_cors import CORS
from openai import OpenAI

load_dotenv()

# --- Config -----------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SENSO_API_BASE = os.environ.get("SENSO_API_BASE", "https://sdk.senso.ai/api/v1")
KIE_API_BASE = os.environ.get("KIE_API_BASE", "https://api.kie.ai")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
KIE_API_KEY = os.environ.get("KIE_API_KEY", "")
SENSO_API_KEY = os.environ.get("SENSO_API_KEY", "")
KIE_CALLBACK_URL = os.environ.get(
    "KIE_CALLBACK_URL",
    "https://httpbin.org/post",
)
# Kie Suno models: **V4** is the budget / entry tier (shortest max length, typically lowest
# credits vs V4_5* / V5*). See https://docs.kie.ai/suno-api/generate-music
_KIE_SUNO_MODELS = frozenset({"V4", "V4_5", "V4_5PLUS", "V4_5ALL", "V5", "V5_5"})


def _kie_suno_model() -> str:
    raw = (os.environ.get("KIE_SUNO_MODEL") or "V4").strip()
    return raw if raw in _KIE_SUNO_MODELS else "V4"


UNKEY_VERIFY = os.environ.get("UNKEY_VERIFY", "").lower() in ("1", "true", "yes")
UNKEY_ROOT_KEY = os.environ.get("UNKEY_ROOT_KEY", "")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": os.environ.get("CORS_ORIGINS", "*")}})


def _client_openai() -> OpenAI:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=OPENAI_API_KEY)


def _sse(event: str, payload: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def _verify_unkey_bearer() -> tuple[bool, str]:
    if not UNKEY_VERIFY:
        return True, ""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False, "Missing or invalid Authorization header"
    key = auth.removeprefix("Bearer ").strip()
    if not key:
        return False, "Empty API key"
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if UNKEY_ROOT_KEY:
        headers["Authorization"] = f"Bearer {UNKEY_ROOT_KEY}"
    try:
        r = httpx.post(
            "https://api.unkey.dev/v1/keys.verify",
            json={"key": key},
            headers=headers,
            timeout=15.0,
        )
        r.raise_for_status()
        body = r.json()
        valid = body.get("valid") is True
        return valid, "" if valid else "Invalid API key"
    except Exception as exc:  # noqa: BLE001
        return False, f"Unkey verification failed: {exc}"


# --- Railtracks function nodes (tools) --------------------------------------


@rt.function_node
def research_topic(topic: str) -> str:
    """Senso search / generate fallback for trending-style context."""
    if not SENSO_API_KEY:
        return (
            f"No Senso API key; using topic only. Topic: {topic}. "
            "Assume short-form vertical video trends for this niche."
        )
    headers = {
        "X-API-Key": SENSO_API_KEY,
        "Content-Type": "application/json",
    }
    query = (
        f"Trending hooks, angles, and audience pain points for short-form "
        f"vertical video (TikTok/Reels/Shorts) about: {topic}"
    )
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            f"{SENSO_API_BASE}/search",
            headers=headers,
            json={"query": query, "max_results": 5},
        )
        if r.status_code == 200:
            data = r.json()
            ans = data.get("answer") or ""
            if ans:
                return ans[:8000]
        gen = client.post(
            f"{SENSO_API_BASE}/generate",
            headers=headers,
            json={
                "content_type": "bullet_list",
                "instructions": query,
                "save": False,
                "max_results": 3,
            },
        )
        if gen.status_code == 200:
            g = gen.json()
            text = g.get("generated_text") or ""
            if text:
                return text[:8000]
    return f"Senso returned no body; rely on topic: {topic}"


@rt.function_node
def generate_script(context: str) -> list[str]:
    """Return 5–7 punchy lines for the reel."""
    client = _client_openai()
    completion = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You write viral short-form on-screen lines. "
                    "Return JSON: {\"lines\": [\"line1\", ...]} with 5 to 7 short lines, "
                    "no hashtags, punchy, second person or imperative, under 80 chars each."
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nProduce the JSON.",
            },
        ],
    )
    raw = completion.choices[0].message.content or "{}"
    data = json.loads(raw)
    lines = data.get("lines") or []
    out = [str(x).strip() for x in lines if str(x).strip()]
    if len(out) < 3:
        raise RuntimeError("Script too short")
    return out[:7]


@rt.function_node
def generate_music(mood: str = "upbeat energetic") -> str:
    """kie.ai Suno: return MP3 URL (duration inferred via ffprobe in assembly)."""
    if not KIE_API_KEY:
        raise RuntimeError("KIE_API_KEY is not set (required for music generation)")
    headers = {
        "Authorization": f"Bearer {KIE_API_KEY}",
        "Content-Type": "application/json",
    }
    prompt = f"{mood} instrumental background music, no vocals, short catchy hook"
    body = {
        "prompt": prompt[:500],
        "customMode": False,
        "instrumental": True,
        "model": _kie_suno_model(),
        "callBackUrl": KIE_CALLBACK_URL,
    }
    with httpx.Client(timeout=120.0) as client:
        pr = client.post(f"{KIE_API_BASE}/api/v1/generate", headers=headers, json=body)
        pr.raise_for_status()
        pj = pr.json()
        if pj.get("code") != 200:
            raise RuntimeError(pj.get("msg") or "kie generate failed")
        task_id = pj.get("data", {}).get("taskId")
        if not task_id:
            raise RuntimeError("No taskId from kie")

        deadline = time.time() + 600
        while time.time() < deadline:
            gr = client.get(
                f"{KIE_API_BASE}/api/v1/generate/record-info",
                headers=headers,
                params={"taskId": task_id},
            )
            gr.raise_for_status()
            gj = gr.json()
            if gj.get("code") != 200:
                raise RuntimeError(gj.get("msg") or "kie record-info failed")
            data = gj.get("data") or {}
            status = data.get("status") or ""
            if status in ("CREATE_TASK_FAILED", "GENERATE_AUDIO_FAILED", "SENSITIVE_WORD_ERROR"):
                raise RuntimeError(data.get("errorMessage") or status)
            resp = data.get("response") or {}
            suno = resp.get("sunoData") or []
            if suno:
                first = suno[0]
                url = first.get("audioUrl") or first.get("streamAudioUrl")
                if url and status in ("FIRST_SUCCESS", "SUCCESS", "TEXT_SUCCESS"):
                    return url
                if url and status == "PENDING":
                    time.sleep(3)
                    continue
            if status == "SUCCESS" and suno:
                first = suno[0]
                url = first.get("audioUrl") or first.get("streamAudioUrl")
                if url:
                    return url
            time.sleep(3)
    raise RuntimeError("Timed out waiting for Suno audio")


@rt.function_node
def generate_visuals(script_lines: list[str]) -> list[str]:
    """DALL-E 3 per line; returns local file paths (JPEG)."""
    client = _client_openai()
    paths: list[str] = []
    for i, line in enumerate(script_lines):
        result = client.images.generate(
            model="dall-e-3",
            prompt=(
                f"Cinematic vertical 9:16 key art for a short video line: {line}. "
                "Bold lighting, no text in image, single clear subject."
            )[:4000],
            size="1024x1792",
            quality="standard",
            n=1,
        )
        u = result.data[0].url
        if not u:
            raise RuntimeError("DALL-E returned no URL")
        with httpx.Client(timeout=120.0) as h:
            im = h.get(u)
            im.raise_for_status()
        ext = ".png" if "png" in (u.lower()) else ".jpg"
        p = OUTPUT_DIR / f"img_{uuid.uuid4().hex}_{i}{ext}"
        p.write_bytes(im.content)
        paths.append(str(p))
    return paths


def _ffprobe_duration(audio_path: str) -> float:
    out = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        return float(out.stdout.strip() or 30.0)
    except ValueError:
        return 30.0


def _sanitize_ass_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")")


def _write_ass(captions: list[str], segment_duration: float, path: Path) -> None:
    """Simple middle-bottom captions, one Dialogue per line."""
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,56,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,40,40,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for i, cap in enumerate(captions):
        start = i * segment_duration
        end = (i + 1) * segment_duration
        s = _format_ass_time(start)
        e = _format_ass_time(end)
        t = _sanitize_ass_text(cap)
        lines.append(f"Dialogue: 0,{s},{e},Default,,0,0,0,,{t}\n")
    path.write_text("".join(lines), encoding="utf-8")


def _format_ass_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    cs = int(round((s - int(s)) * 100))
    sec = int(s)
    return f"{h:d}:{m:02d}:{sec:02d}.{cs:02d}"


@rt.function_node
def assemble_video(
    image_paths: list[str],
    audio_url: str,
    captions: list[str],
) -> str:
    """Download audio, build concat slideshow + ASS, return path to MP4."""
    if not image_paths:
        raise RuntimeError("No images")
    work = Path(tempfile.mkdtemp(prefix="reelforge_"))
    audio_local = work / "audio.mp3"
    with httpx.Client(timeout=120.0) as h:
        ar = h.get(audio_url)
        ar.raise_for_status()
        audio_local.write_bytes(ar.content)

    duration = _ffprobe_duration(str(audio_local))
    n = len(image_paths)
    seg = max(duration / n, 1.25)
    if seg * n > duration + 0.1:
        seg = duration / n

    scaled: list[Path] = []
    for i, ip in enumerate(image_paths):
        op = work / f"sc_{i:03d}.jpg"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                ip,
                "-vf",
                "scale=1080:1920:force_original_aspect_ratio=decrease,"
                "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
                "-frames:v",
                "1",
                str(op),
            ],
            capture_output=True,
            check=True,
        )
        scaled.append(op)

    concat_list = work / "concat.txt"
    lines_txt: list[str] = []
    for i, p in enumerate(scaled):
        lines_txt.append(f"file '{p.as_posix()}'\n")
        lines_txt.append(f"duration {seg}\n")
    lines_txt.append(f"file '{scaled[-1].as_posix()}'\n")
    concat_list.write_text("".join(lines_txt), encoding="utf-8")

    ass_path = work / "subs.ass"
    caps = captions[: len(scaled)] if captions else [f"Slide {i+1}" for i in range(len(scaled))]
    _write_ass(caps, seg, ass_path)

    out_mp4 = OUTPUT_DIR / f"reel_{uuid.uuid4().hex}.mp4"
    vf = f"ass={ass_path.as_posix()},format=yuv420p"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-i",
            str(audio_local),
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-shortest",
            "-movflags",
            "+faststart",
            str(out_mp4),
        ],
        capture_output=True,
        check=True,
    )
    return str(out_mp4)


# Optional Railtracks agent (LLM + tools) — not used for deterministic SSE pipeline.
ReelAgent = rt.agent_node(
    llm=rt.llm.OpenAILLM("gpt-4o"),
    system_message=(
        "You create viral short-form videos. When asked, call tools in order: "
        "research_topic, generate_script, generate_music, generate_visuals, assemble_video."
    ),
    tool_nodes=(
        research_topic,
        generate_script,
        generate_music,
        generate_visuals,
        assemble_video,
    ),
)


def run_pipeline_events(topic: str) -> Generator[str, None, None]:
    """Sequential pipeline with SSE strings (sync)."""
    yield _sse("research", {"status": "started", "topic": topic})
    ctx = research_topic(topic)
    yield _sse("research", {"status": "done", "context": ctx})

    yield _sse("script", {"status": "started"})
    lines = generate_script(ctx)
    yield _sse("script", {"status": "done", "lines": lines})

    yield _sse("music", {"status": "started"})
    audio_url = generate_music()
    yield _sse("music", {"status": "done", "audio_url": audio_url})

    yield _sse("visuals", {"status": "started", "count": len(lines)})
    img_paths = generate_visuals(lines)
    yield _sse(
        "visuals",
        {"status": "done", "paths": [Path(p).name for p in img_paths]},
    )

    yield _sse("render", {"status": "started"})
    video_path = assemble_video(img_paths, audio_url, lines)
    name = Path(video_path).name
    base = ""
    if has_request_context():
        base = request.host_url.rstrip("/")
    rel = f"/videos/{name}"
    yield _sse(
        "done",
        {
            "video_url": f"{base}{rel}" if base else rel,
            "filename": name,
        },
    )

@app.post("/generate")
def generate():
    ok, err = _verify_unkey_bearer()
    if not ok:
        return Response(json.dumps({"error": err}), status=401, mimetype="application/json")

    body = request.get_json(silent=True) or {}
    topic = (body.get("topic") or "").strip()
    if not topic:
        return Response(
            json.dumps({"error": "topic is required"}),
            status=400,
            mimetype="application/json",
        )

    def gen() -> Generator[str, None, None]:
        try:
            yield from run_pipeline_events(topic)
        except Exception as exc:  # noqa: BLE001
            yield _sse("error", {"message": str(exc)})

    return Response(
        gen(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/")
def health():
    return {"ok": True, "service": "reelforge-core"}


@app.get("/videos/<path:name>")
def serve_video(name: str):
    safe = Path(name).name
    if not re.match(r"^[\w.\-]+$", safe):
        return Response("bad filename", status=400)
    path = OUTPUT_DIR / safe
    if not path.is_file():
        return Response("not found", status=404)
    return send_from_directory(OUTPUT_DIR, safe, mimetype="video/mp4")


asgi_app = WsgiToAsgi(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), debug=True)
