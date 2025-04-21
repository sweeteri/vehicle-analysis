from django.views.generic import FormView
from django.apps import apps

from .forms import VehicleSelectForm
from calculator.engines.energy import EnergyCalculator
from calculator.engines.emissions import EmissionsCalculator
from calculator.engines.cost import TCOService


class CalculateView(FormView):
    template_name = 'calculator/calculate.html'
    form_class = VehicleSelectForm
    success_url = '/calculator/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_results'] = False
        return context

    def form_valid(self, form):
        results = self.calculate_results(form.cleaned_data)
        context = self.get_context_data(form=form)
        context.update({
            'results': results,
            'show_results': True
        })
        return self.render_to_response(context)

    def calculate_results(self, data):
        results = []
        ICEVehicle = apps.get_model('vehicles', 'ICEVehicle')
        EVVehicle = apps.get_model('vehicles', 'EVVehicle')
        HEVVehicle = apps.get_model('vehicles', 'HEVVehicle')

        if data['analysis_type'] == 'single':
            vehicles = []
            if data.get('ice_vehicle'):
                vehicles.append(data['ice_vehicle'])
            if data.get('ev_vehicle'):
                vehicles.append(data['ev_vehicle'])
            if data.get('hevv_vehicle'):
                vehicles.append(data['hevv_vehicle'])
        else:
            compare_types = self.request.POST.getlist('compare_types', [])
            vehicles = []
            if 'ICE' in compare_types:
                avg_ice = self.create_average_vehicle(ICEVehicle, 'ICE')
                if avg_ice:
                    vehicles.append(avg_ice)
            if 'EV' in compare_types:
                avg_ev = self.create_average_vehicle(EVVehicle, 'EV')
                if avg_ev:
                    vehicles.append(avg_ev)
            if 'HEV' in compare_types:
                avg_hev = self.create_average_vehicle(HEVVehicle, 'HEV')
                if avg_hev:
                    vehicles.append(avg_hev)

        for vehicle in vehicles:
            distance = data['distance_km']
            energy_result = EnergyCalculator.calculate_energy_consumption(
                vehicle=vehicle,
                distance_km=distance,
                driving_conditions=(data['road_type'])
            )
            emissions_result = EmissionsCalculator.calculate_co2(
                vehicle=vehicle,
                distance_km=distance,
            )
            tco_result = TCOService.calculate_tco(
                vehicle=vehicle,
                distance_km=distance,
            )

            results.append({
                'vehicle': vehicle,
                'energy_kwh': energy_result.get('energy_kwh'),
                'fuel_liters': energy_result.get('fuel_liters'),
                'emissions': emissions_result,
                'tco': tco_result['tco_total'],
            })

        return results

    def create_average_vehicle(self, model, vehicle_type):
        """Создает виртуальное транспортное средство с усредненными характеристиками"""
        vehicles = model.objects.all()
        if not vehicles.exists():
            return None

        numeric_fields = {
            'ICEVehicle': [
                'mass_kg', 'frontal_area_m2', 'drag_coefficient', 'rolling_coefficient',
                'engine_efficiency', 'fuel_consumption_lp100km', 'co2_emissions_gl',
                'transmission_ratio', 'production_price'
            ],
            'EVVehicle': [
                'mass_kg', 'frontal_area_m2', 'drag_coefficient', 'rolling_coefficient',
                'battery_capacity_kwh', 'energy_consumption_kwhp100km',
                'motor_efficiency', 'charging_efficiency', 'production_price'
            ],
            'HEVVehicle': [
                'mass_kg', 'frontal_area_m2', 'drag_coefficient', 'rolling_coefficient',
                'engine_efficiency', 'fuel_consumption_lp100km', 'co2_emissions_gl',
                'transmission_ratio', 'battery_capacity_kwh', 'energy_consumption_kwhp100km',
                'motor_efficiency', 'charging_efficiency', 'ice_share',
                'generator_efficiency', 'production_price'
            ]
        }

        fields_to_avg = numeric_fields.get(model.__name__, [])
        avg_values = {field: [] for field in fields_to_avg}
        other_fields = {}

        for vehicle in vehicles:
            for field in fields_to_avg:
                value = getattr(vehicle, field)
                avg_values[field].append(value)

            for field in vehicle._meta.fields:
                field_name = field.name
                if field_name not in fields_to_avg and field_name not in ['id', 'created_at', 'updated_at']:
                    if field_name not in other_fields:
                        other_fields[field_name] = getattr(vehicle, field_name)

        avg_fields = {}
        for field, values in avg_values.items():
            if values:
                avg_fields[field] = sum(values) / len(values)

        avg_fields.update(other_fields)

        avg_vehicle = model(**avg_fields)
        avg_vehicle.name = f"Average {vehicle_type} Vehicle (based on {len(vehicles)} models)"
        avg_vehicle.id = -1

        if model.__name__ == 'HEVVehicle' and 'ice_share' not in avg_fields:
            avg_vehicle.ice_share = 0.5

        return avg_vehicle
