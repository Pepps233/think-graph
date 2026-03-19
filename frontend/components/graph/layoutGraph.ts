import Dagre from '@dagrejs/dagre';
import type { Node, Edge } from '@xyflow/react';
import type { NodeData } from './graphTypes';

const NODE_WIDTH = 220;
const NODE_HEIGHT = 120;

/**
 * Apply a dagre directed-graph layout to position nodes
 * so that edges are spread out and labels don't overlap.
 */
export function layoutGraph(
  nodes: Node<NodeData>[],
  edges: Edge[],
): Node<NodeData>[] {
  const g = new Dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));

  g.setGraph({
    rankdir: 'TB',
    nodesep: 80,
    ranksep: 160,
    edgesep: 60,
    marginx: 40,
    marginy: 40,
  });

  for (const node of nodes) {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  }

  for (const edge of edges) {
    g.setEdge(edge.source, edge.target);
  }

  Dagre.layout(g);

  return nodes.map((node) => {
    const pos = g.node(node.id);
    return {
      ...node,
      position: {
        x: pos.x - NODE_WIDTH / 2,
        y: pos.y - NODE_HEIGHT / 2,
      },
    };
  });
}
