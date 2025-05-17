import pandas as pd
from datetime import datetime, timedelta
from . import time_based_cost, time_based_emissions, time_based_energy
from vehicles.models import ICEVehicle, EVVehicle, HEVVehicle, PHEVVehicle


class VehicleSimulator:
    """
    Класс для моделирования использования транспортного средства с временной привязкой.
    Интегрирует расчеты стоимости, выбросов и энергопотребления.
    """

    def __init__(self, vehicle, start_date, end_date, daily_usage_hours=8, energy_source='eu_avg'):
        """
        :param vehicle: Объект транспортного средства (ICEVehicle/EVVehicle/HEVVehicle/PHEVVehicle)
        :param start_date: Дата начала симуляции (datetime.date)
        :param end_date: Дата окончания симуляции (datetime.date)
        :param daily_usage_hours: Среднее часов использования в день
        :param energy_source: Источник энергии для электромобилей ('eu_avg', 'coal', 'renewables', etc.)
        """
        self.vehicle = vehicle
        self.start_date = start_date
        self.end_date = end_date
        self.daily_usage_hours = daily_usage_hours
        self.energy_source = energy_source
        self.results = None

    def simulate(self):
        """Основной метод выполнения симуляции"""
        date_range = pd.date_range(self.start_date, self.end_date, freq='D')
        results = []

        for date in date_range:
            # Получаем сезонные коэффициенты
            season_factor = self._get_season_factor(date.month)
            road_type = self._get_road_type_by_month(date.month)

            # Выполняем расчеты
            daily_data = {
                'date': date.date(),
                'cost': time_based_cost.TimeBasedCostCalculator.calculate_daily_cost(
                    vehicle=self.vehicle,
                    hours=self.daily_usage_hours,
                    date=date
                ),
                'emissions': time_based_emissions.TimeBasedEmissions.calculate_daily_emissions(
                    vehicle=self.vehicle,
                    hours=self.daily_usage_hours,
                    date=date,
                    energy_source=self.energy_source
                ),
                'energy': time_based_energy.TimeBasedEnergy.calculate_daily_energy(
                    vehicle=self.vehicle,
                    hours=self.daily_usage_hours,
                    date=date
                ),
                'season_factor': season_factor,
                'road_type': road_type
            }

            # Рассчитываем накопленные значения
            if results:  # Не первый день
                daily_data['cumulative_cost'] = results[-1]['cumulative_cost'] + daily_data['cost']['total']
                daily_data['cumulative_emissions'] = results[-1]['cumulative_emissions'] + daily_data['emissions']
                daily_data['cumulative_energy'] = results[-1]['cumulative_energy'] + daily_data['energy'][
                    'total_energy_mj']
            else:  # Первый день
                daily_data['cumulative_cost'] = daily_data['cost']['total']
                daily_data['cumulative_emissions'] = daily_data['emissions']
                daily_data['cumulative_energy'] = daily_data['energy']['total_energy_mj']

            results.append(daily_data)

        self.results = pd.DataFrame(results)
        return self.results

    def get_daily_data(self):
        """Возвращает ежедневные данные без накопления"""
        if self.results is None:
            self.simulate()
        return self.results

    def get_cumulative_data(self):
        """Возвращает накопленные данные для графиков"""
        if self.results is None:
            self.simulate()

        return {
            'dates': self.results['date'].astype(str).tolist(),
            'daily_cost': self.results['cost'].apply(lambda x: x['total']).tolist(),
            'cumulative_cost': self.results['cumulative_cost'].tolist(),
            'daily_emissions': self.results['emissions'].tolist(),
            'cumulative_emissions': self.results['cumulative_emissions'].tolist(),
            'daily_energy': self.results['energy'].apply(lambda x: x['total_energy_mj']).tolist(),
            'cumulative_energy': self.results['cumulative_energy'].tolist(),
            'energy_types': self._get_energy_types_data()
        }

    def get_summary_stats(self):
        """Сводная статистика по всей симуляции"""
        if self.results is None:
            self.simulate()

        total_days = len(self.results)
        return {
            'total_cost': self.results['cumulative_cost'].iloc[-1],
            'total_emissions': self.results['cumulative_emissions'].iloc[-1],
            'total_energy_mj': self.results['cumulative_energy'].iloc[-1],
            'avg_daily_cost': self.results['cost'].apply(lambda x: x['total']).mean(),
            'avg_daily_emissions': self.results['emissions'].mean(),
            'avg_daily_energy': self.results['energy'].apply(lambda x: x['total_energy_mj']).mean(),
            'simulation_period': {
                'start': self.start_date.strftime('%Y-%m-%d'),
                'end': self.end_date.strftime('%Y-%m-%d'),
                'days': total_days,
                'total_hours': total_days * self.daily_usage_hours
            },
            'vehicle_info': self._get_vehicle_info()
        }

    def _get_energy_types_data(self):
        """Формирует данные по типам энергии для круговых диаграмм"""
        if isinstance(self.vehicle, ICEVehicle):
            return {'fuel': 100}
        elif isinstance(self.vehicle, EVVehicle):
            return {'electricity': 100}
        else:  # HEV/PHEV
            total_fuel = self.results['energy'].apply(lambda x: x.get('fuel_liters', 0)).sum()
            total_electric = self.results['energy'].apply(lambda x: x.get('energy_kwh', 0)).sum()
            total = total_fuel + total_electric
            return {
                'fuel': (total_fuel / total) * 100 if total > 0 else 0,
                'electricity': (total_electric / total) * 100 if total > 0 else 0
            }

    def _get_vehicle_info(self):
        """Информация о транспортном средстве для отчетов"""
        return {
            'name': f"{getattr(self.vehicle, 'mark_name', '')} {getattr(self.vehicle, 'model_name', '')}",
            'type': self._get_vehicle_type(),
            'production_year': getattr(self.vehicle, 'production_year', 'N/A'),
            'fuel_type': getattr(self.vehicle, 'fuel_type', 'electric')
        }

    def _get_vehicle_type(self):
        """Определяет тип транспортного средства"""
        if isinstance(self.vehicle, ICEVehicle):
            return 'ДВС'
        elif isinstance(self.vehicle, EVVehicle):
            return 'Электромобиль'
        elif isinstance(self.vehicle, HEVVehicle):
            return 'Гибрид (HEV)'
        elif isinstance(self.vehicle, PHEVVehicle):
            return 'Подключаемый гибрид (PHEV)'
        return 'Неизвестный тип'

    @staticmethod
    def _get_season_factor(month):
        """Сезонные коэффициенты для расчетов"""
        if month in [12, 1, 2]:  # Зима
            return 1.2
        elif month in [6, 7, 8]:  # Лето
            return 0.9
        return 1.0  # Весна/осень

    @staticmethod
    def _get_road_type_by_month(month):
        """Определяет преобладающий тип дороги по месяцу"""
        if month in [12, 1, 2]:  # Зимой больше городского цикла
            return 'city'
        elif month in [6, 7, 8]:  # Летом больше трассы
            return 'highway'
        return 'mixed'
