"""
# Get datas
    - weight
    - mq2
# Send datas
    - relay bool
    - buzzer bool
    - servo_angle int
"""


import paho.mqtt.client as mqtt
import json
import time
import random

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883

PUB_TOPIC = "tankora/gas_monitor/data"
SUB_TOPIC = "tankora/gas_monitor/control"

# ===== DEVICE STATE =====
relay = 0
buzzer = 0
servo_angle = 0


# ===== ON MESSAGE (RECEIVE CONTROL) =====
def on_message(client, userdata, msg):
    global relay, buzzer, servo_angle

    try:
        data = json.loads(msg.payload.decode())

        relay = data.get("r", relay)
        buzzer = data.get("b", buzzer)
        servo_angle = data.get("s", servo_angle)

        print("Received Control:")
        print("Relay:", relay)
        print("Buzzer:", buzzer)
        print("Servo Angle:", servo_angle)

        time.sleep(1)

    except Exception as e:
        print("Error parsing message:", e)


# ===== MQTT SETUP =====
client = mqtt.Client()
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe(SUB_TOPIC)

print("Connected to MQTT Broker!")

client.loop_start()


# ===== MAIN LOOP (SEND SENSOR DATA) =====
while True:
    # Simulated sensor values
    gas_value = random.randint(8000, 12000)
    weight = random.randint(30, 50)

    payload = {
        "g": gas_value,   # MQ2
        "w": weight       # Weight
    }

    client.publish(PUB_TOPIC, json.dumps(payload))

    print("Sent:", payload)

    time.sleep(1)
