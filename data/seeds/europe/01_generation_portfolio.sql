DELETE FROM serverless_sandbox_tladem_catalog.nexus_europe.generation_portfolio;
INSERT INTO serverless_sandbox_tladem_catalog.nexus_europe.generation_portfolio
SELECT concat('EU_ASSET_', lpad(cast(id as string), 3, '0')),
       concat('European Asset ', cast(id as string)),
       CASE WHEN id % 5 = 0 THEN 'EDF' WHEN id % 5 = 1 THEN 'Engie' WHEN id % 5 = 2 THEN 'RWE' WHEN id % 5 = 3 THEN 'Iberdrola' ELSE 'Statkraft' END,
       CASE WHEN id % 6 = 0 THEN 'DE' WHEN id % 6 = 1 THEN 'FR' WHEN id % 6 = 2 THEN 'NL' WHEN id % 6 = 3 THEN 'BE' WHEN id % 6 = 4 THEN 'ES' ELSE 'NO' END,
       CASE WHEN id <= 6 THEN 'Gas' WHEN id <= 10 THEN 'Nuclear' WHEN id <= 15 THEN 'Wind' WHEN id <= 20 THEN 'Solar' WHEN id <= 23 THEN 'Hydro' ELSE 'Coal' END,
       cast(100 + rand()*1500 as decimal(10,2)), 2000 + cast(rand()*24 as int), CASE WHEN id <= 6 THEN true ELSE false END
FROM range(1,26);
