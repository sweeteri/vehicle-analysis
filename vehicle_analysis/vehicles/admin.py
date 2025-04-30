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
        'battery_only_range_km',
        'energy_consumption_kwhp100km',
        'kwh_100_km_battery_only',
        'frontal_area_m2'
    )
