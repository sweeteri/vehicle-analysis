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
        PHEVVehicle = apps.get_model('vehicles', 'PHEVVehicle')

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
            if 'PHEV' in compare_types:
                avg_phev = self.create_average_vehicle(PHEVVehicle, 'PHEV')
                if avg_phev:
                    vehicles.append(avg_phev)
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
                driving_conditions=(data['road_type'])
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

        # числовые поля модели
        numeric_fields = [
            field.name
            for field in model._meta.get_fields()
            if (
                    hasattr(field, 'get_internal_type')
                    and field.get_internal_type() in [
                        'IntegerField',
                        'FloatField',
                        'DecimalField',
                        'PositiveIntegerField',
                        'PositiveSmallIntegerField'
                    ]
                    and field.name not in ['id', 'created_at', 'updated_at']
            )
        ]

        avg_values = {field: [] for field in numeric_fields}
        other_fields = {}

        for vehicle in vehicles:
            for field in numeric_fields:
                value = getattr(vehicle, field)
                if value is not None:
                    avg_values[field].append(value)

            # Сохраняем нечисловые поля
            for field in vehicle._meta.fields:
                field_name = field.name
                if (field_name not in numeric_fields and
                        field_name not in ['id', 'created_at', 'updated_at'] and
                        field_name not in other_fields):
                    other_fields[field_name] = getattr(vehicle, field_name)

        # Вычисляем средние значения
        avg_fields = {}
        for field, values in avg_values.items():
            if values:
                avg_fields[field] = sum(values) / len(values)

        # нечисловые поля
        avg_fields.update(other_fields)

        avg_vehicle = model(**avg_fields)
        avg_vehicle.name = f"Average {vehicle_type} Vehicle (based on {len(vehicles)} models)"
        avg_vehicle.id = -1  # специальный ID для усредненного ТС

        if model.__name__ in ['HEVVehicle', 'PHEVVehicle'] and 'ice_share' not in avg_fields:
            avg_vehicle.ice_share = 0.5  # Значение по умолчанию для гибридов

        return avg_vehicle
