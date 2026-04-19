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

    last_rebook_sent = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        from app.services import send_rebook_email

        trigger_rebook = False

        # check condition BEFORE saving
        if self.auto_booking_enabled and self.current_level <= self.booking_threshold:
            # prevent repeated emails (cooldown logic)
            if not self.last_rebook_sent or (timezone.now() - self.last_rebook_sent).seconds > 3600:
                trigger_rebook = True

        super().save(*args, **kwargs)

        if trigger_rebook:
            if send_rebook_email():
                self.last_rebook_sent = timezone.now()
                super().save(update_fields=["last_rebook_sent"])

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
