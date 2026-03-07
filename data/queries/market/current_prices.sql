SELECT market, instrument, price, change_pct, timestamp
FROM apex.analytics.market_live_prices
ORDER BY market, instrument;
