from django.views.generic import FormView
from django.apps import apps
import plotly.express as px
from plotly.offline import plot
import pandas as pd

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

        # Создаем графики
        graphs = self.create_plots(results) if results else None

        context.update({
            'results': results,
            'show_results': True,
            'plots': graphs
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
            if data.get('phevv_vehicle'):
                vehicles.append(data['phevv_vehicle'])
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
        vehicles = model.objects.all()
        if not vehicles.exists():
            return None

        numeric_fields = [
            field.name for field in model._meta.get_fields()
            if hasattr(field, 'get_internal_type') and
               field.get_internal_type() in [
                   'IntegerField', 'FloatField', 'DecimalField',
                   'PositiveIntegerField', 'PositiveSmallIntegerField'
               ] and field.name not in ['id', 'created_at', 'updated_at']
        ]

        avg_values = {field: [] for field in numeric_fields}
        other_fields = {}

        for vehicle in vehicles:
            for field in numeric_fields:
                value = getattr(vehicle, field)
                if value is not None:
                    avg_values[field].append(value)

            for field in vehicle._meta.fields:
                field_name = field.name
                if (field_name not in numeric_fields and
                        field_name not in ['id', 'created_at', 'updated_at'] and
                        field_name not in other_fields):
                    other_fields[field_name] = getattr(vehicle, field_name)

        avg_fields = {}
        for field, values in avg_values.items():
            if values:
                avg_fields[field] = sum(values) / len(values)

        avg_fields.update(other_fields)
        avg_vehicle = model(**avg_fields)
        avg_vehicle.mark_name = "Средняя "
        vehicle_types = {
            'ICE': 'ДВС',
            'EV': 'Электромобиль',
            'HEV': 'Гибрид',
            'PHEV': 'Заряжаемый гибрид'
        }
        avg_vehicle.model_name = f"{vehicle_types[vehicle_type]} (на основе {len(vehicles)} моделей)"
        avg_vehicle.id = -1

        if model.__name__ in ['HEVVehicle'] and 'ice_share' not in avg_fields:
            avg_vehicle.ice_share = 0.5
        return avg_vehicle

    def create_plots(self, results):
        if not results:
            return None

        plot_data = []
        for result in results:
            vehicle = result['vehicle']
            name = f"{vehicle.mark_name} {vehicle.model_name}"[:40]
            vehicle_type = vehicle.__class__.__name__.replace('Vehicle', '')

            if result['fuel_liters'] is not None:
                plot_data.append({
                    'Транспорт': name,
                    'Тип': vehicle_type,
                    'Расход': round(result['fuel_liters'], 2),
                    'Единица': 'л',
                    'Выбросы': round(result['emissions'], 2),
                    'Стоимость': round(result['tco'], 2)
                })
            if result['energy_kwh'] is not None:
                plot_data.append({
                    'Транспорт': name,
                    'Тип': vehicle_type,
                    'Расход': round(result['energy_kwh'], 2),
                    'Единица': 'кВт·ч',
                    'Выбросы': round(result['emissions'], 2),
                    'Стоимость': round(result['tco'], 2)
                })

        df = pd.DataFrame(plot_data)

        # Общий стиль и цвета
        common_style = {
            'layout': {
                'plot_bgcolor': '#f8f9fa',
                'paper_bgcolor': '#f8f9fa',
                'font': {'family': 'Arial, sans-serif', 'size': 12},
                'margin': {'t': 40, 'b': 70, 'l': 60, 'r': 40},
                'xaxis': {'tickangle': -30},
                'hoverlabel': {'font_size': 12}
            },
            'config': {'displayModeBar': False}
        }

        color_map = {
            'ICE': '#3498db',
            'EV': '#2ecc71',
            'HEV': '#e74c3c',
            'PHEV': '#9b59b6'
        }

        # Топливо
        df_fuel = df[df['Единица'] == 'л']
        fig_fuel = px.bar(
            df_fuel, x='Транспорт', y='Расход', color='Тип', color_discrete_map=color_map,
            text='Расход', title='<b>Расход топлива (л)</b>'
        )
        fig_fuel.update_traces(textposition='outside')
        fig_fuel.update_layout(yaxis_title='л', **common_style['layout'])
        fig_fuel.update_yaxes(range=[0, df_fuel['Расход'].max() + 1])

        # Энергия
        df_energy = df[df['Единица'] == 'кВт·ч']
        fig_energy = px.bar(
            df_energy, x='Транспорт', y='Расход', color='Тип', color_discrete_map=color_map,
            text='Расход', title='<b>Расход энергии (кВт·ч)</b>'
        )
        fig_energy.update_traces(textposition='outside')
        fig_energy.update_layout(yaxis_title='кВт·ч', **common_style['layout'])
        fig_energy.update_yaxes(range=[0, df['Расход'].max() * 1.1])

        df_unique = df.drop_duplicates(subset=['Транспорт'])

        # Выбросы
        fig_emissions = px.bar(
            df_unique.sort_values('Выбросы'), x='Транспорт', y='Выбросы', color='Тип',
            color_discrete_map=color_map, text='Выбросы', title='<b>Выбросы CO₂</b>'
        )
        fig_emissions.update_traces(textposition='outside')
        fig_emissions.update_layout(yaxis_title='г', **common_style['layout'])
        fig_emissions.update_yaxes(range=[0, df_unique['Выбросы'].max() * 1.1])

        # Стоимость
        fig_cost = px.bar(
            df_unique.sort_values('Стоимость'), x='Транспорт', y='Стоимость', color='Тип',
            color_discrete_map=color_map, text='Стоимость', title='<b>Стоимость владения</b>'
        )
        fig_cost.update_traces(
            texttemplate='%{y:,.0f}',
            textposition='outside'
        )
        fig_cost.update_layout(yaxis_title='руб', **common_style['layout'])
        fig_cost.update_yaxes(range=[0, df_unique['Стоимость'].max() * 1.1])
        return {
            'consumption_fuel': plot(fig_fuel, output_type='div', config=common_style['config']),
            'consumption_energy': plot(fig_energy, output_type='div', config=common_style['config']),
            'emissions': plot(fig_emissions, output_type='div', config=common_style['config']),
            'cost': plot(fig_cost, output_type='div', config=common_style['config']),
        }
