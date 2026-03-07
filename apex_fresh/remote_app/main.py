from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="APEX Fresh Remote App", version="1.0.0")
PERSONAS = {"dispatch", "trader", "risk", "quant", "portfolio"}
PERSONA_LABELS = {
    "dispatch": "Dispatch Console",
    "trader": "Trading Analytics",
    "risk": "Risk Dashboard",
    "quant": "Quant Console",
    "portfolio": "Portfolio Dashboard",
}
MARKET_CONTEXT = {
    "ANZ": {
        "currency": "A$",
        "nodes": ["NSW1", "SA1", "VIC1"],
        "source": "ALIGNE_SIM",
    },
    "EU": {
        "currency": "€",
        "nodes": ["DE-LU", "FR", "NL"],
        "source": "ENDUR_SIM",
    },
    "US": {
        "currency": "$",
        "nodes": ["West Hub", "Houston", "North Hub"],
        "source": "TRIPLE_POINT_SIM",
    },
}


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "theme": "option-d",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _render_page("ANZ")


@app.get("/anz", response_class=HTMLResponse)
def anz_page() -> str:
    return _render_page("ANZ")


@app.get("/eu", response_class=HTMLResponse)
def eu_page() -> str:
    return _render_page("EU")


@app.get("/us", response_class=HTMLResponse)
def us_page() -> str:
    return _render_page("US")


@app.get("/anz/{persona}", response_class=HTMLResponse)
def anz_workspace(persona: str) -> str:
    return _render_workspace("ANZ", persona)


@app.get("/eu/{persona}", response_class=HTMLResponse)
def eu_workspace(persona: str) -> str:
    return _render_workspace("EU", persona)


@app.get("/us/{persona}", response_class=HTMLResponse)
def us_workspace(persona: str) -> str:
    return _render_workspace("US", persona)


