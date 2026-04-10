# APEX Color & Font Reference

Quick reference for developers working on APEX frontend.

---

## 🎨 Databricks Brand Colors

```css
--db-red: #FF3621    /* Databricks primary red */
--db-navy: #1B2431   /* Databricks navy (also main text color) */
```

**Usage:**
```tsx
// Top navigation background
<div style={{ background: 'var(--db-navy)' }}>

// Primary button
<button style={{ background: 'var(--db-red)' }}>

// Active state
<div className={isActive && 'bg-[var(--db-red)]'}>
```

---

## 📝 Text Colors

| Variable | Hex | When to Use |
|----------|-----|-------------|
| `--color-text-primary` | **#1B2431** | Main content, headers, important text |
| `--color-text-secondary` | **#64748B** | Labels, subtitles, less important text |
| `--color-text-tertiary` | **#94A3B8** | Timestamps, metadata, least important |
| `--color-text-inverse` | **#fff** | Text on dark backgrounds |
| `--color-text-muted` | **#64748B** | Disabled or muted content |

```tsx
<h1 style={{ color: 'var(--color-text-primary)' }}>Portfolio Dashboard</h1>
<p style={{ color: 'var(--color-text-secondary)' }}>Updated 5 minutes ago</p>
<span style={{ color: 'var(--color-text-tertiary)' }}>2026-03-22 10:45 AM</span>
```

---

## 🎯 Status Colors

### Green (Healthy, Profit, Up)
```css
--green: #16A34A         /* Main green */
--green-bg: #F0FDF4      /* Very light bg */
--green-lt: #DCFCE7      /* Light bg */
```

```tsx
// Profit indicator
<span style={{ color: 'var(--green)' }}>+$12,450</span>

// Healthy badge
<div style={{ background: 'var(--green-lt)', color: 'var(--green)' }}>
  Healthy
</div>
```

### Amber (Warning, Caution)
```css
--amber: #D97706         /* Main amber */
--amber-bg: #FFFBEB      /* Very light bg */
--amber-lt: #FEF3C7      /* Light bg */
```

```tsx
// Warning badge
<div style={{ background: 'var(--amber-lt)', color: 'var(--amber)' }}>
  Warning
</div>
```

### Red (Error, Loss, Down)
```css
--red: #DC2626           /* Main red */
--red-bg: #FEF2F2        /* Very light bg */
--red-lt: #FEE2E2        /* Light bg */
```

```tsx
// Loss indicator
<span style={{ color: 'var(--red)' }}>-$8,230</span>

// Critical badge
<div style={{ background: 'var(--red-lt)', color: 'var(--red)' }}>
  Critical
</div>
```

---

## 📊 Trading Colors

### Bid/Buy Side (Green)
```css
--color-bid: #16A34A
--color-bid-dim: #DCFCE7
```

### Offer/Sell Side (Red)
```css
--color-offer: #DC2626
--color-offer-dim: #FEE2E2
```

```tsx
// Order book
<div style={{ color: 'var(--color-bid)' }}>BID: $96.50</div>
<div style={{ color: 'var(--color-offer)' }}>ASK: $96.75</div>
```

---

## 📈 P&L Colors

```css
--color-pnl-positive: #16A34A   /* Profit */
--color-pnl-negative: #DC2626   /* Loss */
--color-pnl-flat: #64748B       /* Break-even */
```

```tsx
const pnlColor = pnl > 0 ? 'var(--color-pnl-positive)' :
                 pnl < 0 ? 'var(--color-pnl-negative)' :
                 'var(--color-pnl-flat)';

<span style={{ color: pnlColor }}>{formatCurrency(pnl)}</span>
```

---

## 🔲 Background Colors

```css
--color-bg-void: #F0F2F5    /* Page background */
--color-bg-base: #F0F2F5    /* Base layer */
--color-bg-elevated: #fff   /* Cards, panels */
--color-bg-panel: #fff      /* Panel backgrounds */
--color-bg-input: #fff      /* Input fields */
```

```tsx
// Card/panel
<div style={{
  background: 'var(--color-bg-elevated)',
  boxShadow: 'var(--shadow-panel)'
}}>
  Content
</div>
```

---

## 🔳 Border Colors

```css
--color-border-subtle: #F1F5F9   /* Very light borders */
--color-border-default: #E2E8F0  /* Standard borders */
--color-border-strong: #CBD5E1   /* Emphasized borders */
```

```tsx
// Divider
<hr style={{ borderColor: 'var(--color-border-default)' }} />

// Card border
<div style={{ border: '1px solid var(--color-border-default)' }}>
```

---

## ✍️ Fonts

### IBM Plex Sans (UI)
```css
--font-ui: 'IBM Plex Sans', sans-serif
```

**Use for:**
- Headers, titles
- Button text
- Labels
- Body copy
- All UI elements

```tsx
<div className="font-ui">Portfolio Dashboard</div>
// or
<div style={{ fontFamily: 'var(--font-ui)' }}>Portfolio Dashboard</div>
```

### IBM Plex Mono (Data)
```css
--font-data: 'IBM Plex Mono', monospace
```

