"use client";

import { useEffect, useRef } from "react";
import { useJobStream, JobState } from "@/lib/useJobStream";

const STEPS: { label: string; threshold: number }[] = [
  { label: "Downloading PDF", threshold: 5 },
  { label: "Parsing sections", threshold: 20 },
  { label: "Extracting structure", threshold: 35 },
  { label: "Extracting entities", threshold: 50 },
  { label: "Extracting relationships", threshold: 70 },
  { label: "Extracting reasoning flow", threshold: 85 },
  { label: "Done", threshold: 100 },
];

interface JobProgressProps {
  jobId: string;
  onComplete: (paperId: string) => void;
}

export function JobProgress({ jobId, onComplete }: JobProgressProps) {
  const { job, error } = useJobStream(jobId);
  const completedRef = useRef(false);

  useEffect(() => {
    if (job?.status === "completed" && !completedRef.current) {
      completedRef.current = true;
      setTimeout(() => onComplete(job.paper_id), 600);
    }
  }, [job, onComplete]);

  const progress = job?.progress ?? 0;
  const isFailed = job?.status === "failed" || !!error;
  const isComplete = job?.status === "completed";
  const currentStep = error
    ? "Connection lost"
    : job?.current_step ?? "Connecting...";

  return (
    <div
      style={{
        width: "100%",
        maxWidth: 480,
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 12,
        padding: "28px 32px",
        fontFamily: "var(--font-body), sans-serif",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 20,
        }}
      >
        <span
          style={{
            fontSize: 13,
            fontWeight: 500,
            color: "var(--muted-foreground)",
            fontFamily: "var(--font-mono), monospace",
            letterSpacing: "0.04em",
            textTransform: "uppercase",
          }}
        >
          Processing
        </span>
        <span
          style={{
            fontSize: 13,
            fontWeight: 500,
            color: isFailed
              ? "var(--error)"
              : isComplete
              ? "var(--success)"
              : "var(--accent)",
            fontFamily: "var(--font-mono), monospace",
          }}
        >
          {isFailed ? "Failed" : isComplete ? "Complete" : `${progress}%`}
        </span>
      </div>

      {/* Progress track */}
      <div
        style={{
          height: 2,
          background: "var(--border)",
          borderRadius: 2,
          overflow: "hidden",
          marginBottom: 28,
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${progress}%`,
            background: isFailed
              ? "var(--error)"
              : isComplete
              ? "var(--success)"
              : "var(--accent)",
            borderRadius: 2,
            transition: "width 0.5s ease, background 0.3s ease",
          }}
        />
      </div>

      {/* Steps */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {STEPS.map((step, i) => {
          const isDone = progress >= step.threshold && !isFailed;
          const isActive =
            !isFailed &&
            !isComplete &&
            progress >= (STEPS[i - 1]?.threshold ?? 0) &&
            progress < step.threshold;
          const isPending = !isDone && !isActive;

          return (
            <div
              key={step.label}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                opacity: isPending ? 0.3 : 1,
                transition: "opacity 0.3s ease",
              }}
            >
              {/* Indicator */}
              <div
                style={{
                  width: 16,
                  height: 16,
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  background: isDone
                    ? "var(--success-dim)"
                    : isActive
                    ? "var(--accent-dim)"
                    : "transparent",
                  border: `1px solid ${
                    isDone
                      ? "var(--success)"
                      : isActive
                      ? "var(--accent)"
                      : "var(--border)"
                  }`,
                  transition: "all 0.3s ease",
                }}
              >
                {isDone ? (
                  <svg width="8" height="8" viewBox="0 0 8 8" fill="none">
                    <path
                      d="M1.5 4L3.5 6L6.5 2"
                      stroke="var(--success)"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                ) : isActive ? (
                  <div
                    style={{
                      width: 5,
                      height: 5,
                      borderRadius: "50%",
                      background: "var(--accent)",
                      animation: "scan 1.6s ease-in-out infinite",
                    }}
                  />
                ) : null}
              </div>

              {/* Label */}
              <span
                style={{
                  fontSize: 13,
                  fontWeight: isActive ? 500 : 400,
                  color: isDone
                    ? "var(--foreground)"
                    : isActive
                    ? "var(--accent-hover)"
                    : "var(--muted-foreground)",
                  fontFamily: "var(--font-mono), monospace",
                  letterSpacing: "0.01em",
                  transition: "color 0.3s ease",
                }}
              >
                {step.label}
              </span>

              {isActive && (
                <span
                  style={{
                    fontSize: 11,
                    color: "var(--muted)",
                    fontFamily: "var(--font-mono), monospace",
                    marginLeft: "auto",
                    animation: "scan 1.6s ease-in-out infinite",
                  }}
                >
                  running
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Error message */}
      {(error || job?.error_message) && (
        <div
          style={{
            marginTop: 20,
            padding: "10px 14px",
            background: "var(--error-dim)",
            border: "1px solid rgba(239,68,68,0.2)",
            borderRadius: 8,
            fontSize: 13,
            color: "var(--error)",
            fontFamily: "var(--font-mono), monospace",
          }}
        >
          {error ?? job?.error_message}
        </div>
      )}
    </div>
  );
}
