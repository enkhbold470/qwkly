# Reel stills — GPT Image (`gpt-image-1` / `gpt-image-1.5`)

Runtime prompts and defaults live in **`core/main.py`** (`_reel_image_prompt`, `generate_visuals`).

## DALL·E 3 deprecation

DALL·E 3 is scheduled for deprecation on **May 12, 2026**. OpenAI recommends **GPT Image** models (`gpt-image-1`, `gpt-image-1.5`, etc.) with optional **`moderation: "low"`** for fewer false positives on creative briefs.

## What often trips the content filter

From [OpenAI community — DALL·E tips](https://community.openai.com/t/collection-of-dall-e-3-prompting-tips-issues-and-bugs/889278) and product guidance:

- **“RAW photo” + person + skin-related terms** — can read as disallowed real-photo / ID intent
- **“wet,” “sweat,” “glistening skin”** — often flagged even in innocent contexts
- **Real person / celebrity names**
- **“Realistic human skin,” “ultra-detailed body”**
- **“Analog photo” + women/men** — film language near people can over-trigger

## Safe replacements (summary)

| Risky | Safer |
| --- | --- |
| `RAW photo, analog photo` | `cinematic still, editorial photograph` |
| `ultra-detailed skin` | `sharp cinematic detail, film grain` |
| `photorealistic person` | `editorial portrait, studio photograph` |
| `shot on Sony A7IV` | `medium format photography, f/1.4 depth` |

Urban night scenes **without** people-specific triggers (e.g. neon, wet streets) are often fine.

## Core formula (unchanged idea)

```
[Subject] + [Camera / lens feel] + [Lighting] + [Environment / mood] + [safe quality line]
```

Lead with the **subject**, describe **lighting** positively, end with **vertical 9:16** for reels.

## Example — safer portrait-style line

```
An editorial portrait of a young woman walking through Tokyo at night,
neon city lights reflecting on the pavement, leather jacket, cinematic still,
medium format photography, f/1.4 depth of field, golden and cyan color grading,
film grain, vertical 9:16 format, high quality
```

## API usage in qwkly

Configured via **`.env`** (see **`core/.env.example`**):

- `OPENAI_IMAGE_MODEL` — default `gpt-image-1` (override with `gpt-image-1.5`, etc., as supported).
- `OPENAI_IMAGE_SIZE` — default `1024x1536` (portrait for short vertical video).
- `OPENAI_IMAGE_MODERATION` — default `low` (`auto` is stricter).

The Python SDK returns **base64** for GPT Image models (not a long-lived URL); `generate_visuals` decodes and saves **JPEG** files.
