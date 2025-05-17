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
                'end_date': (datetime.now() + timedelta(days=30)).date(),
                'daily_hours': 8,
                'energy_source': 'eu_avg',
                'compare_types': ['ICE', 'HEV', 'PHEV', 'EV']
            })
        return context

    def form_valid(self, form):
        try:
            data = form.cleaned_data
            print("Получены данные формы:", data)

            # Исправляем получение compare_types для POST-запроса
            if self.request.method == 'POST':
                data['compare_types'] = self.request.POST.getlist('compare_types')
                print("Выбранные типы для сравнения:", data['compare_types'])

            vehicles = self._get_vehicles_for_analysis(data)
            print("Найдено транспортных средств:", len(vehicles))

            if not vehicles:
                form.add_error(None, "Не выбрано ни одного транспортного средства")
                return self.form_invalid(form)

            results = []
            for vehicle in vehicles:
                print(f"Обработка ТС: {vehicle.mark_name} {vehicle.model_name}")
                simulator = VehicleSimulator(
                    vehicle=vehicle,
                    start_date=data['start_date'],
                    end_date=data['end_date'],
                    daily_usage_hours=data['daily_hours'],
                    energy_source=data['energy_source']
                )
                simulator.simulate()

                results.append({
                    'vehicle': vehicle,
                    'data': simulator.get_cumulative_data(),
                    'summary': simulator.get_summary_stats()
                })

            context = {
                'form': form,
                'show_results': True,
                'results': results,
                'plots': self._generate_plots(results)
            }
            print("Контекст сформирован, передаем в шаблон")
            return render(self.request, self.template_name, context)

        except Exception as e:
            print("Ошибка:", str(e), type(e))
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
            'cost': go.Figure(),
            'emissions': go.Figure(),
            'energy': go.Figure()
        }
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#9b59b6']

        for i, result in enumerate(results):
            vehicle = result['vehicle']
            data = result['data']
            name = f"{vehicle.mark_name} {vehicle.model_name}"

            for metric, fig in figures.items():
                fig.add_trace(go.Scatter(
                    x=data['dates'],
                    y=data[f'cumulative_{metric}'],
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
