from datetime import timedelta
import math
import random
from calculator.engines.energy import EnergyCalculator


def simulate_daily_energy(vehicle, start_date, end_date, daily_km, driving_conditions='mixed'):
    results = []
    current = start_date
    alpha = 0.1  # амплитуда сезонного колебания ±10%
    sigma = 0.03  # стандартное отклонение шума 3%

    while current <= end_date:
        # базовый расчёт
        res = EnergyCalculator.calculate_energy_consumption(
            vehicle,
            distance_km=daily_km,
            driving_conditions=driving_conditions
        )

        # сезонный множитель
        month_idx = current.month - 1
        season = 1 + alpha * math.sin(2 * math.pi * month_idx / 12)

        # шумовой множитель
        noise = random.gauss(1, sigma)

        # корректируем все численные поля в res
        for key in list(res.keys()):
            if isinstance(res[key], (int, float)):
                res[key] = res[key] * season * noise

        res['date'] = current
        results.append(res)
        current += timedelta(days=1)

    return results
