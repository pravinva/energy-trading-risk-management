import type { ReactNode } from 'react';

type Persona = 'dispatch' | 'trader' | 'quant' | 'risk' | 'portfolio' | 'anz' | 'europe' | 'americas' | 'neutral';
const personaColor: Record<Persona, string> = {
  dispatch: 'var(--color-persona-dispatch)',
  trader: 'var(--color-persona-trader)',
  quant: 'var(--color-persona-quant)',
  risk: 'var(--color-persona-risk)',
  portfolio: 'var(--color-persona-portfolio)',
  anz: 'var(--color-region-anz)',
  europe: 'var(--color-region-europe)',
  americas: 'var(--color-region-americas)',
  neutral: 'transparent',
};

export function Panel({ title, subtitle, actions, persona = 'neutral', badge, className, children }: { title?: string; subtitle?: string; actions?: ReactNode; persona?: Persona; badge?: string; className?: string; children: ReactNode }): JSX.Element {
  return (
    <div className={className} style={{ background: 'var(--color-bg-base)', border: '1px solid var(--color-border-subtle)', borderLeft: `2px solid ${personaColor[persona]}`, borderRadius: 'var(--radius-none)' }}>
      {(title || actions) && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--color-bg-elevated)', padding: 'var(--space-3)', borderBottom: '1px solid var(--color-border-subtle)' }}>
          <div>
            <div className="label-caps">{title ?? ''}</div>
            {subtitle ? <div className="text-secondary" style={{ fontSize: 'var(--text-xs)', marginTop: 2 }}>{subtitle}</div> : null}
          </div>
          {badge ? <div className="label-caps" style={{ color: personaColor[persona] }}>{badge}</div> : null}
          <div>{actions}</div>
        </div>
      )}
      <div style={{ padding: 'var(--space-3)' }}>{children}</div>
    </div>
  );
}
