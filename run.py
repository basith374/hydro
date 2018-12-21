import serial
import time
import paho.mqtt.client as mqtt
import json
from uuid import getnode as get_mac

ser = serial.Serial('/dev/ttyACM0')
#ser.timeout = 1
mqtt = mqtt.Client()

def send_pin_status():
    try:
        payload = {
                'data': {},
                'type': 'pinstatus'
        }
        #ser = serial.Serial('/dev/ttyACM0')
        #ser.timeout = 1
        ser.write('d') # read_digital
        data = ser.readline().strip()
        if data:
            for i, v in enumerate(data.split(',')):
                payload['data'][str(i)] = v
            print('sending pin status')
            mqtt.publish('/hydroots/client/%d' % get_mac(), bytearray(json.dumps(payload)))
    except Exception as e:
        print('error during read')

def on_message(client, topic, msg):
    if msg == b'':
        print('empty')
        return
    payload = {}
    try:
        payload = json.loads(str(msg.payload))
    except Exception as e:
        print(str(msg.payload))
        print('invalid')
        return
    if 'type' not in payload:
        print('unknown command')
        return
    
    if payload['type'] == 'pinstatus':
        send_pin_status()
    elif payload['type'] == 'changepin':
        if 'data' in payload and type(payload['data']) == dict:
            pins_changed = 0
            try:
                for pin in payload['data']:
                    if type(pin) == str and not str.isdigit(pin): continue
                    ipin = int(pin)
                    pin_val = int(payload['data'][pin])
                    ser.write('s' + chr(ipin) + chr(pin_val))
                    print(ser.readline().strip())
            except Exception as e:
                print('error during write')
            send_pin_status()

mqtt.connect('13.250.41.251')
mqtt.subscribe('/hydroots/server/%d' % get_mac())
mqtt.on_message = on_message
#mqtt.loop_start()

time.sleep(1)
print('init %d' % get_mac())
last_data_time = int(time.time() * 1000)

#send_pin_status()

while True:
    #print('loop')
    try:
        #if last_data_time + 100 < int(time.time() * 1000):
        #ser = serial.Serial('/dev/ttyACM0')
        #ser.timeout = 1
        ser.write('a') # read_analog
        data = ser.readline().strip()
        if data:
            pinvalues = {}
            for i, v in enumerate(data.split(',')):
                pinvalues[str(i)] = v
            payload = {
                    'data': pinvalues,
                    'type': 'sensorvalue'
            }
            mqtt.publish('/hydroots/client/%d' % get_mac(), bytearray(json.dumps(payload)))
        #last_data_time = int(time.time() * 1000)
        print('analog read success')
    except Exception as e:
        data = {'type':'ack'}
        mqtt.publish('/hydroots/client/%d' % get_mac(), bytearray(json.dumps(data)))
        print('exception during read')
    mqtt.loop(timeout=1)
    time.sleep(1)
