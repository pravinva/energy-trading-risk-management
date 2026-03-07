from fastapi import APIRouter

from . import analytics, dispatch, genie, health, market, portfolio, positions, risk, trades, user

router = APIRouter()
router.include_router(health.router)
router.include_router(user.router)
router.include_router(market.router)
router.include_router(trades.router)
router.include_router(positions.router)
router.include_router(dispatch.router)
router.include_router(risk.router)
router.include_router(portfolio.router)
router.include_router(analytics.router)
router.include_router(genie.router)

