"use client";

import { useMemo, useState } from "react";
import { ApprovalRail } from "@/components/approval-rail";
import { ChatComposer } from "@/components/chat-composer";
import { MessageBubble } from "@/components/message-bubble";
import { PipelineOverview } from "@/components/pipeline-overview";
import { StepCard } from "@/components/step-card";
import { initialSteps } from "@/lib/reelforge-data";
import {
  DoneSsePayload,
  ErrorSsePayload,
  MusicSsePayload,
  ReelForgeMessage,
  ReelForgeRun,
  ReelForgeStep,
  ReelForgeStepId,
  RenderSsePayload,
  ResearchSsePayload,
  ScriptSsePayload,
  VisualsSsePayload
} from "@/lib/reelforge-types";

type ParsedSseEvent = {
  event: string;
  data: unknown;
};

const decoder = new TextDecoder();

const createAssistantIntro = (topic: string): ReelForgeMessage => ({
  id: crypto.randomUUID(),
  role: "assistant",
  title: "Pipeline started",
  content: `I’m sending "${topic}" directly into the backend pipeline now. qwkly will stream each stage as script, music, visuals, and rendering complete.`
});

function makeRun(topic: string): ReelForgeRun {
  return {
    id: crypto.randomUUID(),
    topic,
    createdAt: new Date().toISOString(),
    steps: initialSteps()
  };
}

function parseSseChunk(chunk: string): ParsedSseEvent[] {
  const blocks = chunk.split("\n\n").filter(Boolean);
  const events: ParsedSseEvent[] = [];

  for (const block of blocks) {
    const lines = block.split("\n");
    let event = "message";
    const dataLines: string[] = [];

    for (const line of lines) {
      if (line.startsWith("event:")) {
        event = line.slice("event:".length).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice("data:".length).trim());
      }
    }

    if (!dataLines.length) continue;

    try {
      events.push({
        event,
        data: JSON.parse(dataLines.join("\n"))
      });
    } catch {
      // Ignore malformed event payloads.
    }
  }

  return events;
}

