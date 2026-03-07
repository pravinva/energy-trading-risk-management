# Data Seeding

Seed files are organized by region under `data/seeds/` and DDL lives in `data/schema/`.
Use these commands after seed scripts are added in later prompts:

1. Validate schema SQL files are present in `data/schema/`.
2. Run regional seed loaders in order: ANZ, Europe, Americas.
3. Verify row counts and basic quality checks in Databricks SQL.
