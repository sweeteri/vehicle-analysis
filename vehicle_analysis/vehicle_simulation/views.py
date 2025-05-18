from django.apps import apps
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.shortcuts import render
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.offline import plot
from .forms import VehicleSelectForm
from .engines.simulator import VehicleSimulator


class SimulationView(FormView):
    template_name = 'vehicle_simulation/calculate.html'
    form_class = VehicleSelectForm
    success_url = reverse_lazy('vehicle_simulation:simulate')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.POST:
            context['form'] = self.form_class(initial={
                'start_date': datetime.now().date(),
                'end_date': datetime.now().date() + timedelta(days=30),
                'daily_distance': 50,
                'daily_hours': 8,
                'energy_source': 'eu_avg',
                'driving_conditions': 'mixed',
                'compare_types': ['ICE', 'HEV', 'PHEV', 'EV']
            })
        return context

    def form_valid(self, form):
        print("Форма валидна. Данные:", form.cleaned_data)
        try:
            data = form.cleaned_data

            if self.request.method == 'POST':
                data['compare_types'] = self.request.POST.getlist('compare_types')

            vehicles = self._get_vehicles_for_analysis(data)
            if not vehicles:
                form.add_error(None, "Не выбрано ни одного транспортного средства")
                return self.form_invalid(form)

            results = []
            for vehicle in vehicles:
                simulator = VehicleSimulator(
                    vehicle=vehicle,
                    daily_distance_km=data['daily_distance'],
                    daily_usage_hours=data['daily_hours'],
                    start_date=data['start_date'],
                    end_date=data['end_date'],
                    energy_source=data['energy_source'],
                    driving_conditions=data['driving_conditions']
                )
                simulation_result = simulator.simulate()
                results.append({
                    'vehicle': vehicle,
                    'simulation': simulation_result,
                    'daily_data': simulation_result.get_daily_data(),
                    'period_data': simulation_result.get_cumulative_data(),
                    'summary': simulation_result.get_summary_stats()
                })

            context = {
                'form': form,
                'show_results': True,
                'results': results,
                'plots': self._generate_plots(results),
                'simulation_params': {
                    'start_date': data['start_date'],
                    'end_date': data['end_date'],
                    'daily_distance': data['daily_distance'],
                    'daily_hours': data['daily_hours'],
                    'energy_source': dict(form.fields['energy_source'].choices)[data['energy_source']],
                    'driving_conditions': dict(form.fields['driving_conditions'].choices)[data['driving_conditions']]
                }
            }
            return render(self.request, self.template_name, context)

        except Exception as e:
            print(f"Ошибка при обработке формы: {str(e)}")
            form.add_error(None, f"Ошибка при расчетах: {str(e)}")
            return self.form_invalid(form)

    def _get_vehicles_for_analysis(self, data):
        vehicles = []
        if data['analysis_type'] == 'single':
            for field in ['ice_vehicle', 'hevv_vehicle', 'phevv_vehicle', 'ev_vehicle']:
                if vehicle := data.get(field):
                    vehicles.append(vehicle)
        else:
            vehicle_map = {
                'ICE': apps.get_model('vehicles', 'ICEVehicle'),
                'HEV': apps.get_model('vehicles', 'HEVVehicle'),
                'PHEV': apps.get_model('vehicles', 'PHEVVehicle'),
                'EV': apps.get_model('vehicles', 'EVVehicle')
            }
            for v_type in data.get('compare_types', []):
                if model := vehicle_map.get(v_type):
                    if avg_vehicle := self._create_average_vehicle(model, v_type):
                        vehicles.append(avg_vehicle)
        return vehicles

    def _create_average_vehicle(self, model, vehicle_type):
        vehicles = model.objects.all()
        if not vehicles.exists():
            return None

        numeric_fields = [
            f.name for f in model._meta.get_fields()
            if hasattr(f, 'get_internal_type') and
               f.get_internal_type() in [
                   'IntegerField', 'FloatField', 'DecimalField',
                   'PositiveIntegerField', 'PositiveSmallIntegerField'
               ] and f.name not in ['id', 'created_at', 'updated_at']
        ]

        avg_vehicle = model()
        for field in numeric_fields:
            values = [getattr(v, field) for v in vehicles if getattr(v, field) is not None]
            if values:
                setattr(avg_vehicle, field, sum(values) / len(values))

        avg_vehicle.mark_name = "Средний"
        avg_vehicle.model_name = {
            'ICE': 'ДВС',
            'HEV': 'Гибрид',
            'PHEV': 'PHEV',
            'EV': 'Электро'
        }.get(vehicle_type, '')
        avg_vehicle.id = -1

        return avg_vehicle

    def _generate_plots(self, results):
        if not results:
            return None

        figures = {
            'energy': go.Figure(),
            'emissions': go.Figure(),
            'cost': go.Figure()
        }
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#9b59b6']

        for i, result in enumerate(results):
            vehicle = result['vehicle']
            period_data = result['period_data']
            name = f"{vehicle.mark_name} {vehicle.model_name}"

            for metric, fig in figures.items():
                fig.add_trace(go.Scatter(
                    x=period_data['dates'],
                    y=[period_data[metric][day] for day in period_data[metric]],
                    name=name,
                    line=dict(color=colors[i % len(colors)], width=2),
                    mode='lines+markers'
                ))

        for metric, fig in figures.items():
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_title='Дата',
                yaxis_title={
                    'cost': 'Стоимость (руб)',
                    'emissions': 'Выбросы CO₂ (г)',
                    'energy': 'Энергия (МДж)'
                }[metric],
                margin=dict(l=50, r=50, b=50, t=50),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )

        return {k: plot(v, output_type='div', config={'displayModeBar': False})
                for k, v in figures.items()}