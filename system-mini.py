import time
import json
import ubinascii
from umqtt.simple import MQTTClient
import machine

CONFIG = {
    # 'broker': '13.250.41.251',
    'broker': '192.168.0.110',
    'client_id': b'esp8266_' + ubinascii.hexlify(machine.unique_id())
}

client = MQTTClient(CONFIG['client_id'], CONFIG['broker'])
client.connect()

while True:
    topic = '/hydroots/+'
    msg = {}
    msg = bytearray(json.dumps(msg))
    client.publish(topic, msg)
    time.sleep(1)