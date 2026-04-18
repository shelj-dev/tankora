# import paho.mqtt.client as mqtt
# import json


# MQTT_BROKER = "192.168.1.61"
# MQTT_PORT = 1883
# MQTT_TOPIC = "tankora/gas_monitor"


# def on_connect(client, userdata, flags, rc):
#     print("Connected to MQTT Broker:", rc)
#     client.subscribe(MQTT_TOPIC)


# def on_message(client, userdata, msg):
#     try:
#         payload = msg.payload.decode()
#         data = json.loads(payload)

#         print("Received:", data)

#         gas_level_raw = data.get("gas_level", 0)
#         leak = data.get("leak_detected", False)
        
#         # In dummy it's 1000 to 40000, but normally max is 65535.
#         # Ensure it doesn't cross 100
#         gas_level_percentage = min((gas_level_raw / 65535.0) * 100, 100.0)

#         from app.models import GasDevice, LeakageAlert, TelemetryLog
        
#         device, created = GasDevice.objects.get_or_create(device_id="pico_gas_monitor")
#         device.current_level = gas_level_percentage
#         device.save()

#         TelemetryLog.objects.create(device=device, level=gas_level_percentage)
        
#         if leak:
#             LeakageAlert.objects.get_or_create(device=device, resolved=False, defaults={'severity': 'HIGH'})

#         print(f"Gas: {gas_level_raw} ({gas_level_percentage:.1f}%), Leak: {leak}")

#     except Exception as e:
#         print("Error processing message:", e)


# def start_mqtt():
#     client = mqtt.Client()

#     try:
#         client.on_connect = on_connect
#         client.on_message = on_message

#         client.connect(MQTT_BROKER, MQTT_PORT, 60)
#         client.loop_start()

#         print("MQTT started")

#     except Exception as e:
#         print("MQTT connection failed:", e)
        
        
        
        

import json
import logging
import threading
import paho.mqtt.client as mqtt
from django.utils import timezone
from django.db import close_old_connections
import time


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
    from app.models import GasDevice, TelemetryLog, LeakageAlert

    device, _ = GasDevice.objects.get_or_create(
        device_id="pico_gas_monitor"
    )

    device.current_level = percent
    device.current_weight = weight
    device.last_seen = timezone.now()
    device.save(update_fields=["current_level", "last_seen", "current_weight"])

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
