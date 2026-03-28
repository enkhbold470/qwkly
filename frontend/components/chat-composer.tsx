"use client";

import { FormEvent, useState } from "react";

type ChatComposerProps = {
  disabled?: boolean;
  onSubmit: (topic: string) => void;
};

export function ChatComposer({
  disabled = false,
  onSubmit
}: ChatComposerProps) {
  const [topic, setTopic] = useState("");

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextTopic = topic.trim();

    if (!nextTopic) return;

    onSubmit(nextTopic);
    setTopic("");
  };

  return (
    <div className="composer-shell">
      <form className="composer-form" onSubmit={handleSubmit}>
        <textarea
          className="composer-input"
          disabled={disabled}
          onChange={(event) => setTopic(event.target.value)}
          placeholder='Try "dating app for active people who want real, unfiltered connections"'
          value={topic}
        />

        <div className="composer-actions">
          <button className="primary-button" disabled={disabled} type="submit">
            Run full pipeline
          </button>
        </div>

        <p className="composer-caption">
          The first stage now sends your prompt directly into the backend flow,
          then script, music, visuals, and render continue automatically.
        </p>
      </form>
    </div>
  );
}
