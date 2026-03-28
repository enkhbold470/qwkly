export function LoadingBox({ label }: { label: string }) {
  return (
    <div className="loading-box">
      <div className="loading-dots" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <span>{label}</span>
    </div>
  );
}
