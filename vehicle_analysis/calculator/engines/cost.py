from vehicles.models import ICEVehicle, EVVehicle, HEVVehicle, PHEVVehicle


class TCOService:
    """Сервис расчета полной стоимости владения (TCO)"""

    # Константы
    ANNUAL_KM = 20000  # среднегодовой пробег (км)
    LIFETIME_YEARS = 10  # срок службы (лет)
    INSURANCE_COST = 30000  # годовая страховка (руб)
    MAINTENANCE_COST_ICE = 5  # ТО ДВС (руб/км)
    MAINTENANCE_COST_EV = 2  # ТО электромобиля (руб/км)
    TAX_RATE = 0.01  # транспортный налог (% от стоимости)
    DISPOSAL_COST_ICE = 20000  # утилизация ДВС (руб)
    DISPOSAL_COST_EV = 100000  # утилизация электромобиля (руб)
    FUEL_PRICE = 55  # руб/л (средняя цена бензина)
    ELECTRICITY_PRICE = 5  # руб/кВт·ч (средний тариф)
    PHEV_ELECTRIC_RANGE_FACTOR = 0.8  # Коэффициент использования электрического диапазона

    @classmethod
    def calculate_tco(cls, vehicle, distance_km=None, driving_conditions=None):
        """
        Расчет полной стоимости владения

        :param vehicle: объект Vehicle (ICEVehicle/EVVehicle/HEVVehicle)
        :param distance_km: пробег за весь срок (если None - расчет по умолчанию)
        :return: словарь с компонентами TCO
        """
        if distance_km is None:
            distance_km = cls.ANNUAL_KM * cls.LIFETIME_YEARS

        return {
            'tco_total': cls._calculate_total_cost(vehicle, distance_km, driving_conditions),
            'tco_per_km': cls._calculate_cost_per_km(vehicle, distance_km, driving_conditions),
            'components': cls._calculate_cost_components(vehicle, distance_km, driving_conditions),
            'distance_km': distance_km,
            'lifetime_years': cls.LIFETIME_YEARS
        }

    @classmethod
    def _calculate_total_cost(cls, vehicle, distance_km, driving_conditions):
        """Общая стоимость владения"""
        components = cls._calculate_cost_components(vehicle, distance_km, driving_conditions)
        return sum(components.values())

    @classmethod
    def _calculate_cost_per_km(cls, vehicle, distance_km, driving_conditions):
        """Стоимость за 1 км"""
        return cls._calculate_total_cost(vehicle, distance_km, driving_conditions) / distance_km

    @classmethod
    def _calculate_cost_components(cls, vehicle, distance_km, driving_conditions):
        """Все компоненты стоимости"""
        return {
            'production': cls._calculate_production_cost(vehicle),
            'usage': cls._calculate_usage_cost(vehicle, distance_km, driving_conditions),
            'recycling': cls._calculate_recycle_cost(vehicle)
        }

    @classmethod
    def _calculate_production_cost(cls, vehicle):
        """Стоимость производства (покупная цена)"""
        return vehicle.production_price

    @classmethod
    def _calculate_usage_cost(cls, vehicle, distance_km, driving_conditions):
        """Эксплуатационные затраты"""
        energy_cost = cls._calculate_energy_cost(vehicle, distance_km, driving_conditions)
        maintenance_cost = cls._calculate_maintenance_cost(vehicle, distance_km)
        insurance_cost = cls.INSURANCE_COST * cls.LIFETIME_YEARS
        tax_cost = vehicle.production_price * cls.TAX_RATE * cls.LIFETIME_YEARS

        return energy_cost + maintenance_cost + insurance_cost + tax_cost

    @classmethod
    def _calculate_energy_cost(cls, vehicle, distance_km, driving_conditions):
        """Затраты на энергию (топливо/электричество)"""
        if isinstance(vehicle, ICEVehicle):
            return cls._calculate_fuel_cost(vehicle, distance_km)
        elif isinstance(vehicle, EVVehicle):
            return cls._calculate_electricity_cost(vehicle, distance_km)
        elif isinstance(vehicle, HEVVehicle):
            return cls._calculate_hybrid_cost(vehicle, distance_km, driving_conditions)
        elif isinstance(vehicle, PHEVVehicle):
            return cls._calculate_phev_cost(vehicle, distance_km, driving_conditions)
        else:
            raise ValueError(f"Unsupported vehicle type: {type(vehicle)}")

    @classmethod
    def _calculate_fuel_cost(cls, vehicle, distance_km):
        """Затраты на топливо для ДВС"""
        fuel_consumption = vehicle.fuel_consumption_lp100km / 100  # л/км
        return fuel_consumption * distance_km * cls.FUEL_PRICE

    @classmethod
    def _calculate_electricity_cost(cls, vehicle, distance_km):
        """Затраты на электроэнергию"""
        energy_consumption = vehicle.energy_consumption_kwhp100km / 100  # кВт·ч/км
        return energy_consumption * distance_km * cls.ELECTRICITY_PRICE

    @classmethod
    def _calculate_hybrid_cost(cls, vehicle, distance_km, driving_conditions):
        """Расчет стоимости владения гибридом (HEV) на основе:
           - Расхода топлива (fuel_consumption_lp100km)
           - КПД ДВС (engine_efficiency)
           - Условий движения (city/highway)
           - Рекуперации (учитывается через снижение расхода топлива)

        Args:
            vehicle: Объект с параметрами гибрида
            distance_km: Пройденное расстояние (км)
            driving_conditions: 'city' или 'highway'

        Returns:
            Стоимость в рублях (или другой валюте)
        """
        if driving_conditions == "city":
            ice_share = 0.3 + (vehicle.mass_kg / 2000) * 0.1
        else:
            c_d = 0.3
            air_resistance = vehicle.frontal_area_m2 * c_d
            ice_share = 0.7 + (air_resistance / 0.7) * 0.2

        fuel_used_liters = (vehicle.fuel_consumption_lp100km * distance_km / 100) * ice_share
        effective_fuel_used = fuel_used_liters / vehicle.engine_efficiency

        fuel_price_per_liter = 50
        fuel_cost = effective_fuel_used * fuel_price_per_liter

        return fuel_cost

    @classmethod
    def _calculate_phev_cost(cls, vehicle, distance_km, driving_conditions):
        """
        Расчет стоимости поездки на PHEV в рублях с учетом типа дороги
        :param vehicle: объект PHEV с параметрами:
            - battery_only_range_km: запас хода на электротяге (км)
            - mpg_gas_only: расход в режиме ДВС (миль на галлон)
            - kwh_100_km_battery_only: потребление энергии (кВтч/100км)
        :param distance_km: пробег (км)
        :param driving_conditions: тип дороги ('city', 'highway', 'mixed')
        :return: словарь с детализацией расходов
        """
        # Коэффициенты влияния типа дороги на расход
        ROAD_TYPE_FACTORS = {
            'city': {'electric': 1.2, 'fuel': 1.3},  # Городской цикл (частые остановки)
            'highway': {'electric': 0.9, 'fuel': 0.85},  # Трасса (равномерное движение)
            'mixed': {'electric': 1.0, 'fuel': 1.0}  # Смешанный режим
        }

        ELECTRICITY_PRICE_RUB = 5.0  # руб/кВт·ч
        FUEL_PRICE_RUB = 55.0  # руб/литр

        factors = ROAD_TYPE_FACTORS.get(driving_conditions, ROAD_TYPE_FACTORS['mixed'])

        # Разделяем пробег на электротяге и ДВС
        electric_range_km = vehicle.battery_only_range_km * factors['electric']
        electric_distance = min(distance_km, electric_range_km)
        ice_distance = max(0, distance_km - electric_range_km)

        # Расчет потребления с учетом типа дороги
        electric_consumption_kwh = (vehicle.kwh_100_km_battery_only / 100) * electric_distance * factors['electric']

        # Конвертация MPG в л/100км с поправкой на тип дороги
        fuel_consumption_l_100km = (235.214583 / vehicle.mpg_gas_only) * factors['fuel']
        fuel_consumption_liters = (fuel_consumption_l_100km / 100) * ice_distance

        # Расчет стоимости
        electricity_cost_rub = electric_consumption_kwh * ELECTRICITY_PRICE_RUB
        fuel_cost_rub = fuel_consumption_liters * FUEL_PRICE_RUB

        return electricity_cost_rub + fuel_cost_rub

    @classmethod
    def _calculate_maintenance_cost(cls, vehicle, distance_km):
        """Затраты на ТО"""
        if isinstance(vehicle, ICEVehicle):
            return distance_km * cls.MAINTENANCE_COST_ICE
        elif isinstance(vehicle, EVVehicle):
            return distance_km * cls.MAINTENANCE_COST_EV
        elif isinstance(vehicle, HEVVehicle) or isinstance(vehicle, PHEVVehicle):
            return distance_km * (cls.MAINTENANCE_COST_ICE + cls.MAINTENANCE_COST_EV) / 2
        else:
            return 0

    @classmethod
    def _calculate_recycle_cost(cls, vehicle):
        """Стоимость утилизации"""
        if isinstance(vehicle, EVVehicle):
            return cls.DISPOSAL_COST_EV
        elif isinstance(vehicle, ICEVehicle):
            return cls.DISPOSAL_COST_ICE
        elif isinstance(vehicle, HEVVehicle) or isinstance(vehicle, PHEVVehicle):
            return (cls.DISPOSAL_COST_ICE + cls.DISPOSAL_COST_EV) / 2
        else:
            return 0

    @classmethod
    def compare_tco(cls, vehicles, distance_km=None):
        """Сравнение TCO для нескольких автомобилей"""
        return [{
            'vehicle': v,
            'tco': cls.calculate_tco(v, distance_km)
        } for v in vehicles]
