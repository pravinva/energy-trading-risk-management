# APEX ETRM Architecture Diagrams

This directory contains Databricks architecture diagrams for the APEX Energy Trading & Risk Management platform, generated using Bricksmith (nanobanana).

## Diagrams

### 1. Executive-Level Architecture
**File:** `apex_etrm_executive_architecture.png`
**Audience:** Board members, executives, business stakeholders
**Purpose:** High-level business view emphasizing strategic value and decision flow

**Highlights:**
- 5 business-focused zones: Market Data → Intelligence Platform → Forecasting → Applications → Business Decisions
- Emphasis on business outcomes: Trading decisions, risk management, portfolio optimization
- Cross-cutting governance and dual-speed operations (real-time + batch)
- Clean, minimal design with executive-friendly language

**Key Messages:**
- One unified platform powering trading decisions across three global markets (NEM, ERCOT, EPEX)
- ML-powered forecasting reduces risk and improves trading performance
- Governed, auditable flow from market signals to profitable trades

### 2. Architect-Level Architecture (CURRENT)
**File:** `apex_etrm_architect_architecture_v2.png` ⭐ **LATEST**
**Audience:** Solutions architects, technical leads, data engineers
**Purpose:** Comprehensive technical architecture showing all Databricks components

**Highlights:**
- 6 detailed technical zones covering the complete data and application lifecycle
- Medallion architecture (Bronze/Silver/Gold) with Unity Catalog governance
- ML model factory with MLflow tracking and automated retraining
- **NEW:** 7 scheduled Databricks Workflows (3 real-time + 4 daily batch)
- **NEW:** 5 specialized personas with market-specific navigation
- **NEW:** Automated model drift monitoring and EOD reconciliation
- Specific Databricks services: Workflows, SQL Warehouse, Apps, Unity Catalog
- Technical details: Monte Carlo VaR (10,000 paths), AutoML, REST APIs

**Technical Components:**
- **Zone 1:** External Market Data Sources (NEM AEMO, ERCOT, EPEX feeds)
- **Zone 2:** Data Ingestion & Lakehouse Foundation (Medallion + Unity Catalog)
- **Zone 3:** ML Model Factory (Feature engineering, MLflow, forecasting pipelines, AutoML)
- **Zone 4:** Trading Analytics & Risk Engines (VaR, backtesting, BESS optimization, drift monitoring)
- **Zone 5:** Application Delivery (5 personas: Dispatch, Trader, Risk, Quant, Portfolio)
- **Zone 6:** Orchestration, Monitoring & Governance (7 workflows, data quality, audit logs)

**What's New in V2:**
- ✅ Automated daily model training workflow (6:00 AM UTC)
- ✅ Overnight VaR batch calculation (2:00 AM UTC)
- ✅ End-of-day trade reconciliation (5:00 PM UTC)
- ✅ Model drift monitoring with retraining alerts (8:00 AM UTC)
- ✅ Market-specific persona sidebars (NEM: FCAS, ERCOT: Ancillary Services, EPEX: Market Coupling)
- ✅ 5 specialized personas (added Portfolio Manager)
- ✅ Real-time session P&L tracking

**V3 Accuracy Update (2026-03-23):**
- 🔧 Corrected ML model description: Removed LSTM reference (not implemented)
- 🔧 Updated to reflect actual implementation: XGBoost, LightGBM, Random Forest via AutoML
- 🔧 All other technical claims verified against codebase (AutoML, champion/challenger, feature hash tracking)

### 3. Architect-Level Architecture (V1 - Deprecated)
**File:** `apex_etrm_architect_architecture.png`
**Status:** Superseded by V2
**Date:** 2026-03-23 (original)

## Generation Details

**Tool:** Bricksmith (nanobanana) - AI-powered Databricks architecture diagram generator
**Generator:** Gemini 2.5 Flash Image
**MLflow Experiment:** bricksmith-local

**Run IDs:**
- Executive: `apex-etrm-exec-v1` (2026-03-23)
- Architect V1: `apex-etrm-architect-v1` (2026-03-23)
- Architect V2: `apex-etrm-architect-v2` (2026-03-23) - Updated V3 (2026-03-23) ⭐ **LATEST**

## Source Prompts

The detailed prompts used to generate these diagrams are stored in:
- `~/Documents/Demo/bricksmith/prompts/apex_etrm_executive_architecture.txt`
- `~/Documents/Demo/bricksmith/prompts/apex_etrm_architect_architecture.txt` (V1)
- `~/Documents/Demo/bricksmith/prompts/apex_etrm_architect_architecture_v2.txt` (V2 - current)

## Regeneration

To regenerate or refine these diagrams:

```bash
cd ~/Documents/Demo/bricksmith
source .venv/bin/activate
source .env

# Executive diagram
bricksmith generate-raw --prompt-file prompts/apex_etrm_executive_architecture.txt --logo-dir logos/default --run-name "apex-etrm-exec-v2"

# Architect diagram
bricksmith generate-raw --prompt-file prompts/apex_etrm_architect_architecture.txt --logo-dir logos/default --run-name "apex-etrm-architect-v2"
```

## Diagram Usage

These diagrams are designed for:
- **Executive presentations:** Board meetings, stakeholder reviews, funding proposals
- **Technical documentation:** Solution design documents, architecture reviews
- **Sales enablement:** Customer presentations, RFP responses
- **Internal alignment:** Cross-team communication, onboarding new team members

## Architecture Highlights

### Multi-Market Coverage
- **NEM (Australia):** National Electricity Market
- **ERCOT (Texas):** Electric Reliability Council of Texas
- **EPEX (Europe):** European Power Exchange

### Core Capabilities
1. **ML-Powered Forecasting:** AutoML (XGBoost, LightGBM, Random Forest) with MLflow tracking and champion/challenger testing
2. **Risk Analytics:** Monte Carlo VaR with 10,000 simulation paths
3. **Strategy Backtesting:** Mean reversion, momentum, arbitrage strategies
4. **BESS Dispatch:** Battery Energy Storage System optimization
5. **Multi-Persona Workspace:** Dispatch Operator, Trader, Risk Manager, Quant Analyst, Portfolio Manager

### Databricks Services Used
- **Unity Catalog:** Data governance and access controls
- **Lakehouse:** Medallion architecture (Bronze/Silver/Gold)
- **SQL Warehouse:** Interactive analytics (Medium warehouse)
- **Workflows:** Job orchestration and scheduling
- **Apps:** React + FastAPI application delivery
- **MLflow:** Model tracking, versioning, and registry

## Contact

For questions about these diagrams or the APEX architecture:
- Architecture Lead: Pravin Varma (pravin.varma@databricks.com)
- Platform: Databricks (e2-demo-field-eng workspace)
