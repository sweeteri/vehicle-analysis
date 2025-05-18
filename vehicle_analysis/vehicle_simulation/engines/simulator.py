from datetime import timedelta
from calculator.engines.energy import EnergyCalculator
from calculator.engines.emissions import EmissionsCalculator
from calculator.engines.cost import TCOService


class VehicleSimulator:
    def __init__(self, vehicle, daily_distance_km, daily_usage_hours,
                 start_date, end_date, energy_source, driving_conditions):
        """
        Инициализация симулятора

        :param vehicle: Объект транспортного средства
        :param daily_distance_km: Средний дневной пробег (км)
        :param daily_usage_hours: Часы эксплуатации в день
        :param start_date: Дата начала симуляции
        :param end_date: Дата окончания симуляции
        :param energy_source: Источник энергии ('coal', 'gas', etc.)
        :param driving_conditions: Условия движения ('city', 'highway', 'mixed')
        """
        self.vehicle = vehicle
        self.daily_distance_km = daily_distance_km
        self.daily_usage_hours = daily_usage_hours
        self.start_date = start_date
        self.end_date = end_date
        self.energy_source = energy_source
        self.driving_conditions = driving_conditions

        # Рассчитываем количество дней симуляции
        self.days = (end_date - start_date).days + 1

        # Результаты симуляции
        self._daily_results = {}
        self._cumulative_results = {
            'dates': [],
            'energy': {},
            'emissions': {},
            'cost': {}
        }

    def simulate(self):
        """Запуск симуляции для всего периода"""
        # Очищаем предыдущие результаты
        self._daily_results = {}
        self._cumulative_results = {
            'dates': [],
            'energy': {},
            'emissions': {},
            'cost': {}
        }

        # Рассчитываем дневные показатели
        daily_energy = self._calculate_daily_energy()
        daily_emissions = self._calculate_daily_emissions()
        daily_cost = self._calculate_daily_cost()

        # Заполняем результаты по дням
        for day in range(1, self.days + 1):
            current_date = self.start_date + timedelta(days=day - 1)

            # Сохраняем дату
            self._cumulative_results['dates'].append(current_date)

            # Рассчитываем накопленные значения
            for metric in ['energy', 'emissions', 'cost']:
                daily_value = locals()[f'daily_{metric}']
                if isinstance(daily_value, dict):
                    # Для энергии (много показателей)
                    if metric not in self._cumulative_results:
                        self._cumulative_results[metric] = {}

                    for key, value in daily_value.items():
                        if key not in self._cumulative_results[metric]:
                            self._cumulative_results[metric][key] = {}
                        self._cumulative_results[metric][key][day] = value * day
                else:
                    # Для выбросов и стоимости (один показатель)
                    self._cumulative_results[metric][day] = daily_value * day

            # Сохраняем дневные результаты
            self._daily_results[day] = {
                'date': current_date,
                'energy': daily_energy,
                'emissions': daily_emissions,
                'cost': daily_cost,
                'distance': self.daily_distance_km,
                'hours': self.daily_usage_hours
            }

        return self

    def _calculate_daily_energy(self):
        """Расчет дневного потребления энергии"""
        # Используем EnergyCalculator из calculator
        energy_data = EnergyCalculator.calculate_energy_consumption(
            self.vehicle,
            self.daily_distance_km,
            self.driving_conditions
        )

        # Добавляем расчеты, основанные на часах эксплуатации
        if hasattr(self.vehicle, 'idle_energy_consumption_kwh'):
            idle_energy = self.vehicle.idle_energy_consumption_kwh * self.daily_usage_hours
            if 'energy_kwh' in energy_data:
                energy_data['energy_kwh'] += idle_energy
            else:
                energy_data['energy_kwh'] = idle_energy

            # Пересчитываем общую энергию в МДж (1 кВт·ч = 3.6 МДж)
            energy_data['total_energy_mj'] = energy_data.get('total_energy_mj', 0) + (idle_energy * 3.6)

        return energy_data

    def _calculate_daily_emissions(self):
        """Расчет дневных выбросов"""
        # Основные выбросы от пробега
        emissions = EmissionsCalculator.calculate_co2(
            self.vehicle,
            self.daily_distance_km,
            self.energy_source,
            self.driving_conditions
        )

        # Добавляем выбросы от простоя (если есть данные)
        if hasattr(self.vehicle, 'idle_emissions_kgph'):
            idle_emissions = self.vehicle.idle_emissions_kgph * self.daily_usage_hours
            emissions += idle_emissions * 1000  # переводим кг в граммы

        return emissions

    def _calculate_daily_cost(self):
        """Расчет дневной стоимости эксплуатации"""
        # Основная стоимость от пробега
        cost = TCOService._calculate_energy_cost(
            self.vehicle,
            self.daily_distance_km,
            self.driving_conditions
        )

        # Добавляем стоимость простоя (если есть данные)
        if hasattr(self.vehicle, 'idle_cost_rubph'):
            idle_cost = self.vehicle.idle_cost_rubph * self.daily_usage_hours
            cost += idle_cost

        return cost

    def get_daily_data(self, day=None):
        """
        Получение дневных данных

        :param day: Номер дня (если None - возвращаются все данные)
        :return: Словарь с дневными данными
        """
        if day:
            return self._daily_results.get(day)
        return self._daily_results

    def get_cumulative_data(self):
        """
        Получение накопленных данных за период

        :return: Словарь с накопленными данными
        """
        return self._cumulative_results

    def get_summary_stats(self):
        """
        Получение сводной статистики за весь период

        :return: Словарь с итоговыми показателями
        """
        last_day = self.days
        return {
            'total_distance': self.daily_distance_km * last_day,
            'total_hours': self.daily_usage_hours * last_day,
            'total_energy': {
                k: v * last_day
                for k, v in self._daily_results[1]['energy'].items()
                if isinstance(v, (int, float))
            },
            'total_emissions': self._daily_results[1]['emissions'] * last_day,
            'total_cost': self._daily_results[1]['cost'] * last_day,
            'avg_per_km': {
                'energy': {
                    k: v / self.daily_distance_km
                    for k, v in self._daily_results[1]['energy'].items()
                    if isinstance(v, (int, float))
                },
                'emissions': self._daily_results[1]['emissions'] / self.daily_distance_km,
                'cost': self._daily_results[1]['cost'] / self.daily_distance_km
            },
            'avg_per_hour': {
                'energy': {
                    k: v / self.daily_usage_hours
                    for k, v in self._daily_results[1]['energy'].items()
                    if isinstance(v, (int, float))
                },
                'emissions': self._daily_results[1]['emissions'] / self.daily_usage_hours,
                'cost': self._daily_results[1]['cost'] / self.daily_usage_hours
            }
        }