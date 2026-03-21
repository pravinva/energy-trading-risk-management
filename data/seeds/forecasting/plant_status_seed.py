"""
Plant Status and Maintenance Schedule Generator for APEX
Generates realistic outage, maintenance, and ramp events for power plants
Used for the Plant Status Timeline (Gantt chart) visualization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid

class PlantStatusGenerator:
    """Generate plant outage, maintenance, and ramp schedules"""

    def __init__(self, region_id='NSW1', base_date=None):
        self.region_id = region_id
        self.base_date = base_date or datetime.now()

        # Regional power plants by type
        self.regional_plants = {
            'NSW1': [
                ('Bayswater Coal', 'COAL', 2640),
                ('Eraring Coal', 'COAL', 2880),
                ('Vales Point Coal', 'COAL', 1320),
                ('Tallawarra Gas', 'GAS', 435),
                ('Uranquinty Gas', 'GAS', 664),
                ('Capital Wind Farm', 'WIND', 141),
                ('Lake Cargelligo Solar', 'SOLAR', 255),
                ('Broken Hill Solar', 'SOLAR', 53),
            ],
            'VIC1': [
                ('Loy Yang A Coal', 'COAL', 2180),
                ('Yallourn Coal', 'COAL', 1480),
                ('Newport Gas', 'GAS', 500),
                ('Mortlake Gas', 'GAS', 566),
                ('Macarthur Wind Farm', 'WIND', 420),
                ('Glenrowan Solar', 'SOLAR', 120),
            ],
            'QLD1': [
                ('Kogan Creek Coal', 'COAL', 750),
                ('Stanwell Coal', 'COAL', 1460),
                ('Braemar Gas', 'GAS', 519),
                ('Kennedy Wind Farm', 'WIND', 58),
                ('Ross River Solar', 'SOLAR', 148),
                ('Clare Solar Farm', 'SOLAR', 100),
            ],
            'SA1': [
                ('Torrens Island Gas', 'GAS', 800),
                ('Pelican Point Gas', 'GAS', 478),
                ('Snowtown Wind Farm', 'WIND', 370),
                ('Hornsdale Wind Farm', 'WIND', 309),
                ('Bungala Solar', 'SOLAR', 275),
                ('Tailem Bend Solar', 'SOLAR', 95),
            ]
        }

        self.plants = self.regional_plants.get(region_id, self.regional_plants['NSW1'])

        # Event type probabilities by plant type
        self.event_probabilities = {
            'COAL': {
                'OUTAGE': 0.20,
                'MAINTENANCE': 0.40,
                'RAMP_UP': 0.15,
                'RAMP_DOWN': 0.10
            },
            'GAS': {
                'OUTAGE': 0.10,
                'MAINTENANCE': 0.25,
                'RAMP_UP': 0.35,
                'RAMP_DOWN': 0.20
            },
            'WIND': {
                'OUTAGE': 0.05,
                'MAINTENANCE': 0.30,
                'RAMP_UP': 0.25,
                'RAMP_DOWN': 0.15
            },
            'SOLAR': {
                'OUTAGE': 0.05,
                'MAINTENANCE': 0.35,
                'RAMP_UP': 0.20,
                'RAMP_DOWN': 0.15
            }
        }

    def generate_plant_events(self, days=14):
        """
        Generate plant status events for next N days

        Args:
            days: Number of days to forecast

        Returns:
            DataFrame with plant events
        """
        event_data = []

        for idx, (plant_name, plant_type, capacity_mw) in enumerate(self.plants):
            # Generate varied events based on plant type
            events = self._generate_events_for_plant(
                plant_name=plant_name,
                plant_type=plant_type,
                capacity_mw=capacity_mw,
                plant_idx=idx,
                days=days
            )

            event_data.extend(events)

        return pd.DataFrame(event_data)

    def _generate_events_for_plant(self, plant_name, plant_type, capacity_mw, plant_idx, days):
        """Generate events for a single plant"""

        events = []
        probs = self.event_probabilities.get(plant_type, self.event_probabilities['COAL'])

        # Coal plants - longer outages, more frequent maintenance
        if plant_type == 'COAL':
            # Outage
            if plant_idx % 2 == 1:
                events.append(self._create_event(
                    plant_name, plant_type, capacity_mw,
                    event_type='OUTAGE',
                    start_offset=1 + plant_idx,
                    duration_days=2 + plant_idx % 2,
                    description=f'Boiler maintenance - {plant_type}',
                    impact='HIGH'
                ))
            # Maintenance
            if plant_idx % 3 == 0:
                events.append(self._create_event(
                    plant_name, plant_type, capacity_mw,
                    event_type='MAINTENANCE',
                    start_offset=6 + plant_idx,
                    duration_days=2,
                    description=f'Environmental system check - {plant_type}',
                    impact='MEDIUM'
                ))

        # Gas plants - flexible ramps, shorter maintenance
        elif plant_type == 'GAS':
            # Ramp up
            if plant_idx % 2 == 0:
                events.append(self._create_event(
                    plant_name, plant_type, capacity_mw,
                    event_type='RAMP_UP',
                    start_offset=4 + plant_idx,
                    duration_days=2,
                    description=f'Peak demand response - {plant_type}',
                    impact='LOW'
                ))
            # Maintenance
            if plant_idx % 4 == 0:
                events.append(self._create_event(
                    plant_name, plant_type, capacity_mw,
                    event_type='MAINTENANCE',
                    start_offset=10 + plant_idx,
                    duration_days=2,
                    description=f'Turbine maintenance - {plant_type}',
                    impact='MEDIUM'
                ))

        # Wind farms - weather-dependent ramps, periodic maintenance
        elif plant_type == 'WIND':
            # Ramp up (high wind forecast)
            if plant_idx % 2 == 0:
                events.append(self._create_event(
                    plant_name, plant_type, capacity_mw,
                    event_type='RAMP_UP',
                    start_offset=3 + plant_idx,
                    duration_days=2,
                    description=f'High wind conditions - {plant_type}',
                    impact='LOW'
                ))
            # Maintenance
            if plant_idx % 3 == 1:
                events.append(self._create_event(
                    plant_name, plant_type, capacity_mw,
                    event_type='MAINTENANCE',
                    start_offset=7 + plant_idx,
                    duration_days=2,
                    description=f'Turbine blade inspection - {plant_type}',
                    impact='MEDIUM'
                ))

        # Solar farms - daytime ramps, seasonal maintenance
        elif plant_type == 'SOLAR':
            # Ramp up (optimal irradiance)
            if plant_idx % 3 == 0:
                events.append(self._create_event(
                    plant_name, plant_type, capacity_mw,
                    event_type='RAMP_UP',
                    start_offset=5 + plant_idx,
                    duration_days=2,
                    description=f'Optimal solar conditions - {plant_type}',
                    impact='LOW'
                ))
            # Maintenance
            if plant_idx % 4 == 1:
                events.append(self._create_event(
                    plant_name, plant_type, capacity_mw,
                    event_type='MAINTENANCE',
                    start_offset=11 + plant_idx,
                    duration_days=2,
                    description=f'Panel cleaning & inspection - {plant_type}',
                    impact='LOW'
                ))

        return events

    def _create_event(self, plant_name, plant_type, capacity_mw, event_type, start_offset, duration_days, description, impact):
        """Create a single event"""

        start_datetime = self.base_date + timedelta(days=start_offset)
        end_datetime = start_datetime + timedelta(days=duration_days)

        # Calculate capacity impact
        if event_type == 'OUTAGE':
            capacity_impact = capacity_mw  # Full outage
        elif event_type == 'MAINTENANCE':
            capacity_impact = capacity_mw * 0.5  # 50% capacity during maintenance
        elif event_type in ['RAMP_UP', 'RAMP_DOWN']:
            capacity_impact = capacity_mw * 0.2  # 20% capacity change
        else:
            capacity_impact = 0.0

        return {
            'event_id': str(uuid.uuid4()),
            'plant_name': plant_name,
            'plant_type': plant_type,
            'region_id': self.region_id,
            'event_type': event_type,
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
            'capacity_impact_mw': round(capacity_impact, 2),
            'grid_impact': impact,
            'description': description,
            'status': 'SCHEDULED'
        }


def generate_all_regions(days=14):
    """Generate plant status events for all NEM regions"""
    regions = ['NSW1', 'VIC1', 'QLD1', 'SA1']
    all_events = []

    for region in regions:
        generator = PlantStatusGenerator(region_id=region)
        df = generator.generate_plant_events(days=days)
        all_events.append(df)

    combined_df = pd.concat(all_events, ignore_index=True)
    return combined_df


if __name__ == '__main__':
    # Generate 14 days of plant status events for all regions
    plant_events_df = generate_all_regions(days=14)

    print(f"Generated {len(plant_events_df)} plant status events")
    print(f"\nRegions: {plant_events_df['region_id'].unique()}")
    print(f"\nEvent types: {plant_events_df['event_type'].unique()}")

    # Show summary by event type
    print(f"\nEvent count by type:")
    event_counts = plant_events_df['event_type'].value_counts()
    print(event_counts)

    print(f"\nSample events:")
    print(plant_events_df[['plant_name', 'event_type', 'start_datetime', 'end_datetime', 'grid_impact']].head(10))

    # Save to CSV
    output_path = 'plant_status_data.csv'
    plant_events_df.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")
