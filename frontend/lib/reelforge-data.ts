import { ReelForgeStep } from "./reelforge-types";

export const stepMetaById = {
  research: {
    title: "Prompt intake",
    endpoint: "/api/generate"
  },
  script: {
    title: "Write punchy script",
    endpoint: "/api/generate/script"
  },
  music: {
    title: "Generate upbeat music",
    endpoint: "/api/generate/music"
  },
  visuals: {
    title: "Create beat-synced visuals",
    endpoint: "/api/generate/visuals"
  },
  assemble: {
    title: "Assemble vertical reel",
    endpoint: "/api/generate/assemble"
  }
} as const;

export function initialSteps(): ReelForgeStep[] {
  return [
    {
      id: "research",
      title: "Prompt intake",
      category: "Topic",
      endpoint: "/api/generate",
      state: "blocked",
      detail:
        "Your raw prompt is passed straight into the backend pipeline. No Senso targeting step is required."
    },
    {
      id: "script",
      title: "Write punchy script",
      category: "LLM",
      endpoint: "/api/generate/script",
      state: "blocked",
      detail:
        "The backend writes the short-form script lines directly from the prompt context."
    },
    {
      id: "music",
      title: "Generate upbeat music",
      category: "Suno via kie.ai",
      endpoint: "/api/generate/music",
      state: "blocked",
      detail:
        "The backend asks kie.ai Suno for upbeat instrumental music."
    },
    {
      id: "visuals",
      title: "Create beat-synced visuals",
      category: "DALL-E 3",
      endpoint: "/api/generate/visuals",
      state: "blocked",
      detail:
        "The backend generates one visual per script line for the reel."
    },
    {
      id: "assemble",
      title: "Assemble vertical reel",
      category: "FFmpeg",
      endpoint: "/api/generate/assemble",
      state: "blocked",
      detail:
        "FFmpeg assembles the final vertical MP4 once assets are ready."
    }
  ];
}
