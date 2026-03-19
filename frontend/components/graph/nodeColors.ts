import type { NodeType } from './graphTypes';

interface NodeColorConfig {
  bg: string;
  border: string;
  dot: string;
  label: string;
}

export const NODE_COLORS: Record<NodeType, NodeColorConfig> = {
  problem: {
    bg: '#fef2f2',
    border: '#fecaca',
    dot: '#ef4444',
    label: 'Problem',
  },
  method: {
    bg: '#eff6ff',
    border: '#bfdbfe',
    dot: '#3b82f6',
    label: 'Method',
  },
  architecture: {
    bg: '#eef2ff',
    border: '#c7d2fe',
    dot: '#6366f1',
    label: 'Architecture',
  },
  concept: {
    bg: '#f0fdf4',
    border: '#bbf7d0',
    dot: '#22c55e',
    label: 'Concept',
  },
  dataset: {
    bg: '#fff7ed',
    border: '#fed7aa',
    dot: '#f97316',
    label: 'Dataset',
  },
  experiment: {
    bg: '#fdf4ff',
    border: '#e9d5ff',
    dot: '#a855f7',
    label: 'Experiment',
  },
  result: {
    bg: '#f0fdfa',
    border: '#99f6e4',
    dot: '#14b8a6',
    label: 'Result',
  },
  citation: {
    bg: '#f8fafc',
    border: '#e2e8f0',
    dot: '#94a3b8',
    label: 'Citation',
  },
  limitation: {
    bg: '#fefce8',
    border: '#fef08a',
    dot: '#eab308',
    label: 'Limitation',
  },
  future_work: {
    bg: '#fff1f2',
    border: '#fecdd3',
    dot: '#f43f5e',
    label: 'Future Work',
  },
  reasoning: {
    bg: '#faf5ff',
    border: '#ddd6fe',
    dot: '#8b5cf6',
    label: 'Reasoning',
  },
  equation: {
    bg: '#fefce8',
    border: '#fde68a',
    dot: '#d97706',
    label: 'Equation',
  },
  figure: {
    bg: '#ecfdf5',
    border: '#a7f3d0',
    dot: '#059669',
    label: 'Figure',
  },
  table: {
    bg: '#f0f9ff',
    border: '#bae6fd',
    dot: '#0284c7',
    label: 'Table',
  },
};