def _render_page(selected_market: str) -> str:
    html = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>APEX Fresh</title>
  <style>
    body { margin: 0; font-family: Inter, sans-serif; background: #13181D; color: #E2E8F0; }
    .topbar { height: 48px; display: flex; align-items: center; justify-content: space-between;
      padding: 0 24px; background: #1B1F23; border-bottom: 1px solid #2A3038; }
    .wordmark { color: #FF6B6B; font-family: monospace; letter-spacing: .2em; font-size: 16px; }
    .wrap { padding: 24px; }
    .panel { background: #1F2429; border: 1px solid #2A3038; border-radius: 6px; padding: 16px; }
    .muted { color: #E2E8F0; font-size: 13px; font-weight: 500; }
    .selector { display: flex; gap: 8px; margin: 14px 0 16px; }
    .tab {
      padding: 7px 14px; font-size: 12px; border-radius: 4px;
      border: 1px solid #5B6677; color: #E2E8F0; background: transparent; cursor: pointer;
      text-decoration: none; display: inline-block;
    }
    .tab.active { border-color: #FF6B6B; color: #FFFFFF; background: #FF6B6B; }
    .market-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-top: 12px; }
    .market-card { background: #22272C; border: 1px solid #343C47; border-radius: 6px; padding: 10px 12px; }
    .market-card h4 { margin: 0; font-size: 11px; letter-spacing: .08em; color: #E2E8F0; text-transform: uppercase; }
    .market-card .v { margin-top: 6px; font-family: monospace; font-size: 15px; color: #E2E8F0; }
    .market-card .d { margin-top: 3px; font-size: 11px; }
    .up { color: #34D399; } .down { color: #FF6B6B; }
  </style>
</head>
<body>
  <div class="topbar">
    <div class="wordmark">APEX</div>
    <div class="muted">Option D • Slate + Coral</div>
  </div>
  <div class="wrap">
    <div class="panel">
      <h2>APEX Fresh Remote App</h2>
      <p class="muted">Deployed with Databricks CLI on fe-vm as a new app.</p>
      <div class="selector">
        <a class="tab __ANZ_ACTIVE__" id="tab-ANZ" href="/anz">ANZ</a>
        <a class="tab __EU_ACTIVE__" id="tab-EU" href="/eu">EU</a>
        <a class="tab __US_ACTIVE__" id="tab-US" href="/us">US</a>
      </div>
      <p class="muted" id="market-blurb">ANZ selected: NEM focus, AUD settlement, FCAS-aware operations.</p>
      <div class="market-grid" id="market-grid"></div>
      <h3 style="margin:16px 0 8px;">Choose Workspace</h3>
      <div style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;">
        <a class="tab" style="text-align:center;" href="__MARKET_PATH__/dispatch">Dispatch</a>
        <a class="tab" style="text-align:center;" href="__MARKET_PATH__/trader">Trader</a>
        <a class="tab" style="text-align:center;" href="__MARKET_PATH__/risk">Risk</a>
        <a class="tab" style="text-align:center;" href="__MARKET_PATH__/quant">Quant</a>
        <a class="tab" style="text-align:center;" href="__MARKET_PATH__/portfolio">Portfolio</a>
      </div>
      <p><a href="/api/v1/health" style="color:#60A5FA">Open health endpoint</a></p>
    </div>
  </div>
  <script>
    const marketData = {
      ANZ: [
        { n: 'NSW1', v: 'A$94.20', d: '+1.8%', c: 'up' },
        { n: 'SA1', v: 'A$118.40', d: '-0.6%', c: 'down' },
        { n: 'VIC1', v: 'A$87.60', d: '+0.4%', c: 'up' }
      ],
      EU: [
        { n: 'DE-LU', v: '€68.10', d: '-1.2%', c: 'down' },
        { n: 'FR', v: '€66.80', d: '+0.7%', c: 'up' },
        { n: 'NL', v: '€71.30', d: '+0.2%', c: 'up' }
      ],
      US: [
        { n: 'West Hub', v: '$46.20', d: '+2.4%', c: 'up' },
        { n: 'Houston', v: '$50.80', d: '-0.8%', c: 'down' },
        { n: 'North Hub', v: '$43.40', d: '+0.9%', c: 'up' }
      ]
    };
    const blurbs = {
      ANZ: 'ANZ selected: NEM focus, AUD settlement, FCAS-aware operations.',
      EU: 'EU selected: EPEX day-ahead/intraday flow, EUR pricing context.',
      US: 'US selected: ERCOT nodal behavior, USD pricing, RTC+B context.'
    };
    function render(market) {
      document.getElementById('market-blurb').textContent = blurbs[market];
      const grid = document.getElementById('market-grid');
      grid.innerHTML = marketData[market].map(x => `
        <div class="market-card">
          <h4>${x.n}</h4>
          <div class="v">${x.v}</div>
          <div class="d ${x.c}">${x.d}</div>
        </div>
      `).join('');
      ['ANZ','EU','US'].forEach(m => {
        const el = document.getElementById('tab-' + m);
        if (m === market) el.classList.add('active');
        else el.classList.remove('active');
      });
    }
    render('__SELECTED_MARKET__');
  </script>
</body>
</html>
"""
    html = html.replace("__SELECTED_MARKET__", selected_market)
    market_path = "/anz" if selected_market == "ANZ" else "/eu" if selected_market == "EU" else "/us"
    html = html.replace("__MARKET_PATH__", market_path)
    html = html.replace("__ANZ_ACTIVE__", "active" if selected_market == "ANZ" else "")
    html = html.replace("__EU_ACTIVE__", "active" if selected_market == "EU" else "")
    html = html.replace("__US_ACTIVE__", "active" if selected_market == "US" else "")
    return html


def _render_workspace(market: str, persona: str) -> str:
    persona_key = persona.lower()
    if persona_key not in PERSONAS:
        return f"<h1>Unknown workspace: {persona}</h1><p><a href='/{market.lower()}'>Back</a></p>"

    market_path = "/" + market.lower()
    title = f"{market} - {PERSONA_LABELS[persona_key]}"
    ctx = MARKET_CONTEXT[market]
    currency = ctx["currency"]
    node_a, node_b, node_c = ctx["nodes"]
    source = ctx["source"]
    if persona_key == "dispatch":
        metric_1 = ("Fleet SOC Avg", "61.4%")
        metric_2 = ("Dispatch MW", "+182 MW")
        metric_3 = ("Next Interval", f"{currency}91.8/MWh")
        panel_a_title = "Asset Fleet Status"
        panel_a_body = (
            f"<ul><li>{node_a} Battery: SOC 68%, output +90 MW</li>"
            f"<li>{node_b} Battery: SOC 52%, output +61 MW</li>"
            f"<li>{node_c} Battery: SOC 44%, output +31 MW</li></ul>"
        )
        panel_b_title = "Offer Stack Preview"
        panel_b_body = (
            f"<table class='tbl'><tr><th>Band</th><th>Price</th><th>MW</th></tr>"
            f"<tr><td>1</td><td>{currency}82.0</td><td>40</td></tr>"
            f"<tr><td>2</td><td>{currency}94.5</td><td>60</td></tr>"
            f"<tr><td>3</td><td>{currency}118.0</td><td>80</td></tr></table>"
        )
    elif persona_key == "trader":
        metric_1 = ("Net Exposure", "+410 MW")
        metric_2 = ("MTM P&L", f"+{currency}718,920")
        metric_3 = ("Trades Today", "27")
        panel_a_title = "Position Snapshot"
        panel_a_body = (
            f"<ul><li>{node_a} Q1: +320 MW @ {currency}86.4</li>"
            f"<li>{node_b} Q1: -180 MW @ {currency}122.8</li>"
            f"<li>{node_c} Cal: +150 MW @ {currency}78.2</li></ul>"
        )
        panel_b_title = "Trade Blotter (Read-only)"
        panel_b_body = (
            f"<table class='tbl'><tr><th>Time</th><th>Instr</th><th>Dir</th><th>Vol</th></tr>"
            f"<tr><td>14:21</td><td>{node_a}</td><td>BUY</td><td>120</td></tr>"
            f"<tr><td>14:18</td><td>{node_b}</td><td>SELL</td><td>80</td></tr>"
            f"<tr><td>14:11</td><td>{node_c}</td><td>BUY</td><td>60</td></tr></table>"
        )
    elif persona_key == "risk":
        metric_1 = ("VaR 95%", f"{currency}1.24M")
        metric_2 = ("VaR 99%", f"{currency}2.07M")
        metric_3 = ("Limit Util.", "67%")
        panel_a_title = "Stress Scenarios"
        panel_a_body = (
            "<ul><li>Price spike: -A$480k impact</li>"
            "<li>Demand shock: -A$210k impact</li>"
            "<li>Volatility jump: -A$325k impact</li></ul>"
        )
        panel_b_title = "Limit Monitor"
        panel_b_body = (
            "<table class='tbl'><tr><th>Trader</th><th>Type</th><th>Util%</th></tr>"
            "<tr><td>S. Chen</td><td>VAR</td><td>58%</td></tr>"
            "<tr><td>E. Park</td><td>POSITION</td><td>81%</td></tr>"
            "<tr><td>Desk</td><td>CREDIT</td><td>94%</td></tr></table>"
        )
    elif persona_key == "quant":
        metric_1 = ("MAPE", "6.4%")
        metric_2 = ("RMSE", f"{currency}8.1")
        metric_3 = ("Backtests", "12 runs")
        panel_a_title = "Model Performance"
        panel_a_body = (
            f"<ul><li>{node_a}: MAPE 6.1%</li>"
            f"<li>{node_b}: MAPE 7.0%</li>"
            f"<li>{node_c}: MAPE 6.3%</li></ul>"
        )
        panel_b_title = "Backtest Summary"
        panel_b_body = (
            f"<table class='tbl'><tr><th>Strategy</th><th>P&L</th><th>Sharpe</th></tr>"
            f"<tr><td>Threshold</td><td>+{currency}432k</td><td>1.41</td></tr>"
            f"<tr><td>MA Cross</td><td>+{currency}388k</td><td>1.29</td></tr>"
            f"<tr><td>Spike Capture</td><td>+{currency}516k</td><td>1.55</td></tr></table>"
        )
    else:
        metric_1 = ("Fleet ARR", f"{currency}24.8M")
        metric_2 = ("Revenue/MW", f"{currency}132k")
        metric_3 = ("PPA MTM", f"+{currency}2.4M")
        panel_a_title = "Revenue Stacking"
        panel_a_body = (
            "<ul><li>Energy: 44%</li>"
            "<li>Ancillary/FCAS: 29%</li>"
            "<li>Hedges/PPA: 27%</li></ul>"
        )
        panel_b_title = "PPA Book"
        panel_b_body = (
            f"<table class='tbl'><tr><th>PPA</th><th>MW</th><th>MTM</th></tr>"
            f"<tr><td>PPA-001</td><td>100</td><td>+{currency}820k</td></tr>"
            f"<tr><td>PPA-002</td><td>80</td><td>+{currency}610k</td></tr>"
            f"<tr><td>PPA-003</td><td>60</td><td>+{currency}420k</td></tr></table>"
        )

    nav = [
        ("dispatch", "Dispatch Console"),
        ("trader", "Trading Analytics"),
        ("risk", "Risk Dashboard"),
        ("quant", "Quant Console"),
        ("portfolio", "Portfolio Dashboard"),
    ]
    nav_links = "".join(
        f"<a href='{market_path}/{key}' style='display:block;padding:8px 12px;color:{'#FFFFFF' if key==persona_key else '#8896AA'};"
        f"text-decoration:none;border-left:2px solid {'#FF6B6B' if key==persona_key else 'transparent'};"
        f"background:{'#22272C' if key==persona_key else 'transparent'}'>{label}</a>"
        for key, label in nav
    )

    return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    body {{ margin:0; font-family: Inter, sans-serif; background:#13181D; color:#E2E8F0; }}
    .topbar {{ height:48px; display:flex; align-items:center; justify-content:space-between; padding:0 24px; background:#1B1F23; border-bottom:1px solid #2A3038; }}
    .wordmark {{ color:#FF6B6B; font-family:monospace; letter-spacing:.2em; font-size:16px; text-decoration:none; }}
    .workspace {{ display:flex; height:calc(100vh - 48px); }}
    .sidebar {{ width:220px; background:#1B1F23; border-right:1px solid #2A3038; padding-top:12px; }}
    .main {{ flex:1; padding:24px; }}
    .panel {{ background:#1F2429; border:1px solid #2A3038; border-radius:6px; padding:16px; }}
    .muted {{ color:#E2E8F0; font-size:13px; font-weight:500; }}
    .chip {{ display:inline-block; padding:4px 10px; border-radius:4px; background:#2D333B; border:1px solid #5B6677; margin-right:8px; }}
    .metrics {{ display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap:10px; margin:12px 0 14px; }}
    .metric {{ background:#22272C; border:1px solid #343C47; border-radius:6px; padding:10px 12px; }}
    .metric .k {{ font-size:10px; letter-spacing:.08em; text-transform:uppercase; color:#E2E8F0; }}
    .metric .v {{ margin-top:4px; font-family:monospace; font-size:17px; color:#FFFFFF; }}
    .grid2 {{ display:grid; grid-template-columns: 1fr 1fr; gap:10px; }}
    .tbl {{ width:100%; border-collapse:collapse; font-size:12px; }}
    .tbl th, .tbl td {{ border-bottom:1px solid #343C47; padding:6px 8px; text-align:left; color:#E2E8F0; }}
    .tbl th {{ font-size:10px; letter-spacing:.08em; text-transform:uppercase; }}
  </style>
</head>
<body>
  <div class="topbar">
    <a class="wordmark" href="{market_path}">APEX</a>
    <div class="muted">{market} • {persona_key.title()}</div>
  </div>
  <div class="workspace">
    <aside class="sidebar">
      <div style="padding:0 12px 10px;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#4A5568;">Workspaces</div>
      {nav_links}
    </aside>
    <main class="main">
      <div class="panel">
        <h2 style="margin:0 0 8px;">{title}</h2>
        <p class="muted" style="margin:0 0 10px;">Market-scoped {persona_key} view with real content. Source system: {source}.</p>
        <div class="metrics">
          <div class="metric"><div class="k">{metric_1[0]}</div><div class="v">{metric_1[1]}</div></div>
          <div class="metric"><div class="k">{metric_2[0]}</div><div class="v">{metric_2[1]}</div></div>
          <div class="metric"><div class="k">{metric_3[0]}</div><div class="v">{metric_3[1]}</div></div>
        </div>
        <div class="grid2">
          <div class="panel">
            <h3 style="margin:0 0 8px;">{panel_a_title}</h3>
            {panel_a_body}
          </div>
          <div class="panel">
            <h3 style="margin:0 0 8px;">{panel_b_title}</h3>
            {panel_b_body}
          </div>
        </div>
        <div style="margin-top:12px;">
          <span class="chip">Market: {market}</span>
          <span class="chip">Persona: {persona_key.title()}</span>
          <span class="chip"><a href="{market_path}" style="color:#60A5FA;">Back to market home</a></span>
        </div>
      </div>
    </main>
  </div>
</body>
</html>
"""

