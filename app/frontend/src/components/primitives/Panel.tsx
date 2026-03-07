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
    <div className={className} style={{ background: 'var(--color-bg-panel)', border: '1px solid var(--color-border-subtle)', borderRadius: '5px', overflow: 'hidden' }}>
      {(title || actions) && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--color-bg-surface)', padding: '8px 12px', borderBottom: '1px solid var(--color-border-subtle)' }}>
          <div>
            <div className="label-caps" style={{ fontSize: 10, letterSpacing: '0.08em' }}>{title ?? ''}</div>
            {subtitle ? <div className="text-secondary" style={{ fontSize: 11, marginTop: 2 }}>{subtitle}</div> : null}
          </div>
          {badge ? <div className="label-caps" style={{ color: personaColor[persona], fontSize: 10 }}>{badge}</div> : null}
          <div>{actions}</div>
        </div>
      )}
      <div style={{ padding: 12 }}>{children}</div>
    </div>
  );
}
