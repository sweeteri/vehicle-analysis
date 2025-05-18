from datetime import timedelta
import math, random
from vehicles.models import ICEVehicle, EVVehicle, HEVVehicle, PHEVVehicle
from calculator.engines.emissions import EmissionsCalculator

def simulate_daily_emissions(vehicle, start_date, end_date, daily_km,
                             energy_source='eu_avg', driving_conditions='mixed',
                             use_recuperation=True, urban_share=0.5):
    results = []
    current = start_date
    alpha = 0.1
    sigma = 0.03

    while current <= end_date:
        base_co2 = EmissionsCalculator.calculate_co2(
            vehicle,
            distance_km=daily_km,
            energy_source=energy_source,
            driving_conditions=driving_conditions,
            use_recuperation=use_recuperation,
            urban_share=urban_share
        )
        month_idx = current.month - 1
        season = 1 + alpha * math.sin(2 * math.pi * month_idx / 12)
        noise = random.gauss(1, sigma)

        co2 = base_co2 * season * noise
        results.append({'date': current, 'co2_g': co2})
        current += timedelta(days=1)

    return results