# import pandas as pd
# from datetime import datetime, timedelta
# from . import time_based_cost, time_based_emissions, time_based_energy
#
#
# class VehicleSimulator:
#     def __init__(self, vehicle, start_date, end_date, daily_usage_hours=8, energy_source='eu_avg'):
#         self.vehicle = vehicle
#         self.start_date = start_date
#         self.end_date = end_date
#         self.daily_usage_hours = daily_usage_hours
#         self.energy_source = energy_source
#         self.results = None
#
#     def simulate(self):
#         date_range = pd.date_range(self.start_date, self.end_date, freq='D')
#         results = []
#
#         for date in date_range:
#             day_result = {
#                 'date': date,
#                 'cost': time_based_cost.TimeBasedCostCalculator.calculate_daily_cost(
#                     self.vehicle, self.daily_usage_hours, date
#                 ),
#                 'emissions': time_based_emissions.TimeBasedEmissions.calculate_daily_emissions(
#                     self.vehicle, self.daily_usage_hours, date, self.energy_source
#                 ),
#                 'energy': time_based_energy.TimeBasedEnergy.calculate_daily_energy(
#                     self.vehicle, self.daily_usage_hours, date
#                 )
#             }
#             results.append(day_result)
#
#         self.results = pd.DataFrame(results)
#         return self.results
#
#     def get_cumulative_data(self):
#         if self.results is None:
#             self.simulate()
#
#         return {
#             'dates': self.results['date'].dt.strftime('%Y-%m-%d').tolist(),
#             'total_cost': self.results['cost'].apply(lambda x: x['total']).cumsum().tolist(),
#             'total_emissions': self.results['emissions'].cumsum().tolist(),
#             'total_energy': self.results['energy'].apply(lambda x: x['total_energy_mj']).cumsum().tolist()
#         }
#
#     def get_summary_stats(self):
#         if self.results is None:
#             self.simulate()
#
#         return {
#             'total_cost': self.results['cost'].apply(lambda x: x['total']).sum(),
#             'total_emissions': self.results['emissions'].sum(),
#             'total_energy_mj': self.results['energy'].apply(lambda x: x['total_energy_mj']).sum(),
#             'avg_daily_cost': self.results['cost'].apply(lambda x: x['total']).mean(),
#             'avg_daily_emissions': self.results['emissions'].mean(),
#             'avg_daily_energy': self.results['energy'].apply(lambda x: x['total_energy_mj']).mean()
#         }