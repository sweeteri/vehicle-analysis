from django.urls import path
from . import views

app_name = 'vehicle_simulation'

urlpatterns = [
    path('', views.SimulationView.as_view(), name='simulate'),
]