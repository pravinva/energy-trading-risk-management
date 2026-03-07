from __future__ import annotations
from datetime import date, datetime, timedelta, timezone
import random


def _ts(minutes_back: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=minutes_back)


def anz_prices_current() -> list[dict[str, object]]:
    rows = []
    for rid, base in [('QLD', 84.5), ('NSW', 93.1), ('VIC', 97.3), ('SA', 109.7)]:
        prev = base - random.uniform(-3, 3)
        ch = base - prev
        rows.append({'region_id': rid, 'rrp': round(base, 2), 'change_vs_prev': round(ch, 2), 'pct_change': round((ch / prev) * 100 if prev else 0, 2), 'is_spike': base > 1000})
    return rows


def anz_price_history(hours: int = 24, region_id: str | None = None) -> list[dict[str, object]]:
    regions = [region_id] if region_id else ['QLD', 'NSW', 'VIC', 'SA']
    out: list[dict[str, object]] = []
    for reg in regions:
        for i in range(hours * 12):
            t = _ts(i * 5)
            rrp = 90 + random.uniform(-30, 40) + (8 if reg == 'SA' else 0)
            out.append({'interval_datetime': t, 'region_id': reg, 'rrp': round(rrp, 2), 'totaldemand': round(6800 + random.uniform(-500, 500), 2), 'raise5min': round(random.uniform(3, 10), 2), 'lower5min': round(random.uniform(3, 10), 2), 'raisereg': round(random.uniform(1, 6), 2), 'lowerreg': round(random.uniform(1, 6), 2)})
    return sorted(out, key=lambda x: x['interval_datetime'])


def anz_fleet() -> list[dict[str, object]]:
    assets = [
        ('HORNSDALE_1', 'Hornsdale Power Reserve Stage 1', 'Neoen', 'SA', 150.0, 2.0),
        ('WARATAH_1', 'Waratah Super Battery', 'Akaysha Energy', 'NSW', 500.0, 2.0),
        ('BLYTH_1', 'Blyth BESS', 'Neoen', 'SA', 238.5, 2.0),
        ('LATROBE_1', 'LaTrobe Valley BESS', 'Equis', 'VIC', 200.0, 2.0),
        ('BOULDERCOMBE_1', 'Bouldercombe BESS', 'AGL', 'QLD', 100.0, 2.0),
        ('TORRENS_B_BESS', 'Torrens Island B BESS', 'AGL', 'SA', 100.0, 2.0),
        ('DARLINGTON_PT', 'Darlington Point BESS', 'Origin Energy', 'NSW', 100.0, 2.0),
        ('ERARING_BESS_1', 'Eraring BESS Stage 1', 'Origin Energy', 'NSW', 460.0, 4.0),
    ]
    out = []
    for duid, name, op, region, cap, dur in assets:
        out.append({'duid': duid, 'asset_name': name, 'operator': op, 'region_id': region, 'capacity_mw': cap, 'duration_hours': dur, 'current_soc_pct': round(random.uniform(15, 95), 2), 'current_output_mw': round(random.uniform(-80, 120), 2), 'today_revenue': round(random.uniform(2000, 35000), 2), 'annual_revenue_ytd': round(random.uniform(300000, 2600000), 2)})
    return out


def anz_telemetry(duid: str, hours: int = 24) -> list[dict[str, object]]:
    out = []
    for i in range(hours * 12):
        t = _ts(i * 5)
        out.append({'recorded_at': t, 'state_of_charge_pct': round(random.uniform(10, 100), 2), 'output_mw': round(random.uniform(-90, 90), 2), 'fcas_raise_mw': round(random.uniform(3, 20), 2), 'fcas_lower_mw': round(random.uniform(3, 20), 2)})
    return sorted(out, key=lambda x: x['recorded_at'])


def anz_revenue(duid: str, days: int = 30) -> list[dict[str, object]]:
    out = []
    for i in range(days):
        d = (datetime.now(timezone.utc) - timedelta(days=i)).date()
        e = random.uniform(2000, 12000)
        f = random.uniform(1000, 10000)
        out.append({'settlement_date': d, 'energy_revenue': round(e, 2), 'fcas_total_revenue': round(f, 2), 'total_revenue': round(e + f, 2)})
    return sorted(out, key=lambda x: x['settlement_date'])


def anz_fcas_summary() -> list[dict[str, object]]:
    return [{'region_id': r, 'lower6sec_avg': round(random.uniform(2, 35), 2), 'raise6sec_avg': round(random.uniform(2, 35), 2), 'lowerreg_avg': round(random.uniform(1, 12), 2), 'raisereg_avg': round(random.uniform(1, 12), 2)} for r in ['QLD', 'NSW', 'VIC', 'SA']]


