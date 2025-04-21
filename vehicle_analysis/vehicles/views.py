from django.views.generic import View
from django.shortcuts import render, get_object_or_404
from .models import ICEVehicle, EVVehicle, HEVVehicle


class VehicleListView(View):
    template_name = 'vehicles/list.html'
    context_object_name = 'vehicle_list'

    def get(self, request, *args, **kwargs):
        vehicle_type = request.GET.get('type')
        if vehicle_type == 'ICE':
            vehicles = ICEVehicle.objects.all()
        elif vehicle_type == 'EV':
            vehicles = EVVehicle.objects.all()
        elif vehicle_type == 'HEV':
            vehicles = HEVVehicle.objects.all()
        else:
            vehicles = list(ICEVehicle.objects.all()) + list(EVVehicle.objects.all())

        return render(request, self.template_name, {'vehicles': vehicles})


class VehicleDetailView(View):
    template_name = 'vehicles/detail.html'
    context_object_name = 'vehicle_detail'

    def get(self, request, pk, *args, **kwargs):
        vehicle = None
        for model in [ICEVehicle, EVVehicle]:
            try:
                vehicle = model.objects.get(pk=pk)
                break
            except model.DoesNotExist:
                continue

        if not vehicle:
            raise get_object_or_404(ICEVehicle, pk=pk)

        return render(request, self.template_name, {'vehicle': vehicle})
