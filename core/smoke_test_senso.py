#!/usr/bin/env python3
"""
Smoke test for Senso.ai — same paths/headers as main.py (research_topic).

Run from repo root or core/:
  cd core && source .venv/bin/activate && python smoke_test_senso.py

Requires SENSO_KEY (and optionally SENSO_API_BASE) in core/.env
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load core/.env when run from core/ or repo root
_root = Path(__file__).resolve().parent
load_dotenv(_root / ".env")
load_dotenv(_root.parent / ".env", override=False)


def main() -> int:
    base = os.environ.get("SENSO_API_BASE", "https://apiv2.senso.ai/api/v1").rstrip("/")
    search_path = os.environ.get("SENSO_SEARCH_PATH", "/org/search")
    _gen = os.environ.get("SENSO_GENERATE_URL")
    if _gen is None:
        gen_url = "https://sdk.senso.ai/api/v1/generate"
    else:
        gen_url = _gen.strip()
    key = (os.environ.get("SENSO_KEY") or "").strip()
    topic = os.environ.get("SENSO_SMOKE_TOPIC", "morning routine tips for short videos")

    print("=== qwkly Senso smoke test ===")
    print(f"base: {base}")
    print(f"search path: {search_path}")
    print(f"generate URL: {gen_url or '(disabled)'}")
    print(f"topic: {topic!r}")
    if not key:
        print("FAIL: SENSO_KEY is empty. Set it in core/.env")
        return 1

    headers = {
        "X-API-Key": key,
        "Content-Type": "application/json",
    }
    query = (
        f"Trending hooks, angles, and audience pain points for short-form "
        f"vertical video (TikTok/Reels/Shorts) about: {topic}"
    )

    # --- connectivity: HEAD/GET base host (optional) ---
    try:
        origin = base.split("/api/")[0] if "/api/" in base else base
        r0 = httpx.get(origin, timeout=10.0, follow_redirects=True)
        print(f"GET {origin!r} -> {r0.status_code}")
    except Exception as exc:  # noqa: BLE001
        print(f"NOTE: could not reach origin ({exc})")

    ok_any = False

    with httpx.Client(timeout=60.0) as client:
        # 1) POST …/org/search (APIv2 — same as main.py)
        url_search = f"{base}{search_path}"
        body_search = {"query": query, "max_results": 5}
        print(f"\n--- POST {url_search} ---")
        print("body:", json.dumps(body_search)[:200], "...")
        try:
            r = client.post(url_search, headers=headers, json=body_search)
            print(f"status: {r.status_code}")
            print(f"content-type: {r.headers.get('content-type', '')}")
            txt = r.text[:4000]
            print("body (truncated):\n", txt)
            if r.status_code == 200:
                try:
                    data = r.json()
                except json.JSONDecodeError:
                    print("WARN: 200 but not JSON")
                else:
                    ans = (
                        (data.get("answer") or "")
                        or (data.get("data") or {}).get("answer")
                        or ""
                    )
                    if isinstance(ans, list):
                        ans = "\n".join(str(x) for x in ans)
                    if ans:
                        print("OK: search returned non-empty answer")
                        ok_any = True
                    else:
                        print("WARN: search 200 but empty answer (no indexed content?)")
            else:
                print("search did not return 200")
                try:
                    err = r.json()
                    if isinstance(err, dict) and err.get("message"):
                        print(f"Senso says: {err.get('message')}")
                except json.JSONDecodeError:
                    pass
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: {exc}")

        # 2) POST sdk …/generate (optional fallback — not on apiv2 /org)
        if not gen_url:
            print("\n--- generate skipped (SENSO_GENERATE_URL empty) ---")
        for ctype in ("blog_post", "bullet_list"):
            if not gen_url:
                break
            body_gen = {
                "content_type": ctype,
                "instructions": query,
                "save": False,
                "max_results": 3,
            }
            print(f"\n--- POST {gen_url} (content_type={ctype}) ---")
            try:
                gen = client.post(gen_url, headers=headers, json=body_gen)
                print(f"status: {gen.status_code}")
                print(gen.text[:4000])
                if gen.status_code == 200:
                    try:
                        g = gen.json()
                    except json.JSONDecodeError:
                        print("WARN: 200 but not JSON")
                    else:
                        text = g.get("generated_text") or ""
                        if text:
                            print(f"OK: generate ({ctype}) returned text ({len(text)} chars)")
                            ok_any = True
                            break
                        print(f"WARN: generate 200 but empty generated_text keys={list(g.keys())}")
                else:
                    print(f"generate failed for content_type={ctype}")
                    try:
                        err = gen.json()
                        if isinstance(err, dict) and err.get("message"):
                            print(f"Senso says: {err.get('message')}")
                    except json.JSONDecodeError:
                        pass
            except Exception as exc:  # noqa: BLE001
                print(f"ERROR: {exc!r}")

    print("\n=== summary ===")
    if ok_any:
        print("PASS: at least one Senso call returned usable text.")
        return 0
    print(
        "FAIL: Senso did not return usable text. Check:\n"
        "  - API key and project (email from Senso)\n"
        "  - SENSO_API_BASE if your tenant uses a custom host\n"
        "  - Search may need content ingested first; try /generate only\n"
        "  - See response bodies above for Senso error messages",
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
