from datetime import datetime
from vehicles.models import ICEVehicle, EVVehicle, HEVVehicle, PHEVVehicle


class TimeBasedCostCalculator:
    """Расчет стоимости владения на основе времени использования для всех типов ТС"""

    # Константы стоимости
    INSURANCE_PER_DAY = 82.19  # руб/день (30000 руб/год)
    TAX_RATE = 0.01  # Налог (% от стоимости авто в год)
    DEPRECIATION_RATE = 0.15  # Годовая амортизация

    # Стоимость обслуживания (руб/час)
    MAINTENANCE_PER_HOUR = {
        'ice': 150,  # ДВС
        'ev': 80,  # Электромобиль
        'hybrid': 115  # Гибриды
    }

    # Цены на энергоносители (руб)
    FUEL_PRICE = 55  # Бензин АИ-95
    DIESEL_PRICE = 52  # Дизельное топливо
    ELECTRICITY_PRICE = 5  # Тариф на электроэнергию
    LPG_PRICE = 28  # Газ

    @classmethod
    def calculate_daily_cost(cls, vehicle, hours, date):
        """
        Расчет суточных затрат на владение ТС

        :param vehicle: Транспортное средство
        :param hours: Часы использования в день
        :param date: Дата для определения сезона
        :return: Словарь с компонентами затрат
        """
        season_factor = cls._get_season_factor(date.month)
        road_type = cls._get_road_type_by_month(date.month)
        vehicle_type = cls._get_vehicle_type(vehicle)

        return {
            'energy': cls._calculate_energy_cost(vehicle, hours, season_factor, road_type),
            'maintenance': hours * cls.MAINTENANCE_PER_HOUR[vehicle_type] * season_factor,
            'insurance': cls.INSURANCE_PER_DAY,
            'tax': cls._calculate_daily_tax(vehicle),
            'depreciation': cls._calculate_daily_depreciation(vehicle),
            'total': 0  # Сумма рассчитывается ниже
        }

    @classmethod
    def _calculate_energy_cost(cls, vehicle, hours, season_factor, road_type):
        """Расчет затрат на энергию"""
        if isinstance(vehicle, ICEVehicle):
            return cls._calculate_ice_cost(vehicle, hours, season_factor, road_type)
        elif isinstance(vehicle, EVVehicle):
            return cls._calculate_ev_cost(vehicle, hours, season_factor, road_type)
        elif isinstance(vehicle, HEVVehicle):
            return cls._calculate_hev_cost(vehicle, hours, season_factor, road_type)
        elif isinstance(vehicle, PHEVVehicle):
            return cls._calculate_phev_cost(vehicle, hours, season_factor, road_type)

    @classmethod
    def _calculate_ice_cost(cls, vehicle, hours, season_factor, road_type):
        """Расчет для ДВС"""
        avg_speed = 50 if road_type == 'highway' else 30  # км/ч
        distance = hours * avg_speed
        fuel_used = (vehicle.fuel_consumption_lp100km / 100) * distance * season_factor

        # Определяем цену топлива
        fuel_price = {
            'gasoline': cls.FUEL_PRICE,
            'diesel': cls.DIESEL_PRICE,
            'lpg': cls.LPG_PRICE
        }.get(vehicle.fuel_type, cls.FUEL_PRICE)

        return fuel_used * fuel_price

    @classmethod
    def _calculate_ev_cost(cls, vehicle, hours, season_factor, road_type):
        """Расчет для электромобиля"""
        avg_speed = 60 if road_type == 'highway' else 40  # км/ч
        distance = hours * avg_speed

        # Учет рекуперации в городском цикле
        efficiency_factor = 0.85 if road_type == 'city' else 1.0

        energy_used = (vehicle.energy_consumption_kwhp100km / 100 *
                       distance * season_factor * efficiency_factor)

        return energy_used * cls.ELECTRICITY_PRICE

    @classmethod
    def _calculate_hev_cost(cls, vehicle, hours, season_factor, road_type):
        """Расчет для гибрида (HEV)"""
        avg_speed = 55 if road_type == 'highway' else 35  # км/ч
        distance = hours * avg_speed

        # Доля электротяги
        electric_share = 0.2 if road_type == 'highway' else 0.4

        # Затраты на топливо
        fuel_used = (vehicle.fuel_consumption_lp100km / 100 *
                     distance * (1 - electric_share) * season_factor)
        fuel_cost = fuel_used * cls.FUEL_PRICE

        # Затраты на электроэнергию
        electric_energy = (vehicle.energy_consumption_kwhp100km / 100 *
                           distance * electric_share * season_factor)
        electric_cost = electric_energy * cls.ELECTRICITY_PRICE

        return fuel_cost + electric_cost

    @classmethod
    def _calculate_phev_cost(cls, vehicle, hours, season_factor, road_type):
        """Расчет для подключаемого гибрида (PHEV)"""
        avg_speed = 50 if road_type == 'highway' else 30  # км/ч
        total_distance = hours * avg_speed

        # Пробег на электротяге
        electric_range = min(
            vehicle.battery_only_range_km * season_factor,
            total_distance * 0.7  # 70% пробега на электротяге
        )
        ice_distance = max(0, total_distance - electric_range)

        # Затраты на электроэнергию
        electric_energy = (vehicle.kwh_100_km_battery_only / 100 *
                           electric_range * season_factor)
        electric_cost = electric_energy * cls.ELECTRICITY_PRICE

        # Затраты на топливо
        fuel_used = (235.214583 / vehicle.mpg_gas_only / 100 *  # Конвертация MPG в л/100км
                     ice_distance * season_factor)
        fuel_cost = fuel_used * cls.FUEL_PRICE

        return electric_cost + fuel_cost

    @classmethod
    def _calculate_daily_tax(cls, vehicle):
        """Ежедневный транспортный налог"""
        return (vehicle.production_price * cls.TAX_RATE) / 365

    @classmethod
    def _calculate_daily_depreciation(cls, vehicle):
        """Ежедневная амортизация"""
        return (vehicle.production_price * cls.DEPRECIATION_RATE) / 365

    @staticmethod
    def _get_season_factor(month):
        """Сезонные коэффициенты затрат"""
        if month in [12, 1, 2]:  # Зима
            return 1.2
        elif month in [6, 7, 8]:  # Лето
            return 0.9
        return 1.0

    @staticmethod
    def _get_road_type_by_month(month):
        """Определение преобладающего типа дороги по сезону"""
        if month in [12, 1, 2]:  # Зимой больше городского цикла
            return 'city'
        elif month in [6, 7, 8]:  # Летом больше трассы
            return 'highway'
        return 'mixed'

    @staticmethod
    def _get_vehicle_type(vehicle):
        """Определение типа транспортного средства"""
        if isinstance(vehicle, ICEVehicle):
            return 'ice'
        elif isinstance(vehicle, EVVehicle):
            return 'ev'
        return 'hybrid'