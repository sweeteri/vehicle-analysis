from datetime import timedelta
from vehicles.models import ICEVehicle, EVVehicle, HEVVehicle, PHEVVehicle
from calculator.engines.cost import TCOService

def simulate_daily_cost(vehicle, start_date, end_date, daily_km, driving_conditions='mixed'):
    results = []
    current = start_date
    while current <= end_date:
        usage = TCOService._calculate_usage_cost(
            vehicle,
            distance_km=daily_km,
            driving_conditions=driving_conditions
        )
        results.append({'date': current, 'cost_rub': usage})
        current += timedelta(days=1)
    return results