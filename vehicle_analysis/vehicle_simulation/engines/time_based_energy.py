from datetime import datetime
from vehicles.models import ICEVehicle, EVVehicle, HEVVehicle, PHEVVehicle


class TimeBasedEnergy:
    """Расчет энергопотребления на основе времени для всех типов транспортных средств"""

    # Энергетические константы
    FUEL_ENERGY_DENSITY = 34.5  # МДж/л бензина
    ELECTRICITY_ENERGY = 3.6  # МДж/кВт·ч
    PHEV_ELECTRIC_SHARE = 0.7  # Доля пробега на электротяге для PHEV
    HEV_ELECTRIC_SHARE_CITY = 0.4  # Доля электротяги для гибридов в городе
    HEV_ELECTRIC_SHARE_HW = 0.2  # Доля электротяги для гибридов на трассе

    @classmethod
    def calculate_daily_energy(cls, vehicle, hours, date):
        """
        Расчет суточного энергопотребления с учетом сезонных коэффициентов

        :param vehicle: Транспортное средство
        :param hours: Часы использования в день
        :param date: Дата для определения сезона
        :return: Словарь с показателями энергопотребления
        """
        season_factor = cls._get_season_factor(date.month)
        road_type = cls._get_road_type_by_month(date.month)

        if isinstance(vehicle, ICEVehicle):
            return cls._calculate_ice_energy(vehicle, hours, season_factor, road_type)
        elif isinstance(vehicle, EVVehicle):
            return cls._calculate_ev_energy(vehicle, hours, season_factor, road_type)
        elif isinstance(vehicle, HEVVehicle):
            return cls._calculate_hev_energy(vehicle, hours, season_factor, road_type)
        elif isinstance(vehicle, PHEVVehicle):
            return cls._calculate_phev_energy(vehicle, hours, season_factor, road_type)
        else:
            raise ValueError(f"Unsupported vehicle type: {type(vehicle)}")

    @classmethod
    def _calculate_ice_energy(cls, vehicle, hours, season_factor, road_type):
        """Расчет для ДВС"""
        avg_speed = 50 if road_type == 'highway' else 30  # км/ч
        distance = hours * avg_speed
        fuel_used = (vehicle.fuel_consumption_lp100km / 100) * distance * season_factor

        return {
            'fuel_liters': fuel_used,
            'total_energy_mj': fuel_used * cls.FUEL_ENERGY_DENSITY,
            'energy_type': 'fuel',
            'efficiency': 0.3  # Средний КПД ДВС
        }

    @classmethod
    def _calculate_ev_energy(cls, vehicle, hours, season_factor, road_type):
        """Расчет для электромобиля"""
        avg_speed = 60 if road_type == 'highway' else 40  # км/ч
        distance = hours * avg_speed
        energy_kwh = (vehicle.energy_consumption_kwhp100km / 100) * distance * season_factor

        return {
            'energy_kwh': energy_kwh,
            'total_energy_mj': energy_kwh * cls.ELECTRICITY_ENERGY,
            'energy_type': 'electricity',
            'battery_usage_percent': (energy_kwh / vehicle.battery_capacity_kwh) * 100,
            'efficiency': 0.9  # КПД электропривода
        }

    @classmethod
    def _calculate_hev_energy(cls, vehicle, hours, season_factor, road_type):
        """Расчет для гибрида (HEV)"""
        avg_speed = 55 if road_type == 'highway' else 35  # км/ч
        distance = hours * avg_speed

        # Определяем долю электротяги
        electric_share = (cls.HEV_ELECTRIC_SHARE_HW if road_type == 'highway'
                          else cls.HEV_ELECTRIC_SHARE_CITY)

        # Расчет топливной составляющей
        fuel_used = (vehicle.fuel_consumption_lp100km / 100 *
                     distance * (1 - electric_share) * season_factor)

        # Расчет электрической составляющей
        electric_energy = (vehicle.energy_consumption_kwhp100km / 100 *
                           distance * electric_share * season_factor)

        return {
            'fuel_liters': fuel_used,
            'energy_kwh': electric_energy,
            'total_energy_mj': (fuel_used * cls.FUEL_ENERGY_DENSITY +
                                electric_energy * cls.ELECTRICITY_ENERGY),
            'energy_type': 'hybrid',
            'electric_share_percent': electric_share * 100,
            'efficiency': 0.45  # Средний КПД гибрида
        }

    @classmethod
    def _calculate_phev_energy(cls, vehicle, hours, season_factor, road_type):
        """Расчет для подключаемого гибрида (PHEV)"""
        avg_speed = 50 if road_type == 'highway' else 30  # км/ч
        total_distance = hours * avg_speed

        # Пробег на электротяге (ограничен запасом батареи)
        electric_range = min(
            vehicle.battery_only_range_km * season_factor,
            total_distance * cls.PHEV_ELECTRIC_SHARE
        )
        ice_distance = max(0, total_distance - electric_range)

        # Расчет электрической составляющей
        electric_energy = (vehicle.kwh_100_km_battery_only / 100 *
                           electric_range * season_factor)

        # Расчет топливной составляющей
        fuel_used = (235.214583 / vehicle.mpg_gas_only / 100 *  # Конвертация MPG в л/100км
                     ice_distance * season_factor)

        return {
            'fuel_liters': fuel_used,
            'energy_kwh': electric_energy,
            'total_energy_mj': (fuel_used * cls.FUEL_ENERGY_DENSITY +
                                electric_energy * cls.ELECTRICITY_ENERGY),
            'energy_type': 'phev',
            'electric_share_percent': (electric_range / total_distance) * 100,
            'efficiency': 0.6  # Средний КПД PHEV
        }

    @staticmethod
    def _get_season_factor(month):
        """Сезонные коэффициенты энергопотребления"""
        if month in [12, 1, 2]:  # Зима
            return 1.25
        elif month in [6, 7, 8]:  # Лето
            return 0.9
        return 1.0  # Весна/осень

    @staticmethod
    def _get_road_type_by_month(month):
        """Определение преобладающего типа дороги по сезону"""
        if month in [12, 1, 2]:  # Зимой больше городского цикла
            return 'city'
        elif month in [6, 7, 8]:  # Летом больше трассы
            return 'highway'
        return 'mixed'