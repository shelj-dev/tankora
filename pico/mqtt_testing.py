import paho.mqtt.client as mqtt
import json
import time
import random

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "tankora/gas_monitor"

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

print("Connected to MQTT Broker!")

while True:
    gas_value = random.randint(8000, 12000)

    leak = 1 if gas_value > 90000 else 0
    
    weight = 40

    payload = {
        "g": gas_value,
        "l": leak,
        "w": weight,
    }

    client.publish(MQTT_TOPIC, json.dumps(payload))

    print("Sent:", payload)

    time.sleep(2)
