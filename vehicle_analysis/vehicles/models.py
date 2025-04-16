from django.db import models


class BaseVehicle(models.Model):
    """Абстрактная модель с общими параметрами для всех авто"""
    name = models.CharField(max_length=100, verbose_name="Название модели")
    mass_kg = models.FloatField(verbose_name="Масса (кг)")
    frontal_area_m2 = models.FloatField(verbose_name="Лобовая площадь (м²)")
    drag_coefficient = models.FloatField(verbose_name="Коэффициент аэродинамического сопротивления (Cx)")
    rolling_coefficient = models.FloatField(verbose_name="Коэффициент сопротивления качению (Cr)")
    production_price = models.FloatField(verbose_name='Стоимость производства', default=1000)

    ROAD_TYPES = (
        ('city', 'Город'),
        ('highway', 'Трасса'),
        ('mixed', 'Смешанный')
    )
    road_type = models.CharField(max_length=10, choices=ROAD_TYPES, default='mixed')

    class Meta:
        abstract = True


class EngineSpecs(models.Model):
    """Абстрактная модель для ДВС и гибридов"""
    engine_efficiency = models.FloatField(
        verbose_name="КПД двигателя",
        help_text="Пример: 0.35 для 35% КПД",
        null=True, blank=True
    )
    fuel_consumption_lp100km = models.FloatField(
        verbose_name="Расход топлива (л/100 км)",
        null=True, blank=True
    )
    co2_emissions_gl = models.FloatField(
        verbose_name="Выбросы CO₂ (г/л)",
        default=2300,  # Среднее значение для бензина
        null=True, blank=True
    )
    transmission_ratio = models.FloatField(
        verbose_name="Передаточное число трансмиссии",
        null=True, blank=True
    )

    class Meta:
        abstract = True


class ElectricSpecs(models.Model):
    """Абстрактная модель для электромобилей"""
    battery_capacity_kwh = models.FloatField(
        verbose_name="Ёмкость аккумулятора (кВт·ч)",
        null=True, blank=True
    )
    energy_consumption_kwhp100km = models.FloatField(
        verbose_name="Потребление энергии (кВт·ч/100 км)",
        null=True, blank=True
    )
    motor_efficiency = models.FloatField(
        verbose_name="КПД электродвигателя",
        null=True, blank=True
    )
    charging_efficiency = models.FloatField(
        verbose_name="КПД зарядки от сети",
        default=0.9,
        null=True, blank=True
    )

    class Meta:
        abstract = True


class ICEVehicle(BaseVehicle, EngineSpecs):
    """Модель для автомобилей с ДВС"""

    class Meta:
        app_label = 'vehicles'

    def __str__(self):
        return f"{self.name} (ДВС)"


class EVVehicle(BaseVehicle, ElectricSpecs):
    """Модель для электромобилей"""

    class Meta:
        app_label = 'vehicles'

    def __str__(self):
        return f"{self.name} (Электромобиль)"


class HEVVehicle(BaseVehicle, EngineSpecs, ElectricSpecs):
    """Модель для гибридов"""
    ice_share = models.FloatField(
        verbose_name="Доля работы ДВС",
        help_text="От 0 до 1 (например, 0.7 для 70%)",
        default=0.5
    )
    generator_efficiency = models.FloatField(
        verbose_name="КПД генератора",
        default=0.85
    )

    class Meta:
        app_label = 'vehicles'

    def __str__(self):
        return f"{self.name} (Гибрид)"
