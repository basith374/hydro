import machine
import time

adc = machine.ADC(0)

def set_pin(no):
pins = '{0:03b}'.format(no)
machine.Pin(5, machine.Pin.OUT).value(int(pins[2])) # D1 - s0
machine.Pin(4, machine.Pin.OUT).value(int(pins[1])) # D2 - s1
machine.Pin(0, machine.Pin.OUT).value(int(pins[0])) # D3 - s2

def get_pin():
pin1 = machine.Pin(5).value()
pin2 = machine.Pin(4).value()
pin3 = machine.Pin(0).value()
pp = 'S0-%d,S1-%d,S2-%d' % (pin1, pin2, pin3)
val = '%d%d%d' % (pin3, pin2, pin1)
print(pp, 'Y%d' % int(val, 2))

def read_from(pin):
set_pin(pin)
print(adc.read())

def read_all(s):
for i in range(8):
set_pin(i)
time.sleep(s)
print(i, adc.read())

def keep_reading():
while(True):
val = []
for i in range(8):
set_pin(i)
time.sleep(1)
val.append(adc.read())
print(val)
time.sleep(1)