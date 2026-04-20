import json
import logging
import threading
import paho.mqtt.client as mqtt
from django.utils import timezone
from django.db import close_old_connections
import time

from app.services import get_daily_gas_usage, predict_gas_last_days, send_alert_email, send_email
from app.models import GasDevice, TelemetryLog, LeakageAlert


logger = logging.getLogger(__name__)

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "tankora/gas_monitor"

client = None
mqtt_thread_started = False


# ---------------- MQTT CALLBACKS ---------------- #
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("MQTT Connected")
        client.subscribe(MQTT_TOPIC)
    else:
        logger.error(f"MQTT Connection failed: {rc}")


def on_disconnect(client, userdata, rc):
    logger.warning("MQTT Disconnected. Reconnecting...")


def on_message(client, userdata, msg):
    # IMPORTANT: avoid DB connection issues in threads
    close_old_connections()

    try:
        data = json.loads(msg.payload.decode())

        raw = data.get("g", 0)
        leak = data.get("l", False)
        weight = data.get("w", 0)

        percent = min((raw / 65535.0) * 100, 100.0)
        
        print(percent, leak, weight)

        process_sensor_data(percent, leak, weight)

    except Exception as e:
        logger.exception(f"MQTT message error: {e}")


# ---------------- BUSINESS LOGIC ---------------- #
def process_sensor_data(percent, leak, weight):

    device, _ = GasDevice.objects.get_or_create(
        device_id="pico_gas_monitor"
    )

    device.current_level = percent
    device.current_weight = weight
    device.last_seen = timezone.now()

    device.prediction = get_daily_gas_usage(device)
    
    device.save(update_fields=["current_level", "last_seen", "current_weight", "prediction"])

    TelemetryLog.objects.create(
        device=device,
        level=percent,
        current_weight=weight
    )

    # Prevent duplicate alerts
    if leak:
        if not LeakageAlert.objects.filter(device=device, resolved=False).exists():
            LeakageAlert.objects.create(
                device=device,
                severity="HIGH"
            )
            device.valve_status = "CLOSED"
            device.save()
            if device.supplier_email:
                send_alert_email()

    logger.info(f"Data saved: {percent:.2f}% | Leak: {leak}")


# ---------------- MQTT START ---------------- #
def mqtt_loop():
    global client

    while True:
        try:
            client = mqtt.Client()

            client.on_connect = on_connect
            client.on_message = on_message
            client.on_disconnect = on_disconnect

            print("Connecting MQTT...")
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

            client.loop_forever()

        except Exception as e:
            print("MQTT retry after error:", e)
            time.sleep(5)


def start_mqtt():
    global mqtt_thread_started

    if mqtt_thread_started:
        return

    mqtt_thread_started = True

    thread = threading.Thread(target=mqtt_loop, daemon=True)
    thread.start()

    logger.info("MQTT background thread started")


def mqtt_toggle_valve():
    global client

    if client is None:
        print("MQTT not connected")
        return

    try:
        device, _ = GasDevice.objects.get_or_create(
            device_id="pico_gas_monitor"
        )

        if device.valve_status == "CLOSED":
            command = "OPEN_VALVE"
        else:
            command = "CLOSED_VALVE"

        payload = json.dumps({
            "command": command,
            "buzzer": "OFF"
        })

        topic = f"tankora/{device.device_id}/command"

        client.publish(topic, payload)

        print(f"MQTT sent: {payload} → {topic}")

    except Exception as e:
        print("MQTT publish error:", e)