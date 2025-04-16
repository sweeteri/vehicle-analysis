from django.contrib import admin
from .models import ICEVehicle, EVVehicle, HEVVehicle


@admin.register(ICEVehicle)
class ICEVehicleAdmin(admin.ModelAdmin):
    list_display = ('name', 'mass_kg', 'fuel_consumption_lp100km')
    fieldsets = (
        ('Общие параметры', {
            'fields': ('name', 'mass_kg', 'frontal_area_m2', 'drag_coefficient', 'rolling_coefficient')
        }),
        ('Параметры ДВС', {
            'fields': ('engine_efficiency', 'fuel_consumption_lp100km', 'co2_emissions_gl', 'transmission_ratio')
        })
    )


@admin.register(EVVehicle)
class EVVehicleAdmin(admin.ModelAdmin):
    list_display = ('name', 'battery_capacity_kwh', 'energy_consumption_kwhp100km')


@admin.register(HEVVehicle)
class HEVVehicleAdmin(admin.ModelAdmin):
    list_display = ('name', 'ice_share', 'generator_efficiency')
