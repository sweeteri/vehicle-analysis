from vehicles.models import ICEVehicle, HEVVehicle, EVVehicle, PHEVVehicle


class EmissionsCalculator:
    """Калькулятор выбросов CO₂ для разных типов автомобилей"""

    # Коэффициенты выбросов (г/кВт·ч) для разных источников энергии
    EMISSION_FACTORS = {
        'coal': 900,  # Угольные станции
        'gas': 450,  # Газовые станции
        'nuclear': 0,  # АЭС
        'hydro': 0,  # ГЭС
        'eu_avg': 300,  # Среднее по ЕС
        'renewables': 50  # ВИЭ
    }

    # Коэффициенты выбросов ДВС (г/л бензина)
    ICE_EMISSION_FACTOR = 2300
    PHEV_ELECTRIC_RANGE_FACTOR = 0.8  # Коэффициент использования электрического диапазона PHEV

    @classmethod
    def calculate_co2(cls, vehicle, distance_km, energy_source, driving_conditions,
                      use_recuperation=True, urban_share=0.5):
        """
        Расчет выбросов CO₂ за поездку
        """
        if isinstance(vehicle, ICEVehicle):
            return cls._calculate_ice_co2(vehicle, distance_km)
        elif isinstance(vehicle, EVVehicle):
            return cls._calculate_ev_co2(
                vehicle, distance_km, energy_source,
                use_recuperation, urban_share
            )
        elif isinstance(vehicle, HEVVehicle):
            return cls._calculate_hev_co2(
                vehicle, distance_km, driving_conditions,
            )
        elif isinstance(vehicle, PHEVVehicle):
            return cls._calculate_phev_co2(
                vehicle, distance_km, energy_source
            )
        else:
            raise ValueError(f"Unsupported vehicle type: {type(vehicle)}")

    @classmethod
    def _calculate_ice_co2(cls, vehicle, distance_km):
        """Расчет выбросов для ДВС"""
        fuel_consumption = vehicle.fuel_consumption_lp100km / 100  # л/км
        return fuel_consumption * distance_km * cls.ICE_EMISSION_FACTOR

    @classmethod
    def _calculate_ev_co2(cls, vehicle, distance_km, energy_source,
                          use_recuperation, urban_share):
        """Расчет выбросов для электромобиля"""
        energy_consumption = vehicle.energy_consumption_kwhp100km / 100  # кВт·ч/км

        if use_recuperation:
            recuperation_efficiency = 0.6  # КПД рекуперации 60%
            urban_energy = energy_consumption * urban_share * (1 - 0.2 * recuperation_efficiency)
            highway_energy = energy_consumption * (1 - urban_share)
            total_energy = (urban_energy + highway_energy) * distance_km
        else:
            total_energy = energy_consumption * distance_km

        emission_factor = cls.EMISSION_FACTORS.get(energy_source, 300)
        return total_energy * emission_factor

    @classmethod
    def _calculate_hev_co2(cls, vehicle, distance_km, driving_conditions):
        """Расчёт выбросов CO₂ для гибрида (HEV) на основе:
           - Расхода топлива (fuel_consumption_lp100km)
           - Выбросов CO₂ на литр (co2_emissions_gl)
           - КПД ДВС (engine_efficiency)
           - Условий движения (city/highway)
           - Массы (mass_kg) и лобовой площади (frontal_area_m2) для учёта аэродинамики.

        Args:
            vehicle: Объект с параметрами гибрида.
            distance_km: Пройденное расстояние (км).
            driving_conditions: 'city' или 'highway'.

        Returns:
            Выбросы CO₂ в граммах.
        """
        if driving_conditions == "city":
            ice_share = 0.25
        else:
            ice_share = 0.6

        fuel_used = (vehicle.fuel_consumption_lp100km / 100) * distance_km * ice_share
        co2_emissions = fuel_used * 2.31 * 1000  # г CO2

        return co2_emissions

    @classmethod
    def _calculate_phev_co2(cls, vehicle, distance_km, energy_source):
        """
        Расчет выбросов CO2 для PHEV (все в км и литрах)
        """
        emission_factor = cls.EMISSION_FACTORS.get(energy_source, 300)  # г/кВт·ч
        electricity_co2_per_kwh = emission_factor / 1000  # кг/кВт·ч

        electric_range_km = vehicle.battery_only_range_km
        electric_distance = min(distance_km, electric_range_km)
        ice_distance = max(0, distance_km - electric_range_km)

        electric_consumption_kwh = (vehicle.kwh_100_km_battery_only / 100) * electric_distance
        fuel_consumption_l_100km = 235.214583 / vehicle.mpg_gas_only
        fuel_consumption_liters = (fuel_consumption_l_100km / 100) * ice_distance

        electric_co2_kg = electric_consumption_kwh * electricity_co2_per_kwh
        fuel_co2_kg = fuel_consumption_liters * 2.31

        return (electric_co2_kg + fuel_co2_kg) * 1000  # граммы

    @classmethod
    def get_energy_sources(cls):
        """Список доступных источников энергии"""
        return [
            {'id': 'coal', 'name': 'Угольные станции'},
            {'id': 'gas', 'name': 'Газовые станции'},
            {'id': 'nuclear', 'name': 'Атомные станции'},
            {'id': 'hydro', 'name': 'Гидроэнергетика'},
            {'id': 'eu_avg', 'name': 'Среднее по ЕС'},
            {'id': 'renewables', 'name': 'ВИЭ (солнце/ветер)'}
        ]

    @classmethod
    def compare_emissions(cls, vehicles, distance=100, **kwargs):
        """Сравнение выбросов нескольких автомобилей"""
        return [{
            'vehicle': v,
            'emissions': cls.calculate_co2(v, distance, **kwargs)
        } for v in vehicles
        ]