**Use for:**
- Prices, values
- Asset IDs
- Timestamps
- Percentages
- Technical data

```tsx
<div className="font-data">$96.50</div>
// or
<div style={{ fontFamily: 'var(--font-data)' }}>$96.50</div>
```

---

## 🎭 Shadows

```css
--shadow-panel: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-elevated: 0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06);
--shadow-overlay: 0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05);
```

```tsx
// Card
<div style={{ boxShadow: 'var(--shadow-panel)' }}>

// Modal
<div style={{ boxShadow: 'var(--shadow-overlay)' }}>
```

---

## 📏 Common Patterns

### Status Badge
```tsx
const StatusBadge = ({ status }: { status: 'healthy' | 'warning' | 'critical' }) => {
  const colors = {
    healthy: { bg: 'var(--green-lt)', text: 'var(--green)' },
    warning: { bg: 'var(--amber-lt)', text: 'var(--amber)' },
    critical: { bg: 'var(--red-lt)', text: 'var(--red)' }
  };

  return (
    <span style={{
      background: colors[status].bg,
      color: colors[status].text,
      padding: '2px 8px',
      borderRadius: '12px',
      fontSize: '11px',
      fontWeight: 500,
      fontFamily: 'var(--font-data)'
    }}>
      {status.toUpperCase()}
    </span>
  );
};
```

### Price Display
```tsx
const PriceDisplay = ({ price, change }: { price: number; change: number }) => (
  <div className="font-data" style={{ fontSize: 20 }}>
    <span style={{ color: 'var(--color-text-primary)' }}>
      ${price.toFixed(2)}
    </span>
    <span style={{
      color: change > 0 ? 'var(--green)' : 'var(--red)',
      fontSize: 12,
      marginLeft: 8
    }}>
      {change > 0 ? '▲' : '▼'} {Math.abs(change).toFixed(2)}%
    </span>
  </div>
);
```

### Card Component
```tsx
const Card = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <div style={{
    background: 'var(--color-bg-elevated)',
    border: '1px solid var(--color-border-default)',
    borderRadius: '8px',
    padding: '16px',
    boxShadow: 'var(--shadow-panel)'
  }}>
    <h3 style={{
      fontFamily: 'var(--font-ui)',
      fontSize: '10px',
      fontWeight: 500,
      color: 'var(--color-text-secondary)',
      textTransform: 'uppercase',
      letterSpacing: '0.6px',
      marginBottom: '12px'
    }}>
      {title}
    </h3>
    {children}
  </div>
);
```

### Data Label + Value
```tsx
const Metric = ({ label, value, unit }: { label: string; value: string; unit?: string }) => (
  <div>
    <div style={{
      fontSize: '10px',
      color: 'var(--color-text-secondary)',
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
      marginBottom: '4px'
    }}>
      {label}
    </div>
    <div style={{
      fontFamily: 'var(--font-data)',
      fontSize: '24px',
      fontWeight: 500,
      color: 'var(--color-text-primary)'
    }}>
      {value}
      {unit && (
        <span style={{
          fontSize: '14px',
          color: 'var(--color-text-secondary)',
          fontWeight: 400,
          marginLeft: '4px'
        }}>
          {unit}
        </span>
      )}
    </div>
  </div>
);

// Usage:
<Metric label="VaR 95%" value="$22,317" />
<Metric label="Sharpe Ratio" value="1.85" />
```

---

## 🚦 DO's and DON'Ts

### ✅ DO
- Use CSS variables for all colors
- Use `font-data` for numbers, IDs, codes
- Use `font-ui` for UI text, labels
- Use status backgrounds for badges (`--green-lt`, `--amber-lt`, `--red-lt`)
- Use semantic color names (`--color-positive`, not direct hex)

### ❌ DON'T
- Don't hardcode hex colors
- Don't use `font-data` for paragraphs or body text
- Don't use pure white (#fff) for text on light backgrounds
- Don't mix Inter/JetBrains Mono with IBM Plex
- Don't use dark theme variables in light theme

---

## 🔍 Quick Find

**Need a color for...**
- Profit/Up? → `var(--green)` or `var(--color-positive)`
- Loss/Down? → `var(--red)` or `var(--color-negative)`
- Warning? → `var(--amber)` or `var(--color-warning)`
- Main text? → `var(--color-text-primary)`
- Label text? → `var(--color-text-secondary)`
- Timestamp? → `var(--color-text-tertiary)`
- Border? → `var(--color-border-default)`
- Background? → `var(--color-bg-elevated)`
- Accent/CTA? → `var(--db-red)`

**Need a font for...**
- Price/number? → `var(--font-data)` or `className="font-data"`
- Button/label? → `var(--font-ui)` or `className="font-ui"`
- Asset ID? → `var(--font-data)`
- Header? → `var(--font-ui)`

---

## 📚 More Resources

- Full design system: `docs/DESIGN_SYSTEM_UPDATE.md`
- All tokens: `app/frontend/src/styles/tokens.css`
- Global styles: `app/frontend/src/styles/global.css`
- Typography: `app/frontend/src/styles/typography.css`

---

**Last Updated**: 2026-03-22
