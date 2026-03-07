export type Market = "NEM" | "EPEX" | "ERCOT";
export type Persona = "dispatch" | "trader" | "risk" | "quant" | "portfolio";

export const GENIE_SPACE_IDS: Record<Market, string> = {
  NEM: "apex-genie-nem",
  EPEX: "apex-genie-epex",
  ERCOT: "apex-genie-ercot",
};

export const GENIE_QUESTIONS_FALLBACK: Record<Market, Record<Persona, string[]>> = {
  NEM: {
    dispatch: ["What is the SOC of all BESS assets above 70%?"],
    trader: ["Show aggregate long exposure across all NEM regions"],
    risk: ["What is our current net position in SA1 for Q1 2026?"],
    quant: ["What is the MAPE of the NSW1 5-minute forecast this week?"],
    portfolio: ["Which BESS asset generated the most FCAS revenue last quarter?"],
  },
  EPEX: {
    dispatch: ["Which EPEX BESS asset has the highest current SOC?"],
    trader: ["Which EPEX zone had the most negative price hours last month?"],
    risk: ["How has our P&L changed since the MTU changed to 15 minutes?"],
    quant: ["How does forecast error vary by condition bucket?"],
    portfolio: ["What is the revenue per MW for our European BESS fleet?"],
  },
  ERCOT: {
    dispatch: ["What is the current RTC+B signal vs day-ahead price for West Hub?"],
    trader: ["Which dispatch interval had the highest LMP at West Hub this week?"],
    risk: ["What was our P&L before vs after RTC+B went live?"],
    quant: ["Does backtest perform better using RTC+B signal?"],
    portfolio: ["Show RTC+B revenue contribution per ERCOT BESS asset"],
  },
};

