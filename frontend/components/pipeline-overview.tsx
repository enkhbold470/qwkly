type PipelineOverviewProps = {
  completedCount: number;
  totalCount: number;
  topic?: string;
};

export function PipelineOverview({
  completedCount,
  totalCount,
  topic
}: PipelineOverviewProps) {
  return (
    <aside className="overview-card">
      <div className="overview-pill">
        <span className="badge complete">Live pipeline</span>
        <span>Prompt in, reel out</span>
      </div>

      <h3>Run overview</h3>
      <p>
        All progress lives inline with the conversation so the user can follow
        one continuous flow instead of switching between separate panes.
      </p>

      <div className="overview-stats">
        <div className="overview-stat">
          <span className="step-label">Current topic</span>
          <span className="overview-value">{topic ?? "Waiting"}</span>
        </div>
        <div className="overview-stat">
          <span className="step-label">Progress</span>
          <span className="overview-value">
            {completedCount}/{totalCount}
          </span>
        </div>
      </div>
    </aside>
  );
}
