import machine
import time

# MQ2 connected to ADC pin (GP26 / GP27 / GP28)
mq2 = machine.ADC(28)

while True:
    raw = mq2.read_u16()   # 0 - 65535

    # Convert to percentage (approx)
    percent = (raw / 65535) * 100

    print("Raw:", raw, "| Approx %:", round(percent, 2))

    time.sleep(1)
