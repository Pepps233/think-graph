'use client';

import Link from 'next/link';

interface GraphErrorProps {
  error: Error & { digest?: string };
}

export default function GraphError({ error }: GraphErrorProps) {
  return (
    <div
      style={{
        height: '100vh',
        background: '#f8f9fb',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 16,
        fontFamily: 'var(--font-body), sans-serif',
        padding: '0 24px',
      }}
    >
      <div
        style={{
          fontSize: 13,
          fontFamily: 'var(--font-mono), monospace',
          color: '#ef4444',
          background: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: 7,
          padding: '9px 14px',
          maxWidth: 480,
          textAlign: 'center',
        }}
      >
        {error.message || 'Failed to load graph'}
      </div>

      <Link
        href="/"
        style={{
          fontSize: 13,
          color: '#6366f1',
          textDecoration: 'none',
          fontFamily: 'var(--font-mono), monospace',
          borderBottom: '1px solid rgba(99,102,241,0.3)',
          paddingBottom: 1,
        }}
      >
        Back to home
      </Link>
    </div>
  );
}
