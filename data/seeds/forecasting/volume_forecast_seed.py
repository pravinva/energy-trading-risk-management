"""
15-Day BUY/SELL Volume Forecast Generator for APEX
Generates daily BUY or SELL volume forecasts based on:
- Weather forecast (wind/solar generation impact)
- Production forecast (outages/maintenance impact)
- Market demand patterns (weekday vs weekend)
- Random market conditions

This is the KEY feature borrowed from Sahil's demo!
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import uuid

class VolumeForecastGenerator:
    """Generate 15-day BUY/SELL volume forecast for energy trading"""

    def __init__(self, region_id='NSW1', base_date=None):
        self.region_id = region_id
        self.base_date = base_date or datetime.now()

        # Regional base trading volumes (MWh per day)
        self.regional_base_volumes = {
            'NSW1': 2500,
            'VIC1': 2200,
            'QLD1': 2000,
            'SA1': 1500
        }

        self.base_volume = self.regional_base_volumes.get(region_id, 2500)

        # Maintenance/outage days (simulated)
        # These days will bias toward BUY (need to purchase energy)
        self.maintenance_days = [3, 7, 12]  # Days 3, 7, 12 have outages

    def generate_15day_forecast(self, weather_df=None):
        """
        Generate 15-day BUY/SELL volume forecast

        Args:
            weather_df: Optional weather forecast DataFrame to use for impact

        Returns:
            DataFrame with daily volume forecasts
        """
        forecast_data = []

        for day_offset in range(15):
            forecast_date = (self.base_date + timedelta(days=day_offset)).date()
            forecast_datetime = self.base_date + timedelta(days=day_offset)

            # Calculate volume with various impact factors
            volume, impacts = self._calculate_daily_volume(
                day_offset=day_offset,
                forecast_datetime=forecast_datetime,
                weather_df=weather_df
            )

            # Determine if this is a BUY or SELL day
            forecast_type, confidence = self._determine_buy_sell(
                day_offset=day_offset,
                impacts=impacts
            )

            forecast_data.append({
                'forecast_id': str(uuid.uuid4()),
                'region_id': self.region_id,
                'forecast_date': forecast_date,
                'forecast_type': forecast_type,  # 'BUY' or 'SELL'
                'volume_mwh': round(volume, 2),
                'base_volume_mwh': round(self.base_volume, 2),
                'weather_impact_pct': round(impacts['weather'], 2),
                'maintenance_impact_pct': round(impacts['maintenance'], 2),
                'outage_impact_pct': round(impacts['outage'], 2),
                'market_demand_factor': round(impacts['market_demand'], 2),
                'confidence_level': confidence,
                'created_at': self.base_date
            })

        return pd.DataFrame(forecast_data)

    def _calculate_daily_volume(self, day_offset, forecast_datetime, weather_df=None):
        """Calculate daily trading volume with impact factors"""

        # Base volume
        volume = self.base_volume

        # Weather impact (if weather data available)
        weather_impact = self._calculate_weather_impact(day_offset, weather_df)

        # Maintenance/outage impact
        maintenance_impact = self._calculate_maintenance_impact(day_offset)
        outage_impact = self._calculate_outage_impact(day_offset)

        # Market demand factor (weekday vs weekend)
        market_demand_factor = self._calculate_market_demand(forecast_datetime)

        # Random market conditions
        random_factor = 1.0 + np.random.normal(0, 0.15)

        # Apply all factors
        volume = volume * (1 + weather_impact/100)
        volume = volume * (1 + maintenance_impact/100)
        volume = volume * (1 + outage_impact/100)
        volume = volume * market_demand_factor
        volume = volume * random_factor

        # Ensure volume is positive
        volume = max(100, volume)

        impacts = {
            'weather': weather_impact,
            'maintenance': maintenance_impact,
            'outage': outage_impact,
            'market_demand': market_demand_factor
        }

        return volume, impacts

    def _calculate_weather_impact(self, day_offset, weather_df=None):
        """
        Calculate weather impact on volume
        High wind/solar = more generation = more SELL volume = positive impact on SELL
        """
        if weather_df is None:
            # Simulate weather impact with sine wave (realistic patterns)
            wind_factor = np.sin(day_offset * 0.3) * 0.4  # -40% to +40%
            solar_factor = np.sin(day_offset * 0.2 + 1) * 0.3  # -30% to +30%
            return (wind_factor + solar_factor) * 100 / 2  # Average impact as percentage
        else:
            # Use actual weather data (future enhancement)
            # Filter weather_df for this day, calculate wind/solar generation
            pass

        return 0.0

    def _calculate_maintenance_impact(self, day_offset):
        """
        Maintenance reduces generation capacity
        = need to BUY more = negative impact on volume (favor BUY)
        """
        if day_offset in self.maintenance_days:
            return -12.0  # -12% impact (reduction in selling capacity)
        return 0.0

    def _calculate_outage_impact(self, day_offset):
        """
        Unplanned outages reduce generation
        = need to BUY more = negative impact
        """
        # Simulate rare outage events
        if np.random.random() < 0.05:  # 5% chance of outage on any day
            return -np.random.uniform(5.0, 15.0)
        return 0.0

    def _calculate_market_demand(self, forecast_datetime):
        """
        Market demand varies by day of week
        Weekends have lower demand
        """
        weekday = forecast_datetime.weekday()

        # Weekday (Mon-Fri): 0-4
        # Weekend (Sat-Sun): 5-6
        if weekday >= 5:
            return 0.80  # 20% lower demand on weekends
        else:
            return 1.0  # Normal demand on weekdays

    def _determine_buy_sell(self, day_offset, impacts):
        """
        Determine if this day should be BUY or SELL based on impacts

        Logic:
        - High wind/solar forecast → more generation → SELL day
        - Maintenance/outage → less generation → BUY day
        - Calculate net probability
        """

        # Start with 50/50 probability
        sell_probability = 0.5

        # Weather impact (positive = more SELL)
        wind_solar_impact = impacts['weather'] / 100
        sell_probability += wind_solar_impact * 0.4

        # Maintenance impact (negative = more BUY)
        maintenance_bias = impacts['maintenance'] / 100
        sell_probability += maintenance_bias * 0.5  # Maintenance strongly favors BUY

        # Outage impact (negative = more BUY)
        outage_bias = impacts['outage'] / 100
        sell_probability += outage_bias * 0.5

        # Random market conditions
        market_bias = np.random.normal(0, 0.2)
        sell_probability += market_bias

        # Clamp between 0 and 1
        sell_probability = max(0, min(1, sell_probability))

        # Determine BUY or SELL
        is_sell_day = sell_probability > 0.5

        # Determine confidence based on how strong the signal is
        confidence_score = abs(sell_probability - 0.5) * 2  # 0 to 1 scale
        if confidence_score > 0.6:
            confidence = 'HIGH'
        elif confidence_score > 0.3:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'

        forecast_type = 'SELL' if is_sell_day else 'BUY'

        return forecast_type, confidence


def generate_all_regions(days=15):
    """Generate 15-day volume forecast for all NEM regions"""
    regions = ['NSW1', 'VIC1', 'QLD1', 'SA1']
    all_forecasts = []

    for region in regions:
        generator = VolumeForecastGenerator(region_id=region)
        df = generator.generate_15day_forecast()
        all_forecasts.append(df)

    combined_df = pd.concat(all_forecasts, ignore_index=True)
    return combined_df


def generate_with_weather(weather_df):
    """Generate volume forecast using weather data"""
    regions = weather_df['region_id'].unique()
    all_forecasts = []

    for region in regions:
        region_weather = weather_df[weather_df['region_id'] == region]
        generator = VolumeForecastGenerator(region_id=region)
        df = generator.generate_15day_forecast(weather_df=region_weather)
        all_forecasts.append(df)

    combined_df = pd.concat(all_forecasts, ignore_index=True)
    return combined_df


if __name__ == '__main__':
    # Generate 15-day volume forecast for all regions
    volume_df = generate_all_regions(days=15)

    print(f"Generated {len(volume_df)} volume forecast records (15 days × {len(volume_df)//15} regions)")
    print(f"\nRegions: {volume_df['region_id'].unique()}")

    # Show summary
    buy_count = len(volume_df[volume_df['forecast_type'] == 'BUY'])
    sell_count = len(volume_df[volume_df['forecast_type'] == 'SELL'])

    print(f"\nForecast Summary:")
    print(f"  BUY days: {buy_count}")
    print(f"  SELL days: {sell_count}")
    print(f"  Avg volume: {volume_df['volume_mwh'].mean():.2f} MWh")

    print(f"\nSample data (first 15 days - NSW1):")
    nsw_data = volume_df[volume_df['region_id'] == 'NSW1'].head(15)
    print(nsw_data[['forecast_date', 'forecast_type', 'volume_mwh', 'weather_impact_pct', 'confidence_level']])

    # Save to CSV
    output_path = 'volume_forecast_data.csv'
    volume_df.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")
