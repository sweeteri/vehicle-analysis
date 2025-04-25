from django.contrib import admin
from .models import ICEVehicle, EVVehicle, HEVVehicle, PHEVVehicle

from import_export.admin import ImportExportModelAdmin


@admin.register(ICEVehicle)
class ICEVehicleAdmin(ImportExportModelAdmin):
    list_display = ('mark_name', 'model_name', 'mass_kg', 'fuel_consumption_lp100km')
    fieldsets = (
        ('Общие параметры', {
            'fields': ('mark_name', 'model_name', 'mass_kg', 'frontal_area_m2')
        }),
        ('Параметры ДВС', {
            'fields': ('engine_efficiency', 'fuel_consumption_lp100km', 'co2_emissions_gl')
        })
    )


@admin.register(EVVehicle)
class EVVehicleAdmin(ImportExportModelAdmin):
    list_display = ('mark_name', 'model_name', 'battery_capacity_kwh', 'energy_consumption_kwhp100km')


@admin.register(HEVVehicle)
class HEVVehicleAdmin(ImportExportModelAdmin):
    list_display = ('mark_name', 'model_name', 'ice_share', 'generator_efficiency')


@admin.register(PHEVVehicle)
class PHEVVehicleAdmin(ImportExportModelAdmin):
    list_display = (
        'mark_name',
        'model_name',
        'electric_range_km',
        'ice_range_km',
        'battery_depletion_threshold',
        'charging_power_kw',
        'regen_braking_efficiency'
    )
