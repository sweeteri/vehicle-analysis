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
    def calculate_co2(cls, vehicle, distance_km, energy_source='eu_avg',
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
                vehicle, distance_km, energy_source,
            )
        elif isinstance(vehicle, PHEVVehicle):
            return cls._calculate_phev_co2(
                vehicle, distance_km, energy_source,
                use_recuperation, urban_share
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
        # 1. Определяем долю работы ДВС в зависимости от условий движения и параметров авто
        if driving_conditions == "city":
            # В городе доля ДВС ниже (активная рекуперация). Зависит от массы.
            ice_share = 0.3 + (vehicle.mass_kg / 2000) * 0.1  # 30-40% для массы 1000-2000 кг
        else:
            # На трассе доля ДВС выше. Зависит от аэродинамики (frontal_area_m2).
            c_d = 0.3  # Коэффициент лобового сопротивления (примерный)
            air_resistance = vehicle.frontal_area_m2 * c_d
            ice_share = 0.7 + (air_resistance / 0.7) * 0.2  # 70-90%

        # 2. Расход топлива с учётом КПД ДВС и доли его работы
        fuel_used_liters = (vehicle.fuel_consumption_lp100km * distance_km / 100) * ice_share
        effective_fuel_used = fuel_used_liters / vehicle.engine_efficiency  # Коррекция на КПД

        # 3. Выбросы CO₂ от сожжённого топлива
        co2_emissions = effective_fuel_used * vehicle.co2_emissions_gl

        # 4. Поправка на потери при зарядке батареи от ДВС (для трассы)
        if driving_conditions == "highway":
            co2_emissions *= 1.15  # +15% из-за КПД генератора и передачи энергии

        return co2_emissions

    @classmethod
    def _calculate_phev_co2(cls, vehicle, distance_km, energy_source,
                            use_recuperation, urban_share):
        """
        Расчет выбросов для подзаряжаемого гибрида (PHEV)
        """
        # Определяем часть пути, которая будет пройдена на электротяге
        electric_range = vehicle.electric_range_km * cls.PHEV_ELECTRIC_RANGE_FACTOR
        electric_distance = min(distance_km, electric_range)
        ice_distance = max(0, distance_km - electric_distance)

        # Расчет выбросов для электрической части
        ev_emissions = cls._calculate_ev_co2(
            vehicle, electric_distance, energy_source,
            use_recuperation, urban_share
        )

        # Расчет выбросов для ДВС части
        ice_emissions = cls._calculate_ice_co2(vehicle, ice_distance)

        return ev_emissions + ice_emissions

    @classmethod
    def get_energy_sources(cls):
        """Список доступных источников энергии"""
        return [
            {'id': 'coal', 'name': 'Угольные станции'},
            {'id': 'gas', 'name': 'Газовые станции'},
            {'id': 'nuclear', 'name': 'Атомные станции'},
            {'id': 'hydro', 'name': 'Гидроэнергетика'},
            {'id': 'eu_avg', 'name': 'Среднее по ЕС'},
            {'id': 'russia_avg', 'name': 'Среднее по России'},
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
