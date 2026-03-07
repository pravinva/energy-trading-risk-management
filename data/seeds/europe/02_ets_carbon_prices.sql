DELETE FROM serverless_sandbox_tladem_catalog.nexus_europe.ets_carbon_prices;
INSERT INTO serverless_sandbox_tladem_catalog.nexus_europe.ets_carbon_prices
SELECT d, cast(65 + (rand()-0.5)*20 as decimal(10,4)), cast(50000 + rand()*150000 as decimal(16,2)), 'EEX', 'SIMULATED'
FROM (SELECT explode(sequence(date'2024-01-01', date'2026-03-01', interval 1 day)) as d) x;
