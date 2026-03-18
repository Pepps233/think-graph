import type { Edge, Node } from '@xyflow/react';
import Link from 'next/link';
import { apiFetch } from '@/lib/api';
import GraphCanvas from '@/components/graph/GraphCanvas';
import type { NodeData } from '@/components/graph/graphTypes';

interface GraphPageProps {
  params: { id: string };
}

export default async function GraphPage({ params }: GraphPageProps) {
  const data = await apiFetch<{ nodes: Node<NodeData>[]; edges: Edge[] }>(
    `/papers/${params.id}/graph`
  );

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        background: '#f8f9fb',
        fontFamily: 'var(--font-body), sans-serif',
      }}
    >
      {/* Top bar */}
      <header
        style={{
          height: 48,
          background: '#ffffff',
          borderBottom: '1px solid rgba(0,0,0,0.06)',
          display: 'flex',
          alignItems: 'center',
          padding: '0 16px',
          flexShrink: 0,
          gap: 12,
        }}
      >
        <Link
          href="/"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            textDecoration: 'none',
          }}
        >
          <div
            style={{
              width: 24,
              height: 24,
              borderRadius: 5,
              background: '#6366f1',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg width="12" height="12" viewBox="0 0 14 14" fill="none">
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
              fontSize: 14,
              fontWeight: 600,
              color: '#0f172a',
              letterSpacing: '-0.02em',
            }}
          >
            ThinkGraph
          </span>
        </Link>

        <div
          style={{
            width: 1,
            height: 16,
            background: 'rgba(0,0,0,0.08)',
          }}
        />

        <span
          style={{
            fontSize: 12,
            color: '#94a3b8',
            fontFamily: 'var(--font-mono), monospace',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {params.id}
        </span>

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span
            style={{
              fontSize: 11,
              fontFamily: 'var(--font-mono), monospace',
              color: '#94a3b8',
            }}
          >
            {data.nodes.length} nodes &middot; {data.edges.length} edges
          </span>
        </div>
      </header>

      {/* Canvas */}
      <div style={{ flex: 1, position: 'relative' }}>
        <GraphCanvas initialNodes={data.nodes} initialEdges={data.edges} />
      </div>
    </div>
  );
}
