from datetime import datetime
from vehicles.models import ICEVehicle, EVVehicle, HEVVehicle, PHEVVehicle


class TimeBasedEmissions:
    """Расчет выбросов CO₂ на основе времени использования для всех типов ТС"""

    # Коэффициенты выбросов (г/кВт·ч) для разных источников энергии
    EMISSION_FACTORS = {
        'coal': 900,  # Угольные электростанции
        'gas': 450,  # Газовые электростанции
        'nuclear': 0,  # Атомные электростанции
        'hydro': 0,  # Гидроэлектростанции
        'renewables': 50,  # ВИЭ (солнце/ветер)
        'eu_avg': 300,  # Среднее по ЕС
        'russia_avg': 350  # Среднее по России
    }

    # Коэффициенты выбросов для ДВС (г/л бензина)
    ICE_EMISSION_FACTOR = 2300
    DIESEL_EMISSION_FACTOR = 2650

    # Коэффициенты для гибридов
    HEV_ELECTRIC_SHARE_CITY = 0.4  # Доля электротяги в городе
    HEV_ELECTRIC_SHARE_HW = 0.2  # Доля электротяги на трассе

    @classmethod
    def calculate_daily_emissions(cls, vehicle, hours, date, energy_source='eu_avg'):
        """
        Расчет суточных выбросов CO₂ с учетом сезона и типа двигателя

        :param vehicle: Транспортное средство
        :param hours: Часы использования в день
        :param date: Дата для определения сезона
        :param energy_source: Тип источника энергии для электромобилей
        :return: Выбросы CO₂ в граммах
        """
        season_factor = cls._get_season_factor(date.month)
        road_type = cls._get_road_type_by_month(date.month)

        if isinstance(vehicle, ICEVehicle):
            return cls._calculate_ice_emissions(vehicle, hours, season_factor, road_type)
        elif isinstance(vehicle, EVVehicle):
            return cls._calculate_ev_emissions(vehicle, hours, energy_source, season_factor, road_type)
        elif isinstance(vehicle, HEVVehicle):
            return cls._calculate_hev_emissions(vehicle, hours, season_factor, road_type, energy_source)
        elif isinstance(vehicle, PHEVVehicle):
            return cls._calculate_phev_emissions(vehicle, hours, season_factor, road_type, energy_source)
        else:
            raise ValueError(f"Unsupported vehicle type: {type(vehicle)}")

    @classmethod
    def _calculate_ice_emissions(cls, vehicle, hours, season_factor, road_type):
        """Расчет выбросов для ДВС"""
        avg_speed = 50 if road_type == 'highway' else 30  # км/ч
        distance = hours * avg_speed
        fuel_used = (vehicle.fuel_consumption_lp100km / 100) * distance * season_factor

        # Определяем коэффициент выбросов в зависимости от типа топлива
        emission_factor = (cls.DIESEL_EMISSION_FACTOR if vehicle.fuel_type == 'diesel'
                           else cls.ICE_EMISSION_FACTOR)

        return fuel_used * emission_factor

    @classmethod
    def _calculate_ev_emissions(cls, vehicle, hours, energy_source, season_factor, road_type):
        """Расчет выбросов для электромобиля"""
        avg_speed = 60 if road_type == 'highway' else 40  # км/ч
        distance = hours * avg_speed
        energy_used = (vehicle.energy_consumption_kwhp100km / 100) * distance * season_factor

        # Учет рекуперации при городском цикле
        if road_type == 'city':
            energy_used *= 0.85  # Снижение на 15% благодаря рекуперации

        return energy_used * cls.EMISSION_FACTORS.get(energy_source, 300)

    @classmethod
    def _calculate_hev_emissions(cls, vehicle, hours, season_factor, road_type, energy_source):
        """Расчет выбросов для гибрида (HEV)"""
        avg_speed = 55 if road_type == 'highway' else 35  # км/ч
        distance = hours * avg_speed

        # Определяем долю электротяги
        electric_share = (cls.HEV_ELECTRIC_SHARE_HW if road_type == 'highway'
                          else cls.HEV_ELECTRIC_SHARE_CITY)

        # Выбросы от ДВС составляющей
        fuel_used = (vehicle.fuel_consumption_lp100km / 100 *
                     distance * (1 - electric_share) * season_factor)
        ice_emissions = fuel_used * cls.ICE_EMISSION_FACTOR

        # Выбросы от электрической составляющей (генерация энергии)
        electric_energy = (vehicle.energy_consumption_kwhp100km / 100 *
                           distance * electric_share * season_factor)
        ev_emissions = electric_energy * cls.EMISSION_FACTORS.get(energy_source, 300)

        return ice_emissions + ev_emissions

    @classmethod
    def _calculate_phev_emissions(cls, vehicle, hours, season_factor, road_type, energy_source):
        """Расчет выбросов для подключаемого гибрида (PHEV)"""
        avg_speed = 50 if road_type == 'highway' else 30  # км/ч
        total_distance = hours * avg_speed

        # Пробег на электротяге (ограничен запасом батареи)
        electric_range = min(
            vehicle.battery_only_range_km * season_factor,
            total_distance * 0.7  # 70% пробега на электротяге
        )
        ice_distance = max(0, total_distance - electric_range)

        # Выбросы от электрической составляющей
        electric_energy = (vehicle.kwh_100_km_battery_only / 100 *
                           electric_range * season_factor)
        ev_emissions = electric_energy * cls.EMISSION_FACTORS.get(energy_source, 300)

        # Выбросы от ДВС составляющей
        fuel_used = (235.214583 / vehicle.mpg_gas_only / 100 *  # Конвертация MPG в л/100км
                     ice_distance * season_factor)
        ice_emissions = fuel_used * cls.ICE_EMISSION_FACTOR

        return ev_emissions + ice_emissions

    @staticmethod
    def _get_season_factor(month):
        """Сезонные коэффициенты выбросов"""
        if month in [12, 1, 2]:  # Зима - повышенные выбросы
            return 1.15
        elif month in [6, 7, 8]:  # Лето - пониженные выбросы
            return 0.95
        return 1.0

    @staticmethod
    def _get_road_type_by_month(month):
        """Определение преобладающего типа дороги по сезону"""
        if month in [12, 1, 2]:  # Зимой больше городского цикла
            return 'city'
        elif month in [6, 7, 8]:  # Летом больше трассы
            return 'highway'
        return 'mixed'

    @classmethod
    def get_energy_sources(cls):
        """Список доступных источников энергии для расчета"""
        return [
            {'id': 'coal', 'name': 'Угольные станции'},
            {'id': 'gas', 'name': 'Газовые станции'},
            {'id': 'nuclear', 'name': 'Атомные станции'},
            {'id': 'hydro', 'name': 'Гидроэнергетика'},
            {'id': 'renewables', 'name': 'ВИЭ (солнце/ветер)'},
            {'id': 'eu_avg', 'name': 'Среднее по ЕС'},
            {'id': 'russia_avg', 'name': 'Среднее по России'}
        ]