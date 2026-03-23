# APEX ETRM Architecture Diagrams

This directory contains two Databricks architecture diagrams for the APEX Energy Trading & Risk Management platform, generated using Bricksmith (nanobanana).

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

### 2. Architect-Level Architecture
**File:** `apex_etrm_architect_architecture.png`
**Audience:** Solutions architects, technical leads, data engineers
**Purpose:** Comprehensive technical architecture showing all Databricks components

**Highlights:**
- 6 detailed technical zones covering the complete data and application lifecycle
- Medallion architecture (Bronze/Silver/Gold) with Unity Catalog governance
- ML model factory with MLflow tracking and lineage
- Specific Databricks services: Workflows, SQL Warehouse, Apps, Unity Catalog
- Technical details: Monte Carlo VaR (10,000 paths), LSTM/Gradient Boosting models, REST APIs

**Technical Components:**
- **Zone 1:** External Market Data Sources (NEM AEMO, ERCOT, EPEX feeds)
- **Zone 2:** Data Ingestion & Lakehouse Foundation (Medallion + Unity Catalog)
- **Zone 3:** ML Model Factory (Feature engineering, MLflow, forecasting pipelines)
- **Zone 4:** Trading Analytics & Risk Engines (VaR, backtesting, BESS optimization)
- **Zone 5:** Application Delivery (Databricks Apps with React + FastAPI)
- **Zone 6:** Orchestration, Monitoring & Governance (Workflows, data quality, audit logs)

## Generation Details

**Tool:** Bricksmith (nanobanana) - AI-powered Databricks architecture diagram generator
**Generator:** Gemini 2.5 Flash Image
**Date Generated:** 2026-03-23
**MLflow Experiment:** bricksmith-local

**Run IDs:**
- Executive: `apex-etrm-exec-v1`
- Architect: `apex-etrm-architect-v1`

## Source Prompts

The detailed prompts used to generate these diagrams are stored in:
- `~/Documents/Demo/bricksmith/prompts/apex_etrm_executive_architecture.txt`
- `~/Documents/Demo/bricksmith/prompts/apex_etrm_architect_architecture.txt`

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
1. **ML-Powered Forecasting:** Gradient Boosting + LSTM models with MLflow tracking
2. **Risk Analytics:** Monte Carlo VaR with 10,000 simulation paths
3. **Strategy Backtesting:** Mean reversion, momentum, arbitrage strategies
4. **BESS Dispatch:** Battery Energy Storage System optimization
5. **Multi-Persona Workspace:** Trader, Risk Manager, Quant Analyst, Dispatch Operator

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
