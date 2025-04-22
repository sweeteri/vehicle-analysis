from django import forms
from vehicles.models import ICEVehicle, EVVehicle, HEVVehicle, PHEVVehicle, BaseVehicle


class VehicleSelectForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ice_vehicle'].widget.attrs.update({'class': 'form-select w-100'})
        self.fields['hevv_vehicle'].widget.attrs.update({'class': 'form-select w-100'})
        self.fields['phevv_vehicle'].widget.attrs.update({'class': 'form-select w-100'})
        self.fields['ev_vehicle'].widget.attrs.update({'class': 'form-select w-100'})
        self.fields['energy_source'].widget.attrs.update({'class': 'form-select'})
        self.fields['road_type'].widget.attrs.update({'class': 'form-select'})

    ANALYSIS_CHOICES = [
        ('single', 'Анализ одной машины'),
        ('type_avg', 'Сравнение по типу')
    ]

    analysis_type = forms.ChoiceField(
        choices=ANALYSIS_CHOICES,
        widget=forms.RadioSelect,
        label="Тип анализа"
    )

    # Поля для одиночного анализа
    ice_vehicle = forms.ModelChoiceField(
        queryset=ICEVehicle.objects.all(),
        required=False,
        label="ДВС"
    )
    ev_vehicle = forms.ModelChoiceField(
        queryset=EVVehicle.objects.all(),
        required=False,
        label="Электромобиль"
    )
    hevv_vehicle = forms.ModelChoiceField(
        queryset=HEVVehicle.objects.all(),
        required=False,
        label="Гибрид"
    )

    phevv_vehicle = forms.ModelChoiceField(
        queryset=PHEVVehicle.objects.all(),
        required=False,
        label="Заряжаемый Гибрид"
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

    distance_km = forms.FloatField(
        label="Расстояние (км)",
        initial=100,
        min_value=1
    )
    road_type = forms.ChoiceField(
        choices=BaseVehicle.ROAD_TYPES,
        label="Тип дороги"
    )
