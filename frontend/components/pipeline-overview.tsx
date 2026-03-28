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
        <span className="badge complete">Human-in-the-loop</span>
        <span>Cursor-style approvals</span>
      </div>

      <h3>Control panel</h3>
      <p>
        Step cards unlock one by one. Each stage gets a pretty loading box and a
        clear backend handoff note.
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
