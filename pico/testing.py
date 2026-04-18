import machine
import time

BUZZER_PIN = 15          # Digital output for Alarm Buzzer
RELAY_PIN = 14           # Digital output for Solenoid Valve (Gas Shut-off)
GAS_SENSOR_PIN = 26      # ADC pin for MQ Gas Sensor (e.g., MQ-2/MQ-6)
LEVEL_SENSOR_PIN = 27    # ADC pin for Gas Level / Load Cell analog input

# Initialize hardware pins
buzzer = machine.Pin(BUZZER_PIN, machine.Pin.OUT)
relay = machine.Pin(RELAY_PIN, machine.Pin.OUT)
gas_sensor = machine.ADC(machine.Pin(GAS_SENSOR_PIN))
level_sensor = machine.ADC(machine.Pin(LEVEL_SENSOR_PIN))


def test_buzzer():
    """Test the buzzer by turning it on for 2 seconds."""
    print("\n--- Testing Buzzer ---")
    print("Buzzer ON")
    buzzer.value(1)
    time.sleep(2)
    buzzer.value(0)
    time.sleep(2)
    print("Buzzer OFF")


def test_relay():
    """Test the relay by toggling it. You should hear a 'click'."""
    print("\n--- Testing Relay (Solenoid Valve) ---")
    print("Relay ON (Valve Closed)")
    relay.value(1)
    time.sleep(2)
    print("Relay OFF (Valve Open)")
    relay.value(0)


def test_gas_sensor(duration_seconds=10):
    """Continuously read from the MQ gas sensor."""
    print(f"\n--- Testing MQ Gas Sensor ({duration_seconds} sec) ---")
    print("Bring a gas lighter (unlit) near the sensor to see values change.")
    for i in range(duration_seconds):
        val = gas_sensor.read_u16()
        print(f"[{i+1}/{duration_seconds}] Gas Raw ADC Value: {val}")
        time.sleep(1)

def test_level_sensor(duration_seconds=10):
    """Continuously read from the analog load cell/level sensor."""
    print(f"\n--- Testing Level Sensor ({duration_seconds} sec) ---")
    print("Apply pressure or weight to the sensor to see values change.")
    for i in range(duration_seconds):
        val = level_sensor.read_u16()
        print(f"[{i+1}/{duration_seconds}] Level Raw ADC Value: {val}")
        time.sleep(1)

def run_all_tests():
    """Run a complete diagnostic sequence of all hardware components."""
    print("=========================================")
    print("  INITIALIZING HARDWARE DIAGNOSTICS      ")
    print("=========================================")
    
    test_buzzer()
    time.sleep(1)
    
    test_relay()
    time.sleep(1)
    
    test_gas_sensor(5)  # Read for 5 seconds
    time.sleep(1)
    
    test_level_sensor(5) # Read for 5 seconds
    
    print("\n=========================================")
    print("  DIAGNOSTICS COMPLETE                   ")
    print("=========================================")

# if __name__ == '__main__':
buzzer.value(0)
relay.value(0)

while True:
    try:
        # Ensure components are off to start
        
        # Uncomment the specific test you want to run, 
        # or leave run_all_tests() uncommented to test everything in sequence.
        
        test_buzzer()
        
    except Exception as e:
        print(e)
