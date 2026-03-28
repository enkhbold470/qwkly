export type ReelForgeStepId =
  | "research"
  | "script"
  | "music"
  | "visuals"
  | "assemble";

export type ReelForgeStepState =
  | "blocked"
  | "loading"
  | "complete"
  | "error";

export type ReelForgeStep = {
  id: ReelForgeStepId;
  title: string;
  category: string;
  endpoint: string;
  state: ReelForgeStepState;
  detail: string;
  context?: string | null;
  lines?: string[] | null;
  audioUrl?: string | null;
  paths?: string[] | null;
  count?: number | null;
  videoUrl?: string | null;
  filename?: string | null;
};

export type ReelForgeRun = {
  id: string;
  topic: string;
  createdAt: string;
  steps: ReelForgeStep[];
};

export type ReelForgeMessage = {
  id: string;
  role: "user" | "assistant";
  title: string;
  content: string;
};

export type ResearchSsePayload = {
  status: "started" | "done";
  topic?: string;
  context?: string;
};

export type ScriptSsePayload = {
  status: "started" | "done";
  lines?: string[];
};

export type MusicSsePayload = {
  status: "started" | "done";
  audio_url?: string;
};

export type VisualsSsePayload = {
  status: "started" | "done";
  count?: number;
  paths?: string[];
};

export type RenderSsePayload = {
  status: "started";
};

export type DoneSsePayload = {
  video_url: string;
  filename: string;
};

export type ErrorSsePayload = {
  message: string;
};
