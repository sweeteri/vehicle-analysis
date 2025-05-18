from calculator.engines.cost import TCOService
from vehicles.models import ICEVehicle, EVVehicle, HEVVehicle, PHEVVehicle


class TimeBasedCostCalculator:
    @staticmethod
    def calculate_daily_cost(vehicle, daily_distance_km, driving_conditions='mixed'):
        """Расчет дневной стоимости"""
        return TCOService._calculate_energy_cost(
            vehicle, daily_distance_km, driving_conditions
        )

    @staticmethod
    def calculate_cost_for_period(vehicle, daily_distance_km, days, driving_conditions='mixed'):
        """Расчет стоимости за период (в днях)"""
        daily_cost = TCOService._calculate_energy_cost(
            vehicle, daily_distance_km, driving_conditions
        )

        return {day: daily_cost * day for day in range(1, days + 1)}