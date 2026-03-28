Solid idea. You have exactly **3 hours left**. Here's the full plan.

## The Agent: "ReelForge"

User types a topic → agent researches trending context → writes a script → generates upbeat music → assembles a 9:16 vertical video with captions + beat-synced visuals. Fully autonomous after one prompt.

## Tech Stack

| Layer | Tool | Why |
|-------|------|-----|
| Agent brain | **Railtracks**  [youtube](https://www.youtube.com/watch?v=0WJ_I_zWX8I) | Chains all tools, Python-native, $700 prize |
| Content context | **Senso.ai**  [docs.senso](https://docs.senso.ai) | Trending topic research + verified script context |
| Chat UI | **assistant-ui**  [github](https://github.com/assistant-ui/assistant-ui) | Streams progress live to user |
| Music | **kie.ai Suno API**  [kie](https://kie.ai/suno-api) | Upbeat instrumental from text prompt, ~20s gen |
| Visuals | OpenAI DALL-E 3 | Beat-synced image generation per script line |
| Assembly | **FFmpeg + Python**  [youtube](https://www.youtube.com/watch?v=IYnJTjmbJv8) | Stitch images + captions + music into 9:16 MP4 |
| Auth | **Unkey**  [unkey](https://www.unkey.com/docs/quickstart/quickstart) | Rate limit API per user key |
| Deploy | **DigitalOcean** | App Platform, 1-click deploy |

## Railtracks Agent Flow

```python
import railtracks as rt

@rt.function_node
def research_topic(topic: str) -> str:
    # Senso.ai search for trending context
    return senso_search(topic)

@rt.function_node
def generate_script(context: str) -> list[str]:
    # GPT-4o: returns 5-7 punchy lines for the reel
    return openai_script(context)

@rt.function_node
def generate_music(mood: str = "upbeat energetic") -> str:
    # kie.ai Suno API → returns mp3 URL
    return suno_generate(f"{mood} background music no vocals")

@rt.function_node
def generate_visuals(script_lines: list[str]) -> list[str]:
    # DALL-E 3 per line → list of image URLs
    return [dalle_generate(line) for line in script_lines]

@rt.function_node
def assemble_video(images, audio_url, captions) -> str:
    # FFmpeg: 9:16, overlay captions, merge audio
    return ffmpeg_assemble(images, audio_url, captions)

ReelAgent = rt.agent_node(
    llm=rt.llm.OpenAILLM("gpt-4o"),
    system_message="You create viral short-form videos. Use tools in order.",
    tool_nodes=[research_topic, generate_script, generate_music,
                generate_visuals, assemble_video]
)
```

## 3-Hour Sprint Plan

1. **1:30–2:15 PM** - Next.js + `assistant-ui` chat scaffold. One input field, streaming agent messages
2. **2:15–3:00 PM** - Railtracks pipeline: research → script → music. Test end-to-end with Senso.ai + kie.ai
3. **3:00–3:30 PM** - FFmpeg assembly: `ffmpeg-python` lib, 9:16 crop, caption overlay with `drawtext`, merge audio
4. **3:30–3:45 PM** - Unkey middleware on `/api/generate` route (10 min setup) [unkey](https://www.unkey.com/docs/quickstart/quickstart)
5. **3:45–4:15 PM** - Deploy to DigitalOcean App Platform, test live URL
6. **4:15–4:30 PM** - Record demo, push GitHub, submit Devpost

## FFmpeg Assembly (key snippet)

```python
import ffmpeg

def assemble_video(image_paths, audio_url, captions):
    # Create slideshow from images at 2s each
    input_imgs = ffmpeg.input('pipe:', framerate=0.5, format='image2pipe')
    audio = ffmpeg.input(audio_url)
    
    out = (
        ffmpeg
        .overlay(input_imgs, audio)
        .filter('scale', 1080, 1920)  # 9:16
        .filter('drawtext', text=captions, fontsize=48, 
                fontcolor='white', x='(w-text_w)/2', y='h*0.8')
        .output('reel_output.mp4', vcodec='libx264', acodec='aac')
    )
    out.run()
```

## Demo Script (3 min)

1. Type "best morning routine tips" into the chat (10s)
2. Show agent live: Senso researching → script appearing → music generating (60s)
3. Play the finished 30-second reel with music + captions (30s)
4. Show Unkey dashboard: API calls logged (20s)
5. Pitch: "Any creator can make 10 reels in the time it takes to film one" (40s)

The music-driven angle is your hook. Senso.ai  gives you real trending context so scripts aren't generic, which is what makes this different from basic video generators. Start coding now. [sensoai.mintlify](https://sensoai.mintlify.app/introduction)