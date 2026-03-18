'use client';

import React from 'react';
import 'katex/dist/katex.min.css';
import { BlockMath } from 'react-katex';
import { X } from 'lucide-react';
import {
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import type { NodeData, NeighborInfo } from './graphTypes';
import { NODE_COLORS } from './nodeColors';

interface NodeDetailPanelProps {
  node: (NodeData & { id: string }) | null;
  onClose: () => void;
  neighbors: NeighborInfo[];
}

export default function NodeDetailPanel({
  node,
  onClose,
  neighbors,
}: NodeDetailPanelProps) {
  if (!node) return null;

  const colors = NODE_COLORS[node.type] ?? NODE_COLORS.concept;
  const hasProvenance =
    node.section_number || node.section_name || node.page_number || node.label;

  return (
    <SheetContent
      side="right"
      className="w-[420px] sm:max-w-[420px] overflow-y-auto p-0 border-l"
      showCloseButton={false}
      style={{
        background: '#ffffff',
        borderLeft: '1px solid rgba(0,0,0,0.08)',
      }}
    >
      {/* Sticky header */}
      <div
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 10,
          background: '#ffffff',
          borderBottom: '1px solid rgba(0,0,0,0.06)',
          padding: '14px 16px 12px',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            gap: 12,
          }}
        >
          <div style={{ flex: 1, minWidth: 0 }}>
            {/* Type badge */}
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 5,
                padding: '2px 8px',
                borderRadius: 20,
                background: colors.bg,
                border: `1px solid ${colors.border}`,
                marginBottom: 8,
              }}
            >
              <div
                style={{
                  width: 5,
                  height: 5,
                  borderRadius: '50%',
                  background: colors.dot,
                }}
              />
              <span
                style={{
                  fontSize: 11,
                  fontFamily: 'var(--font-mono), monospace',
                  color: colors.dot,
                  fontWeight: 500,
                  letterSpacing: '0.02em',
                  textTransform: 'uppercase',
                }}
              >
                {colors.label}
              </span>
            </div>

            {/* Title */}
            <SheetHeader style={{ padding: 0 }}>
              <SheetTitle
                style={{
                  fontSize: 17,
                  fontWeight: 600,
                  color: '#0f172a',
                  letterSpacing: '-0.02em',
                  lineHeight: 1.3,
                  fontFamily: 'var(--font-body), sans-serif',
                }}
              >
                {node.title}
              </SheetTitle>
            </SheetHeader>
          </div>

          {/* Close button */}
          <button
            onClick={onClose}
            style={{
              flexShrink: 0,
              width: 28,
              height: 28,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 6,
              border: '1px solid rgba(0,0,0,0.08)',
              background: 'transparent',
              cursor: 'pointer',
              color: '#94a3b8',
              transition: 'background 0.12s ease, color 0.12s ease',
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background =
                '#f1f5f9';
              (e.currentTarget as HTMLButtonElement).style.color = '#0f172a';
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background =
                'transparent';
              (e.currentTarget as HTMLButtonElement).style.color = '#94a3b8';
            }}
          >
            <X size={14} />
          </button>
        </div>

        {/* Provenance pills */}
        {hasProvenance && (
          <button
            style={{
              marginTop: 10,
              display: 'flex',
              flexWrap: 'wrap',
              gap: 5,
              background: 'none',
              border: 'none',
              padding: 0,
              cursor: node.page_number != null ? 'pointer' : 'default',
              textAlign: 'left',
            }}
          >
            {node.section_number && (
              <span style={pillStyle}>&sect;&nbsp;{node.section_number}</span>
            )}
            {node.section_name && (
              <span style={pillStyle}>{node.section_name}</span>
            )}
            {node.page_number != null && (
              <span style={{ ...pillStyle, color: '#6366f1', borderColor: '#c7d2fe', background: '#eef2ff' }}>
                Page {node.page_number}
              </span>
            )}
            {node.label && (
              <span style={pillStyle}>{node.label}</span>
            )}
          </button>
        )}
      </div>

      {/* Body */}
      <div style={{ padding: '16px 16px 32px', display: 'flex', flexDirection: 'column', gap: 20 }}>

        {/* Description */}
        {node.description && (
          <p
            style={{
              fontSize: 14,
              color: '#374151',
              lineHeight: 1.75,
              margin: 0,
              fontFamily: 'var(--font-body), sans-serif',
            }}
          >
            {node.description}
          </p>
        )}

        {/* Simplified explanation */}
        {node.simplified_explanation && (
          <div
            style={{
              background: '#eff6ff',
              borderLeft: '3px solid #3b82f6',
              borderRadius: '0 6px 6px 0',
              padding: '10px 14px',
            }}
          >
            <div
              style={{
                fontSize: 11,
                fontFamily: 'var(--font-mono), monospace',
                color: '#3b82f6',
                fontWeight: 500,
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                marginBottom: 6,
              }}
            >
              In plain language
            </div>
            <p
              style={{
                fontSize: 13,
                color: '#1e40af',
                lineHeight: 1.65,
                margin: 0,
                fontFamily: 'var(--font-body), sans-serif',
              }}
            >
              {node.simplified_explanation}
            </p>
          </div>
        )}

        {/* Key equations */}
        {node.key_equations && node.key_equations.length > 0 && (
          <div>
            <SectionLabel>Key Equations</SectionLabel>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {node.key_equations.map((eq, i) => (
                <div
                  key={i}
                  style={{
                    overflowX: 'auto',
                    background: '#f8f9fb',
                    border: '1px solid rgba(0,0,0,0.06)',
                    borderRadius: 8,
                    padding: 16,
                  }}
                >
                  <BlockMath
                    math={eq}
                    renderError={() => (
                      <code style={{ color: '#ef4444', fontSize: 13 }}>{eq}</code>
                    )}
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Advantages */}
        {node.advantages && node.advantages.length > 0 && (
          <div>
            <SectionLabel>Advantages</SectionLabel>
            <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 6 }}>
              {node.advantages.map((adv, i) => (
                <li key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                  <span
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      background: '#22c55e',
                      flexShrink: 0,
                      marginTop: 5,
                    }}
                  />
                  <span style={{ fontSize: 13, color: '#374151', lineHeight: 1.6, fontFamily: 'var(--font-body), sans-serif' }}>
                    {adv}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Limitations */}
        {node.limitations && node.limitations.length > 0 && (
          <div>
            <SectionLabel>Limitations</SectionLabel>
            <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 6 }}>
              {node.limitations.map((lim, i) => (
                <li key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                  <span
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      background: '#ef4444',
                      flexShrink: 0,
                      marginTop: 5,
                    }}
                  />
                  <span style={{ fontSize: 13, color: '#374151', lineHeight: 1.6, fontFamily: 'var(--font-body), sans-serif' }}>
                    {lim}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Source text */}
        {node.source_text && (
          <div>
            <SectionLabel>Source</SectionLabel>
            <blockquote
              style={{
                margin: 0,
                borderLeft: '3px solid #e2e8f0',
                paddingLeft: 12,
                fontFamily: 'var(--font-mono), monospace',
                fontSize: 12,
                color: '#64748b',
                fontStyle: 'italic',
                lineHeight: 1.7,
              }}
            >
              {node.source_text}
            </blockquote>
          </div>
        )}

        {/* Connected nodes */}
        {neighbors.length > 0 && (
          <div>
            <SectionLabel>Connected Nodes</SectionLabel>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {neighbors.slice(0, 5).map((n) => {
                const nc = NODE_COLORS[n.type] ?? NODE_COLORS.concept;
                return (
                  <div
                    key={n.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      padding: '8px 10px',
                      background: '#f8f9fb',
                      border: '1px solid rgba(0,0,0,0.05)',
                      borderRadius: 7,
                    }}
                  >
                    <div
                      style={{
                        width: 7,
                        height: 7,
                        borderRadius: '50%',
                        background: nc.dot,
                        flexShrink: 0,
                      }}
                    />
                    <span
                      style={{
                        fontSize: 13,
                        color: '#0f172a',
                        fontWeight: 500,
                        flex: 1,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        fontFamily: 'var(--font-body), sans-serif',
                      }}
                    >
                      {n.title}
                    </span>
                    <span
                      style={{
                        fontSize: 10,
                        fontFamily: 'var(--font-mono), monospace',
                        color: '#94a3b8',
                        background: '#f1f5f9',
                        border: '1px solid #e2e8f0',
                        borderRadius: 4,
                        padding: '2px 6px',
                        whiteSpace: 'nowrap',
                        flexShrink: 0,
                      }}
                    >
                      {n.relationship.toLowerCase().replace(/_/g, ' ')}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </SheetContent>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontSize: 11,
        fontFamily: 'var(--font-mono), monospace',
        color: '#94a3b8',
        fontWeight: 500,
        letterSpacing: '0.06em',
        textTransform: 'uppercase',
        marginBottom: 8,
      }}
    >
      {children}
    </div>
  );
}

const pillStyle: React.CSSProperties = {
  fontSize: 11,
  fontFamily: 'var(--font-mono), monospace',
  color: '#64748b',
  background: '#f8fafc',
  border: '1px solid #e2e8f0',
  borderRadius: 4,
  padding: '2px 7px',
};
