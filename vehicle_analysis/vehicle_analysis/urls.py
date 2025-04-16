from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('vehicles.urls')),
    path('calculator/', include('calculator.urls')),
    path('admin/', admin.site.urls),

]
