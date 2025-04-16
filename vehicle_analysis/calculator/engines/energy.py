from vehicles.models import ICEVehicle, HEVVehicle, EVVehicle


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
        """Расчет для гибрида"""
        ice_share = cls._get_ice_share(vehicle, driving_conditions)
        ice_result = cls._calculate_ice_energy(vehicle, distance_km, driving_conditions)
        ev_result = cls._calculate_ev_energy(vehicle, distance_km, driving_conditions)

        ice_energy = ice_result['energy_mj'] * ice_share
        ev_energy = ev_result['energy_mj'] * (1 - ice_share)

        if driving_conditions == 'highway':
            ev_energy /= cls.GENERATOR_EFFICIENCY * cls.CHARGING_EFFICIENCY

        return {
            'fuel_liters': ice_result['fuel_liters'] * ice_share,
            'energy_kwh': ev_result['energy_kwh'] * (1 - ice_share),
            'total_energy_mj': ice_energy + ev_energy,
            'ice_share': ice_share,
            'efficiency': cls._calculate_hev_efficiency(ice_share)
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