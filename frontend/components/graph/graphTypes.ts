export type NodeType =
  | 'problem'
  | 'method'
  | 'architecture'
  | 'concept'
  | 'dataset'
  | 'experiment'
  | 'result'
  | 'citation'
  | 'limitation'
  | 'future_work'
  | 'reasoning'
  | 'equation'
  | 'figure'
  | 'table';

export interface NodeData extends Record<string, unknown> {
  title: string;
  description: string;
  type: NodeType;
  simplified_explanation: string | null;
  advantages: string[];
  limitations: string[];
  key_equations: string[];
  source_text: string | null;
  section_name: string | null;
  section_number: string | null;
  page_number: number | null;
  label: string | null;
  image_url: string | null;
}

export interface NeighborInfo {
  id: string;
  title: string;
  type: NodeType;
  relationship: string;
}
