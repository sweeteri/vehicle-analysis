from django import forms
from datetime import datetime, timedelta
from vehicles.models import ICEVehicle, HEVVehicle, PHEVVehicle, EVVehicle
from calculator.engines.emissions import EmissionsCalculator


class VehicleSelectForm(forms.Form):
    ANALYSIS_TYPES = (
        ('single', 'Анализ одного ТС'),
        ('type_avg', 'Сравнение типов ТС'),
    )

    analysis_type = forms.ChoiceField(
        choices=ANALYSIS_TYPES,
        widget=forms.RadioSelect(attrs={'class': 'btn-check'}),
        initial='single'
    )

    # Поля для выбора конкретных ТС
    ice_vehicle = forms.ModelChoiceField(
        queryset=ICEVehicle.objects.all(),
        required=False,
        label='ДВС',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    hevv_vehicle = forms.ModelChoiceField(
        queryset=HEVVehicle.objects.all(),
        required=False,
        label='Гибрид (HEV)',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    phevv_vehicle = forms.ModelChoiceField(
        queryset=PHEVVehicle.objects.all(),
        required=False,
        label='Заражаемый гибрид (PHEV)',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    ev_vehicle = forms.ModelChoiceField(
        queryset=EVVehicle.objects.all(),
        required=False,
        label='Электромобиль',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Поля для параметров симуляции
    start_date = forms.DateField(
        label='Дата начала',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        initial=datetime.now().date
    )
    end_date = forms.DateField(
        label='Дата окончания',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        initial=lambda: datetime.now().date() + timedelta(days=30)
    )
    daily_distance = forms.FloatField(
        label='Дневной пробег (км)',
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '1'
        }),
        initial=50,
        required=True
    )
    daily_hours = forms.FloatField(
        label='Часов эксплуатации в день',
        min_value=0,
        max_value=24,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.5'
        }),
        initial=8,
        required=True
    )
    energy_source = forms.ChoiceField(
        choices=[(src['id'], src['name']) for src in EmissionsCalculator.get_energy_sources()],
        initial='eu_avg',
        label="Источник электроэнергии",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    driving_conditions = forms.ChoiceField(
        choices=[
            ('city', 'Городской цикл'),
            ('highway', 'Трасса'),
            ('mixed', 'Смешанный цикл')
        ],
        initial='mixed',
        label="Условия движения",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    compare_types = forms.MultipleChoiceField(
        choices=[
            ('ICE', 'ДВС'),
            ('HEV', 'Гибриды'),
            ('PHEV', 'Заряжаемые гибриды'),
            ('EV', 'Электро')
        ],
        widget=forms.CheckboxSelectMultiple,
        initial=['ICE', 'HEV', 'PHEV', 'EV'],
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.data:
            self.initial['compare_types'] = ['ICE', 'HEV', 'PHEV', 'EV']

    def clean(self):
        cleaned_data = super().clean()

        # Проверка обязательных полей
        required_fields = ['daily_distance', 'daily_hours', 'energy_source',
                           'driving_conditions', 'start_date', 'end_date']
        for field in required_fields:
            if field not in cleaned_data:
                self.add_error(field, "Это поле обязательно для заполнения")

        # Проверка дат
        if cleaned_data.get('start_date') and cleaned_data.get('end_date'):
            if cleaned_data['start_date'] > cleaned_data['end_date']:
                self.add_error('end_date', "Дата окончания должна быть после даты начала")

        # Проверка выбора ТС
        if cleaned_data.get('analysis_type') == 'single':
            if not any([
                cleaned_data.get('ice_vehicle'),
                cleaned_data.get('hevv_vehicle'),
                cleaned_data.get('phevv_vehicle'),
                cleaned_data.get('ev_vehicle')
            ]):
                self.add_error(None, "Выберите хотя бы одно транспортное средство")

        return cleaned_data
