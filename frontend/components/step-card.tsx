import clsx from "clsx";
import { ReelForgeStep } from "@/lib/reelforge-types";
import { LoadingBox } from "./loading-box";

type StepCardProps = {
  busy: boolean;
  index: number;
  step: ReelForgeStep;
};

function StringList({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;

  return (
    <section className="research-section">
      <h4>{title}</h4>
      <ul className="research-list">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

export function StepCard({ busy, index, step }: StepCardProps) {
  const badgeLabel = {
    blocked: "Waiting",
    loading: "Running",
    complete: "Done",
    error: "Needs attention"
  }[step.state];

  return (
    <article className="step-card">
      <div className="step-header">
        <div className="step-title-wrap">
          <span className="step-index">{index}</span>
          <span className="step-label">{step.category}</span>
          <h3 className="step-title">{step.title}</h3>
        </div>

        <span className={clsx("badge", step.state)}>{badgeLabel}</span>
      </div>

      <p className="step-detail">{step.detail}</p>

      {busy || step.state === "loading" ? (
        <LoadingBox label="Backend pipeline is working on this stage..." />
      ) : null}

      {step.context ? (
        <section className="research-section">
          <h4>Context</h4>
          <p>{step.context}</p>
        </section>
      ) : null}

      <StringList title="Script lines" items={step.lines ?? []} />
      <StringList title="Generated visuals" items={step.paths ?? []} />

      {typeof step.count === "number" ? (
        <section className="research-section">
          <h4>Visual count</h4>
          <p>{step.count}</p>
        </section>
      ) : null}

      {step.audioUrl ? (
        <section className="research-section">
          <h4>Music URL</h4>
          <p className="mono-wrap">{step.audioUrl}</p>
        </section>
      ) : null}

      {step.videoUrl ? (
        <section className="research-section">
          <h4>Video output</h4>
          <p className="mono-wrap">{step.videoUrl}</p>
          {step.filename ? <p className="mono-wrap">{step.filename}</p> : null}
        </section>
      ) : null}

      <div className="step-footer">
        <code>{step.endpoint}</code>
      </div>
    </article>
  );
}
