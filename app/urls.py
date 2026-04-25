from django.urls import path
from . import views


urlpatterns = [
    # path('', views.dashboard, name='dashboard'),
    path('', views.custom_login, name='dashboard'),
    # path('new/', views.new_dashboard, name='new_dashboard'),
    path('toggle_valve/<str:device_id>/', views.toggle_valve, name='toggle_valve'),
    # path('api/update/', views.update_sensor_data, name='update_sensor_data'),
    path('api/dashboard-data/', views.dashboard_data, name='dashboard_data'),
    path('testing/', views.testing_email, name="testing"),
    path('rebook/', views.rebook, name="rebook"),

    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    path('gas-devices/', views.gas_devices_list, name='gas_devices_list'),
    path('gas-devices/edit/<int:device_id>/', views.gas_device_edit, name='gas_device_edit'),
    
    path('leakage-alerts/', views.leakage_alerts, name='leakage_alerts'),
    path('leakage-alerts/resolve/<int:alert_id>/', views.resolve_alert, name='resolve_alert'),
    path('telemetry-logs/', views.telemetry_logs, name='telemetry_logs'),
]
