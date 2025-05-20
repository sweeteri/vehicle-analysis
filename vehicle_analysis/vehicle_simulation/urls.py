from django.urls import path
from . import views
from django.views import View
from django.http import JsonResponse


class TestPostView(View):
    def post(self, request):
        print("Получен POST-запрос! Данные:", request.POST)
        return JsonResponse({'status': 'success', 'data': dict(request.POST)})


app_name = 'vehicle_simulation'

urlpatterns = [
    path('', views.SimulationView.as_view(), name='simulate'),
    path('test-post/', TestPostView.as_view(), name='test_post')
]
