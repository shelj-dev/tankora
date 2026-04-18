import machine
import time
import network
import gc
from umqtt import MQTTClient

# ---------------- CONFIG ---------------- #
WIFI_SSID = 'iot kids'
WIFI_PASSWORD = 'bright kidoos'

MQTT_BROKER = '10.195.245.236'
MQTT_PORT = 1883
MQTT_CLIENT_ID = 'pico_gas_monitor'
MQTT_TOPIC = 'tankora/gas_monitor'

GAS_LEAK_THRESHOLD = 9000
PUBLISH_INTERVAL = 2        # seconds
CHANGE_THRESHOLD = 500      # only send if change > this

# ---------------- HARDWARE ---------------- #
buzzer = machine.Pin(15, machine.Pin.OUT)
relay = machine.Pin(14, machine.Pin.OUT)
gas_sensor = machine.ADC(28)

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
        client.connect()
        mqtt_client = client
        print("MQTT Connected")
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


def handle_alert(leak):
    if leak:
        buzzer.value(1)
        relay.value(1)
    else:
        buzzer.value(0)
        relay.value(0)


# ---------------- MQTT SEND ---------------- #
def publish_data(value, leak):
    global mqtt_client

    if mqtt_client is None:
        return

    try:
        payload = '{"g":%d,"l":%d}' % (value, leak)
        mqtt_client.publish(MQTT_TOPIC, payload)
        print(payload)

    except Exception as e:
        print("Publish failed:", e)
        mqtt_client = None
        gc.collect()


# ---------------- MAIN LOOP ---------------- #
def main():
    global last_value, last_publish_time

    connect_wifi()
    connect_mqtt()

    print("System Started")

    while True:
        try:
            ensure_connections()

            value = read_gas()
            leak = value > GAS_LEAK_THRESHOLD

            handle_alert(leak)

            current_time = time.time()

            # Smart publishing logic
            should_send = False

            if last_value is None:
                should_send = True

            elif abs(value - last_value) > CHANGE_THRESHOLD:
                should_send = True

            elif current_time - last_publish_time >= PUBLISH_INTERVAL:
                should_send = True

            if should_send:
                publish_data(value, leak)
                last_value = value
                last_publish_time = current_time

            print("Gas:", value, "| Leak:", leak)

            gc.collect()
            time.sleep(1)

        except Exception as e:
            print("Main loop error:", e)
            time.sleep(2)
            gc.collect()


# ---------------- START ---------------- #
main()
