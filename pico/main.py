from machine import Pin
import time

class HX711:
    def __init__(self, d_out, pd_sck, gain=128):
        self.pd_sck = Pin(pd_sck, Pin.OUT)
        self.d_out = Pin(d_out, Pin.IN)

        self.gain = 0
        self.offset = 0
        self.scale = 1

        self.set_gain(gain)

    def is_ready(self):
        return self.d_out.value() == 0

    def set_gain(self, gain):
        if gain == 128:
            self.gain = 1
        elif gain == 64:
            self.gain = 3
        elif gain == 32:
            self.gain = 2

        self.pd_sck.value(0)
        self.read()

    def read(self):
        while not self.is_ready():
            time.sleep_us(10)

        count = 0

        for _ in range(24):
            self.pd_sck.value(1)
            count = count << 1
            self.pd_sck.value(0)

            if self.d_out.value():
                count += 1

        # Set channel and gain
        for _ in range(self.gain):
            self.pd_sck.value(1)
            self.pd_sck.value(0)

        # Convert to signed value
        if count & 0x800000:
            count |= ~0xffffff

        return count

    def read_average(self, times=5):
        total = 0
        for _ in range(times):
            total += self.read()
        return total / times

    def tare(self, times=15):
        self.offset = self.read_average(times)

    def set_scale(self, scale):
        self.scale = scale

    def get_units(self, times=5):
        value = self.read_average(times)
        return (value - self.offset) / self.scale

    def power_down(self):
        self.pd_sck.value(0)
        self.pd_sck.value(1)
        time.sleep_us(60)

    def power_up(self):
        self.pd_sck.value(0)


import machine
import time
import network
import gc
import json
from umqtt import MQTTClient

# ---------------- CONFIG ---------------- #
WIFI_SSID = 'FOXTECH'
WIFI_PASSWORD = 'Foxtechajalad'

MQTT_BROKER = '192.168.1.61'
MQTT_PORT = 1883
MQTT_CLIENT_ID = 'pico_gas_monitor'

PUB_TOPIC = 'tankora/gas_monitor'
SUB_TOPIC = 'tankora/pico_gas_monitor/command'

GAS_LEAK_THRESHOLD = 64000
PUBLISH_INTERVAL = 2
CHANGE_THRESHOLD = 500


# ---------------- HARDWARE ---------------- #
buzzer = machine.Pin(15, machine.Pin.OUT)
relay = machine.Pin(14, machine.Pin.OUT)
gas_sensor = machine.ADC(28)


hx = HX711(d_out=4, pd_sck=5)
hx.set_scale(45000)

print("Stabilizing...")
time.sleep(2)

print("Taring...")
hx.tare()
time.sleep(1)

# ---------------- GLOBALS ---------------- #
mqtt_client = None
last_value = None
last_publish_time = 0


# ---------------- WIFI ---------------- #
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1

    if wlan.isconnected():
        print("WiFi OK:", wlan.ifconfig())
        return wlan
    else:
        print("WiFi FAILED")
        return None


# ---------------- MQTT CALLBACK ---------------- #
def on_message(topic, msg):
    print("Received:", msg)

    try:
        data = json.loads(msg)

        command = data.get("command")
        buzzer_cmd = data.get("buzzer")

        # 🔥 VALVE CONTROL FROM DJANGO
        if command == "OPEN_VALVE":
            relay.value(1)
            print("Valve OPEN")

        elif command == "CLOSED_VALVE":
            relay.value(0)
            print("Valve CLOSED")

        # 🔊 BUZZER CONTROL
        if buzzer_cmd == "ON":
            buzzer.value(1)
        elif buzzer_cmd == "OFF":
            buzzer.value(0)

    except Exception as e:
        print("Command error:", e)


# ---------------- MQTT ---------------- #
def connect_mqtt():
    global mqtt_client

    try:
        print("Connecting MQTT...")
        client = MQTTClient(
            MQTT_CLIENT_ID,
            MQTT_BROKER,
            port=MQTT_PORT,
            keepalive=60
        )

        client.set_callback(on_message)
        client.connect()
        client.subscribe(SUB_TOPIC)

        mqtt_client = client
        print("MQTT Connected & Subscribed")

        return True

    except Exception as e:
        print("MQTT Error:", e)
        mqtt_client = None
        gc.collect()
        return False


def ensure_connections():
    wlan = network.WLAN(network.STA_IF)

    if not wlan.isconnected():
        print("WiFi lost. Reconnecting...")
        connect_wifi()

    global mqtt_client
    if mqtt_client is None:
        connect_mqtt()


# ---------------- SENSOR ---------------- #
def read_gas():
    return gas_sensor.read_u16()


def read_weight():
    samples = 5
    total = 0
    for _ in range(samples):
        total += hx.get_units(1)
        time.sleep(0.01)
    return round((total / samples), 2)


def handle_alert(leak):
    if leak:
        buzzer.value(1)
    else:
        buzzer.value(0)


# ---------------- MQTT SEND ---------------- #
def publish_data(value, leak, weight):
    global mqtt_client

    if mqtt_client is None:
        return

    try:
        payload = json.dumps({
            "g": value,
            "l": int(leak),
            "w": weight
        })

        mqtt_client.publish(PUB_TOPIC, payload)
        print(payload)

    except Exception as e:
        print("Publish failed:", e)
        mqtt_client = None
        gc.collect()


# ---------------- MAIN LOOP ---------------- #
def start():
    global last_value, last_publish_time

    connect_wifi()
    connect_mqtt()

    print("System Started")

    while True:
        try:
            ensure_connections()

            if mqtt_client:
                mqtt_client.check_msg()

            value = read_gas()
            weight = read_weight()

            leak = value > GAS_LEAK_THRESHOLD
            
            if leak:
                relay.value(0)

            handle_alert(leak)

            current_time = time.time()

            should_send = False

            if last_value is None:
                should_send = True

            elif abs(value - last_value) > CHANGE_THRESHOLD:
                should_send = True

            elif current_time - last_publish_time >= PUBLISH_INTERVAL:
                should_send = True

            if should_send:
                publish_data(value, leak, weight)
                last_value = value
                last_publish_time = current_time

            print("Gas:", value, "| Leak:", leak, "| Weight:", weight)

            gc.collect()
            time.sleep(1)

        except Exception as e:
            print("Main loop error:", e)
            time.sleep(2)
            gc.collect()


print("Starting")
start()