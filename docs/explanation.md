# How qwkly Works (Simple Version)

Imagine you want a **tiny movie** for your phone screen (tall like TikTok), with **pictures**, **words on the screen**, and **music**—and you only type **one idea** (like “best morning routine tips”). **qwkly** is the helper that tries to build that for you.

---

## The big picture

1. You (or a friend’s website) send **one topic** to the **backend** (the brain in `core/`).
2. The backend does **one step after another**—like stations on an assembly line.
3. While it works, it sends **updates** (“I’m researching…”, “I’m writing lines…”) so the screen can show progress.
4. At the end you get a **link to a video file** you can play.

---

## What happens step by step?

Think of it like making a school poster project, but the computer does the work.

### Step 1 — Learn about the topic (research)

The program asks **Senso** (a smart search helper) for ideas about what’s **trending** or interesting for short videos on that topic.

- If there is **no Senso key**, it still continues using **only your topic** so the rest can run.

### Step 2 — Write short lines (script)

**GPT‑4o** (a writing AI) reads that research and writes **5 to 7 short lines**—like lines that could flash on screen in a reel. Each line is meant to be **punchy** and easy to read fast.

### Step 3 — Make background music (music)

The program asks **kie’s Suno API** to create **upbeat instrumental** music (no singing words). It waits until the music is ready and gets a **link to the audio file**.

- The default music model is **V4**, picked to be **affordable** on kie.

### Step 3b — Voiceover (TTS)

**OpenAI text-to-speech** reads your script lines aloud (one voice track). In the final video, that voice is **mixed with** the Suno music (music is turned down a bit so you can hear the voice). You can turn TTS off with `TTS_ENABLED=false` in `.env`.

### Step 4 — Make pictures (visuals)

For **each line**, the program asks **DALL·E 3** to draw **one tall picture** that matches that line. The pictures are saved on the server as files.

### Step 5 — Glue it into a video (assembly)

A tool called **FFmpeg** (video glue) does the real “movie” work:

- It shows each picture for a **fixed time** (default **3 seconds** per image), with a **maximum reel length** (default **30 seconds**), so extra images are dropped if there are too many.
- It adds **captions** (the script lines) timed with each picture.
- It mixes **Suno music** and **TTS voice** into one soundtrack, then adds that to the video.
- It saves one **MP4** file (phone-shaped: **9:16**).

Then the backend tells you the **filename** and a **URL** so you can download or play the video.

---

## How does the website know what’s happening?

The backend does **not** wait until the end to say nothing. It uses **SSE** (Server-Sent Events)—think of it like **text messages** that say: “Still working… now I’m on music… now pictures…” so the front page can show a **live progress** bar or messages.

---

## What about keys and safety?

- **API keys** are secret passwords stored in a `.env` file (not shared on the internet).
- **Unkey** (optional): if turned on, the backend checks that the request has a **valid key**—like a ticket at a movie theater—so random people can’t spam your expensive steps.

---

## What is Railtracks?

**Railtracks** is a Python library that wraps each step as a **named tool** (like labeled boxes). The main run uses those tools **in order** so the video always builds the same way: research → script → music → pictures → final video.

---

## Where do things live?

| Piece | Plain English |
| ----- | ------------- |
| `core/main.py` | The recipe: all the steps and the web server. |
| `core/output/` | Finished video files land here. |
| Friend’s **Next.js** app | The pretty chat screen; it talks to the backend over the network. |

---

## One sentence summary

**You give a topic; the server researches, writes lines, makes music and art for each line, stitches a tall video with captions, then gives you a link to watch it.**