export default function Home() {
  const [messages, setMessages] = useState<ReelForgeMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      title: "qwkly",
      content:
        "Drop in a prompt and qwkly will pass it straight into the backend flow. The stage cards will update live as the reel is produced."
    }
  ]);
  const [run, setRun] = useState<ReelForgeRun | null>(null);
  const [busyStep, setBusyStep] = useState<ReelForgeStepId | null>(null);

  const completedCount = useMemo(() => {
    if (!run) return 0;
    return run.steps.filter((step) => step.state === "complete").length;
  }, [run]);

  const activeStep = useMemo(() => {
    if (!run) return null;
    if (busyStep) {
      return run.steps.find((step) => step.id === busyStep) ?? null;
    }
    return (
      run.steps.find((step) => step.state === "loading") ??
      run.steps.find((step) => step.state === "error") ??
      run.steps[run.steps.length - 1] ??
      null
    );
  }, [busyStep, run]);

  const updateStep = (stepId: ReelForgeStepId, patch: Partial<ReelForgeStep>) => {
    setRun((current) => {
      if (!current) return current;

      return {
        ...current,
        steps: current.steps.map((step) =>
          step.id === stepId
            ? {
                ...step,
                ...patch
              }
            : step
        )
      };
    });
  };

  const pushAssistantMessage = (title: string, content: string) => {
    setMessages((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        role: "assistant",
        title,
        content
      }
    ]);
  };

  const markEarlierStepsComplete = (stepId: ReelForgeStepId) => {
    setRun((current) => {
      if (!current) return current;
      const index = current.steps.findIndex((step) => step.id === stepId);
      if (index <= 0) return current;

      return {
        ...current,
        steps: current.steps.map((step, currentIndex) => {
          if (currentIndex < index && step.state === "loading") {
            return { ...step, state: "complete" as const };
          }
          return step;
        })
      };
    });
  };

  const handleResearchEvent = (payload: ResearchSsePayload) => {
    if (payload.status === "started") {
      setBusyStep("research");
      updateStep("research", {
        state: "loading",
        detail: "Prompt accepted. The backend is preparing source context for the reel.",
        context: payload.topic ?? null
      });
      return;
    }

    updateStep("research", {
      state: "complete",
      detail: "The backend returned context and moved on to script generation.",
      context: payload.context ?? null
    });
    setBusyStep("script");
    updateStep("script", {
      state: "loading",
      detail: "Writing punchy short-form script lines from the prompt and research context."
    });
    pushAssistantMessage("Research done", "Context is ready and the script stage is now running.");
  };

  const handleScriptEvent = (payload: ScriptSsePayload) => {
    if (payload.status === "started") {
      setBusyStep("script");
      updateStep("script", {
        state: "loading",
        detail: "Writing punchy short-form script lines from the prompt and research context."
      });
      return;
    }

    updateStep("script", {
      state: "complete",
      detail: "Script lines are ready and have been handed off to music generation.",
      lines: payload.lines ?? []
    });
    setBusyStep("music");
    updateStep("music", {
      state: "loading",
      detail: "Waiting for upbeat instrumental music from the backend."
    });
    pushAssistantMessage(
      "Script done",
      `The backend produced ${payload.lines?.length ?? 0} script lines.`
    );
  };

  const handleMusicEvent = (payload: MusicSsePayload) => {
    if (payload.status === "started") {
      setBusyStep("music");
      updateStep("music", {
        state: "loading",
        detail: "Waiting for upbeat instrumental music from the backend."
      });
      return;
    }

    updateStep("music", {
      state: "complete",
      detail: "Music is ready and the backend has moved on to visual generation.",
      audioUrl: payload.audio_url ?? null
    });
    setBusyStep("visuals");
    updateStep("visuals", {
      state: "loading",
      detail: "Generating one visual per script line."
    });
    pushAssistantMessage("Music done", "Audio is ready and visuals are now being generated.");
  };

  const handleVisualsEvent = (payload: VisualsSsePayload) => {
    if (payload.status === "started") {
      setBusyStep("visuals");
      updateStep("visuals", {
        state: "loading",
        detail: `Generating visuals for ${payload.count ?? 0} script lines.`,
        count: payload.count ?? null
      });
      return;
    }

    updateStep("visuals", {
      state: "complete",
      detail: "Visual assets are ready and rendering has started.",
      paths: payload.paths ?? []
    });
    setBusyStep("assemble");
    updateStep("assemble", {
      state: "loading",
      detail: "FFmpeg is assembling the final vertical MP4."
    });
    pushAssistantMessage(
      "Visuals done",
      `Generated ${payload.paths?.length ?? 0} visuals and moved into render.`
    );
  };

  const handleRenderEvent = (_payload: RenderSsePayload) => {
    setBusyStep("assemble");
    markEarlierStepsComplete("assemble");
    updateStep("assemble", {
      state: "loading",
      detail: "FFmpeg is assembling the final vertical MP4."
    });
  };

  const handleDoneEvent = (payload: DoneSsePayload) => {
    setBusyStep(null);
    updateStep("assemble", {
      state: "complete",
      detail: "The reel is ready.",
      videoUrl: payload.video_url,
      filename: payload.filename
    });
    pushAssistantMessage("Video ready", `Finished reel: ${payload.filename}`);
  };

  const handleErrorEvent = (payload: ErrorSsePayload) => {
    if (busyStep) {
      updateStep(busyStep, {
        state: "error",
        detail: payload.message
      });
    }
    setBusyStep(null);
    pushAssistantMessage("Pipeline error", payload.message);
  };

  const executePipeline = async (topic: string) => {
    setBusyStep("research");
    updateStep("research", {
      state: "loading",
      detail: "Sending your raw prompt directly into the backend."
    });

    try {
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ topic })
      });

      if (!response.ok || !response.body) {
        const text = await response.text();
        throw new Error(text || "qwkly could not start the backend pipeline.");
      }

      const reader = response.body.getReader();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const completeBlocks = buffer.split("\n\n");
        buffer = completeBlocks.pop() ?? "";

        for (const eventText of completeBlocks) {
          for (const parsed of parseSseChunk(`${eventText}\n\n`)) {
            switch (parsed.event) {
              case "research":
                handleResearchEvent(parsed.data as ResearchSsePayload);
                break;
              case "script":
                handleScriptEvent(parsed.data as ScriptSsePayload);
                break;
              case "music":
                handleMusicEvent(parsed.data as MusicSsePayload);
                break;
              case "visuals":
                handleVisualsEvent(parsed.data as VisualsSsePayload);
                break;
              case "render":
                handleRenderEvent(parsed.data as RenderSsePayload);
                break;
              case "done":
                handleDoneEvent(parsed.data as DoneSsePayload);
                break;
              case "error":
                handleErrorEvent(parsed.data as ErrorSsePayload);
                break;
              default:
                break;
            }
          }
        }
      }
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unexpected pipeline error";
      handleErrorEvent({ message });
    }
  };

  const handleSubmitTopic = (topic: string) => {
    const nextRun = makeRun(topic);
    setRun(nextRun);
    setMessages((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        role: "user",
        title: "Prompt submitted",
        content: topic
      },
      createAssistantIntro(topic)
    ]);

    void executePipeline(topic);
  };

  const handleReset = () => {
    setRun(null);
    setBusyStep(null);
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        title: "qwkly",
        content:
          "Drop in a prompt and qwkly will pass it straight into the backend flow. The stage cards will update live as the reel is produced."
      }
    ]);
  };

  return (
    <main className="app-shell single-flow-shell">
      <section className="hero-panel single-flow-hero">
        <div className="hero-copy">
          <span className="eyebrow">Prompt-first pipeline</span>
          <h1>qwkly</h1>
          <p>
            One prompt, one scroll. The conversation, the active task, and the
            pipeline timeline all live in the same place.
          </p>
        </div>

        <PipelineOverview
          completedCount={completedCount}
          totalCount={initialSteps().length}
          topic={run?.topic}
        />
      </section>

      <section className="single-flow-thread">
        <div className="thread-panel">
          <div className="thread-header">
            <div>
              <p className="panel-kicker">Conversation</p>
              <h2>qwkly chat</h2>
            </div>

            <button className="ghost-button" onClick={handleReset} type="button">
              Reset run
            </button>
          </div>

          <div className="message-list inline-message-list">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </div>

          {run ? (
            <section className="workspace-card">
              <div className="workspace-header">
                <div>
                  <p className="panel-kicker">Active task</p>
                  <h2>Pipeline workspace</h2>
                </div>
                {busyStep ? (
                  <span className="workspace-status">
                    Running {activeStep?.title.toLowerCase() ?? "pipeline"}
                  </span>
                ) : (
                  <span className="workspace-status complete-status">
                    Pipeline finished
                  </span>
                )}
              </div>

              {activeStep ? (
                <div className="spotlight-card">
                  <StepCard
                    active
                    busy={Boolean(busyStep)}
                    index={run.steps.findIndex((step) => step.id === activeStep.id) + 1}
                    step={activeStep}
                  />
                </div>
              ) : null}

              <div className="timeline-section">
                <div className="timeline-header">
                  <p className="panel-kicker">All stages</p>
                  <h3>Timeline</h3>
                </div>
                <ApprovalRail busyStep={busyStep} run={run} />
              </div>
            </section>
          ) : (
            <div className="empty-state inline-empty-state">
              <p>Submit a prompt to start the backend pipeline in this same thread.</p>
            </div>
          )}

          <div className="composer-dock">
            <ChatComposer
              disabled={Boolean(run && busyStep)}
              onSubmit={handleSubmitTopic}
            />
          </div>
        </div>
      </section>
    </main>
  );
}
