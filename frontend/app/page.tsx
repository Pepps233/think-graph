"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { JobProgress } from "@/components/JobProgress";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type InputMode = "url" | "pdf";
type PageState = "idle" | "loading" | "processing";

// ─── Shared sub-components ────────────────────────────────────────────────────

function LogoMark({ size = 28 }: { size?: number }) {
  const r = Math.round(size * 0.21);
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: Math.round(size * 0.21),
        background: "#6366f1",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}
    >
      <svg
        width={Math.round(size * 0.5)}
        height={Math.round(size * 0.5)}
        viewBox="0 0 14 14"
        fill="none"
      >
        <circle cx="7" cy="3" r={r} fill="white" />
        <circle cx="2.5" cy="10" r={r} fill="white" />
        <circle cx="11.5" cy="10" r={r} fill="white" />
        <line x1="7" y1="3" x2="2.5" y2="10" stroke="white" strokeWidth="1" strokeOpacity="0.55" />
        <line x1="7" y1="3" x2="11.5" y2="10" stroke="white" strokeWidth="1" strokeOpacity="0.55" />
        <line x1="2.5" y1="10" x2="11.5" y2="10" stroke="white" strokeWidth="1" strokeOpacity="0.55" />
      </svg>
    </div>
  );
}

function Nav() {
  return (
    <nav
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 50,
        height: 64,
        background: "rgba(255,255,255,0.88)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        borderBottom: "1px solid rgba(0,0,0,0.06)",
        display: "flex",
        alignItems: "center",
        padding: "0 28px",
        fontFamily: "var(--font-body), -apple-system, sans-serif",
      }}
    >
      {/* Brand */}
      <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
        <LogoMark size={28} />
        <span
          style={{
            fontSize: 15,
            fontWeight: 600,
            color: "#0f172a",
            letterSpacing: "-0.03em",
          }}
        >
          ThinkGraph
        </span>
      </div>

      {/* Spacer */}
      <div style={{ flex: 1 }} />

      {/* Nav links */}
      <div className="tg-nav-links" style={{ display: "flex", alignItems: "center", gap: 4 }}>
        <button
          className="tg-nav-btn"
          style={{
            background: "transparent",
            border: "none",
            cursor: "pointer",
            fontSize: 14,
            fontWeight: 400,
            color: "#64748b",
            letterSpacing: "-0.01em",
            padding: "6px 12px",
            borderRadius: 7,
            fontFamily: "inherit",
            transition: "background 0.12s ease, color 0.12s ease",
          }}
        >
          Pricing
        </button>
        <button
          className="tg-nav-btn"
          style={{
            background: "transparent",
            border: "none",
            cursor: "pointer",
            fontSize: 14,
            fontWeight: 400,
            color: "#64748b",
            letterSpacing: "-0.01em",
            padding: "6px 12px",
            borderRadius: 7,
            fontFamily: "inherit",
            transition: "background 0.12s ease, color 0.12s ease",
          }}
        >
          Login
        </button>
      </div>

      <div style={{ width: 12 }} />

      <button
        style={{
          background: "#6366f1",
          border: "none",
          cursor: "pointer",
          fontSize: 13,
          fontWeight: 500,
          color: "#ffffff",
          letterSpacing: "-0.02em",
          padding: "8px 16px",
          borderRadius: 8,
          fontFamily: "inherit",
          transition: "background 0.15s ease",
          boxShadow: "0 1px 2px rgba(99,102,241,0.25)",
        }}
        className="tg-cta-btn"
      >
        Book a Demo
      </button>
    </nav>
  );
}

function ThinkGraphStyles() {
  return (
    <style>{`
      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(18px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      @keyframes pulse-dot {
        0%, 100% { opacity: 0.4; transform: scale(0.85); }
        50%       { opacity: 1;   transform: scale(1); }
      }

      .tg-nav-btn:hover  { background: rgba(0,0,0,0.05) !important; color: #0f172a !important; }
      .tg-cta-btn:hover  { background: #4f52d4 !important; }
      .tg-feature:hover  { border-color: rgba(99,102,241,0.18) !important; box-shadow: 0 4px 24px rgba(99,102,241,0.07) !important; }
      .tg-dropzone:hover { border-color: #6366f1 !important; background: rgba(99,102,241,0.02) !important; }
      .tg-submit:hover   { opacity: 0.88 !important; }
      .tg-mode-btn:hover { color: #0f172a !important; }

      @media (max-width: 768px) {
        .tg-hero-headline { font-size: 38px !important; letter-spacing: -0.04em !important; }
        .tg-hero-sub      { font-size: 16px !important; }
        .tg-features-grid { grid-template-columns: 1fr !important; }
        .tg-input-card    { padding: 28px !important; }
        .tg-nav-links     { display: none !important; }
        .tg-hero-section  { padding-top: 72px !important; padding-bottom: 48px !important; }
      }
      @media (max-width: 480px) {
        .tg-hero-headline { font-size: 30px !important; }
        .tg-hero-sub      { font-size: 15px !important; }
        .tg-page-pad      { padding-left: 16px !important; padding-right: 16px !important; }
      }
    `}</style>
  );
}

