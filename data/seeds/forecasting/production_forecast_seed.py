"""
Production Forecast Generator for APEX
Generates energy production forecasts by asset type:
- Renewables (Wind + Solar + Hydro)
- Nuclear
- Coal
- Gas
- Biomass
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid

class ProductionForecastGenerator:
    """Generate production forecast by asset type"""

    def __init__(self, region_id='NSW1', base_date=None):
        self.region_id = region_id
        self.base_date = base_date or datetime.now()

        # Regional generation capacity by asset type (MW)
        self.regional_capacity = {
            'NSW1': {
                'RENEWABLES': 8500, 'NUCLEAR': 0, 'COAL': 12000,
                'GAS': 4500, 'BIOMASS': 500
            },
            'VIC1': {
                'RENEWABLES': 7200, 'NUCLEAR': 0, 'COAL': 6500,
                'GAS': 3800, 'BIOMASS': 400
            },
            'QLD1': {
                'RENEWABLES': 9500, 'NUCLEAR': 0, 'COAL': 8000,
                'GAS': 3200, 'BIOMASS': 300
            },
            'SA1': {
                'RENEWABLES': 5500, 'NUCLEAR': 0, 'COAL': 1200,
                'GAS': 2800, 'BIOMASS': 200
            }
        }

        self.capacity = self.regional_capacity.get(region_id, self.regional_capacity['NSW1'])

        # Base efficiency and availability by asset type
        self.asset_params = {
            'RENEWABLES': {'efficiency': 35.0, 'availability': 80.0},  # Weather dependent
            'NUCLEAR': {'efficiency': 92.0, 'availability': 98.0},
            'COAL': {'efficiency': 88.0, 'availability': 85.0},
            'GAS': {'efficiency': 90.0, 'availability': 92.0},
            'BIOMASS': {'efficiency': 75.0, 'availability': 90.0}
        }

    def generate_hourly_forecast(self, days=7, weather_df=None):
        """
        Generate hourly production forecast for next N days

        Args:
            days: Number of days to forecast
            weather_df: Optional weather forecast DataFrame (for renewables impact)

        Returns:
            DataFrame with production forecast by asset type
        """
        hours = days * 24
        timestamps = [self.base_date + timedelta(hours=i) for i in range(hours)]

        forecast_data = []

        for asset_type, capacity_mw in self.capacity.items():
            if capacity_mw == 0:
                continue  # Skip if region has no capacity for this asset type

            params = self.asset_params[asset_type]

            for idx, ts in enumerate(timestamps):
                hour_of_day = ts.hour
                day_of_year = ts.timetuple().tm_yday

                # Calculate generation based on asset type
                generation_mw, efficiency, availability = self._calculate_generation(
                    asset_type=asset_type,
                    capacity_mw=capacity_mw,
                    hour_of_day=hour_of_day,
                    day_of_year=day_of_year,
                    forecast_idx=idx,
                    weather_df=weather_df
                )

                # Confidence decreases with horizon
                confidence = self._determine_confidence(idx, asset_type)

                forecast_data.append({
                    'forecast_id': str(uuid.uuid4()),
                    'region_id': self.region_id,
                    'forecast_datetime': ts,
                    'asset_type': asset_type,
                    'generation_mw': round(generation_mw, 2),
                    'capacity_mw': round(capacity_mw, 2),
                    'efficiency_percent': round(efficiency, 2),
                    'availability_percent': round(availability, 2),
                    'confidence_level': confidence,
                    'forecast_horizon_hours': idx,
                    'created_at': self.base_date
                })

        return pd.DataFrame(forecast_data)

    def _calculate_generation(self, asset_type, capacity_mw, hour_of_day, day_of_year, forecast_idx, weather_df=None):
        """Calculate generation for specific asset type"""

        params = self.asset_params[asset_type]
        base_efficiency = params['efficiency']
        base_availability = params['availability']

        if asset_type == 'RENEWABLES':
            # Renewables heavily depend on weather
            generation, efficiency, availability = self._calculate_renewables_generation(
                capacity_mw, hour_of_day, day_of_year, weather_df
            )
        elif asset_type == 'COAL':
            # Coal follows load patterns (ramp up during day)
            generation, efficiency, availability = self._calculate_coal_generation(
                capacity_mw, hour_of_day, base_efficiency, base_availability
            )
        elif asset_type == 'GAS':
            # Gas is flexible (peak shaving)
            generation, efficiency, availability = self._calculate_gas_generation(
                capacity_mw, hour_of_day, base_efficiency, base_availability
            )
        elif asset_type == 'NUCLEAR':
            # Nuclear is baseload (constant)
            generation, efficiency, availability = self._calculate_baseload_generation(
                capacity_mw, base_efficiency, base_availability
            )
        elif asset_type == 'BIOMASS':
            # Biomass is baseload (constant)
            generation, efficiency, availability = self._calculate_baseload_generation(
                capacity_mw, base_efficiency, base_availability
            )
        else:
            generation = 0
            efficiency = 0
            availability = 0

        return generation, efficiency, availability

    def _calculate_renewables_generation(self, capacity_mw, hour_of_day, day_of_year, weather_df=None):
        """Calculate renewables generation (wind + solar)"""

        # Simulate wind generation (higher at night)
        wind_factor = 0.3 + 0.4 * np.sin((hour_of_day - 18) * 2 * np.pi / 24)

        # Simulate solar generation (only during day)
        if 6 <= hour_of_day <= 18:
            solar_factor = max(0, np.sin((hour_of_day - 6) * 2 * np.pi / 12))
        else:
            solar_factor = 0.0

        # Combine (assume 60% wind, 30% solar, 10% hydro)
        renewable_factor = (0.6 * wind_factor + 0.3 * solar_factor + 0.1 * 0.8)

        # Seasonal variation
        seasonal_factor = 1.0 + 0.2 * np.sin((day_of_year - 15) * 2 * np.pi / 365)

        # Random weather variability
        weather_noise = np.random.uniform(0.8, 1.2)

        generation = capacity_mw * renewable_factor * seasonal_factor * weather_noise
        efficiency = renewable_factor * 100  # Effective efficiency
        availability = 70 + np.random.normal(0, 10)  # Weather dependent

        return generation, efficiency, max(0, min(100, availability))

    def _calculate_coal_generation(self, capacity_mw, hour_of_day, base_efficiency, base_availability):
        """Calculate coal generation (load following)"""

        # Coal follows demand pattern (higher during day)
        if 6 <= hour_of_day <= 22:
            load_factor = 0.75 + 0.15 * np.sin((hour_of_day - 6) * 2 * np.pi / 16)
        else:
            load_factor = 0.60  # Lower at night

        # Random variations
        noise = np.random.uniform(0.95, 1.05)

        generation = capacity_mw * load_factor * noise * (base_availability / 100)
        efficiency = base_efficiency + np.random.normal(0, 2)
        availability = base_availability + np.random.normal(0, 3)

        return generation, efficiency, max(0, min(100, availability))

    def _calculate_gas_generation(self, capacity_mw, hour_of_day, base_efficiency, base_availability):
        """Calculate gas generation (peak shaving and flexible)"""

        # Gas responds to peak demand (morning and evening peaks)
        if 7 <= hour_of_day <= 9 or 17 <= hour_of_day <= 20:
            load_factor = 0.85  # Peak hours
        elif 10 <= hour_of_day <= 16:
            load_factor = 0.60  # Mid-day
        else:
            load_factor = 0.40  # Off-peak

        # Random variations
        noise = np.random.uniform(0.90, 1.10)

        generation = capacity_mw * load_factor * noise * (base_availability / 100)
        efficiency = base_efficiency + np.random.normal(0, 2)
        availability = base_availability + np.random.normal(0, 2)

        return generation, efficiency, max(0, min(100, availability))

    def _calculate_baseload_generation(self, capacity_mw, base_efficiency, base_availability):
        """Calculate baseload generation (nuclear, biomass)"""

        # Baseload is constant (high capacity factor)
        load_factor = 0.95 + np.random.uniform(-0.05, 0.05)

        generation = capacity_mw * load_factor * (base_availability / 100)
        efficiency = base_efficiency + np.random.normal(0, 1)
        availability = base_availability + np.random.normal(0, 1)

        return generation, efficiency, max(0, min(100, availability))

    def _determine_confidence(self, horizon_hours, asset_type):
        """Determine forecast confidence based on horizon and asset type"""

        # Renewables have lower confidence (weather dependent)
        if asset_type == 'RENEWABLES':
            if horizon_hours <= 12:
                return 'MEDIUM'
            elif horizon_hours <= 48:
                return 'LOW'
            else:
                return 'LOW'
        else:
            # Dispatchable assets have higher confidence
            if horizon_hours <= 24:
                return 'HIGH'
            elif horizon_hours <= 72:
                return 'MEDIUM'
            else:
                return 'LOW'


def generate_all_regions(days=7):
    """Generate production forecast for all NEM regions"""
    regions = ['NSW1', 'VIC1', 'QLD1', 'SA1']
    all_forecasts = []

    for region in regions:
        generator = ProductionForecastGenerator(region_id=region)
        df = generator.generate_hourly_forecast(days=days)
        all_forecasts.append(df)

    combined_df = pd.concat(all_forecasts, ignore_index=True)
    return combined_df


if __name__ == '__main__':
    # Generate 7 days of hourly production forecast for all regions
    production_df = generate_all_regions(days=7)

    print(f"Generated {len(production_df)} production forecast records")
    print(f"\nRegions: {production_df['region_id'].unique()}")
    print(f"\nAsset types: {production_df['asset_type'].unique()}")

    # Show summary by asset type
    print(f"\nAverage generation by asset type (MW):")
    avg_by_asset = production_df.groupby('asset_type')['generation_mw'].mean()
    print(avg_by_asset)

    print(f"\nSample data:")
    print(production_df.head(10))

    # Save to CSV
    output_path = 'production_forecast_data.csv'
    production_df.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")
