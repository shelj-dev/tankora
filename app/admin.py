from django.contrib import admin
from .models import GasDevice, TelemetryLog, LeakageAlert

@admin.register(GasDevice)
class GasDeviceAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'current_level', 'valve_status', 'user', 'auto_booking_enabled')
    search_fields = ('device_id', 'user__username')

@admin.register(TelemetryLog)
class TelemetryLogAdmin(admin.ModelAdmin):
    list_display = ('device', 'level', 'timestamp')
    list_filter = ('device', 'timestamp')

@admin.register(LeakageAlert)
class LeakageAlertAdmin(admin.ModelAdmin):
    list_display = ('device', 'severity', 'resolved', 'timestamp')
    list_filter = ('severity', 'resolved', 'timestamp')