def anz_spikes(days: int = 90) -> list[dict[str, object]]:
    out = []
    for _ in range(14):
        start = datetime.now(timezone.utc) - timedelta(days=random.randint(1, days))
        dur = random.choice([5, 10, 15, 20, 25])
        out.append({'start_datetime': start, 'end_datetime': start + timedelta(minutes=dur), 'region_id': random.choice(['QLD', 'NSW', 'VIC', 'SA']), 'peak_rrp': round(random.uniform(1200, 13000), 2), 'duration_minutes': dur})
    return out


def europe_prices_current() -> list[dict[str, object]]:
    zones = ['DE-LU', 'FR', 'BE', 'NL', 'ES', 'NO1', 'NO2', 'CH']
    return [{'bidding_zone': z, 'delivery_datetime': datetime.now(timezone.utc), 'price_eur_mwh': round(random.uniform(30, 160), 2), 'volume_mwh': round(random.uniform(1000, 9000), 2), 'mtu_minutes': 15, 'is_negative': False} for z in zones]


def europe_history(zone: str | None, hours: int) -> list[dict[str, object]]:
    z = zone or 'DE-LU'
    out = []
    for i in range(hours):
        dt = datetime.now(timezone.utc) - timedelta(hours=i)
        price = round(random.uniform(20, 180), 2)
        out.append({'bidding_zone': z, 'delivery_datetime': dt, 'price_eur_mwh': price, 'volume_mwh': round(random.uniform(1000, 5000), 2), 'mtu_minutes': 15 if dt.date() >= date(2025, 9, 1) else 60, 'is_negative': price < 0})
    return sorted(out, key=lambda x: x['delivery_datetime'])


def europe_mix(zone: str) -> list[dict[str, object]]:
    vals = [('Nuclear', 42000 if zone == 'FR' else 8000), ('Gas', 12000), ('Wind Onshore', 15000), ('Solar', 9000), ('Hydro', 3500)]
    total = sum(v for _, v in vals)
    return [{'fuel_type': k, 'generation_mw': float(v), 'pct_of_total': round(v / total * 100, 2)} for k, v in vals]


def europe_spreads(zone: str) -> list[dict[str, object]]:
    out = []
    for i in range(30):
        dt = datetime.now(timezone.utc) - timedelta(days=i)
        power = random.uniform(55, 150)
        gas = random.uniform(20, 45)
        ets = random.uniform(50, 85)
        spark = power - gas * 0.45
        clean = spark - ets * 0.35
        out.append({'calculation_datetime': dt, 'power_price': round(power, 2), 'gas_price_mmbtu': round(gas, 2), 'ets_price': round(ets, 2), 'spark_spread': round(spark, 2), 'clean_spark_spread': round(clean, 2)})
    return sorted(out, key=lambda x: x['calculation_datetime'])


def europe_assets() -> list[dict[str, object]]:
    out = []
    for i in range(25):
        out.append({'asset_id': f'EU_ASSET_{i+1:03d}', 'asset_name': f'Generation Asset {i+1}', 'operator': random.choice(['EDF', 'Engie', 'RWE', 'Iberdrola']), 'country': random.choice(['DE', 'FR', 'BE', 'NL', 'ES', 'NO']), 'fuel_type': random.choice(['Gas', 'Nuclear', 'Wind', 'Solar', 'Hydro', 'Coal']), 'capacity_mw': round(random.uniform(120, 1600), 2), 'openlink_incumbent': i < 6})
    return out


def europe_flows() -> list[dict[str, object]]:
    corridors = [('DE', 'FR'), ('DE', 'NL'), ('DE', 'BE'), ('FR', 'BE'), ('FR', 'ES'), ('NO1', 'DE')]
    out = []
    for a, b in corridors:
        atc = random.uniform(1200, 3600)
        flow = random.uniform(atc * 0.5, atc * 1.03)
        util = flow / atc * 100
        out.append({'from_zone': a, 'to_zone': b, 'flow_mw': round(flow, 2), 'atc_mw': round(atc, 2), 'utilisation_pct': round(util, 2), 'is_constrained': util > 90})
    return sorted(out, key=lambda x: x['utilisation_pct'], reverse=True)


def europe_audit(zone: str, audit_date: str) -> list[dict[str, object]]:
    base = datetime.fromisoformat(audit_date).replace(tzinfo=timezone.utc)
    return [{'delivery_datetime': base + timedelta(hours=h), 'bidding_zone': zone, 'price_eur_mwh': round(random.uniform(35, 180), 2), 'data_source': 'SIMULATED', 'recorded_at': base + timedelta(hours=h-10)} for h in range(24)]


