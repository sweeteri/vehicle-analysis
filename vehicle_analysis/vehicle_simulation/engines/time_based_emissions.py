from datetime import timedelta
from vehicles.models import ICEVehicle, EVVehicle, HEVVehicle, PHEVVehicle
from calculator.engines.emissions import EmissionsCalculator

def simulate_daily_emissions(vehicle, start_date, end_date, daily_km,
                             energy_source='eu_avg', driving_conditions='mixed',
                             use_recuperation=True, urban_share=0.5):
    results = []
    current = start_date
    while current <= end_date:
        co2 = EmissionsCalculator.calculate_co2(
            vehicle,
            distance_km=daily_km,
            energy_source=energy_source,
            driving_conditions=driving_conditions,
            use_recuperation=use_recuperation,
            urban_share=urban_share
        )
        results.append({'date': current, 'co2_g': co2})
        current += timedelta(days=1)
    return results