from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone



class GasDevice(models.Model):
    device_id = models.CharField(max_length=50, unique=True, help_text="Unique Identifier for the Pico 2W")
    current_level = models.FloatField(default=0.0, help_text="Current gas level percentage (0-100)")
    valve_status = models.CharField(max_length=10, choices=[('OPEN', 'Open'), ('CLOSED', 'Closed')], default='OPEN')
    auto_booking_enabled = models.BooleanField(default=True)
    booking_threshold = models.FloatField(default=15.0, help_text="Percentage below which auto-booking triggers")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices', null=True, blank=True)

    supplier_email = models.EmailField(max_length=255, blank=True, null=True, help_text="Email of the LPG supply center")
    alert_email = models.EmailField(max_length=255, blank=True, null=True, help_text="Email of the security center")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    
    full_weight = models.IntegerField(null=True, blank=True)
    gross_weight = models.IntegerField(null=True, blank=True)
    current_weight = models.IntegerField(null=True, blank=True)
    
    prediction = models.IntegerField(null=True, blank=True)
    average_duration_days = models.IntegerField(default=40, help_text="Average days a full tank lasts")

    last_rebook_sent = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        from app.services import send_rebook_email
        from django.utils import timezone

        trigger_rebook = False
        
        # try:
        #     # percentage = (self.current_weight / self.gross_weight) * 100
        #     percentage = (self.current_weight / (self.full_weight - self.gross_weight)) * 100
        # except:
        #     percentage = 0

        try:
            total_capacity = self.full_weight - self.gross_weight
            if self.gross_weight > self.current_weight:
                gas_balance_percent = 0
            else:
                remaining_gas = self.current_weight - self.gross_weight
                gas_balance_percent = (remaining_gas / total_capacity) * 100 if total_capacity > 0 else 0
                gas_balance_percent = round(gas_balance_percent)
        except:
            gas_balance_percent = 0

        print("percentage:", gas_balance_percent)
        if self.auto_booking_enabled and gas_balance_percent <= self.booking_threshold and self.current_weight is not None:
            trigger_rebook = True

        super().save(*args, **kwargs)

        if trigger_rebook:
            print("Rebook trigger_rebook")
            stat_rebook = send_rebook_email(self)
            print(stat_rebook)
            if stat_rebook:
                print("Rebook send_rebook_email")
                self.last_rebook_sent = timezone.now()
                self.auto_booking_enabled = False
                super().save(update_fields=["last_rebook_sent", "auto_booking_enabled"])
                print("Rebook finished")

    def __str__(self):
        return f"Device {self.device_id} ({self.current_level}%)"
    

class TelemetryLog(models.Model):
    device = models.ForeignKey(GasDevice, on_delete=models.CASCADE, related_name='telemetry')
    level = models.FloatField(help_text="Gas level at the time of reading")
    timestamp = models.DateTimeField(default=timezone.now)
    current_weight = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.device.device_id} - {self.level}% at {self.timestamp}"


class LeakageAlert(models.Model):
    SEVERITY_CHOICES = [
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
    ]
    device = models.ForeignKey(GasDevice, on_delete=models.CASCADE, related_name='alerts')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='HIGH')
    timestamp = models.DateTimeField(default=timezone.now)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Leak in {self.device.device_id} ({self.severity}) - Resolved: {self.resolved}"
