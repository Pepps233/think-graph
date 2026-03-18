'use client';

import React, { memo } from 'react';
import { Handle, Position, type NodeProps, type Node } from '@xyflow/react';
import type { NodeData } from './graphTypes';
import { NODE_COLORS } from './nodeColors';

function GraphNode({ data, selected }: NodeProps<Node<NodeData>>) {
  const colors = NODE_COLORS[data.type] ?? NODE_COLORS.concept;

  return (
    <div
      style={{
        width: 220,
        background: colors.bg,
        border: `1px solid ${colors.border}`,
        borderRadius: 10,
        padding: '10px 12px',
        cursor: 'pointer',
        boxShadow: selected
          ? `0 0 0 2px #6366f1, 0 4px 12px rgba(0,0,0,0.08)`
          : '0 1px 3px rgba(0,0,0,0.07), 0 0 0 1px rgba(0,0,0,0.04)',
        transition: 'box-shadow 0.15s ease',
        fontFamily: 'var(--font-body), sans-serif',
      }}
      onMouseEnter={(e) => {
        if (!selected) {
          (e.currentTarget as HTMLDivElement).style.boxShadow =
            '0 4px 12px rgba(0,0,0,0.10), 0 0 0 1px rgba(0,0,0,0.04)';
        }
      }}
      onMouseLeave={(e) => {
        if (!selected) {
          (e.currentTarget as HTMLDivElement).style.boxShadow =
            '0 1px 3px rgba(0,0,0,0.07), 0 0 0 1px rgba(0,0,0,0.04)';
        }
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        style={{
          width: 6,
          height: 6,
          background: colors.dot,
          border: 'none',
          opacity: 0,
          transition: 'opacity 0.15s ease',
        }}
        className="graph-node-handle"
      />

      {/* Type label row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 5,
          marginBottom: 6,
        }}
      >
        <div
          style={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            background: colors.dot,
            flexShrink: 0,
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
      <div
        style={{
          fontSize: 14,
          fontWeight: 600,
          color: '#0f172a',
          lineHeight: 1.35,
          letterSpacing: '-0.01em',
          marginBottom: 5,
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
        }}
      >
        {data.title}
      </div>

      {/* Description */}
      {data.description && (
        <div
          style={{
            fontSize: 12,
            color: '#64748b',
            lineHeight: 1.5,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {data.description}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Right}
        style={{
          width: 6,
          height: 6,
          background: colors.dot,
          border: 'none',
          opacity: 0,
          transition: 'opacity 0.15s ease',
        }}
        className="graph-node-handle"
      />
    </div>
  );
}

export default memo(GraphNode);
