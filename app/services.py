from django.utils import timezone
from datetime import timedelta
from .models import GasDevice, TelemetryLog

def check_auto_booking(device: GasDevice):
    """
    Checks if the gas level is below the threshold and auto-booking is enabled.
    Returns True if an auto-booking was triggered.
    """
    if device.auto_booking_enabled and device.current_level <= device.booking_threshold:
        # Here we would normally integrate with an email/SMS API or the supply center API
        # For now, we will just print to console and maybe we could log an event.
        print(f"AUTO-BOOKING TRIGGERED for Device {device.device_id} at {device.current_level}%")
        # To prevent spam, you'd usually have a "booking_pending" boolean on the device, 
        # so you only book once per refill cycle. Let's assume there's logic here for that.
        return True
    return False

def predict_gas_last_days(device: GasDevice) -> float:
    """
    Calculates the estimated days left based on the gas percentage and average duration.
    Formula: (Gas Percentage / 100) * Average Days
    """
    if not device.average_duration_days:
        average_days = 40
    else:
        average_days = device.average_duration_days
        
    days_left = (device.current_level / 100.0) * average_days
    return round(days_left, 1)


def get_daily_gas_usage(device: GasDevice) -> float:
    now = timezone.now()
    past = now - timedelta(days=2)

    logs = TelemetryLog.objects.filter(
        device=device,
        timestamp__gte=past
    ).order_by('timestamp')


    if logs.count() < 2:
        return 0.0


    first_log = logs.first()
    last_log = logs.last()

    level_diff = first_log.level - last_log.level
    print(level_diff)
    time_diff_days = (last_log.timestamp - first_log.timestamp).total_seconds() / 86400.0

    if level_diff <= 0 or time_diff_days <= 0:
        return 0.0
        
    daily_usage = level_diff / time_diff_days
    
    return round(daily_usage, 2)






from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging


logger = logging.getLogger(__name__)


def send_email() -> bool:
    to_email = "shelj73@gmail.com"
    try:
        html_content = render_to_string("emails/alert.html", {
            "project_name": "Gas Alert Notification",
        })

        msg = EmailMultiAlternatives(
            subject="LPG Testing",
            body=f"",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html_content, "text/html")

        result = msg.send()  # returns 1 on success

        return result == 1  # return True or False

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_alert_email() -> bool:
    device, _ = GasDevice.objects.get_or_create(
            device_id="pico_gas_monitor"
        )

    to_email = device.alert_email

    try:
        html_content = render_to_string("emails/alert.html", {
            "project_name": "Gas Alert Notification",
        })

        msg = EmailMultiAlternatives(
            subject="LPG Alert Email",
            body=f"Emergency Gas Leakage detected",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html_content, "text/html")

        result = msg.send()  # returns 1 on success

        return result == 1  # return True or False

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False
    

def send_rebook_email(device: GasDevice = None) -> bool:
    if device is None:
        device, _ = GasDevice.objects.get_or_create(
                device_id="pico_gas_monitor"
            )

    to_email = device.supplier_email
    if not to_email:
        logger.warning(f"No supplier email set for device {device.device_id}")
        return False
    try:
        html_content = render_to_string("emails/rebook.html", {
            "project_name": "Gas Rebook Notification",
            "device_id": device.device_id,
            "current_level": device.current_level,
        })

        msg = EmailMultiAlternatives(
            subject="LPG Rebooking Request",
            body=f"This is an automated system. Detected low gas level ({device.current_level}%) and requesting rebooking order for device {device.device_id}.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html_content, "text/html")

        result = msg.send()  # returns 1 on success

        return result == 1  # return True or False

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False