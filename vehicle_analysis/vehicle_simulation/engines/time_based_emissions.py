from calculator.engines.emissions import EmissionsCalculator
from vehicles.models import ICEVehicle, EVVehicle, HEVVehicle, PHEVVehicle


class TimeBasedEmissionsCalculator:
    @staticmethod
    def calculate_daily_emissions(vehicle, daily_distance_km, energy_source='eu_avg', driving_conditions='mixed'):
        """Расчет дневных выбросов"""
        return EmissionsCalculator.calculate_co2(
            vehicle, daily_distance_km, energy_source, driving_conditions
        )

    @staticmethod
    def calculate_emissions_for_period(vehicle, daily_distance_km, days, energy_source='eu_avg',
                                       driving_conditions='mixed'):
        """Расчет выбросов за период (в днях)"""
        daily_emissions = EmissionsCalculator.calculate_co2(
            vehicle, daily_distance_km, energy_source, driving_conditions
        )

        return {day: daily_emissions * day for day in range(1, days + 1)}