import json
import logging
import threading
import paho.mqtt.client as mqtt
from django.utils import timezone
from django.db import close_old_connections
import time

from app.services import get_daily_gas_usage, predict_gas_last_days, send_alert_email, send_email
from app.models import GasDevice, TelemetryLog, LeakageAlert
from main.settings import GAS_THRESHOLD_PERCENTAGE


logger = logging.getLogger(__name__)

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "tankora/gas_monitor/data"
MQTT_SUB_TOPIC = "tankora/gas_monitor/control"

client = None
mqtt_thread_started = False


# ---------------- MQTT CALLBACKS ---------------- #
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("MQTT Connected")
        client.subscribe(MQTT_TOPIC)
        client.subscribe(MQTT_SUB_TOPIC)
    else:
        logger.error(f"MQTT Connection failed: {rc}")


def on_disconnect(client, userdata, rc):
    logger.warning("MQTT Disconnected. Reconnecting...")


def on_message(client, userdata, msg):
    # IMPORTANT: avoid DB connection issues in threads
    close_old_connections()

    try:
        data = json.loads(msg.payload.decode())

        gas = data.get("g", 0)
        weight = data.get("w", 0)

        percent = round(min((gas / 65535.0) * 100, 100.0))
        
        print(percent, weight)

        process_sensor_data(percent, weight)

    except Exception as e:
        logger.exception(f"MQTT message error: {e}")




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


def mqtt_send_value():
    global client

    if client is None:
        print("MQTT not connected")
        return

    try:
        device, _ = GasDevice.objects.get_or_create(
            device_id="pico_gas_monitor"
        )

        payload = json.dumps({
            "r": True,
            "b": True,
            "s": 180
        })


        client.publish(MQTT_SUB_TOPIC, payload)

        print(f"MQTT sent: {payload} → {MQTT_TOPIC}")

    except Exception as e:
        print("MQTT publish error:", e)





# ---------------- BUSINESS LOGIC ---------------- #
def process_sensor_data(percent, weight):

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
    
    leak = True if percent < GAS_THRESHOLD_PERCENTAGE else False

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
