DELETE FROM serverless_sandbox_tladem_catalog.nexus_anz.settlement_revenues;
INSERT INTO serverless_sandbox_tladem_catalog.nexus_anz.settlement_revenues
SELECT row_number() OVER (ORDER BY settlement_date, duid), duid, settlement_date, timestamp(settlement_date),
       cast(energy_revenue as decimal(14,4)), cast(fcas_raise5 as decimal(14,4)), cast(fcas_lower5 as decimal(14,4)),
       cast(fcas_raise60 as decimal(14,4)), cast(fcas_lower60 as decimal(14,4)),
       cast(fcas_raise6 as decimal(14,4)), cast(fcas_lower6 as decimal(14,4)),
       cast(energy_revenue+fcas_raise5+fcas_lower5+fcas_raise60+fcas_lower60+fcas_raise6+fcas_lower6 as decimal(14,4)),
       cast(1.0 + rand()*0.1 as decimal(8,6)), 'SIMULATED'
FROM (
  SELECT d.settlement_date, a.duid,
         (2000 + rand()*12000) * (CASE WHEN rand()>0.93 THEN 6+rand()*4 ELSE 1 END) as energy_revenue,
         500 + rand()*3000 as fcas_raise5,
         500 + rand()*3000 as fcas_lower5,
         300 + rand()*2000 as fcas_raise60,
         300 + rand()*2000 as fcas_lower60,
         300 + rand()*2500 as fcas_raise6,
         300 + rand()*2500 as fcas_lower6
  FROM (SELECT explode(sequence(date'2025-01-01', date'2026-03-01', interval 1 day)) as settlement_date) d
  CROSS JOIN (SELECT duid FROM serverless_sandbox_tladem_catalog.nexus_anz.bess_assets) a
) r;
