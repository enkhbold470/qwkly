import { ReelForgeRun, ReelForgeStepId } from "@/lib/reelforge-types";
import { StepCard } from "./step-card";

type ApprovalRailProps = {
  busyStep: ReelForgeStepId | null;
  run: ReelForgeRun;
};

export function ApprovalRail({
  busyStep,
  run
}: ApprovalRailProps) {
  return (
    <div className="approval-rail">
      {run.steps.map((step, index) => (
        <StepCard
          key={step.id}
          busy={busyStep === step.id}
          index={index + 1}
          step={step}
        />
      ))}
    </div>
  );
}
