from django.db import models


class BaseVehicle(models.Model):
    """Абстрактная модель с общими параметрами для всех авто"""
    mark_name = models.CharField(max_length=120, verbose_name="Название марки", default='')
    model_name = models.CharField(max_length=100, verbose_name="Название модели")
    mass_kg = models.FloatField(verbose_name="Масса (кг)")
    frontal_area_m2 = models.FloatField(verbose_name="Лобовая площадь (м²)")
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
        return f"{self.mark_name} {self.model_name} (ДВС)"


class EVVehicle(BaseVehicle, ElectricSpecs):
    """Модель для электромобилей"""

    class Meta:
        app_label = 'vehicles'

    def __str__(self):
        return f"{self.mark_name} {self.model_name} (Электромобиль)"


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
        return f"{self.mark_name} {self.model_name} (Гибрид)"


class PHEVVehicle(BaseVehicle, EngineSpecs, ElectricSpecs):
    """Модель для подключаемых гибридов (PHEV)"""
    battery_only_range_km = models.FloatField(
        default=0.0,
        verbose_name="Запас хода только на батарее (км)",
        help_text="По данным производителя (WLTP или NEDC)"
    )
    mpg_gas_only = models.FloatField(
        default=0.0,
        verbose_name="MPG при работе только на ДВС",
        help_text="Miles per gallon в режиме только ДВС"
    )
    kwh_100_km_battery_only = models.FloatField(
        default=0.0,
        verbose_name="Потребление энергии (кВт·ч/100 км)",
        help_text="В режиме только на батарее"
    )

    engine_efficiency = None
    fuel_consumption_lp100km = None
    battery_capacity_kwh = None
    energy_consumption_kwhp100km = None

    class Meta:
        app_label = 'vehicles'

    def __str__(self):
        return f"{self.mark_name} {self.model_name} (PHEV)"
