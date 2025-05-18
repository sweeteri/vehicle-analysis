from calculator.engines.energy import EnergyCalculator
from vehicles.models import ICEVehicle, EVVehicle, HEVVehicle, PHEVVehicle


class TimeBasedEnergyCalculator:
    @staticmethod
    def calculate_daily_energy(vehicle, daily_distance_km, driving_conditions='mixed'):
        """Расчет дневного потребления энергии"""
        return EnergyCalculator.calculate_energy_consumption(
            vehicle, daily_distance_km, driving_conditions
        )

    @staticmethod
    def calculate_energy_for_period(vehicle, daily_distance_km, days, driving_conditions='mixed'):
        """Расчет потребления энергии за период (в днях)"""
        daily_data = EnergyCalculator.calculate_energy_consumption(
            vehicle, daily_distance_km, driving_conditions
        )

        result = {}
        for day in range(1, days + 1):
            day_data = {}
            for key, value in daily_data.items():
                if isinstance(value, (int, float)):
                    day_data[key] = value * day
                else:
                    day_data[key] = value
            result[day] = day_data

        return result