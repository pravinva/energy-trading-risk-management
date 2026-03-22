import { useState, useRef, useEffect } from 'react';

interface TooltipProps {
  children: React.ReactNode;
  title: string;
  description: string;
  table?: string;
  calculation?: string;
}

export function Tooltip({ children, title, description, table, calculation }: TooltipProps): JSX.Element {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const updatePosition = () => {
    if (!triggerRef.current || !tooltipRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let top = triggerRect.bottom + 8;
    let left = triggerRect.left;

    // Adjust if tooltip goes off right edge
    if (left + tooltipRect.width > viewportWidth - 16) {
      left = viewportWidth - tooltipRect.width - 16;
    }

    // Adjust if tooltip goes off left edge
    if (left < 16) {
      left = 16;
    }

    // Flip to top if no room at bottom
    if (top + tooltipRect.height > viewportHeight - 16) {
      top = triggerRect.top - tooltipRect.height - 8;
    }

    setPosition({ top, left });
  };

  useEffect(() => {
    if (isVisible) {
      updatePosition();
      window.addEventListener('scroll', updatePosition);
      window.addEventListener('resize', updatePosition);
      return () => {
        window.removeEventListener('scroll', updatePosition);
        window.removeEventListener('resize', updatePosition);
      };
    }
  }, [isVisible]);

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          cursor: 'help',
          borderBottom: '1px dotted var(--color-border-strong)',
        }}
      >
        {children}
      </div>

      {isVisible && (
        <div
          ref={tooltipRef}
          style={{
            position: 'fixed',
            top: `${position.top}px`,
            left: `${position.left}px`,
            background: 'var(--color-bg-panel)',
            border: '1px solid var(--color-border-default)',
            borderRadius: 'var(--radius-md)',
            padding: '12px',
            maxWidth: '320px',
            boxShadow: 'var(--shadow-elevated)',
            zIndex: 10000,
            fontSize: 'var(--text-sm)',
            lineHeight: 'var(--leading-snug)',
            pointerEvents: 'none',
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 6, color: 'var(--color-text-primary)' }}>{title}</div>
          <div style={{ marginBottom: 8, color: 'var(--color-text-secondary)' }}>{description}</div>

          {table && (
            <div
              style={{
                marginTop: 8,
                paddingTop: 8,
                borderTop: '1px solid var(--color-border-subtle)',
                fontSize: 'var(--text-xs)',
                color: 'var(--color-text-tertiary)',
              }}
            >
              <div style={{ fontWeight: 600, marginBottom: 4 }}>Data Source:</div>
              <code
                style={{
                  fontFamily: 'var(--font-data)',
                  background: 'var(--color-bg-elevated)',
                  padding: '2px 6px',
                  borderRadius: '3px',
                  fontSize: '11px',
                }}
              >
                {table}
              </code>
            </div>
          )}

          {calculation && (
            <div
              style={{
                marginTop: 8,
                paddingTop: 8,
                borderTop: '1px solid var(--color-border-subtle)',
                fontSize: 'var(--text-xs)',
                color: 'var(--color-text-tertiary)',
              }}
            >
              <div style={{ fontWeight: 600, marginBottom: 4 }}>Calculation:</div>
              <div style={{ fontFamily: 'var(--font-data)', fontSize: '11px' }}>{calculation}</div>
            </div>
          )}
        </div>
      )}
    </>
  );
}
