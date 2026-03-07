SELECT ppa_id, counterparty, volume_mw, strike_price, tenor_years
FROM apex.portfolio.ppa_book
ORDER BY ppa_id;
