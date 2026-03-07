SELECT trade_id, trader, instrument, side, volume_mw, price, counterparty, trade_time
FROM apex.trading.trades
ORDER BY trade_time DESC
LIMIT 1000;
