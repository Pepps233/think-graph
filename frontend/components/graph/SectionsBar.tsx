'use client';

import React, { useState } from 'react';

interface SectionInfo {
  section_number: string;
  section_name: string;
  page_start: number;
  page_end?: number | null;
}

interface SectionsBarProps {
  sections: SectionInfo[];
}

export default function SectionsBar({ sections }: SectionsBarProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      style={{
        background: '#ffffff',
        borderBottom: '1px solid rgba(0,0,0,0.06)',
        flexShrink: 0,
      }}
    >
      {/* Toggle header */}
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '8px 16px',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          fontFamily: 'var(--font-mono), monospace',
        }}
      >
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          style={{
            transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)',
            transition: 'transform 0.15s ease',
            flexShrink: 0,
          }}
        >
          <path
            d="M4 2l4 4-4 4"
            stroke="#94a3b8"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <span
          style={{
            fontSize: 11,
            fontWeight: 500,
            color: '#64748b',
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
          }}
        >
          Parsed Sections
        </span>
        <span
          style={{
            fontSize: 11,
            color: '#94a3b8',
            background: '#f1f5f9',
            border: '1px solid #e2e8f0',
            borderRadius: 4,
            padding: '1px 6px',
          }}
        >
          {sections.length}
        </span>
      </button>

      {/* Expandable section list */}
      {expanded && (
        <div
          style={{
            padding: '0 16px 10px',
            display: 'flex',
            flexWrap: 'wrap',
            gap: 6,
          }}
        >
          {sections.map((s, i) => {
            const label = s.section_number
              ? `${s.section_number} ${s.section_name}`
              : s.section_name;
            const pageLabel = s.page_end && s.page_end !== s.page_start
              ? `pp. ${s.page_start}-${s.page_end}`
              : `p. ${s.page_start}`;

            // Determine depth: "3" = 0, "3.2" = 1, "3.2.1" = 2
            const dotCount = s.section_number
              ? (s.section_number.match(/\./g) || []).length
              : 0;
            const isSubsection = dotCount >= 1;
            const isSubSubsection = dotCount >= 2;

            return (
              <div
                key={i}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: isSubSubsection ? '3px 8px' : '4px 10px',
                  background: isSubSubsection ? '#f1f5f9' : '#f8fafc',
                  border: `1px solid ${isSubSubsection ? '#e2e8f0' : '#e2e8f0'}`,
                  borderRadius: 6,
                  fontSize: isSubSubsection ? 11 : 12,
                  color: isSubsection ? '#475569' : '#0f172a',
                  fontFamily: 'var(--font-body), sans-serif',
                  fontWeight: isSubsection ? 400 : 500,
                  lineHeight: 1.4,
                }}
              >
                <span>{label}</span>
                <span
                  style={{
                    fontSize: 10,
                    fontFamily: 'var(--font-mono), monospace',
                    color: '#94a3b8',
                  }}
                >
                  {pageLabel}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