def americas_current(iso_id: str | None = None) -> list[dict[str, object]]:
    isos = ['ERCOT', 'PJM', 'CAISO', 'MISO', 'SPP', 'NYISO', 'ISONE', 'IESO', 'AESO']
    target = [iso_id] if iso_id else isos
    out = []
    for iso in target:
        lmp = random.uniform(20, 180)
        out.append({'iso_id': iso, 'node_id': f'{iso}_HUB', 'node_name': f'{iso} Hub', 'zone': 'HUB', 'lmp': round(lmp, 2), 'energy_component': round(lmp * 0.8, 2), 'congestion_component': 0.0 if iso == 'ERCOT' else round(lmp * 0.12, 2), 'loss_component': 0.0 if iso == 'ERCOT' else round(lmp * 0.08, 2), 'interval_datetime': datetime.now(timezone.utc)})
    return out


def americas_rtcb(resource_id: str) -> list[dict[str, object]]:
    return [{'period': 'pre_rtcb', 'avg_tb4_spread': 24.1, 'avg_drrs_mw': 0.0, 'avg_output_mw': 18.3, 'avg_soc_pct': 54.2, 'record_count': 1000}, {'period': 'post_rtcb', 'avg_tb4_spread': 31.9, 'avg_drrs_mw': 17.4, 'avg_output_mw': 25.1, 'avg_soc_pct': 57.4, 'record_count': 1020}]


def americas_pjm() -> list[dict[str, object]]:
    return [
        {'delivery_year': '2024/2025', 'clearing_price_mw_day': 28.92, 'total_cost_billions': 3.5, 'data_center_cost_pct': 0.0, 'price_cap_hit': False, 'reliability_shortfall_mw': 0.0, 'capacity_cost_per_mw_per_year': 28.92 * 365},
        {'delivery_year': '2025/2026', 'clearing_price_mw_day': 269.92, 'total_cost_billions': 16.1, 'data_center_cost_pct': 63.0, 'price_cap_hit': False, 'reliability_shortfall_mw': 0.0, 'capacity_cost_per_mw_per_year': 269.92 * 365},
        {'delivery_year': '2026/2027', 'clearing_price_mw_day': 329.17, 'total_cost_billions': 16.1, 'data_center_cost_pct': 40.0, 'price_cap_hit': False, 'reliability_shortfall_mw': 0.0, 'capacity_cost_per_mw_per_year': 329.17 * 365},
        {'delivery_year': '2027/2028', 'clearing_price_mw_day': 333.44, 'total_cost_billions': 16.4, 'data_center_cost_pct': 40.0, 'price_cap_hit': True, 'reliability_shortfall_mw': 6625.0, 'capacity_cost_per_mw_per_year': 333.44 * 365},
    ]


def americas_ieso_basis() -> list[dict[str, object]]:
    return [{'node_id': f'IESO_NODE_{i:03d}', 'node_name': f'Ontario Node {i}', 'avg_basis_spread': round(random.uniform(8, 28), 2), 'max_basis_spread': round(random.uniform(18, 45), 2), 'pct_hours_positive': round(random.uniform(55, 97), 2)} for i in range(1, 11)]


def americas_data_center(iso_id: str) -> list[dict[str, object]]:
    out = []
    for month in range(0, 12):
        m = (datetime.now(timezone.utc).replace(day=1) - timedelta(days=month * 30)).date().isoformat()
        out.append({'node_id': f'{iso_id}_DC_{month+1}', 'month_start': m, 'avg_lmp': round(random.uniform(45, 130), 2), 'avg_congestion': round(random.uniform(2, 25), 2), 'avg_basis_vs_hub': round(random.uniform(3, 18), 2)})
    return out


def americas_cross_iso() -> list[dict[str, object]]:
    out = []
    for d in range(30):
        dt = (datetime.now(timezone.utc) - timedelta(days=d)).date()
        pjm = random.uniform(35, 140)
        ercot = random.uniform(30, 145)
        spread = pjm - ercot
        out.append({'date': dt, 'pjm_aep_hub_price': round(pjm, 2), 'ercot_houston_price': round(ercot, 2), 'spread': round(spread, 2), 'spread_direction': 'PJM_PREMIUM' if spread > 0.5 else 'ERCOT_PREMIUM' if spread < -0.5 else 'FLAT'})
    return sorted(out, key=lambda x: x['date'])
