declare module 'react-katex' {
  import type { ReactNode } from 'react';

  interface MathProps {
    math: string;
    block?: boolean;
    errorColor?: string;
    renderError?: (error: Error) => ReactNode;
    settings?: object;
  }

  export function InlineMath(props: MathProps): JSX.Element;
  export function BlockMath(props: MathProps): JSX.Element;
}
