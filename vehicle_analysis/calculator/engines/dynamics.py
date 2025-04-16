import math
from vehicles.models import ICEVehicle, HEVVehicle, EVVehicle


class VehicleDynamics:
    """
    Класс для расчета динамики автомобиля на основе физических уравнений
    """

    # Константы
    AIR_DENSITY = 1.225  # кг/м³ (плотность воздуха при 15°C)
    GRAVITY = 9.81  # м/с² (ускорение свободного падения)

    def calculate_required_force(self, vehicle, velocity_kmh, acceleration_mss, road_grade_deg=0):
        """
        Расчет требуемой силы двигателя

        :param vehicle: объект Vehicle (должен иметь mass_kg, frontal_area_m2 и др.)
        :param velocity_kmh: текущая скорость (км/ч)
        :param acceleration_mss: ускорение (м/с²), положительное - разгон, отрицательное - торможение
        :param road_grade_deg: уклон дороги в градусах (положительный - подъем)
        :return: словарь с силами и мощностью
        """
        # скорость в м/с
        velocity_ms = velocity_kmh / 3.6

        forces = {
            'rolling': self._calculate_rolling_resistance(vehicle),
            'acceleration': self._calculate_acceleration_force(vehicle, acceleration_mss),
            'grade': self._calculate_grade_force(vehicle, road_grade_deg),
            'air': self._calculate_air_resistance(vehicle, velocity_ms)
        }

        total_force = sum(forces.values())

        power_kw = (total_force * velocity_ms) / 1000

        return {
            'total_force_n': total_force,
            'power_kw': power_kw,
            'forces': forces,
            'velocity_ms': velocity_ms,
            'efficiency': self._calculate_efficiency(vehicle, power_kw, velocity_ms)
        }

    def _calculate_rolling_resistance(self, vehicle):
        """Сила сопротивления качению"""
        return vehicle.rolling_coefficient * vehicle.mass_kg * self.GRAVITY

    def _calculate_acceleration_force(self, vehicle, acceleration_mss):
        """Сила инерции при ускорении"""
        return vehicle.mass_kg * acceleration_mss

    def _calculate_grade_force(self, vehicle, road_grade_deg):
        """Сила на уклоне дороги"""
        angle_rad = math.radians(road_grade_deg)
        return vehicle.mass_kg * self.GRAVITY * math.sin(angle_rad)

    def _calculate_air_resistance(self, vehicle, velocity_ms):
        """Аэродинамическое сопротивление"""
        return 0.5 * self.AIR_DENSITY * vehicle.drag_coefficient * vehicle.frontal_area_m2 * (velocity_ms ** 2)

    def _calculate_efficiency(self, vehicle, power_kw, velocity_ms):
        """
        Расчет эффективности использования энергии
        (упрощенный вариант)
        """
        if isinstance(vehicle, ICEVehicle):
            return min(0.35, 0.1 + 0.002 * velocity_ms)
        elif isinstance(vehicle, EVVehicle):
            return min(0.9, 0.7 + 0.003 * velocity_ms)
        elif isinstance(vehicle, HEVVehicle):
            return min(0.5, 0.3 + 0.0025 * velocity_ms)

    def simulate_acceleration(self, vehicle, initial_velocity=0, max_time=10, throttle=0.8, road_grade=0):
        """
        Моделирование разгона автомобиля
        :param throttle: 0-1 (дроссельная заслонка)
        :return: массив точек [time, velocity, distance]
        """
        results = []
        velocity = initial_velocity
        distance = 0
        dt = 0.1  # шаг времени (сек)

        for t in [i * dt for i in range(int(max_time / dt))]:
            forces = self.calculate_required_force(
                vehicle,
                velocity,
                throttle * vehicle.max_acceleration,
                road_grade
            )

            acceleration = forces['total_force_n'] / vehicle.mass_kg
            velocity += acceleration * dt * 3.6  # в км/ч
            distance += velocity / 3.6 * dt

            results.append({
                'time': t,
                'velocity_kmh': velocity,
                'distance_m': distance,
                'acceleration_mss': acceleration,
                'power_kw': forces['power_kw']
            })

            if velocity >= vehicle.max_speed:
                break

        return results