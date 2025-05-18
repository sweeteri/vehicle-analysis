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
        """Расчет энергопотребления для PHEV"""
        electric_range_km = vehicle.battery_only_range_km

        # Расчет расстояний на электротяге и ДВС
        electric_distance = min(distance_km, electric_range_km)
        ice_distance = max(0, distance_km - electric_range_km)

        # Расчет потребления электроэнергии (кВтч)
        electric_consumption_kwh = (vehicle.kwh_100_km_battery_only / 100) * electric_distance

        # Конвертация MPG в л/100км для расчета расхода топлива
        fuel_consumption_l_100km = 235.214583 / vehicle.mpg_gas_only
        fuel_consumption_liters = (fuel_consumption_l_100km / 100) * ice_distance

        # Расчет энергии (1 кВт·ч = 3.6 МДж, 1 л бензина ≈ 32 МДж)
        electric_energy_mj = electric_consumption_kwh * 3.6
        fuel_energy_mj = fuel_consumption_liters * 32

        # Общая энергия (без учета КПД)
        total_energy_mj = electric_energy_mj + fuel_energy_mj

        mpge = 0
        if distance_km > 0:
            electric_ratio = electric_distance / distance_km
            mpge_ev = 100 / (vehicle.kwh_100_km_battery_only / 337)
            mpge = 1 / ((electric_ratio / mpge_ev) + ((1 - electric_ratio) / vehicle.mpg_gas_only))

        return {
            'fuel_liters': fuel_consumption_liters,
            'energy_kwh': electric_consumption_kwh,
            'total_energy_mj': total_energy_mj,
            'electric_share': electric_distance / distance_km if distance_km > 0 else 0,
            'MPGe': mpge,
            'electric_distance_km': electric_distance,
            'ice_distance_km': ice_distance,
            'fuel_consumption_l_100km': fuel_consumption_l_100km
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
