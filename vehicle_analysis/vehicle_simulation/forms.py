from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime

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
        queryset=None,
        required=False,
        label='ДВС',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    hevv_vehicle = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='Гибрид (HEV)',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    phevv_vehicle = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='Подключаемый гибрид (PHEV)',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    ev_vehicle = forms.ModelChoiceField(
        queryset=None,
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
        })
    )
    end_date = forms.DateField(
        label='Дата окончания',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    daily_hours = forms.FloatField(
        label='Часов эксплуатации в день',
        min_value=0,
        max_value=24,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.5'
        })
    )
    energy_source = forms.ChoiceField(
        choices=[
            ('coal', 'Угольные станции'),
            ('gas', 'Газовые станции'),
            ('nuclear', 'Атомные станции'),
            ('hydro', 'Гидроэнергетика'),
            ('eu_avg', 'Среднее по ЕС'),
        ],
        initial='eu_avg',
        label="Источник электроэнергии"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Устанавливаем queryset'ы
        from vehicles.models import ICEVehicle, HEVVehicle, PHEVVehicle, EVVehicle
        self.fields['ice_vehicle'].queryset = ICEVehicle.objects.all()
        self.fields['hevv_vehicle'].queryset = HEVVehicle.objects.all()
        self.fields['phevv_vehicle'].queryset = PHEVVehicle.objects.all()
        self.fields['ev_vehicle'].queryset = EVVehicle.objects.all()

        # Устанавливаем все типы по умолчанию
        if not self.data:  # Только при GET-запросе
            self.initial['compare_types'] = ['ICE', 'HEV', 'PHEV', 'EV']

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise ValidationError("Дата начала не может быть позже даты окончания")

        # Проверка, что выбрано хотя бы одно ТС в режиме single
        if cleaned_data.get('analysis_type') == 'single':
            vehicle_selected = any([
                cleaned_data.get('ice_vehicle'),
                cleaned_data.get('hevv_vehicle'),
                cleaned_data.get('phevv_vehicle'),
                cleaned_data.get('ev_vehicle')
            ])
            if not vehicle_selected:
                raise ValidationError("Выберите хотя бы одно транспортное средство")

        return cleaned_data
    compare_types = forms.MultipleChoiceField(
        choices=[
            ('ICE', 'ДВС'),
            ('HEV', 'Гибрид'),
            ('PHEV', 'PHEV'),
            ('EV', 'Электро')
        ],
        widget=forms.CheckboxSelectMultiple,
        initial=['ICE', 'HEV', 'PHEV', 'EV']  # Все типы выбраны по умолчанию
    )
