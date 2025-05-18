from django.apps import apps
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.shortcuts import render
from datetime import datetime
from math import ceil
from .forms import VehicleSelectForm
from .engines.simulator import run_simulation


class SimulationView(FormView):
    template_name = 'vehicle_simulation/calculate.html'
    form_class = VehicleSelectForm
    success_url = reverse_lazy('vehicle_simulation:simulate')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if not self.request.POST:
            ctx['form'] = self.form_class(initial={
                'start_date': datetime.now().date(),
                'end_date':   (datetime.now().date()),
                'daily_distance': 50,
                'daily_hours':    8,
                'energy_source': 'eu_avg',
                'driving_conditions': 'mixed',
                'compare_types': ['ICE', 'HEV', 'PHEV', 'EV']
            })
        return ctx

    def form_valid(self, form):
        data = form.cleaned_data
        # поправляем compare_types из POST
        data['compare_types'] = self.request.POST.getlist('compare_types')

        vehicles = self._get_vehicles_for_analysis(data)
        if not vehicles:
            form.add_error(None, "Нужно выбрать хотя бы одно ТС или тип")
            return self.form_invalid(form)

        # параметры симуляции
        start_date = data['start_date']
        end_date   = data['end_date']
        # считаем, сколько полных дней +1 (включительно)
        total_days = (end_date - start_date).days + 1
        # переводим дни в «месяцы» по 30 дн.
        months = total_days / 30.0

        daily_km   = data['daily_distance']
        cond       = data.get('driving_conditions', 'mixed')
        source     = data['energy_source']
        use_recup  = data.get('use_recuperation', True)
        urban_share= data.get('urban_share', 0.5)

        results = []
        for v in vehicles:
            sim = run_simulation(
                vehicle = v,
                start_date = start_date,
                end_date = end_date,
                daily_km = daily_km,
                driving_conditions = cond,
                energy_source = source,
                use_recuperation = use_recup,
                urban_share = urban_share
                )

            # считаем суммарные показатели
            total_energy = sum(
                day['energy'].get('energy_mj',
                                  day['energy'].get('energy_kwh', 0) * 3.6)
                for day in sim
            )
            total_co2  = sum(day['co2_g'] for day in sim)
            total_cost = sum(day['cost_rub'] for day in sim)

            results.append({
                'vehicle': v,
                'daily':   sim,
                'summary': {
                    'energy_mj': total_energy,
                    'co2_g':     total_co2,
                    'cost_rub':  total_cost
                }
            })

        context = {
            'form':         form,
            'show_results': True,
            'results':      results,
            'plots':        self._generate_plots(results),
        }
        return render(self.request, self.template_name, context)

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
                    if avg := self._create_average_vehicle(model, v_type):
                        vehicles.append(avg)
        return vehicles

    def _create_average_vehicle(self, model, vehicle_type):
        qs = model.objects.all()
        if not qs.exists():
            return None
        numeric_fields = [
            f.name for f in model._meta.get_fields()
            if hasattr(f, 'get_internal_type') and
               f.get_internal_type() in [
                   'IntegerField', 'FloatField', 'DecimalField',
                   'PositiveIntegerField', 'PositiveSmallIntegerField'
               ] and f.name != 'id'
        ]
        avg = model()
        for field in numeric_fields:
            vals = [getattr(v, field) for v in qs if getattr(v, field) is not None]
            if vals:
                setattr(avg, field, sum(vals) / len(vals))
        avg.mark_name = "Средний"
        avg.model_name = {
            'ICE': 'ДВС', 'HEV': 'Гибрид',
            'PHEV': 'PHEV', 'EV': 'Электро'
        }[vehicle_type]
        avg.id = -1
        return avg

    def _generate_plots(self, results):
        import plotly.graph_objects as go
        from plotly.offline import plot

        default_height = 350
        figs = {
            'fuel':     go.Figure(layout={'height': default_height}),
            'electric': go.Figure(layout={'height': default_height}),
            'emissions':go.Figure(layout={'height': default_height}),
            'cost':     go.Figure(layout={'height': default_height}),
        }
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#9b59b6']

        for idx, item in enumerate(results):
            v    = item['vehicle']
            name = f"{v.mark_name} {v.model_name}"
            dates = [d['date'] for d in item['daily']]

            # расход топлива (л/день)
            fuel_vals = [d['energy'].get('fuel_liters', 0) for d in item['daily']]
            figs['fuel'].add_trace(go.Scatter(
                x=dates, y=fuel_vals, name=name,
                line=dict(color=colors[idx % len(colors)], width=2)
            ))

            # расход электроэнергии (кВт·ч/день)
            elec_vals = [d['energy'].get('energy_kwh', 0) for d in item['daily']]
            figs['electric'].add_trace(go.Scatter(
                x=dates, y=elec_vals, name=name,
                line=dict(color=colors[idx % len(colors)], width=2)
            ))

            # выбросы CO₂ (г/день)
            co2 = [d['co2_g'] for d in item['daily']]
            figs['emissions'].add_trace(go.Scatter(
                x=dates, y=co2, name=name,
                line=dict(color=colors[idx % len(colors)], width=2)
            ))

            # стоимость (руб/день)
            cost_vals = [d['cost_rub'] for d in item['daily']]
            figs['cost'].add_trace(go.Scatter(
                x=dates, y=cost_vals, name=name,
                line=dict(color=colors[idx % len(colors)], width=2)
            ))

        # Настройки графиков
        figs['fuel'].update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title='Дата',
            yaxis_title='Расход топлива (л/день)',
            margin=dict(l=40, r=20, t=30, b=40),
            legend=dict(orientation='h', y=1.1, x=0),
        )
        figs['electric'].update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title='Дата',
            yaxis_title='Расход электроэнергии (кВт·ч/день)',
            margin=dict(l=40, r=20, t=30, b=40),
            legend=dict(orientation='h', y=1.1, x=0),
        )
        figs['emissions'].update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title='Дата',
            yaxis_title='Выбросы CO₂ (г/день)',
            margin=dict(l=40, r=20, t=30, b=40),
            legend=dict(orientation='h', y=1.1, x=0),
        )
        figs['cost'].update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title='Дата',
            yaxis_title='Стоимость в день (руб)',
            margin=dict(l=40, r=20, t=30, b=40),
            legend=dict(orientation='h', y=1.1, x=0),
        )

        return {
            key: plot(fig, output_type='div', config={'displayModeBar': False})
            for key, fig in figs.items()
        }
