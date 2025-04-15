from django.shortcuts import render, get_object_or_404
from .models import ICEVehicle, EVVehicle


def vehicle_list(request):
    vehicles = []

    # Добавляем все типы авто в один список
    vehicles.extend(ICEVehicle.objects.all())
    vehicles.extend(EVVehicle.objects.all())

    # Фильтрация по типу
    vehicle_type = request.GET.get('type')
    if vehicle_type == 'ICE':
        vehicles = ICEVehicle.objects.all()
    elif vehicle_type == 'EV':
        vehicles = EVVehicle.objects.all()

    return render(request, 'vehicles/list.html', {'vehicles': vehicles})


def vehicle_detail(request, pk):
    # Пробуем найти авто в каждой модели
    vehicle = None
    for model in [ICEVehicle, EVVehicle]:
        try:
            vehicle = model.objects.get(pk=pk)
            break
        except model.DoesNotExist:
            continue

    if not vehicle:
        raise get_object_or_404("Автомобиль не найден")

    return render(request, 'vehicles/detail.html', {'vehicle': vehicle})
