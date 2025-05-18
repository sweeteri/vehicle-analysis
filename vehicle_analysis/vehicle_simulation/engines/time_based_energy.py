from datetime import timedelta
from vehicles.models import ICEVehicle, EVVehicle, HEVVehicle, PHEVVehicle
from calculator.engines.energy import EnergyCalculator

def simulate_daily_energy(vehicle, start_date, end_date, daily_km, driving_conditions='mixed'):
    """
    Возвращает список:
      [{'date': date, 'energy_mj':…, …}, …]
    для каждого дня от start_date до end_date (включительно).
    """
    results = []
    current = start_date
    while current <= end_date:
        res = EnergyCalculator.calculate_energy_consumption(
            vehicle,
            distance_km=daily_km,
            driving_conditions=driving_conditions
        )
        res['date'] = current
        results.append(res)
        current += timedelta(days=1)
    return results