// ─── Feature data ─────────────────────────────────────────────────────────────

const FEATURES = [
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="5" r="2" stroke="#6366f1" strokeWidth="1.5" />
        <circle cx="4" cy="15" r="2" stroke="#6366f1" strokeWidth="1.5" />
        <circle cx="16" cy="15" r="2" stroke="#6366f1" strokeWidth="1.5" />
        <line x1="10" y1="7" x2="4.8" y2="13" stroke="#6366f1" strokeWidth="1.5" strokeLinecap="round" />
        <line x1="10" y1="7" x2="15.2" y2="13" stroke="#6366f1" strokeWidth="1.5" strokeLinecap="round" />
        <line x1="6" y1="15" x2="14" y2="15" stroke="#6366f1" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    ),
    title: "Concept Extraction",
    body: "GPT-4o reads every section of your paper and pulls out concepts, methods, datasets, and citations — each tagged with provenance back to the source text.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M3 10h14M10 3v14" stroke="#6366f1" strokeWidth="1.5" strokeLinecap="round" />
        <path d="M5.5 5.5l9 9M14.5 5.5l-9 9" stroke="#6366f1" strokeWidth="1" strokeLinecap="round" strokeOpacity="0.4" />
      </svg>
    ),
    title: "Relationship Mapping",
    body: "Every entity is linked by typed relationships — BUILDS_ON, EVALUATES, CITES, EXTENDS — forming a precise semantic graph of how ideas connect.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <rect x="3" y="3" width="6" height="6" rx="1.5" stroke="#6366f1" strokeWidth="1.5" />
        <rect x="11" y="3" width="6" height="6" rx="1.5" stroke="#6366f1" strokeWidth="1.5" />
        <rect x="3" y="11" width="6" height="6" rx="1.5" stroke="#6366f1" strokeWidth="1.5" />
        <rect x="11" y="11" width="6" height="6" rx="1.5" stroke="#6366f1" strokeWidth="1.5" />
      </svg>
    ),
    title: "Interactive Exploration",
    body: "Pan, zoom, and click any node to open a detail panel with equations rendered in KaTeX, source text, and a list of connected concepts.",
  },
];

// ─── Main page ────────────────────────────────────────────────────────────────

