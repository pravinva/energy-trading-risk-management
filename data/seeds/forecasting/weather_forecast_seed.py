"""
Weather Forecast Data Generator for APEX
Generates realistic weather forecast data for energy trading analysis
Supports NEM regions (NSW1, VIC1, QLD1, SA1)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid

class WeatherForecastGenerator:
    """Generate realistic weather forecast data for energy markets"""

    def __init__(self, region_id='NSW1', base_date=None):
        self.region_id = region_id
        self.base_date = base_date or datetime.now()

        # Regional weather parameters (Australian climate)
        self.regional_params = {
            'NSW1': {
                'temp_base': 22.0, 'temp_range': 15.0, 'temp_seasonal': 8.0,
                'wind_base': 12.0, 'wind_range': 8.0,
                'solar_base': 500.0, 'solar_range': 350.0,
                'precip_prob': 0.15, 'humidity_base': 65.0
            },
            'VIC1': {
                'temp_base': 18.0, 'temp_range': 14.0, 'temp_seasonal': 10.0,
                'wind_base': 15.0, 'wind_range': 10.0,
                'solar_base': 450.0, 'solar_range': 320.0,
                'precip_prob': 0.20, 'humidity_base': 70.0
            },
            'QLD1': {
                'temp_base': 25.0, 'temp_range': 10.0, 'temp_seasonal': 5.0,
                'wind_base': 10.0, 'wind_range': 6.0,
                'solar_base': 550.0, 'solar_range': 380.0,
                'precip_prob': 0.25, 'humidity_base': 75.0
            },
            'SA1': {
                'temp_base': 20.0, 'temp_range': 16.0, 'temp_seasonal': 9.0,
                'wind_base': 18.0, 'wind_range': 12.0,
                'solar_base': 520.0, 'solar_range': 360.0,
                'precip_prob': 0.12, 'humidity_base': 60.0
            }
        }

        self.params = self.regional_params.get(region_id, self.regional_params['NSW1'])

    def generate_hourly_forecast(self, days=7, hourly_intervals=True):
        """
        Generate hourly weather forecast for next N days

        Args:
            days: Number of days to forecast
            hourly_intervals: If True, generate hourly data; if False, daily

        Returns:
            DataFrame with weather forecast data
        """
        if hourly_intervals:
            hours = days * 24
            timestamps = [self.base_date + timedelta(hours=i) for i in range(hours)]
        else:
            timestamps = [self.base_date + timedelta(days=i) for i in range(days)]

        forecast_data = []

        for idx, ts in enumerate(timestamps):
            hour_of_day = ts.hour
            day_of_year = ts.timetuple().tm_yday

            # Temperature (diurnal and seasonal patterns)
            temp = self._generate_temperature(hour_of_day, day_of_year)

            # Wind speed (tends to be higher at night/early morning)
            wind = self._generate_wind_speed(hour_of_day)

            # Solar irradiance (zero at night, peak at solar noon)
            solar = self._generate_solar_irradiance(hour_of_day, day_of_year)

            # Precipitation
            precip = self._generate_precipitation()

            # Humidity
            humidity = self._generate_humidity(temp, precip)

            # Confidence level (decreases with forecast horizon)
            horizon_hours = idx if hourly_intervals else idx * 24
            confidence = self._determine_confidence(horizon_hours)

            forecast_data.append({
                'forecast_id': str(uuid.uuid4()),
                'region_id': self.region_id,
                'forecast_datetime': ts,
                'temperature_celsius': round(temp, 2),
                'wind_speed_ms': round(wind, 2),
                'solar_irradiance_wm2': round(solar, 2),
                'precipitation_mm': round(precip, 2),
                'humidity_percent': round(humidity, 2),
                'confidence_level': confidence,
                'forecast_horizon_hours': horizon_hours,
                'created_at': self.base_date
            })

        return pd.DataFrame(forecast_data)

    def _generate_temperature(self, hour_of_day, day_of_year):
        """Generate realistic temperature with diurnal and seasonal patterns"""
        params = self.params

        # Seasonal variation (summer peak around day 15 of Jan, winter min around day 200)
        seasonal_factor = np.sin((day_of_year - 15) * 2 * np.pi / 365)
        seasonal_temp = params['temp_seasonal'] * seasonal_factor

        # Diurnal variation (peak around 14:00, min around 04:00)
        diurnal_factor = np.sin((hour_of_day - 4) * 2 * np.pi / 24)
        diurnal_temp = params['temp_range'] * diurnal_factor

        # Random noise
        noise = np.random.normal(0, 1.5)

        temp = params['temp_base'] + seasonal_temp + diurnal_temp + noise
        return max(-5.0, min(50.0, temp))  # Clamp to realistic bounds

    def _generate_wind_speed(self, hour_of_day):
        """Generate realistic wind speed (higher at night/early morning)"""
        params = self.params

        # Wind tends to be higher at night
        diurnal_factor = np.sin((hour_of_day - 18) * 2 * np.pi / 24)
        diurnal_wind = (params['wind_range'] / 2) * diurnal_factor

        # Random gusts
        noise = np.random.normal(0, 2.0)

        wind = params['wind_base'] + diurnal_wind + noise
        return max(0.0, min(40.0, wind))  # Clamp to realistic bounds

    def _generate_solar_irradiance(self, hour_of_day, day_of_year):
        """Generate realistic solar irradiance (zero at night, peak at noon)"""
        params = self.params

        # Solar elevation (zero at night, peak around 12:00)
        if hour_of_day < 6 or hour_of_day > 18:
            return 0.0  # Night time

        # Solar elevation angle
        solar_elevation = np.sin((hour_of_day - 6) * 2 * np.pi / 12)

        # Seasonal variation (higher in summer)
        seasonal_factor = 1.0 + 0.3 * np.sin((day_of_year - 15) * 2 * np.pi / 365)

        # Cloud cover (random factor)
        cloud_factor = np.random.uniform(0.7, 1.0)

        solar = params['solar_base'] * solar_elevation * seasonal_factor * cloud_factor
        noise = np.random.normal(0, 30)

        return max(0.0, min(1200.0, solar + noise))

    def _generate_precipitation(self):
        """Generate realistic precipitation"""
        params = self.params

        # Precipitation is sparse (use probability)
        if np.random.random() > params['precip_prob']:
            return 0.0

        # When it rains, use exponential distribution
        precip = np.random.exponential(scale=5.0)
        return min(precip, 50.0)  # Cap at 50mm per hour

    def _generate_humidity(self, temperature, precipitation):
        """Generate realistic humidity based on temp and precipitation"""
        params = self.params

        # Base humidity
        base = params['humidity_base']

        # Higher humidity when it's raining
        rain_factor = 15.0 if precipitation > 0 else 0.0

        # Humidity inversely related to temperature
        temp_factor = -0.3 * (temperature - 22.0)

        # Random noise
        noise = np.random.normal(0, 5.0)

        humidity = base + rain_factor + temp_factor + noise
        return max(20.0, min(100.0, humidity))

    def _determine_confidence(self, horizon_hours):
        """Determine forecast confidence level based on horizon"""
        if horizon_hours <= 24:
            return 'HIGH'
        elif horizon_hours <= 72:
            return 'MEDIUM'
        else:
            return 'LOW'


def generate_all_regions(days=7):
    """Generate weather forecast for all NEM regions"""
    regions = ['NSW1', 'VIC1', 'QLD1', 'SA1']
    all_forecasts = []

    for region in regions:
        generator = WeatherForecastGenerator(region_id=region)
        df = generator.generate_hourly_forecast(days=days, hourly_intervals=True)
        all_forecasts.append(df)

    combined_df = pd.concat(all_forecasts, ignore_index=True)
    return combined_df


if __name__ == '__main__':
    # Generate 7 days of hourly weather forecast for all regions
    forecast_df = generate_all_regions(days=7)

    print(f"Generated {len(forecast_df)} weather forecast records")
    print(f"\nRegions: {forecast_df['region_id'].unique()}")
    print(f"\nSample data:")
    print(forecast_df.head(10))

    # Save to CSV for loading into Delta
    output_path = 'weather_forecast_data.csv'
    forecast_df.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")
