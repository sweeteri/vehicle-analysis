from django.contrib import admin
from .models import ICEVehicle, EVVehicle, HEVVehicle, PHEVVehicle


@admin.register(ICEVehicle)
class ICEVehicleAdmin(admin.ModelAdmin):
    list_display = ('mark_name', 'model_name', 'mass_kg', 'fuel_consumption_lp100km')
    fieldsets = (
        ('Общие параметры', {
            'fields': ('mark_name', 'model_name', 'mass_kg', 'frontal_area_m2', 'drag_coefficient', 'rolling_coefficient')
        }),
        ('Параметры ДВС', {
            'fields': ('engine_efficiency', 'fuel_consumption_lp100km', 'co2_emissions_gl', 'transmission_ratio')
        })
    )


@admin.register(EVVehicle)
class EVVehicleAdmin(admin.ModelAdmin):
    list_display = ('mark_name', 'model_name', 'battery_capacity_kwh', 'energy_consumption_kwhp100km')


@admin.register(HEVVehicle)
class HEVVehicleAdmin(admin.ModelAdmin):
    list_display = ('mark_name', 'model_name', 'ice_share', 'generator_efficiency')


@admin.register(PHEVVehicle)
class PHEVVehicleAdmin(admin.ModelAdmin):
    list_display = (
        'mark_name',
        'model_name',
        'electric_range_km',
        'ice_range_km',
        'battery_depletion_threshold',
        'charging_power_kw',
        'regen_braking_efficiency'
    )
