from datetime import timedelta
import math
import random
from calculator.engines.cost import TCOService


def simulate_daily_cost(vehicle, start_date, end_date, daily_km, driving_conditions='mixed'):
    results = []
    current = start_date
    alpha = 0.1
    sigma = 0.03

    while current <= end_date:
        base_cost = TCOService._calculate_usage_cost(
            vehicle,
            distance_km=daily_km,
            driving_conditions=driving_conditions
        )
        month_idx = current.month - 1
        season = 1 + alpha * math.sin(2 * math.pi * month_idx / 12)
        noise = random.gauss(1, sigma)

        cost = base_cost * season * noise
        results.append({'date': current, 'cost_rub': cost})
        current += timedelta(days=1)

    return results
