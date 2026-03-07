import { Outlet, RootRoute, Route, Router } from '@tanstack/react-router';
import { ApexWorkspaceLayout } from '@/layouts/ApexWorkspaceLayout';
import { AmericasLayout } from '@/layouts/AmericasLayout';
import { ANZLayout } from '@/layouts/ANZLayout';
import { EuropeLayout } from '@/layouts/EuropeLayout';
import { PersonaSelector } from '@/pages/PersonaSelector';
import { EPEXPersonaEntry, ERCOTPersonaEntry, NEMPersonaEntry } from '@/pages/MarketPersonaEntry';
import { RegionSelector } from '@/pages/RegionSelector';
import { CreditExposure, DispatchConsole, LimitMonitor, PortfolioDashboard, QuantConsole, RiskDashboard, StressTesting, TradingBlotter } from '@/pages/apex';
import { AmericasBESSIntelligence, AmericasETRMPositioning, AmericasMarketDashboard } from '@/pages/americas';
import { ANZBESSIntelligence, ANZETRMPositioning, ANZMarketDashboard } from '@/pages/anz';
import { EuropeETRMPositioning, EuropeMarketDashboard, EuropePortfolioIntelligence } from '@/pages/europe';

const rootRoute = new RootRoute({ component: () => <Outlet /> });
const indexRoute = new Route({ getParentRoute: () => rootRoute, path: '/', component: RegionSelector });
const nemPersonaRoute = new Route({ getParentRoute: () => rootRoute, path: '/nem', component: NEMPersonaEntry });
const epexPersonaRoute = new Route({ getParentRoute: () => rootRoute, path: '/epex', component: EPEXPersonaEntry });
const ercotPersonaRoute = new Route({ getParentRoute: () => rootRoute, path: '/ercot', component: ERCOTPersonaEntry });
const apexRoute = new Route({ getParentRoute: () => rootRoute, path: '/workspace', component: ApexWorkspaceLayout });
const dispatchRoute = new Route({ getParentRoute: () => apexRoute, path: '/dispatch', component: DispatchConsole });
const tradingRoute = new Route({ getParentRoute: () => apexRoute, path: '/trading', component: TradingBlotter });
const riskRoute = new Route({ getParentRoute: () => apexRoute, path: '/risk', component: RiskDashboard });
const stressTestingRoute = new Route({ getParentRoute: () => apexRoute, path: '/risk/stress-testing', component: StressTesting });
const limitMonitorRoute = new Route({ getParentRoute: () => apexRoute, path: '/risk/limit-monitor', component: LimitMonitor });
const creditExposureRoute = new Route({ getParentRoute: () => apexRoute, path: '/risk/credit-exposure', component: CreditExposure });
const quantRoute = new Route({ getParentRoute: () => apexRoute, path: '/quant', component: QuantConsole });
const portfolioRoute = new Route({ getParentRoute: () => apexRoute, path: '/portfolio', component: PortfolioDashboard });
const regionsIndexRoute = new Route({ getParentRoute: () => rootRoute, path: '/regions', component: RegionSelector });
const legacyPersonaRoute = new Route({ getParentRoute: () => rootRoute, path: '/personas', component: PersonaSelector });
const anzRoute = new Route({ getParentRoute: () => rootRoute, path: '/anz', component: ANZLayout });
const anzIndex = new Route({ getParentRoute: () => anzRoute, path: '/', component: ANZMarketDashboard });
const anzMarket = new Route({ getParentRoute: () => anzRoute, path: '/market', component: ANZMarketDashboard });
const anzBess = new Route({ getParentRoute: () => anzRoute, path: '/bess', component: ANZBESSIntelligence });
const anzEtrm = new Route({ getParentRoute: () => anzRoute, path: '/etrm', component: ANZETRMPositioning });
const europeRoute = new Route({ getParentRoute: () => rootRoute, path: '/europe', component: EuropeLayout });
const europeIndex = new Route({ getParentRoute: () => europeRoute, path: '/', component: EuropeMarketDashboard });
const europeMarket = new Route({ getParentRoute: () => europeRoute, path: '/market', component: EuropeMarketDashboard });
const europePortfolio = new Route({ getParentRoute: () => europeRoute, path: '/portfolio', component: EuropePortfolioIntelligence });
const europeEtrm = new Route({ getParentRoute: () => europeRoute, path: '/etrm', component: EuropeETRMPositioning });
const americasRoute = new Route({ getParentRoute: () => rootRoute, path: '/americas', component: AmericasLayout });
const americasIndex = new Route({ getParentRoute: () => americasRoute, path: '/', component: AmericasMarketDashboard });
const americasMarket = new Route({ getParentRoute: () => americasRoute, path: '/market', component: AmericasMarketDashboard });
const americasBess = new Route({ getParentRoute: () => americasRoute, path: '/bess', component: AmericasBESSIntelligence });
const americasEtrm = new Route({ getParentRoute: () => americasRoute, path: '/etrm', component: AmericasETRMPositioning });
const routeTree = rootRoute.addChildren([
  indexRoute,
  nemPersonaRoute,
  epexPersonaRoute,
  ercotPersonaRoute,
  legacyPersonaRoute,
  regionsIndexRoute,
  apexRoute.addChildren([dispatchRoute, tradingRoute, riskRoute, stressTestingRoute, limitMonitorRoute, creditExposureRoute, quantRoute, portfolioRoute]),
  anzRoute.addChildren([anzIndex, anzMarket, anzBess, anzEtrm]),
  europeRoute.addChildren([europeIndex, europeMarket, europePortfolio, europeEtrm]),
  americasRoute.addChildren([americasIndex, americasMarket, americasBess, americasEtrm]),
]);
export const router = new Router({ routeTree });
declare module '@tanstack/react-router' { interface Register { router: typeof router; } }
