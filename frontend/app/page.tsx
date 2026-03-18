"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { JobProgress } from "@/components/JobProgress";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type InputMode = "url" | "pdf";
type PageState = "idle" | "loading" | "processing";

export default function Home() {
  const router = useRouter();
  const [mode, setMode] = useState<InputMode>("url");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [pageState, setPageState] = useState<PageState>("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async () => {
    setError(null);
    setPageState("loading");

    try {
      let data: { job_id: string; paper_id: string };

      if (mode === "url") {
        if (!url.trim()) {
          setError("Please enter an arXiv URL");
          setPageState("idle");
          return;
        }
        const res = await fetch(`${BACKEND_URL}/papers/ingest/url`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ arxiv_url: url.trim() }),
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail ?? "Failed to start ingestion");
        }
        data = await res.json();
      } else {
        if (!file) {
          setError("Please select a PDF file");
          setPageState("idle");
          return;
        }
        const form = new FormData();
        form.append("file", file);
        const res = await fetch(`${BACKEND_URL}/papers/ingest/pdf`, {
          method: "POST",
          body: form,
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail ?? "Failed to start ingestion");
        }
        data = await res.json();
      }

      setJobId(data.job_id);
      setPageState("processing");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setPageState("idle");
    }
  };

  const handleComplete = useCallback(
    (paperId: string) => {
      router.push(`/graph/${paperId}`);
    },
    [router]
  );

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "var(--background)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px 24px",
        fontFamily: "var(--font-body), sans-serif",
      }}
    >
      {/* Logo */}
      <div
        style={{
          marginBottom: 56,
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}
      >
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: 6,
            background: "var(--accent)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <circle cx="7" cy="3" r="1.5" fill="white" />
            <circle cx="2.5" cy="10" r="1.5" fill="white" />
            <circle cx="11.5" cy="10" r="1.5" fill="white" />
            <line x1="7" y1="3" x2="2.5" y2="10" stroke="white" strokeWidth="1" strokeOpacity="0.6" />
            <line x1="7" y1="3" x2="11.5" y2="10" stroke="white" strokeWidth="1" strokeOpacity="0.6" />
            <line x1="2.5" y1="10" x2="11.5" y2="10" stroke="white" strokeWidth="1" strokeOpacity="0.6" />
          </svg>
        </div>
        <span
          style={{
            fontSize: 16,
            fontWeight: 600,
            color: "var(--foreground)",
            letterSpacing: "-0.02em",
          }}
        >
          ThinkGraph
        </span>
      </div>

      {pageState === "processing" && jobId ? (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 20,
            width: "100%",
          }}
        >
          <div style={{ textAlign: "center", marginBottom: 8 }}>
            <h2
              style={{
                fontSize: 20,
                fontWeight: 600,
                color: "var(--foreground)",
                letterSpacing: "-0.03em",
                marginBottom: 6,
              }}
            >
              Analyzing your paper
            </h2>
            <p
              style={{
                fontSize: 13,
                color: "var(--muted-foreground)",
                fontFamily: "var(--font-mono), monospace",
                maxWidth: 400,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {mode === "url" ? url : file?.name}
            </p>
          </div>
          <JobProgress jobId={jobId} onComplete={handleComplete} />
        </div>
      ) : (
        <div
          style={{
            width: "100%",
            maxWidth: 480,
            display: "flex",
            flexDirection: "column",
          }}
        >
          {/* Heading */}
          <div style={{ marginBottom: 40, textAlign: "center" }}>
            <h1
              style={{
                fontSize: 32,
                fontWeight: 600,
                color: "var(--foreground)",
                letterSpacing: "-0.04em",
                lineHeight: 1.15,
                marginBottom: 12,
              }}
            >
              Turn any paper into
              <br />a knowledge graph
            </h1>
            <p
              style={{
                fontSize: 14,
                color: "var(--muted-foreground)",
                lineHeight: 1.7,
              }}
            >
              Paste an arXiv link or upload a PDF. ThinkGraph extracts concepts,
              methods, and relationships into an interactive graph.
            </p>
          </div>

          {/* Mode toggle */}
          <div
            style={{
              display: "flex",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: 3,
              marginBottom: 16,
            }}
          >
            {(["url", "pdf"] as InputMode[]).map((m) => (
              <button
                key={m}
                onClick={() => { setMode(m); setError(null); }}
                style={{
                  flex: 1,
                  padding: "7px 0",
                  borderRadius: 6,
                  border: "none",
                  cursor: "pointer",
                  fontSize: 13,
                  fontWeight: 500,
                  fontFamily: "var(--font-body), sans-serif",
                  transition: "all 0.15s ease",
                  background: mode === m ? "var(--surface-raised)" : "transparent",
                  color: mode === m ? "var(--foreground)" : "var(--muted-foreground)",
                  boxShadow: mode === m ? "0 0 0 1px var(--border)" : "none",
                }}
              >
                {m === "url" ? "arXiv URL" : "Upload PDF"}
              </button>
            ))}
          </div>

          {/* Input */}
          <div style={{ marginBottom: 12 }}>
            {mode === "url" ? (
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
                placeholder="https://arxiv.org/abs/2301.00001"
                style={{
                  width: "100%",
                  padding: "11px 14px",
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  color: "var(--foreground)",
                  fontSize: 14,
                  fontFamily: "var(--font-mono), monospace",
                  outline: "none",
                  transition: "border-color 0.15s ease",
                }}
                onFocus={(e) => (e.currentTarget.style.borderColor = "var(--accent)")}
                onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
              />
            ) : (
              <div
                onClick={() => fileInputRef.current?.click()}
                style={{
                  width: "100%",
                  padding: "28px 14px",
                  background: "var(--surface)",
                  border: `1px dashed ${file ? "var(--accent)" : "var(--border)"}`,
                  borderRadius: 8,
                  cursor: "pointer",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 8,
                  transition: "border-color 0.15s ease",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--accent)")}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = file ? "var(--accent)" : "var(--border)")}
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M10 2v10M10 2L7 5M10 2l3 3" stroke={file ? "var(--accent)" : "var(--muted-foreground)"} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M3 14v2a1 1 0 001 1h12a1 1 0 001-1v-2" stroke={file ? "var(--accent)" : "var(--muted-foreground)"} strokeWidth="1.5" strokeLinecap="round" />
                </svg>
                <span style={{ fontSize: 13, color: file ? "var(--foreground)" : "var(--muted-foreground)", fontFamily: "var(--font-mono), monospace" }}>
                  {file ? file.name : "Click to select PDF"}
                </span>
                {!file && (
                  <span style={{ fontSize: 11, color: "var(--muted)", fontFamily: "var(--font-mono), monospace" }}>
                    .pdf up to 50MB
                  </span>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,application/pdf"
                  style={{ display: "none" }}
                  onChange={(e) => { const f = e.target.files?.[0]; if (f) setFile(f); }}
                />
              </div>
            )}
          </div>

          {/* Error */}
          {error && (
            <div
              style={{
                marginBottom: 12,
                padding: "9px 12px",
                background: "var(--error-dim)",
                border: "1px solid rgba(239,68,68,0.2)",
                borderRadius: 7,
                fontSize: 13,
                color: "var(--error)",
                fontFamily: "var(--font-mono), monospace",
              }}
            >
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={pageState === "loading"}
            style={{
              width: "100%",
              padding: "11px 0",
              background: pageState === "loading" ? "rgba(99,102,241,0.6)" : "var(--accent)",
              border: "none",
              borderRadius: 8,
              color: "white",
              fontSize: 14,
              fontWeight: 500,
              fontFamily: "var(--font-body), sans-serif",
              cursor: pageState === "loading" ? "not-allowed" : "pointer",
              transition: "opacity 0.15s ease",
              letterSpacing: "-0.01em",
            }}
            onMouseEnter={(e) => { if (pageState !== "loading") e.currentTarget.style.opacity = "0.88"; }}
            onMouseLeave={(e) => { e.currentTarget.style.opacity = "1"; }}
          >
            {pageState === "loading" ? "Starting..." : "Analyze paper"}
          </button>

          <p
            style={{
              marginTop: 20,
              fontSize: 12,
              color: "var(--muted)",
              textAlign: "center",
              fontFamily: "var(--font-mono), monospace",
            }}
          >
            Processing takes 2–5 minutes per paper
          </p>
        </div>
      )}
    </main>
  );
}
