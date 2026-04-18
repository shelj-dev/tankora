from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('toggle_valve/<str:device_id>/', views.toggle_valve, name='toggle_valve'),
    path('api/update/', views.update_sensor_data, name='update_sensor_data'),
    path('api/dashboard-data/', views.dashboard_data, name='dashboard_data'),
]
