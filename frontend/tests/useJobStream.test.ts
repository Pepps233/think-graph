import { renderHook, act } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useJobStream, JobState } from "@/lib/useJobStream";
import { EventSourceMock } from "./setup";

const PROCESSING_JOB: JobState = {
  id: "job-1",
  paper_id: "paper-1",
  status: "processing",
  current_step: "Extracting entities",
  progress: 50,
  error_message: null,
};

const COMPLETED_JOB: JobState = {
  ...PROCESSING_JOB,
  status: "completed",
  progress: 100,
  current_step: "Done",
};

const FAILED_JOB: JobState = {
  ...PROCESSING_JOB,
  status: "failed",
  progress: 0,
  current_step: "Failed",
  error_message: "Something went wrong",
};

function getLatestInstance(): EventSourceMock {
  const instance = EventSourceMock.latestInstance;
  if (!instance) throw new Error("No EventSource instance created");
  return instance;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("useJobStream", () => {
  it("does not create EventSource when jobId is null", () => {
    renderHook(() => useJobStream(null));
    expect(EventSourceMock.latestInstance).toBeNull();
  });

  it("returns null job and null error when jobId is null", () => {
    const { result } = renderHook(() => useJobStream(null));
    expect(result.current.job).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("creates EventSource with correct URL when jobId is provided", () => {
    renderHook(() => useJobStream("job-123"));
    const es = getLatestInstance();
    expect(es.url).toContain("/jobs/job-123/stream");
  });

  it("updates job state on valid message", () => {
    const { result } = renderHook(() => useJobStream("job-1"));
    const es = getLatestInstance();

    act(() => {
      es.simulateMessage(PROCESSING_JOB);
    });

    expect(result.current.job).toEqual(PROCESSING_JOB);
    expect(result.current.error).toBeNull();
  });

  it("closes EventSource when status is completed", () => {
    renderHook(() => useJobStream("job-1"));
    const es = getLatestInstance();

    act(() => {
      es.simulateMessage(COMPLETED_JOB);
    });

    expect(es.close).toHaveBeenCalledOnce();
  });

  it("closes EventSource when status is failed", () => {
    renderHook(() => useJobStream("job-1"));
    const es = getLatestInstance();

    act(() => {
      es.simulateMessage(FAILED_JOB);
    });

    expect(es.close).toHaveBeenCalledOnce();
  });

  it("does not close EventSource when status is processing", () => {
    renderHook(() => useJobStream("job-1"));
    const es = getLatestInstance();

    act(() => {
      es.simulateMessage(PROCESSING_JOB);
    });

    expect(es.close).not.toHaveBeenCalled();
  });

  it("sets error and closes on malformed JSON", () => {
    const { result } = renderHook(() => useJobStream("job-1"));
    const es = getLatestInstance();

    act(() => {
      // Directly call onmessage with bad JSON
      es.onmessage?.({ data: "not-json{{" } as MessageEvent);
    });

    expect(result.current.error).toBe("Malformed response from server");
    expect(es.close).toHaveBeenCalledOnce();
  });

  it("sets error and closes on onerror", () => {
    const { result } = renderHook(() => useJobStream("job-1"));
    const es = getLatestInstance();

    act(() => {
      es.simulateError();
    });

    expect(result.current.error).toBe("Connection to job stream lost");
    expect(es.close).toHaveBeenCalledOnce();
  });

  it("closes EventSource on unmount", () => {
    const { unmount } = renderHook(() => useJobStream("job-1"));
    const es = getLatestInstance();

    unmount();

    expect(es.close).toHaveBeenCalled();
  });

  it("opens EventSource when jobId changes from null to a value", () => {
    const { rerender } = renderHook(({ jobId }: { jobId: string | null }) => useJobStream(jobId), {
      initialProps: { jobId: null as string | null },
    });

    expect(EventSourceMock.latestInstance).toBeNull();

    rerender({ jobId: "job-1" });

    expect(EventSourceMock.latestInstance).not.toBeNull();
  });

  it("opens new EventSource when jobId changes to a new value", () => {
    const { rerender } = renderHook(({ jobId }: { jobId: string | null }) => useJobStream(jobId), {
      initialProps: { jobId: "job-1" as string | null },
    });

    const first = getLatestInstance();

    rerender({ jobId: "job-2" });

    const second = EventSourceMock.latestInstance;
    expect(second).not.toBe(first);
    expect(second?.url).toContain("job-2");
  });

  it("closes old EventSource when jobId changes", () => {
    const { rerender } = renderHook(({ jobId }: { jobId: string | null }) => useJobStream(jobId), {
      initialProps: { jobId: "job-1" as string | null },
    });

    const first = getLatestInstance();

    rerender({ jobId: "job-2" });

    expect(first.close).toHaveBeenCalled();
  });
});
