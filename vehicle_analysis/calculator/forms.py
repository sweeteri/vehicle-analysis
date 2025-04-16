from django import forms
from vehicles.models import ICEVehicle, EVVehicle, HEVVehicle, BaseVehicle


class VehicleSelectForm(forms.Form):
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