export default function Home() {
  const router = useRouter();
  const [mode, setMode] = useState<InputMode>("url");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [pageState, setPageState] = useState<PageState>("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
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

  const isLoading = pageState === "loading";

  return (
    <>
      <ThinkGraphStyles />

      <div
        style={{
          background: "#ffffff",
          minHeight: "100vh",
          fontFamily: "var(--font-body), -apple-system, sans-serif",
          color: "#0f172a",
          WebkitFontSmoothing: "antialiased",
        }}
      >
        <Nav />

        <div style={{ paddingTop: 64 }}>
          {/* ── Processing state ───────────────────────────────────────────── */}
          {pageState === "processing" && jobId ? (
            <div
              style={{
                minHeight: "calc(100vh - 64px)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                padding: "60px 24px",
                animation: "fadeIn 0.35s ease forwards",
              }}
            >
              <div style={{ textAlign: "center", marginBottom: 40 }}>
                <h2
                  style={{
                    fontSize: 28,
                    fontWeight: 600,
                    color: "#0f172a",
                    letterSpacing: "-0.04em",
                    marginBottom: 10,
                  }}
                >
                  Analyzing your paper
                </h2>
                <p
                  style={{
                    fontSize: 13,
                    color: "#94a3b8",
                    fontFamily: "var(--font-mono), ui-monospace, monospace",
                    maxWidth: 440,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {mode === "url" ? url : file?.name}
                </p>
              </div>

              {/* CSS variable override — re-themes JobProgress to light */}
              <div
                style={
                  {
                    width: "100%",
                    maxWidth: 520,
                    "--surface": "#ffffff",
                    "--surface-raised": "#f8fafc",
                    "--border": "rgba(0,0,0,0.08)",
                    "--border-subtle": "rgba(0,0,0,0.04)",
                    "--foreground": "#0f172a",
                    "--muted-foreground": "#64748b",
                    "--muted": "#94a3b8",
                    "--accent": "#6366f1",
                    "--accent-dim": "rgba(99,102,241,0.08)",
                    "--accent-hover": "#4f52d4",
                    "--success": "#16a34a",
                    "--success-dim": "rgba(22,163,74,0.08)",
                    "--error": "#dc2626",
                    "--error-dim": "rgba(239,68,68,0.06)",
                  } as React.CSSProperties
                }
              >
                <JobProgress jobId={jobId} onComplete={handleComplete} />
              </div>
            </div>
          ) : (
            /* ── Landing page (idle / loading) ──────────────────────────── */
            <>
              {/* Hero */}
              <section
                className="tg-hero-section tg-page-pad"
                style={{
                  maxWidth: 680,
                  margin: "0 auto",
                  paddingTop: 100,
                  paddingBottom: 80,
                  paddingLeft: 24,
                  paddingRight: 24,
                  textAlign: "center",
                  animation: "fadeInUp 0.5s ease forwards",
                }}
              >
                {/* Badge */}
                <div
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 6,
                    background: "rgba(99,102,241,0.07)",
                    border: "1px solid rgba(99,102,241,0.15)",
                    borderRadius: 20,
                    padding: "4px 12px",
                    marginBottom: 28,
                  }}
                >
                  <div
                    style={{
                      width: 5,
                      height: 5,
                      borderRadius: "50%",
                      background: "#6366f1",
                      animation: "pulse-dot 2s ease-in-out infinite",
                    }}
                  />
                  <span
                    style={{
                      fontSize: 12,
                      fontWeight: 500,
                      color: "#6366f1",
                      letterSpacing: "0.01em",
                      fontFamily: "var(--font-mono), ui-monospace, monospace",
                    }}
                  >
                    Powered by GPT-4o
                  </span>
                </div>

                {/* Headline */}
                <h1
                  className="tg-hero-headline"
                  style={{
                    fontSize: 56,
                    fontWeight: 600,
                    color: "#0f172a",
                    letterSpacing: "-0.05em",
                    lineHeight: 1.08,
                    marginBottom: 20,
                  }}
                >
                  Turn any research paper
                  <br />
                  into a knowledge graph
                </h1>

                {/* Subheadline */}
                <p
                  className="tg-hero-sub"
                  style={{
                    fontSize: 18,
                    fontWeight: 400,
                    color: "#64748b",
                    letterSpacing: "-0.01em",
                    lineHeight: 1.65,
                    maxWidth: 520,
                    margin: "0 auto 44px",
                  }}
                >
                  Paste an arXiv link or upload a PDF. ThinkGraph extracts
                  concepts, methods, and relationships into an interactive,
                  explorable graph.
                </p>

                {/* Input card */}
                <div
                  className="tg-input-card"
                  style={{
                    background: "#ffffff",
                    border: "1px solid rgba(0,0,0,0.07)",
                    borderRadius: 16,
                    padding: 36,
                    boxShadow:
                      "0 2px 16px rgba(0,0,0,0.05), 0 0 0 1px rgba(0,0,0,0.04)",
                    textAlign: "left",
                    maxWidth: 520,
                    margin: "0 auto",
                  }}
                >
                  {/* Mode toggle */}
                  <div
                    style={{
                      display: "flex",
                      background: "#f1f5f9",
                      borderRadius: 10,
                      padding: 3,
                      marginBottom: 20,
                    }}
                  >
                    {(["url", "pdf"] as InputMode[]).map((m) => (
                      <button
                        key={m}
                        className="tg-mode-btn"
                        onClick={() => {
                          setMode(m);
                          setError(null);
                        }}
                        style={{
                          flex: 1,
                          padding: "8px 0",
                          borderRadius: 8,
                          border: "none",
                          cursor: "pointer",
                          fontSize: 13,
                          fontWeight: mode === m ? 500 : 400,
                          fontFamily: "inherit",
                          color: mode === m ? "#0f172a" : "#94a3b8",
                          background:
                            mode === m
                              ? "#ffffff"
                              : "transparent",
                          boxShadow:
                            mode === m
                              ? "0 1px 3px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.05)"
                              : "none",
                          transition: "all 0.15s ease",
                          letterSpacing: "-0.01em",
                        }}
                      >
                        {m === "url" ? "arXiv URL" : "Upload PDF"}
                      </button>
                    ))}
                  </div>

                  {/* Input area */}
                  <div style={{ marginBottom: 14 }}>
                    {mode === "url" ? (
                      <input
                        type="text"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        onKeyDown={(e) =>
                          e.key === "Enter" && !isLoading && handleSubmit()
                        }
                        placeholder="https://arxiv.org/abs/2301.00001"
                        disabled={isLoading}
                        style={{
                          width: "100%",
                          padding: "12px 14px",
                          background: "#f8fafc",
                          border: "1px solid rgba(0,0,0,0.09)",
                          borderRadius: 9,
                          color: "#0f172a",
                          fontSize: 14,
                          fontFamily:
                            "var(--font-mono), ui-monospace, monospace",
                          outline: "none",
                          transition: "border-color 0.15s ease, background 0.15s ease",
                          boxSizing: "border-box",
                        }}
                        onFocus={(e) => {
                          e.currentTarget.style.borderColor = "#6366f1";
                          e.currentTarget.style.background = "#ffffff";
                        }}
                        onBlur={(e) => {
                          e.currentTarget.style.borderColor =
                            "rgba(0,0,0,0.09)";
                          e.currentTarget.style.background = "#f8fafc";
                        }}
                      />
                    ) : (
                      <div
                        className="tg-dropzone"
                        onClick={() => fileInputRef.current?.click()}
                        onDragOver={(e) => {
                          e.preventDefault();
                          setDragOver(true);
                        }}
                        onDragLeave={() => setDragOver(false)}
                        onDrop={(e) => {
                          e.preventDefault();
                          setDragOver(false);
                          const f = e.dataTransfer.files[0];
                          if (f?.type === "application/pdf") setFile(f);
                        }}
                        style={{
                          width: "100%",
                          padding: "32px 16px",
                          background: dragOver
                            ? "rgba(99,102,241,0.04)"
                            : "#f8fafc",
                          border: `1.5px dashed ${
                            file
                              ? "#6366f1"
                              : dragOver
                              ? "#6366f1"
                              : "rgba(0,0,0,0.12)"
                          }`,
                          borderRadius: 9,
                          cursor: "pointer",
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                          gap: 8,
                          transition:
                            "border-color 0.15s ease, background 0.15s ease",
                          boxSizing: "border-box",
                        }}
                      >
                        <svg
                          width="22"
                          height="22"
                          viewBox="0 0 20 20"
                          fill="none"
                        >
                          <path
                            d="M10 2v10M10 2L7 5M10 2l3 3"
                            stroke={
                              file || dragOver ? "#6366f1" : "#94a3b8"
                            }
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                          <path
                            d="M3 14v2a1 1 0 001 1h12a1 1 0 001-1v-2"
                            stroke={
                              file || dragOver ? "#6366f1" : "#94a3b8"
                            }
                            strokeWidth="1.5"
                            strokeLinecap="round"
                          />
                        </svg>
                        <span
                          style={{
                            fontSize: 13,
                            color: file ? "#0f172a" : "#64748b",
                            fontFamily:
                              "var(--font-mono), ui-monospace, monospace",
                            fontWeight: file ? 500 : 400,
                          }}
                        >
                          {file ? file.name : "Click or drag to upload PDF"}
                        </span>
                        {!file && (
                          <span
                            style={{
                              fontSize: 11,
                              color: "#94a3b8",
                              fontFamily:
                                "var(--font-mono), ui-monospace, monospace",
                            }}
                          >
                            .pdf up to 50 MB
                          </span>
                        )}
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept=".pdf,application/pdf"
                          style={{ display: "none" }}
                          onChange={(e) => {
                            const f = e.target.files?.[0];
                            if (f) setFile(f);
                          }}
                        />
                      </div>
                    )}
                  </div>

                  {/* Error */}
                  {error && (
                    <div
                      style={{
                        marginBottom: 14,
                        padding: "9px 13px",
                        background: "rgba(239,68,68,0.06)",
                        border: "1px solid rgba(239,68,68,0.18)",
                        borderRadius: 8,
                        fontSize: 13,
                        color: "#dc2626",
                        fontFamily:
                          "var(--font-mono), ui-monospace, monospace",
                      }}
                    >
                      {error}
                    </div>
                  )}

                  {/* CTA button */}
                  <button
                    className="tg-submit"
                    onClick={handleSubmit}
                    disabled={isLoading}
                    style={{
                      width: "100%",
                      height: 48,
                      background: isLoading
                        ? "rgba(99,102,241,0.55)"
                        : "#6366f1",
                      border: "none",
                      borderRadius: 10,
                      color: "#ffffff",
                      fontSize: 15,
                      fontWeight: 500,
                      fontFamily: "inherit",
                      cursor: isLoading ? "not-allowed" : "pointer",
                      letterSpacing: "-0.02em",
                      transition: "opacity 0.15s ease, background 0.15s ease",
                      boxShadow: isLoading
                        ? "none"
                        : "0 1px 3px rgba(99,102,241,0.3), 0 4px 12px rgba(99,102,241,0.15)",
                    }}
                  >
                    {isLoading ? "Starting..." : "Analyze paper"}
                  </button>
                </div>

                {/* Trust line */}
                <div
                  style={{
                    marginTop: 20,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 20,
                    flexWrap: "wrap",
                  }}
                >
                  {[
                    "No signup required",
                    "2–5 min per paper",
                    "Free to use",
                  ].map((text, i) => (
                    <span
                      key={i}
                      style={{
                        fontSize: 12,
                        color: "#94a3b8",
                        fontFamily:
                          "var(--font-mono), ui-monospace, monospace",
                        display: "flex",
                        alignItems: "center",
                        gap: 5,
                      }}
                    >
                      <svg
                        width="12"
                        height="12"
                        viewBox="0 0 12 12"
                        fill="none"
                      >
                        <circle
                          cx="6"
                          cy="6"
                          r="5"
                          stroke="#94a3b8"
                          strokeWidth="1"
                        />
                        <path
                          d="M3.5 6l1.8 1.8L8.5 4"
                          stroke="#94a3b8"
                          strokeWidth="1"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                      {text}
                    </span>
                  ))}
                </div>
              </section>

              {/* Features strip */}
              <section
                style={{
                  background: "#f9f9fb",
                  borderTop: "1px solid rgba(0,0,0,0.05)",
                  paddingTop: 80,
                  paddingBottom: 96,
                }}
              >
                <div
                  className="tg-page-pad"
                  style={{
                    maxWidth: 960,
                    margin: "0 auto",
                    paddingLeft: 24,
                    paddingRight: 24,
                  }}
                >
                  <div style={{ textAlign: "center", marginBottom: 52 }}>
                    <p
                      style={{
                        fontSize: 12,
                        fontFamily:
                          "var(--font-mono), ui-monospace, monospace",
                        color: "#94a3b8",
                        letterSpacing: "0.06em",
                        textTransform: "uppercase",
                        marginBottom: 12,
                      }}
                    >
                      How it works
                    </p>
                    <h2
                      style={{
                        fontSize: 32,
                        fontWeight: 600,
                        color: "#0f172a",
                        letterSpacing: "-0.04em",
                        lineHeight: 1.15,
                      }}
                    >
                      From PDF to graph in minutes
                    </h2>
                  </div>

                  <div
                    className="tg-features-grid"
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(3, 1fr)",
                      gap: 16,
                    }}
                  >
                    {FEATURES.map((f, i) => (
                      <div
                        key={i}
                        className="tg-feature"
                        style={{
                          background: "#ffffff",
                          border: "1px solid rgba(0,0,0,0.06)",
                          borderRadius: 12,
                          padding: 28,
                          transition:
                            "border-color 0.15s ease, box-shadow 0.15s ease",
                        }}
                      >
                        <div
                          style={{
                            width: 40,
                            height: 40,
                            background: "rgba(99,102,241,0.07)",
                            borderRadius: 10,
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            marginBottom: 18,
                          }}
                        >
                          {f.icon}
                        </div>
                        <h3
                          style={{
                            fontSize: 14,
                            fontWeight: 600,
                            color: "#0f172a",
                            letterSpacing: "-0.02em",
                            marginBottom: 8,
                          }}
                        >
                          {f.title}
                        </h3>
                        <p
                          style={{
                            fontSize: 13,
                            color: "#64748b",
                            lineHeight: 1.65,
                            margin: 0,
                          }}
                        >
                          {f.body}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            </>
          )}
        </div>
      </div>
    </>
  );
}
