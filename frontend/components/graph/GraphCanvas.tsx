'use client';

import React, { useState, useMemo, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeTypes,
  type NodeMouseHandler,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { Sheet } from '@/components/ui/sheet';
import GraphNode from './GraphNode';
import NodeDetailPanel from './NodeDetailPanel';
import type { NodeData, NeighborInfo } from './graphTypes';
import { NODE_COLORS } from './nodeColors';

// Module-level constant — avoids React Flow re-mount on render
const nodeTypes: NodeTypes = {
  problem: GraphNode,
  method: GraphNode,
  architecture: GraphNode,
  concept: GraphNode,
  dataset: GraphNode,
  experiment: GraphNode,
  result: GraphNode,
  citation: GraphNode,
  limitation: GraphNode,
  future_work: GraphNode,
  reasoning: GraphNode,
};

const defaultEdgeOptions = {
  type: 'smoothstep',
  style: { stroke: '#cbd5e1', strokeWidth: 1.5 },
  labelStyle: {
    fontSize: 10,
    fontFamily: 'var(--font-mono), monospace',
    fill: '#94a3b8',
  },
  labelBgStyle: { fill: '#f8f9fb' },
  labelBgPadding: [4, 2] as [number, number],
};

function formatEdgeLabel(label: string | undefined): string | undefined {
  if (!label) return undefined;
  return label.toLowerCase().replace(/_/g, ' ');
}

interface GraphCanvasProps {
  initialNodes: Node<NodeData>[];
  initialEdges: Edge[];
}

export default function GraphCanvas({ initialNodes, initialEdges }: GraphCanvasProps) {
  const formattedEdges = useMemo(
    () =>
      initialEdges.map((e) => ({
        ...e,
        label: formatEdgeLabel(e.label as string | undefined),
      })),
    [initialEdges]
  );

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(formattedEdges);
  const [selectedNode, setSelectedNode] = useState<(NodeData & { id: string }) | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  // Build neighbor map from edges — no extra API call needed
  const neighborMap = useMemo(() => {
    const map = new Map<string, NeighborInfo[]>();
    const nodeById = new Map(nodes.map((n) => [n.id, n]));

    for (const edge of edges) {
      const addNeighbor = (fromId: string, toId: string, rel: string) => {
        const target = nodeById.get(toId);
        if (!target) return;
        const existing = map.get(fromId) ?? [];
        existing.push({
          id: toId,
          title: target.data.title,
          type: target.data.type,
          relationship: rel,
        });
        map.set(fromId, existing);
      };
      addNeighbor(edge.source, edge.target, String(edge.label ?? ''));
      addNeighbor(edge.target, edge.source, String(edge.label ?? ''));
    }

    return map;
  }, [nodes, edges]);

  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      setSelectedNode({ ...(node.data as NodeData), id: node.id });
      setIsPanelOpen(true);
    },
    []
  );

  const onPaneClick = useCallback(() => {
    setIsPanelOpen(false);
  }, []);

  const neighbors = selectedNode ? (neighborMap.get(selectedNode.id) ?? []) : [];

  return (
    <div style={{ position: 'absolute', inset: 0 }}>
      <style>{`
        .graph-node-handle { opacity: 0 !important; transition: opacity 0.15s ease; }
        .react-flow__node:hover .graph-node-handle { opacity: 1 !important; }
        .react-flow__controls { box-shadow: 0 1px 3px rgba(0,0,0,0.07), 0 0 0 1px rgba(0,0,0,0.04) !important; border-radius: 8px !important; overflow: hidden; }
        .react-flow__controls-button { background: #ffffff !important; border-bottom: 1px solid rgba(0,0,0,0.06) !important; color: #64748b !important; }
        .react-flow__controls-button:hover { background: #f8f9fb !important; }
        .react-flow__minimap { border-radius: 8px !important; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.07), 0 0 0 1px rgba(0,0,0,0.04) !important; }
        .react-flow__edge-label { font-family: var(--font-mono), monospace !important; }
      `}</style>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        minZoom={0.2}
        maxZoom={2.5}
        proOptions={{ hideAttribution: true }}
        style={{ background: '#f8f9fb' }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="#d1d5db"
        />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={(n) => {
            const data = n.data as NodeData;
            return NODE_COLORS[data?.type]?.dot ?? '#94a3b8';
          }}
          maskColor="rgba(248,249,251,0.85)"
          style={{ background: '#ffffff' }}
        />
      </ReactFlow>

      <Sheet
        open={isPanelOpen}
        onOpenChange={(open: boolean) => {
          if (!open) setIsPanelOpen(false);
        }}
      >
        <NodeDetailPanel
          node={selectedNode}
          onClose={() => setIsPanelOpen(false)}
          neighbors={neighbors}
        />
      </Sheet>
    </div>
  );
}
