import { render, screen, act } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { JobProgress } from "@/components/JobProgress";
import type { JobState } from "@/lib/useJobStream";

// ---------------------------------------------------------------------------
// Mock useJobStream
// ---------------------------------------------------------------------------

const mockUseJobStream = vi.fn();

vi.mock("@/lib/useJobStream", () => ({
  useJobStream: (jobId: string) => mockUseJobStream(jobId),
}));

function setup(job: Partial<JobState> | null, error: string | null = null) {
  mockUseJobStream.mockReturnValue({ job, error });
}

const STEP_LABELS = [
  "Downloading PDF",
  "Parsing sections",
  "Extracting structure",
  "Extracting entities",
  "Extracting relationships",
  "Extracting reasoning flow",
  "Done",
];

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("JobProgress", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUseJobStream.mockReturnValue({ job: null, error: null });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders all 7 step labels", () => {
    setup({ id: "j", paper_id: "p", status: "processing", current_step: "Downloading PDF", progress: 0, error_message: null });
    render(<JobProgress jobId="j" onComplete={vi.fn()} />);

    for (const label of STEP_LABELS) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it("shows progress percentage while processing", () => {
    setup({ id: "j", paper_id: "p", status: "processing", current_step: "Downloading PDF", progress: 0, error_message: null });
    render(<JobProgress jobId="j" onComplete={vi.fn()} />);
    expect(screen.getByText("0%")).toBeInTheDocument();
  });

  it("shows 'Complete' text when status is completed", () => {
    setup({ id: "j", paper_id: "p", status: "completed", current_step: "Done", progress: 100, error_message: null });
    render(<JobProgress jobId="j" onComplete={vi.fn()} />);
    expect(screen.getByText("Complete")).toBeInTheDocument();
  });

  it("shows 'Failed' text when status is failed", () => {
    setup({ id: "j", paper_id: "p", status: "failed", current_step: "Failed", progress: 0, error_message: "error" });
    render(<JobProgress jobId="j" onComplete={vi.fn()} />);
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });

  it("shows 'Failed' text when error is set from hook", () => {
    setup(null, "Connection to job stream lost");
    render(<JobProgress jobId="j" onComplete={vi.fn()} />);
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });

  it("calls onComplete with paper_id after 600ms when completed", () => {
    const onComplete = vi.fn();
    setup({ id: "j", paper_id: "paper-xyz", status: "completed", current_step: "Done", progress: 100, error_message: null });
    render(<JobProgress jobId="j" onComplete={onComplete} />);

    expect(onComplete).not.toHaveBeenCalled();
    act(() => { vi.advanceTimersByTime(600); });
    expect(onComplete).toHaveBeenCalledWith("paper-xyz");
  });

  it("calls onComplete exactly once even if re-rendered with completed status", () => {
    const onComplete = vi.fn();
    setup({ id: "j", paper_id: "paper-xyz", status: "completed", current_step: "Done", progress: 100, error_message: null });
    const { rerender } = render(<JobProgress jobId="j" onComplete={onComplete} />);

    act(() => { vi.advanceTimersByTime(600); });
    expect(onComplete).toHaveBeenCalledTimes(1);

    // Re-render — should not call again
    rerender(<JobProgress jobId="j" onComplete={onComplete} />);
    act(() => { vi.advanceTimersByTime(600); });
    expect(onComplete).toHaveBeenCalledTimes(1);
  });

  it("shows error_message from job in error panel", () => {
    const errorMsg = "AI extraction failed due to timeout";
    setup({ id: "j", paper_id: "p", status: "failed", current_step: "Failed", progress: 0, error_message: errorMsg });
    render(<JobProgress jobId="j" onComplete={vi.fn()} />);
    expect(screen.getByText(errorMsg)).toBeInTheDocument();
  });

  it("shows error from hook in error panel", () => {
    const errorMsg = "Connection to job stream lost";
    setup(null, errorMsg);
    render(<JobProgress jobId="j" onComplete={vi.fn()} />);
    expect(screen.getByText(errorMsg)).toBeInTheDocument();
  });

  it("progress bar width matches progress percentage", () => {
    setup({ id: "j", paper_id: "p", status: "processing", current_step: "Extracting entities", progress: 50, error_message: null });
    const { container } = render(<JobProgress jobId="j" onComplete={vi.fn()} />);

    // Find the progress fill element by its inline width style
    const fills = container.querySelectorAll('[style*="width: 50%"], [style*="width:50%"]');
    expect(fills.length).toBeGreaterThan(0);
  });
});
