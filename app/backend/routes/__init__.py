from fastapi import APIRouter
from .health import router as health_router
from .user import router as user_router
from .anz import router as anz_router
from .europe import router as europe_router
from .americas import router as americas_router
from .gtm import router as gtm_router
from .market import router as market_router
from .trades import router as trades_router
from .positions import router as positions_router
from .dispatch import router as dispatch_router
from .risk import router as risk_router
from .portfolio import router as portfolio_router
from .analytics import router as analytics_router
from .forecasting import router as forecasting_router
from .strategies import router as strategies_router

router = APIRouter()
router.include_router(health_router)
router.include_router(user_router)
router.include_router(anz_router)
router.include_router(europe_router)
router.include_router(americas_router)
router.include_router(gtm_router)
router.include_router(market_router)
router.include_router(trades_router)
router.include_router(positions_router)
router.include_router(dispatch_router)
router.include_router(risk_router)
router.include_router(portfolio_router)
router.include_router(analytics_router)
router.include_router(forecasting_router)
router.include_router(strategies_router)
