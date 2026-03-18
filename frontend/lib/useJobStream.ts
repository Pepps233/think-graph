"use client";

import { useEffect, useState } from "react";

export type JobStatus = "queued" | "processing" | "completed" | "failed";

export interface JobState {
  id: string;
  paper_id: string;
  status: JobStatus;
  current_step: string;
  progress: number;
  error_message: string | null;
}

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export function useJobStream(jobId: string | null) {
  const [job, setJob] = useState<JobState | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const es = new EventSource(`${BACKEND_URL}/jobs/${jobId}/stream`);

    es.onmessage = (event) => {
      try {
        const data: JobState = JSON.parse(event.data);
        setJob(data);
        if (data.status === "completed" || data.status === "failed") {
          es.close();
        }
      } catch {
        setError("Malformed response from server");
        es.close();
      }
    };

    es.onerror = () => {
      setError("Connection to job stream lost");
      es.close();
    };

    return () => es.close();
  }, [jobId]);

  return { job, error };
}
