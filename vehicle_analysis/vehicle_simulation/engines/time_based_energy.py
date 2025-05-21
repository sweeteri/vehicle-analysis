from datetime import timedelta
import math
import random
from calculator.engines.energy import EnergyCalculator


def simulate_daily_energy(vehicle, start_date, end_date, daily_km, driving_conditions):
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

        # Список всех числовых полей, которые нужно скорректировать
        numeric_fields = [
            'fuel_liters', 'energy_mj', 'useful_energy_mj', 'energy_kwh',
            'total_energy_mj', 'battery_depletion', 'MPGe',
            'fuel_consumption_l_100km', 'efficiency', 'ice_share',
            'electric_share'
        ]

        # корректируем все численные поля в res
        for field in numeric_fields:
            if field in res and isinstance(res[field], (int, float)):
                res[field] = res[field] * season * noise

        res['date'] = current
        results.append(res)
        current += timedelta(days=1)

    return results
