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
                use_recuperation, urban_share
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
    def _calculate_hev_co2(cls, vehicle, distance_km, energy_source,
                           use_recuperation, urban_share):
        """Расчет выбросов для гибрида"""
        ice_share = vehicle.ice_share  # Доля работы ДВС
        ice_emissions = ice_share * cls._calculate_ice_co2(vehicle, distance_km)
        ev_emissions = (1 - ice_share) * cls._calculate_ev_co2(
            vehicle, distance_km, energy_source, use_recuperation, urban_share
        )
        return ice_emissions + ev_emissions

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
