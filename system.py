import time
import network
import machine
from umqtt.simple import MQTTClient
import ubinascii
import ujson as json
import socket
import sys

machineid = int.from_bytes(machine.unique_id(), 4)

print('init %d' % machineid)

ssid = 'Area51'
psk = 'badsector99'
CONFIG = {
    'broker': '13.250.41.251',
    'client_id': b'esp8266_' + ubinascii.hexlify(machine.unique_id())
    # 'client_id': machineid
}

pins = [
    16, # D0
    5,  # D1
    4,  # D2
    0,  # D3
    2,  # D4
    14, # D5
    12, # D6
    13, # D7
    15, # D8
    1,  # TX
    3,  # RX
    9,  # SDD2
    10, # SDD3
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
    print('no internet')
    machine.reset()

client = MQTTClient(CONFIG['client_id'], CONFIG['broker'])
client.connect()

def read_from(pin):
    pin_val = '{0:03b}'.format(pin)
    for i in range(3):
        machine.Pin(pins[i], machine.Pin.OUT).value(int(pin_val[i]))
    return machine.ADC(0).read()

def check_data_send():
    threshold = last_send_time + 5 * 60 * 60
    if time.time() > threshold:
        print('sending data')
        data = {}
        for i in range(8):
            data[i] = read_from(i)
        payload = bytearray({'data':data,'type':'sensorvalue'})
        client.publish('{}/{}'.format('/hydroots/client', machineid), payload)

def on_mqtt_msg(topic, msg):
    print('mqtt received')
    if msg == b'':
        print('empty received')
        return
    payload = {'type': None}
    try:
        payload = json.loads(msg)
    except Exception as e:
        print(msg)
        print('invalid received')
        return
    print(payload)
    _pins = pins[3:]
    def send_pin_status():
        data = {}
        for i in range(6):
            data[i] = machine.Pin(_pins[i]).value()
        payload = {'data':data,'type':'pinstatus'}
        client.publish('{}/{}'.format('/hydroots/client', machineid), bytearray(json.dumps(payload)))
    
    if payload['type'] == 'pinstatus':
        send_pin_status()
    elif payload['type'] == 'changepin':
        for pin in payload['data']:
            pin_val = int(payload['data'][pin])
            pin = int(pin)
            machine.Pin(_pins[pin], machine.Pin.OUT).value(pin_val)
        send_pin_status()
        

client.set_callback(on_mqtt_msg)
channel = '{}/{}'.format('/hydroots/server', machineid)
client.subscribe(channel)
print('subscribed', channel)

last_send_time = 0
while True:
    check_data_send()
    client.check_msg()
    time.sleep(1)