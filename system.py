import time
import network
import machine
from umqtt.robust import MQTTClient
import ubinascii
import ujson as json
import socket
import sys

last_send_time = time.time()

machineid = int.from_bytes(machine.unique_id(), 4)

print('init %d' % machineid)

ssid = 'Area51'
psk = 'badsector99'
CONFIG = {
    'broker': '13.250.41.251',
    'client_id': b'esp8266_' + ubinascii.hexlify(machine.unique_id())
    # 'client_id': machineid
}

# missing pins 6,7,8,11

analog_control_pins = [
    16, # D0 deepsleep
    5,  # D1
    4,  # D2
]

digital_out_pins = [
    0,  # D3 flash
    2,  # D4 tied to vcc
    14, # D5
    12, # D6
    13, # D7
    15, # D8 tied to gnd
    # 1,  # TX dont touch
    # 3,  # RX
    # 9,  # SD2
    # 10, # SD3
]

intervals = {
    'data': 5 * 60 * 60 * 1000
}

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(ssid, psk)
while not sta.isconnected():
    pass

print('wifi connected')

try:
    socket.getaddrinfo('micropython.org', 80)
    print('internet connected')
except Exception as e:
    # no internet
    machine.reset()

client = MQTTClient(CONFIG['client_id'], CONFIG['broker'])
try:
    client.connect()
except Exception as e:
    # mqtt lib error
    machine.reset()

def read_from(pin):
    pin_val = '{0:03b}'.format(pin)
    for i in range(len(analog_control_pins)):
        machine.Pin(analog_control_pins[i], machine.Pin.OUT).value(int(pin_val[i]))
    return machine.ADC(0).read()

def check_data_send():
    global last_send_time
    # threshold = last_send_time + 5 * 60 * 60
    threshold = last_send_time + 5
    if time.time() > threshold:
        print('sending data')
        data = {}
        for i in range(8):
            data[str(i)] = read_from(i)
        print(data)
        payload = bytearray(json.dumps({'data':data,'type':'sensorvalue'}))
        client.publish('{}/{}'.format('/hydroots/client', machineid), payload)
        last_send_time = time.time()

def send_pin_status():
    data = {}
    for i in range(max(6, len(digital_out_pins))):
        data[str(i)] = machine.Pin(digital_out_pins[i]).value()
    payload = {'data':data,'type':'pinstatus'}
    client.publish('{}/{}'.format('/hydroots/client', machineid), bytearray(json.dumps(payload)))

def on_mqtt_msg(topic, msg):
    print('mqtt received')
    if msg == b'':
        print('empty received')
        return
    payload = {}
    try:
        payload = json.loads(msg)
    except Exception as e:
        print(msg)
        print('invalid received')
        return
    print(payload)
    
    if 'type' not in payload:
        print('unknown command')
        return

    if payload['type'] == 'pinstatus': 
        send_pin_status()
    elif payload['type'] == 'changepin':
        if 'data' in payload and type(payload['data']) == dict:
            pins_changed = 0
            for pin in payload['data']:
                if type(pin) == str and not str.isdigit(pin): continue
                ipin = int(pin)
                if ipin < len(digital_out_pins):
                    pin_val = int(payload['data'][pin])
                    machine.Pin(digital_out_pins[ipin], machine.Pin.OUT).value(pin_val)
                    pins_changed += 1
            if pins_changed: send_pin_status()
        
send_pin_status()
client.set_callback(on_mqtt_msg)
channel = '{}/{}'.format('/hydroots/server', machineid)
client.subscribe(channel)
print('subscribed', channel)

if __name__ == '__main__':
    while True:
        print('looping')
        check_data_send()
        client.check_msg()
        time.sleep(1)