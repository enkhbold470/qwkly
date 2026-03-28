#!/usr/bin/env python3
"""
Ingest local files into Senso org knowledge base (APIv2).

Uses `requests` like docs/senso.md (POST /org/kb/upload → PUT → GET /org/kb/nodes/{id}).

Examples:
  cd core && uv run ingest_senso.py ./data/my-notes.txt
  uv run ingest_senso.py --no-wait ./docs/*.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

_root = Path(__file__).resolve().parent
load_dotenv(_root / ".env")
load_dotenv(_root.parent / ".env", override=False)

DEFAULT_BASE = "https://apiv2.senso.ai/api/v1"

# Senso quickstart pattern (supports SENSO_API_KEY for qwkly main.py compatibility)
KEY = (os.environ.get("SENSO_KEY") or os.environ.get("SENSO_API_KEY") or "").strip()
BASE = os.environ.get("SENSO_API_BASE", DEFAULT_BASE).rstrip("/")
HEADERS = {"X-API-Key": KEY, "Content-Type": "application/json"}

_HTTP_TIMEOUT = (30, 120)


def _content_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    if guessed:
        return guessed
    ext = path.suffix.lower()
    return {
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }.get(ext, "application/octet-stream")


def _node_id_from_result(first: dict) -> str:
    for k in ("node_id", "kb_node_id", "id", "existing_content_id", "content_id"):
        val = first.get(k)
        if val:
            return str(val)
    sys.exit(f"No id to poll in upload result: {first}")


def upload_one(base: str, path: Path) -> str:
    if not KEY:
        sys.exit("Set SENSO_KEY (or SENSO_API_KEY) in core/.env")

    file_bytes = path.read_bytes()
    resp = requests.post(
        f"{base}/org/kb/upload",
        headers=HEADERS,
        json={
            "files": [
                {
                    "filename": path.name,
                    "file_size_bytes": len(file_bytes),
                    "content_type": _content_type(path),
                    "content_hash_md5": hashlib.md5(file_bytes).hexdigest(),
                }
            ]
        },
        timeout=_HTTP_TIMEOUT,
    )
    try:
        data = resp.json()
    except json.JSONDecodeError:
        data = {}
    results = data.get("results") or []
    first = results[0] if results else {}

    if resp.status_code == 422 and first.get("status") == "conflict":
        node_id = _node_id_from_result(first)
        print(f"  duplicate content (hash already in KB) → reusing id={node_id} ({path.name})")
        return node_id

    if resp.status_code != 200:
        sys.stderr.write(f"upload request failed {resp.status_code}: {resp.text}\n")
        resp.raise_for_status()
    if not results:
        sys.exit(f"Unexpected response (no results): {data}")
    first = results[0]
    upload_url = first.get("upload_url")
    if not upload_url:
        sys.exit(f"Missing upload_url: {first}")

    result = first
    content_id = result.get("content_id")
    node_id = _node_id_from_result(result)
    put = requests.put(upload_url, data=file_bytes, timeout=_HTTP_TIMEOUT)
    if put.status_code not in (200, 204):
        sys.stderr.write(f"PUT to presigned URL failed {put.status_code}: {put.text[:500]}\n")
        put.raise_for_status()
    extra = f" content_id={content_id}" if content_id else ""
    print(f"  uploaded → node_id={node_id}{extra} ({path.name})")
    return node_id


def _status_from_node_payload(item: dict) -> str:
    for k in ("processing_status", "status", "processing_state", "sync_status"):
        v = item.get(k)
        if v:
            return str(v)
    nested = item.get("node") or item.get("data")
    if isinstance(nested, dict):
        for k in ("processing_status", "status"):
            v = nested.get(k)
            if v:
                return str(v)
    return ""


def wait_complete(
    base: str,
    node_id: str,
    *,
    poll_interval: float,
    timeout_s: float,
) -> None:
    h = {"X-API-Key": KEY}
    url = f"{base}/org/kb/nodes/{node_id}"
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        gr = requests.get(url, headers=h, timeout=30)
        if gr.status_code != 200:
            sys.stderr.write(f"poll failed {gr.status_code}: {gr.text}\n")
            gr.raise_for_status()
        item = gr.json()
        if isinstance(item, dict) and isinstance(item.get("data"), dict):
            inner = item["data"]
            if any(k in inner for k in ("processing_status", "status", "processing_state")):
                item = inner
        status = _status_from_node_payload(item)
        print(f"    status: {status or '(empty — check API response keys)'}")
        if status.lower() in ("complete", "completed", "ready", "indexed"):
            return
        if status.lower() in ("failed", "error"):
            sys.exit(f"processing failed for {node_id}: {item}")
        time.sleep(poll_interval)
    sys.exit(f"timeout waiting for indexing: {node_id}")


def main() -> None:
    p = argparse.ArgumentParser(description="Ingest files into Senso KB (apiv2)")
    p.add_argument("files", nargs="+", type=Path, help="Files to ingest")
    p.add_argument(
        "--base",
        default=BASE,
        help=f"API base (default {DEFAULT_BASE})",
    )
    p.add_argument("--no-wait", action="store_true", help="Do not poll for indexing")
    p.add_argument("--poll-interval", type=float, default=1.0, help="Seconds between polls")
    p.add_argument("--timeout", type=float, default=300.0, help="Max seconds to wait per file")
    args = p.parse_args()

    base = str(args.base).rstrip("/")
    paths: list[Path] = []
    for f in args.files:
        if not f.is_file():
            sys.exit(f"Not a file: {f}")
        paths.append(f.resolve())

    print(f"Senso KB ingest — base={base}")
    print(f"files: {len(paths)}")

    for path in paths:
        print(f"\n→ {path}")
        node_id = upload_one(base, path)
        if not args.no_wait:
            print("  waiting for indexing…")
            wait_complete(
                base,
                node_id,
                poll_interval=args.poll_interval,
                timeout_s=args.timeout,
            )
            print("  indexed.")

    print("\nDone. You can query with POST /org/search (see docs/senso.md).")


if __name__ == "__main__":
    main()
