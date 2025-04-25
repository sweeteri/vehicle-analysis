from vehicles.models import ICEVehicle, HEVVehicle, EVVehicle, PHEVVehicle


class EnergyCalculator:
    """
    Калькулятор энергопотребления для разных типов автомобилей
    """

    # Константы
    FUEL_ENERGY_DENSITY = 42  # МДж/кг (бензин)
    DENSITY_PETROL = 0.745  # кг/л (плотность бензина)
    ICE_EFFICIENCY = 0.3  # КПД ДВС (30%)
    EV_EFFICIENCY = 0.9  # КПД электродвигателя (90%)
    GENERATOR_EFFICIENCY = 0.85  # КПД генератора (85%)
    CHARGING_EFFICIENCY = 0.9  # КПД зарядки (90%)
    PHEV_ELECTRIC_RANGE_FACTOR = 0.7  # Коэффициент использования электрического диапазона PHEV
    FUEL_ENERGY_DENSITY_MJ_PER_L = 34.5  # Энергетическая плотность топлива для бензина

    @classmethod
    def calculate_energy_consumption(cls, vehicle, distance_km, driving_conditions='mixed'):
        """
        Расчет общего энергопотребления
        """
        if isinstance(vehicle, ICEVehicle):
            return cls._calculate_ice_energy(vehicle, distance_km, driving_conditions)
        elif isinstance(vehicle, EVVehicle):
            return cls._calculate_ev_energy(vehicle, distance_km, driving_conditions)
        elif isinstance(vehicle, HEVVehicle):
            return cls._calculate_hev_energy(vehicle, distance_km, driving_conditions)
        elif isinstance(vehicle, PHEVVehicle):
            return cls._calculate_phev_energy(vehicle, distance_km, driving_conditions)
        else:
            raise ValueError("Unsupported vehicle type")

    @classmethod
    def _calculate_ice_energy(cls, vehicle, distance_km, driving_conditions):
        """Расчет для ДВС"""
        base_consumption = vehicle.fuel_consumption_lp100km
        adjusted_consumption = cls._adjust_for_driving_conditions(base_consumption, driving_conditions)

        liters = adjusted_consumption * distance_km / 100
        energy_mj = liters * cls.DENSITY_PETROL * cls.FUEL_ENERGY_DENSITY
        useful_energy = energy_mj * cls.ICE_EFFICIENCY

        return {
            'fuel_liters': liters,
            'energy_mj': energy_mj,
            'useful_energy_mj': useful_energy,
            'efficiency': cls.ICE_EFFICIENCY
        }

    @classmethod
    def _calculate_ev_energy(cls, vehicle, distance_km, driving_conditions):
        """Расчет для электромобиля"""
        base_consumption = vehicle.energy_consumption_kwhp100km
        adjusted_consumption = cls._adjust_for_driving_conditions(base_consumption, driving_conditions, is_ev=True)

        kwh = adjusted_consumption * distance_km / 100
        energy_mj = kwh * 3.6
        useful_energy = energy_mj * cls.EV_EFFICIENCY

        return {
            'energy_kwh': kwh,
            'energy_mj': energy_mj,
            'useful_energy_mj': useful_energy,
            'efficiency': cls.EV_EFFICIENCY,
            'battery_depletion': kwh / vehicle.battery_capacity_kwh * 100
        }

    @classmethod
    def _calculate_hev_energy(cls, vehicle, distance_km, driving_conditions):
        # Расчет энергии ДВС
        fuel_used_liters = vehicle.fuel_consumption_lp100km * distance_km / 100
        ice_energy_mj = fuel_used_liters * cls.FUEL_ENERGY_DENSITY_MJ_PER_L * vehicle.engine_efficiency

        # Расчет электроэнергии (рекуперация + заряд от ДВС)
        if driving_conditions == "city":
            ev_energy_kwh = 0.3 * (vehicle.mass_kg / 1500) * (distance_km / 100)
            ice_share = 0.4
        else:  # highway
            ev_energy_kwh = 0.1 * (vehicle.mass_kg / 1500) * (distance_km / 100) * vehicle.engine_efficiency
            ice_share = 0.8

        ev_energy_mj = ev_energy_kwh * 3.6

        # Общая энергия с учетом доли ДВС/электромотора
        total_energy_mj = (ice_energy_mj * ice_share) + (ev_energy_mj * (1 - ice_share))

        return {
            "fuel_liters": fuel_used_liters * ice_share,
            "energy_kwh": ev_energy_kwh * (1 - ice_share),
            "total_energy_mj": total_energy_mj,
            "ice_share": ice_share,
            "efficiency": (vehicle.engine_efficiency * ice_share) + (cls.EV_EFFICIENCY * (1 - ice_share))
        }

    @classmethod
    def _calculate_phev_energy(cls, vehicle, distance_km, driving_conditions):
        """Расчет для подзаряжаемого гибрида (PHEV)"""
        # Определяем часть пути, которая будет пройдена на электротяге
        electric_range = vehicle.electric_range_km * cls.PHEV_ELECTRIC_RANGE_FACTOR
        electric_distance = min(distance_km, electric_range)
        ice_distance = max(0, distance_km - electric_distance)

        # Расчет потребления для электрической части
        ev_result = cls._calculate_ev_energy(vehicle, electric_distance, driving_conditions)

        # Расчет потребления для ДВС части
        ice_result = cls._calculate_ice_energy(vehicle, ice_distance, driving_conditions)

        # Комбинируем результаты
        total_energy_mj = ev_result['energy_mj'] + ice_result['energy_mj']
        useful_energy_mj = (ev_result['useful_energy_mj'] +
                            ice_result['useful_energy_mj'])

        # Рассчитываем общий КПД
        if total_energy_mj > 0:
            efficiency = useful_energy_mj / total_energy_mj
        else:
            efficiency = cls.EV_EFFICIENCY if electric_distance > 0 else cls.ICE_EFFICIENCY

        return {
            'fuel_liters': ice_result['fuel_liters'],
            'energy_kwh': ev_result['energy_kwh'],
            'total_energy_mj': total_energy_mj,
            'useful_energy_mj': useful_energy_mj,
            'efficiency': efficiency,
            'electric_share': electric_distance / distance_km if distance_km > 0 else 0,
            'battery_depletion': ev_result['battery_depletion'] if electric_distance > 0 else 0
        }

    @classmethod
    def _adjust_for_driving_conditions(cls, base_consumption, conditions, is_ev=False):
        factors = {
            'city': 1.2 if not is_ev else 1.1,
            'highway': 0.9 if not is_ev else 0.8,
            'mixed': 1.0
        }
        return base_consumption * factors.get(conditions, 1.0)

    @classmethod
    def _get_ice_share(cls, vehicle, conditions):
        base_share = vehicle.ice_share
        if conditions == 'city':
            return max(0.1, base_share * 0.7)
        elif conditions == 'highway':
            return min(0.9, base_share * 1.3)
        return base_share

    @classmethod
    def _calculate_hev_efficiency(cls, ice_share):
        ice_efficiency = cls.ICE_EFFICIENCY * ice_share
        ev_efficiency = cls.EV_EFFICIENCY * (1 - ice_share)
        return (ice_efficiency + ev_efficiency) * cls.GENERATOR_EFFICIENCY

    @classmethod
    def compare_efficiency(cls, vehicles, distance=100, conditions='mixed'):
        return [{
            'vehicle': v,
            'result': cls.calculate_energy_consumption(v, distance, conditions)
        } for v in vehicles]
