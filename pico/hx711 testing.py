# hx711.py
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









import time
from hx711 import HX711

hx = HX711(d_out=4, pd_sck=5)


#hx.set_scale(45000)
hx.set_scale(1)

print("Stabilizing...")
time.sleep(2)

print("Taring...")
hx.tare()
time.sleep(1)

print("Ready...")

def get_stable():
    samples = 5
    total = 0
    for _ in range(samples):
        total += hx.get_units(1)
        time.sleep(0.01)
    return round((total / samples), 2)

while True:
    val = get_stable()
    print("Weight:", val)
    time.sleep(0.3)
    
    
    
